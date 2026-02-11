"""入金消込サービス: CSVから入金データを取り込み、請求書と自動照合"""
import csv
import io
import re
import unicodedata
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus


# ---------------------------------------------------------------------------
# Fuzzy matching helpers (module-level, no external dependencies)
# ---------------------------------------------------------------------------

# Mapping table: full-width katakana → half-width katakana
# Built from Unicode charts (U+30A1..U+30F6 → U+FF66..U+FF9D + dakuten/handakuten)
_FULLWIDTH_TO_HALFWIDTH_KANA: dict[str, str] = {
    "ア": "ア", "イ": "イ", "ウ": "ウ", "エ": "エ", "オ": "オ",
    "カ": "カ", "キ": "キ", "ク": "ク", "ケ": "ケ", "コ": "コ",
    "サ": "サ", "シ": "シ", "ス": "ス", "セ": "セ", "ソ": "ソ",
    "タ": "タ", "チ": "チ", "ツ": "ツ", "テ": "テ", "ト": "ト",
    "ナ": "ナ", "ニ": "ニ", "ヌ": "ヌ", "ネ": "ネ", "ノ": "ノ",
    "ハ": "ハ", "ヒ": "ヒ", "フ": "フ", "ヘ": "ヘ", "ホ": "ホ",
    "マ": "マ", "ミ": "ミ", "ム": "ム", "メ": "メ", "モ": "モ",
    "ヤ": "ヤ", "ユ": "ユ", "ヨ": "ヨ",
    "ラ": "ラ", "リ": "リ", "ル": "ル", "レ": "レ", "ロ": "ロ",
    "ワ": "ワ", "ヲ": "ヲ", "ン": "ン",
    "ァ": "ァ", "ィ": "ィ", "ゥ": "ゥ", "ェ": "ェ", "ォ": "ォ",
    "ッ": "ッ", "ャ": "ャ", "ュ": "ュ", "ョ": "ョ",
    "ガ": "ガ", "ギ": "ギ", "グ": "グ", "ゲ": "ゲ", "ゴ": "ゴ",
    "ザ": "ザ", "ジ": "ジ", "ズ": "ズ", "ゼ": "ゼ", "ゾ": "ゾ",
    "ダ": "ダ", "ヂ": "ヂ", "ヅ": "ヅ", "デ": "デ", "ド": "ド",
    "バ": "バ", "ビ": "ビ", "ブ": "ブ", "ベ": "ベ", "ボ": "ボ",
    "パ": "パ", "ピ": "ピ", "プ": "プ", "ペ": "ペ", "ポ": "ポ",
    "ヴ": "ヴ",
    "ー": "ー",
    "。": "。", "「": "「", "」": "」", "、": "、", "・": "・",
}

# Company name prefixes/suffixes to strip for normalization
_COMPANY_PREFIXES = [
    "カ）", "カ)", "(株)", "（株）",
    "株式会社",
    "(有)", "（有）", "ユ）", "ユ)",
    "有限会社",
    "(合)", "（合）",
    "合同会社",
]


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _similarity_ratio(s1: str, s2: str) -> float:
    """Return similarity ratio between two strings (1.0 = identical, 0.0 = completely different)."""
    if s1 == s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    distance = _levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def _normalize_kana(text: str) -> str:
    """Normalize katakana: convert full-width to half-width for consistent comparison."""
    # Use NFKC normalization first — this handles most full-width → half-width
    # ASCII and some kana conversions
    result = unicodedata.normalize("NFKC", text)
    return result


def _normalize_company_name(name: str) -> str:
    """Normalize a company name for fuzzy comparison.

    - Strips common prefixes/suffixes like 株式会社, カ）, (有) etc.
    - Normalizes katakana (full-width → NFKC-normalized form)
    - Removes spaces
    - Uppercases Latin characters
    """
    if not name:
        return ""

    normalized = name.strip()

    # Normalize kana first so that half-width prefixes like ｶ） become カ）
    normalized = _normalize_kana(normalized)

    # Remove company type prefixes/suffixes
    for prefix in _COMPANY_PREFIXES:
        norm_prefix = _normalize_kana(prefix)
        normalized = normalized.replace(norm_prefix, "")

    # Remove all whitespace (full-width and half-width)
    normalized = re.sub(r"[\s\u3000]+", "", normalized)

    # Uppercase for Latin characters
    normalized = normalized.upper()

    return normalized


def parse_bank_csv(content: str) -> list[dict]:
    """銀行入金CSV(Shift-JIS/UTF-8)をパースして入金データのリストを返す。"""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    if len(rows) < 2:
        return []

    header = rows[0]
    col_map = _detect_columns(header)

    results = []
    for row in rows[1:]:
        if not row or len(row) < 2:
            continue
        entry = {
            "payment_date": _parse_date(row[col_map["date"]]) if col_map.get("date") is not None else None,
            "amount": _parse_amount(row[col_map["amount"]]) if col_map.get("amount") is not None else None,
            "payer_name": row[col_map["payer"]].strip() if col_map.get("payer") is not None else None,
            "reference_number": row[col_map["ref"]].strip() if col_map.get("ref") is not None and col_map["ref"] < len(row) else None,
            "bank_name": row[col_map["bank"]].strip() if col_map.get("bank") is not None and col_map["bank"] < len(row) else None,
        }
        if entry["amount"] and entry["amount"] > 0:
            results.append(entry)

    return results


