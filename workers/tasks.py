"""追加Celeryタスク: レポート生成・入金消込・請求書PDF処理"""
from celery import shared_task

from app.database import SessionLocal
from app.models.automation import ProcessingJob, ProcessingLog, JobStatus


def _add_log(db, job_id: int, step: str, status: str, message: str):
    log = ProcessingLog(
        job_id=job_id,
        step_name=step,
        status=status,
        message=message,
    )
    db.add(log)
    db.commit()


@shared_task(name="workers.generate_report")
def generate_report_task(report_type: str, year: int, month: int) -> dict:
    """レポートを非同期で生成してファイルに保存する。"""
    import os
    from workers.report_generator import ReportGenerator

    db = SessionLocal()
    try:
        generator = ReportGenerator()
        if report_type == "monthly_summary":
            excel_bytes = generator.generate_monthly_summary(year, month, db=db)
        else:
            return {"error": f"未対応のレポートタイプ: {report_type}"}

        report_dir = "/app/uploads/reports"
        os.makedirs(report_dir, exist_ok=True)
        file_name = f"report_{report_type}_{year}_{month:02d}.xlsx"
        file_path = os.path.join(report_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(excel_bytes)

        return {"status": "completed", "file_path": file_path, "file_name": file_name}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="workers.auto_reconcile")
def auto_reconcile_task() -> dict:
    """未消込の入金を自動マッチングする。"""
    from app.models.payment import Payment, PaymentStatus
    from app.services.reconciliation import auto_match_payments

    db = SessionLocal()
    try:
        unmatched = db.query(Payment).filter(Payment.status == PaymentStatus.unmatched).all()
        if not unmatched:
            return {"status": "completed", "matched": 0, "total": 0}

        results = auto_match_payments(db, unmatched)
        matched_count = sum(1 for r in results if r["status"] == "matched")
        return {"status": "completed", "matched": matched_count, "total": len(unmatched)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="workers.process_order_async", bind=True, max_retries=3)
def process_order_async(self, job_id: int) -> dict:
    """承認後の発注登録+Web入力を非同期で実行する。"""
    from app.services.order_registration import register_order_from_job
    from app.services.mcp_executor import execute_mcp_input

    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        job.status = JobStatus.executing
        db.commit()
        _add_log(db, job_id, "order_registration", "started", "発注登録を開始")

        try:
            reg_result = register_order_from_job(db, job)
            _add_log(db, job_id, "order_registration", "completed", f"登録完了: {reg_result}")
        except Exception as e:
            _add_log(db, job_id, "order_registration", "failed", str(e))
            raise

        _add_log(db, job_id, "web_input", "started", f"Web入力を開始: {job.assigned_system}")

        try:
            mcp_result = execute_mcp_input(db, job)
            _add_log(db, job_id, "web_input", "completed", f"Web入力完了")
        except Exception as e:
            _add_log(db, job_id, "web_input", "failed", str(e))
            raise

        job.status = JobStatus.completed
        db.commit()
        return {"status": "completed", "job_id": job_id}

    except Exception as e:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = JobStatus.failed
            job.error_message = f"処理エラー: {e}"
            db.commit()
        try:
            self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {"error": str(e), "job_id": job_id}
    finally:
        db.close()
