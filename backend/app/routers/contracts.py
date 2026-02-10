from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractType
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("", summary="契約一覧")
def list_contracts(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    engineer_id: int | None = None,
    project_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Contract)
    if status:
        query = query.filter(Contract.status == status)
    if engineer_id is not None:
        query = query.filter(Contract.engineer_id == engineer_id)
    if project_id is not None:
        query = query.filter(Contract.project_id == project_id)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{contract_id}", response_model=ContractResponse, summary="契約詳細")
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="契約が見つかりません")
    return contract


@router.post("", response_model=ContractResponse, status_code=201, summary="契約作成")
def create_contract(
    req: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = Contract(**req.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.put("/{contract_id}", response_model=ContractResponse, summary="契約更新")
def update_contract(
    contract_id: int,
    req: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="契約が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract, key, value)
    db.commit()
    db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=204, summary="契約削除")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="契約が見つかりません")
    db.delete(contract)
    db.commit()