def auto_match_payments(db: Session, payments: list[Payment]) -> list[dict]:
    """未消込の入金を請求書に自動マッチングする。"""
    from sqlalchemy.orm import joinedload

    unpaid_invoices = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.contract),
        )
        .filter(Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue]))
        .all()
    )

    results = []
    matched_invoice_ids: set[int] = set()

    for payment in payments:
        if payment.status != PaymentStatus.unmatched:
            results.append({"payment_id": payment.id, "score": 0, "status": "already_matched"})
            continue

        best_match = None
        best_score = 0

        for invoice in unpaid_invoices:
            if invoice.id in matched_invoice_ids:
                continue
            score = _calculate_match_score(payment, invoice)
            if score > best_score:
                best_score = score
                best_match = invoice

        if best_match and best_score >= 50:
            payment.invoice_id = best_match.id
            payment.status = PaymentStatus.matched
            matched_invoice_ids.add(best_match.id)
            results.append({
                "payment_id": payment.id,
                "invoice_id": best_match.id,
                "invoice_number": best_match.invoice_number,
                "score": best_score,
                "status": "matched",
            })
        else:
            results.append({
                "payment_id": payment.id,
                "score": best_score,
                "status": "unmatched",
            })

    db.commit()
    return results


def confirm_match(db: Session, payment_id: int) -> Payment:
    """マッチングを確定し、請求書を入金済みにする。"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise ValueError("入金データが見つかりません")
    if not payment.invoice_id:
        raise ValueError("マッチング先の請求書が設定されていません")

    payment.status = PaymentStatus.confirmed

    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if invoice:
        invoice.status = InvoiceStatus.paid
        invoice.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(payment)
    return payment


def _detect_columns(header: list[str]) -> dict:
    """CSVヘッダーから各列の位置を推定する。"""
    col_map: dict[str, int | None] = {"date": None, "amount": None, "payer": None, "ref": None, "bank": None}

    for i, h in enumerate(header):
        h_clean = h.strip()
        if re.search(r"日付|入金日|振込日|取引日", h_clean):
            col_map["date"] = i
        elif re.search(r"金額|入金額|振込額|お預り金額", h_clean):
            col_map["amount"] = i
        elif re.search(r"振込人|依頼人|支払人|名前|摘要", h_clean):
            col_map["payer"] = i
        elif re.search(r"番号|No|参照|整理番号", h_clean):
            col_map["ref"] = i
        elif re.search(r"銀行|金融機関", h_clean):
            col_map["bank"] = i

    # Fallback: assume standard positions if not detected
    if col_map["date"] is None and len(header) >= 3:
        col_map["date"] = 0
    if col_map["amount"] is None and len(header) >= 3:
        col_map["amount"] = 1
    if col_map["payer"] is None and len(header) >= 3:
        col_map["payer"] = 2

    return col_map


def _parse_date(value: str) -> date | None:
    """日付文字列をdateに変換。"""
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(value: str) -> int | None:
    """金額文字列をintに変換。"""
    cleaned = value.strip().replace(",", "").replace("¥", "").replace("￥", "").replace("円", "")
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def _calculate_match_score(payment: Payment, invoice: Invoice) -> int:
    """入金と請求書のマッチングスコアを計算(0-100)。"""
    score = 0

    # 金額一致: 最重要 (50点)
    if payment.amount == invoice.total_amount:
        score += 50
    elif abs(payment.amount - invoice.total_amount) <= invoice.total_amount * 0.01:
        score += 30  # 1%以内の誤差

    # 振込人名に企業名が含まれる (30点)
    name_score = 0
    if payment.payer_name and invoice.contract:
        company_name = None
        if invoice.contract.project and invoice.contract.project.client_company:
            company_name = invoice.contract.project.client_company.name

        if company_name:
            payer = payment.payer_name.upper()

            # Exact / substring match (best: 30 points)
            if company_name in payer or company_name.upper() in payer:
                name_score = 30
            elif any(part in payer for part in company_name.split()):
                name_score = 15

            # Fuzzy match on normalized names (if no exact match yet)
            if name_score < 30:
                norm_payer = _normalize_company_name(payment.payer_name)
                norm_company = _normalize_company_name(company_name)
                if norm_payer and norm_company:
                    # Exact match after normalization
                    if norm_payer == norm_company:
                        name_score = 30
                    else:
                        ratio = _similarity_ratio(norm_payer, norm_company)
                        if ratio >= 0.7:
                            name_score = max(name_score, 20)
                        elif ratio >= 0.5:
                            name_score = max(name_score, 10)

    score += min(name_score, 30)

    # 参照番号に請求番号が含まれる (20点)
    if payment.reference_number and invoice.invoice_number:
        if invoice.invoice_number in payment.reference_number:
            score += 20
        elif payment.reference_number in invoice.invoice_number:
            score += 20

    return min(score, 100)
