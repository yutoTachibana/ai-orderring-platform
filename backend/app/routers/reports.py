import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.automation import ReportSchedule
from app.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportScheduleCreate,
    ReportScheduleUpdate,
    ReportScheduleResponse,
)
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter()

REPORT_DIR = "/app/uploads/reports"


@router.post("/generate", summary="レポート生成")
def generate_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """指定した年月のレポートをExcelで生成してダウンロードする。"""
    from workers.report_generator import ReportGenerator

    generator = ReportGenerator()

    if req.report_type == "monthly_summary":
        excel_bytes = generator.generate_monthly_summary(req.year, req.month, db=db)
    else:
        raise HTTPException(status_code=400, detail=f"未対応のレポートタイプ: {req.report_type}")

    file_name = f"report_{req.report_type}_{req.year}_{req.month:02d}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/types", summary="レポートタイプ一覧")
def list_report_types(
    current_user: User = Depends(get_current_user),
):
    """利用可能なレポートタイプを返す。"""
    return [
        {
            "type": "monthly_summary",
            "label": "月次サマリーレポート",
            "description": "案件・契約・請求・ジョブ実績の月次集計",
        },
    ]


# --- スケジュール CRUD ---


@router.get("/schedules", summary="スケジュール一覧")
def list_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedules = db.query(ReportSchedule).all()
    return {"items": schedules, "total": len(schedules)}


@router.post(
    "/schedules",
    response_model=ReportScheduleResponse,
    status_code=201,
    summary="スケジュール作成",
)
def create_schedule(
    req: ReportScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = ReportSchedule(**req.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.put(
    "/schedules/{schedule_id}",
    response_model=ReportScheduleResponse,
    summary="スケジュール更新",
)
def update_schedule(
    schedule_id: int,
    req: ReportScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/generate-async", summary="レポート非同期生成")
def generate_report_async(
    req: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """レポートをCeleryで非同期生成する。タスクIDを返す。"""
    try:
        from workers.tasks import generate_report_task
        result = generate_report_task.delay(req.report_type, req.year, req.month)
        return {"task_id": result.id, "status": "PENDING"}
    except Exception:
        raise HTTPException(status_code=503, detail="非同期タスクキューが利用できません")


@router.delete("/schedules/{schedule_id}", status_code=204, summary="スケジュール削除")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")
    db.delete(schedule)
    db.commit()
