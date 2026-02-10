from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("", summary="請求一覧")
def list_invoices(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    contract_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    if contract_id is not None:
        query = query.filter(Invoice.contract_id == contract_id)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{invoice_id}", response_model=InvoiceResponse, summary="請求詳細")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求が見つかりません")
    return invoice


@router.post("", response_model=InvoiceResponse, status_code=201, summary="請求作成")
def create_invoice(
    req: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = Invoice(**req.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse, summary="請求更新")
def update_invoice(
    invoice_id: int,
    req: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(invoice, key, value)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=204, summary="請求削除")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求が見つかりません")
    db.delete(invoice)
    db.commit()


@router.post("/{invoice_id}/send", response_model=InvoiceResponse, summary="請求送付")
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求が見つかりません")
    if invoice.status != InvoiceStatus.draft:
        raise HTTPException(status_code=400, detail="下書き状態の請求のみ送付できます")
    invoice.status = InvoiceStatus.sent
    invoice.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/pay", response_model=InvoiceResponse, summary="請求支払い")
def pay_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求が見つかりません")
    if invoice.status not in (InvoiceStatus.sent, InvoiceStatus.overdue):
        raise HTTPException(status_code=400, detail="送付済みまたは期限超過の請求のみ支払い処理できます")
    invoice.status = InvoiceStatus.paid
    invoice.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice
