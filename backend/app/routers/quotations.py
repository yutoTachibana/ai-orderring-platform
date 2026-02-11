from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.engineer import Engineer
from app.models.project import Project
from app.models.quotation import Quotation, QuotationStatus
from app.schemas.quotation import QuotationCreate, QuotationUpdate, QuotationResponse
from app.services.tier_eligibility import validate_engineer_eligibility
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter()


@router.get("", summary="見積一覧")
def list_quotations(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    project_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(Quotation)
    if status:
        base_query = base_query.filter(Quotation.status == status)
    if project_id is not None:
        base_query = base_query.filter(Quotation.project_id == project_id)
    total = base_query.count()
    items = base_query.options(
        joinedload(Quotation.project),
        joinedload(Quotation.engineer),
    ).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{quotation_id}", response_model=QuotationResponse, summary="見積詳細")
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    return quotation


@router.post("", response_model=QuotationResponse, status_code=201, summary="見積作成")
def create_quotation(
    req: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engineer = db.query(Engineer).filter(Engineer.id == req.engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")
    try:
        validate_engineer_eligibility(engineer, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    quotation = Quotation(**req.model_dump())
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.put("/{quotation_id}", response_model=QuotationResponse, summary="見積更新")
def update_quotation(
    quotation_id: int,
    req: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quotation, key, value)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.delete("/{quotation_id}", status_code=204, summary="見積削除")
def delete_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    db.delete(quotation)
    db.commit()


@router.post("/{quotation_id}/submit", response_model=QuotationResponse, summary="見積提出")
def submit_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status != QuotationStatus.draft:
        raise HTTPException(status_code=400, detail="下書き状態の見積のみ提出できます")
    quotation.status = QuotationStatus.submitted
    quotation.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.post("/{quotation_id}/approve", response_model=QuotationResponse, summary="見積承認")
def approve_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status != QuotationStatus.submitted:
        raise HTTPException(status_code=400, detail="提出済みの見積のみ承認できます")
    quotation.status = QuotationStatus.approved
    quotation.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(quotation)
    return quotation
