from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentResponse, PaymentManualMatch, ReconciliationSummary
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/import", summary="入金CSVインポート")
def import_bank_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """銀行入金CSVをアップロードして入金データを取り込む。"""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSVファイルのみ対応しています")

    from app.services.reconciliation import parse_bank_csv

    raw = file.file.read()
    # Try UTF-8 first, then Shift-JIS
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("shift_jis", errors="replace")

    entries = parse_bank_csv(content)
    if not entries:
        raise HTTPException(status_code=422, detail="入金データが見つかりませんでした")

    created = []
    for entry in entries:
        payment = Payment(
            payment_date=entry["payment_date"],
            amount=entry["amount"],
            payer_name=entry.get("payer_name"),
            reference_number=entry.get("reference_number"),
            bank_name=entry.get("bank_name"),
        )
        db.add(payment)
        db.flush()
        created.append(payment)

    db.commit()
    for p in created:
        db.refresh(p)

    return {
        "imported_count": len(created),
        "payments": [
            {
                "id": p.id,
                "payment_date": str(p.payment_date),
                "amount": p.amount,
                "payer_name": p.payer_name,
                "status": p.status.value,
            }
            for p in created
        ],
    }


@router.post("/match", summary="自動消込実行")
def run_auto_match(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """未消込の入金を請求書に自動マッチングする。"""
    from app.services.reconciliation import auto_match_payments

    unmatched = db.query(Payment).filter(Payment.status == PaymentStatus.unmatched).all()
    if not unmatched:
        return {"message": "未消込の入金データがありません", "results": []}

    results = auto_match_payments(db, unmatched)
    matched_count = sum(1 for r in results if r["status"] == "matched")
    return {
        "message": f"{len(unmatched)}件中{matched_count}件をマッチングしました",
        "results": results,
    }


@router.get("", summary="入金一覧")
def list_payments(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    total = query.count()
    items = query.order_by(Payment.payment_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "invoice_number": p.invoice.invoice_number if p.invoice else None,
                "payment_date": str(p.payment_date),
                "amount": p.amount,
                "payer_name": p.payer_name,
                "reference_number": p.reference_number,
                "bank_name": p.bank_name,
                "status": p.status.value,
                "notes": p.notes,
            }
            for p in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/summary", response_model=ReconciliationSummary, summary="消込サマリー")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_payments = db.query(Payment).all()
    total = len(all_payments)
    matched = sum(1 for p in all_payments if p.status == PaymentStatus.matched)
    unmatched = sum(1 for p in all_payments if p.status == PaymentStatus.unmatched)
    confirmed = sum(1 for p in all_payments if p.status == PaymentStatus.confirmed)
    total_amount = sum(p.amount for p in all_payments)
    matched_amount = sum(p.amount for p in all_payments if p.status in (PaymentStatus.matched, PaymentStatus.confirmed))

    return ReconciliationSummary(
        total_payments=total,
        matched=matched,
        unmatched=unmatched,
        confirmed=confirmed,
        total_amount=total_amount,
        matched_amount=matched_amount,
    )


@router.post("/{payment_id}/match", summary="手動消込")
def manual_match(
    payment_id: int,
    req: PaymentManualMatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """入金を手動で特定の請求書に紐付ける。"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="入金データが見つかりません")

    invoice = db.query(Invoice).filter(Invoice.id == req.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求書が見つかりません")

    payment.invoice_id = invoice.id
    payment.status = PaymentStatus.matched
    db.commit()
    db.refresh(payment)
    return {"message": "マッチングしました", "payment_id": payment.id, "invoice_id": invoice.id}


@router.post("/{payment_id}/confirm", summary="消込確定")
def confirm_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """マッチング済みの入金を確定し、請求書を入金済みにする。"""
    from app.services.reconciliation import confirm_match

    try:
        payment = confirm_match(db, payment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "消込を確定しました", "payment_id": payment.id, "status": payment.status.value}


@router.post("/{payment_id}/unmatch", summary="消込取消")
def unmatch_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """マッチングを取り消す。"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="入金データが見つかりません")
    if payment.status == PaymentStatus.confirmed:
        raise HTTPException(status_code=400, detail="確定済みの消込は取り消せません")

    payment.invoice_id = None
    payment.status = PaymentStatus.unmatched
    db.commit()
    return {"message": "マッチングを取り消しました", "payment_id": payment.id}
