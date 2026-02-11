"""ジョブプロセッサ: Celeryタスクとして自動化パイプラインを実行"""
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.automation import ProcessingJob, ProcessingLog, JobStatus
from workers.excel_parser import ExcelParser, ExcelParseError
from workers.routing_engine import RoutingEngine


def _add_log(db: Session, job_id: int, step: str, status: str, message: str, screenshot: str | None = None):
    log = ProcessingLog(
        job_id=job_id,
        step_name=step,
        status=status,
        message=message,
        screenshot_path=screenshot,
    )
    db.add(log)
    db.commit()


@shared_task(name="workers.process_order")
def process_order(job_id: int) -> dict:
    """発注処理パイプラインのメインタスク"""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        # Step 1: Excel解析
        job.status = JobStatus.parsing
        db.commit()
        _add_log(db, job_id, "excel_parse", "started", "Excel解析を開始")

        try:
            parser = ExcelParser()
            result = parser.smart_parse(job.excel_file_path)
            if isinstance(result, list):
                # テーブル形式: 複数レコード → 最初のレコードを使用、全件数を記録
                order_data = result[0] if result else {}
                _add_log(db, job_id, "excel_parse", "completed", f"一覧形式: {len(result)}件検出、{len(order_data)}フィールド抽出")
                job.result = {"all_records": [{k: str(v) for k, v in r.items()} for r in result]}
                db.commit()
            else:
                order_data = result
                _add_log(db, job_id, "excel_parse", "completed", f"仕様書形式: {len(order_data)}フィールド抽出")
        except ExcelParseError as e:
            job.status = JobStatus.failed
            job.error_message = str(e)
            db.commit()
            _add_log(db, job_id, "excel_parse", "failed", str(e))
            return {"error": str(e)}

        # Step 2: 振り分け判定
        job.status = JobStatus.routing
        db.commit()
        _add_log(db, job_id, "routing", "started", "振り分け判定を開始")

        engine = RoutingEngine(db)
        target = engine.determine_target(order_data)

        if target:
            job.assigned_system = target
            _add_log(db, job_id, "routing", "completed", f"振り分け先: {target}")
        else:
            job.assigned_system = None
            _add_log(db, job_id, "routing", "manual_required", "自動振り分け不可。手動振り分けが必要です")

        # Step 3: 承認待ち
        job.status = JobStatus.pending_approval
        job.result = {"order_data": {k: str(v) for k, v in order_data.items()}}
        db.commit()
        _add_log(db, job_id, "approval", "waiting", "承認待ち")

        return {"status": "pending_approval", "target": target, "job_id": job_id}

    finally:
        db.close()


@shared_task(name="workers.execute_web_input")
def execute_web_input(job_id: int) -> dict:
    """承認後のWeb入力実行タスク"""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        job.status = JobStatus.executing
        db.commit()
        _add_log(db, job_id, "web_input", "started", f"Web入力を開始: {job.assigned_system}")

        try:
            # MCP経由でWebシステムに入力 (モック)
            from mcp_servers.common.mcp_base import MockMCPClient
            client = MockMCPClient(job.assigned_system or "system_a")
            result = client.execute_order_input(job.result.get("order_data", {}))

            job.status = JobStatus.completed
            job.result = {**(job.result or {}), "web_result": result}
            db.commit()
            _add_log(db, job_id, "web_input", "completed", f"Web入力完了: {result.get('order_number', 'N/A')}", result.get("screenshot_path"))

            return {"status": "completed", "result": result}

        except Exception as e:
            job.status = JobStatus.failed
            job.error_message = str(e)
            db.commit()
            _add_log(db, job_id, "web_input", "failed", str(e))
            return {"error": str(e)}

    finally:
        db.close()
