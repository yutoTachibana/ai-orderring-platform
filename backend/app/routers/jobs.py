from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.automation import ProcessingJob, JobStatus
from app.schemas.job import JobResponse, JobApproveRequest
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("", summary="処理ジョブ一覧")
def list_jobs(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcessingJob)
    if status:
        query = query.filter(ProcessingJob.status == status)
    query = query.order_by(ProcessingJob.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
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

    if req.approved:
        job.status = JobStatus.executing
    else:
        job.status = JobStatus.failed
        job.error_message = "承認が却下されました"

    job.approved_by = current_user.id
    job.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job
