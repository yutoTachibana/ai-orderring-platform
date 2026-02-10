"""入金消込: 入金データと請求データを照合"""
from datetime import date
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.invoice import Invoice, InvoiceStatus


@dataclass
class PaymentRecord:
    date: date
    amount: int
    payer_name: str
    reference: str = ""


@dataclass
class ReconciliationResult:
    matched: list[tuple]  # (payment, invoice)
    unmatched_payments: list[PaymentRecord]
    unmatched_invoices: list
    total_matched_amount: int = 0


class PaymentReconciliation:
    """入金データと請求書を照合する"""

    def reconcile(self, payments: list[PaymentRecord], db: Session | None = None) -> ReconciliationResult:
        """入金データと未入金請求書をマッチングする"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            unpaid_invoices = (
                db.query(Invoice)
                .filter(Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue]))
                .all()
            )

            matched = []
            unmatched_payments = []
            matched_invoice_ids = set()

            for payment in payments:
                best_match = None
                for inv in unpaid_invoices:
                    if inv.id in matched_invoice_ids:
                        continue
                    if inv.total_amount == payment.amount:
                        best_match = inv
                        break

                if best_match:
                    matched.append((payment, best_match))
                    matched_invoice_ids.add(best_match.id)
                else:
                    unmatched_payments.append(payment)

            unmatched_invoices = [inv for inv in unpaid_invoices if inv.id not in matched_invoice_ids]
            total_matched = sum(p.amount for p, _ in matched)

            return ReconciliationResult(
                matched=matched,
                unmatched_payments=unmatched_payments,
                unmatched_invoices=unmatched_invoices,
                total_matched_amount=total_matched,
            )
        finally:
            if should_close:
                db.close()

    def apply_matches(self, result: ReconciliationResult, db: Session | None = None) -> int:
        """マッチング結果を適用して請求書を入金済みにする"""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            from datetime import datetime, timezone
            count = 0
            for payment, invoice in result.matched:
                invoice.status = InvoiceStatus.paid
                invoice.paid_at = datetime.now(timezone.utc)
                count += 1
            db.commit()
            return count
        finally:
            if should_close:
                db.close()
