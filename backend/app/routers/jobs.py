from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.automation import ProcessingJob, ProcessingLog, JobStatus
from app.schemas.job import JobResponse, JobApproveRequest
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("", summary="処理ジョブ一覧")
def list_jobs(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    base_query = db.query(ProcessingJob)
    if status:
        base_query = base_query.filter(ProcessingJob.status == status)
    base_query = base_query.order_by(ProcessingJob.created_at.desc())
    total = base_query.count()
    items = base_query.options(
        joinedload(ProcessingJob.logs),
    ).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{job_id}", response_model=JobResponse, summary="処理ジョブ詳細")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="処理ジョブが見つかりません")
    return job


@router.post("/{job_id}/approve", response_model=JobResponse, summary="処理ジョブ承認")
def approve_job(
    job_id: int,
    req: JobApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="処理ジョブが見つかりません")
    if job.status != JobStatus.pending_approval:
        raise HTTPException(status_code=400, detail="承認待ちのジョブのみ承認できます")

    job.approved_by = current_user.id
    job.approved_at = datetime.now(timezone.utc)

    if req.approved:
        job.status = JobStatus.executing
        db.commit()

        # Celery非同期実行を試行、失敗時は同期実行にフォールバック
        try:
            from workers.tasks import process_order_async
            process_order_async.delay(job_id)
        except Exception:
            # Redis未接続時は同期実行
            from app.services.order_registration import register_order_from_job
            from app.services.mcp_executor import execute_mcp_input
            try:
                register_order_from_job(db, job)
                execute_mcp_input(db, job)
                job.status = JobStatus.completed
                db.commit()
            except Exception as e:
                job.status = JobStatus.failed
                job.error_message = f"処理エラー: {e}"
                db.commit()
    else:
        job.status = JobStatus.failed
        job.error_message = "承認が却下されました"
        db.commit()

    db.refresh(job)
    return job


@router.get("/tasks/{task_id}/status", summary="Celeryタスクステータス")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Celeryタスクの実行状態を返す。"""
    try:
        from app.celery_app import celery
        result = celery.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    except Exception:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "result": None,
        }
