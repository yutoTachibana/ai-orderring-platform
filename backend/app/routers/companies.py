from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.company import Company, CompanyType
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.user import UserRole
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter()


@router.get("", summary="企業一覧")
def list_companies(
    page: int = 1,
    per_page: int = 20,
    company_type: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Company)
    if company_type:
        query = query.filter(Company.company_type == company_type)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{company_id}", response_model=CompanyResponse, summary="企業詳細")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")
    return company


@router.post("", response_model=CompanyResponse, status_code=201, summary="企業作成")
def create_company(
    req: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = Company(**req.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyResponse, summary="企業更新")
def update_company(
    company_id: int,
    req: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204, summary="企業削除")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")
    db.delete(company)
    db.commit()
