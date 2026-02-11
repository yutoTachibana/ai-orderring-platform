"""請求書PDF取り込みサービス: PDFから請求データを抽出"""
import re
from datetime import date
from pathlib import Path

import pdfplumber


def extract_invoice_from_pdf(file_path: str) -> dict:
    """PDFから請求書データを抽出して構造化辞書を返す。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    full_text = ""
    line_items: list[dict] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

            for table in page.extract_tables():
                for row in table:
                    if row and len(row) >= 2:
                        line_items.append({
                            "description": (row[0] or "").strip(),
                            "quantity": (row[1] or "").strip() if len(row) > 2 else "",
                            "unit_price": (row[2] or "").strip() if len(row) > 3 else "",
                            "amount": (row[-1] or "").strip(),
                        })

    result = {
        "invoice_number": _extract_invoice_number(full_text),
        "vendor_name": _extract_vendor_name(full_text),
        "billing_date": _extract_date(full_text, r'(?:請求日|発行日|日付)\s*[:：]?\s*(\d{4}[/\-年]\d{1,2}[/\-月]\d{1,2}日?)'),
        "billing_month": _extract_date(full_text, r'(?:対象(?:期間|月)|請求月)\s*[:：]?\s*(\d{4}[/\-年]\d{1,2}[/\-月]?)'),
        "due_date": _extract_date(full_text, r'(?:支払期[日限]|振込期限)\s*[:：]?\s*(\d{4}[/\-年]\d{1,2}[/\-月]\d{1,2}日?)'),
        "subtotal": _extract_amount(full_text, r'(?:小計|税抜[き]?(?:金額|合計))\s*[:：]?\s*[¥￥]?\s*([\d,]+)'),
        "tax_amount": _extract_amount(full_text, r'(?:消費税|税額)\s*[:：]?\s*[¥￥]?\s*([\d,]+)'),
        "total_amount": _extract_total(full_text),
        "working_hours": _extract_hours(full_text),
        "line_items": line_items,
        "raw_text": full_text.strip(),
    }

    # subtotalが取れなければtotal - taxで計算
    if result["subtotal"] is None and result["total_amount"] and result["tax_amount"]:
        result["subtotal"] = result["total_amount"] - result["tax_amount"]

    return result


def _extract_invoice_number(text: str) -> str | None:
    patterns = [
        r'請求(?:書)?(?:番号|No\.?|NO\.?)\s*[:：]?\s*(\S+)',
        r'(?:INV|inv)[\-_]?(\S+)',
        r'No\.?\s*[:：]?\s*(\d[\d\-]+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None


def _extract_vendor_name(text: str) -> str | None:
    patterns = [
        r'(?:発行者|請求元|差出人)\s*[:：]?\s*(.+?)(?:\n|$)',
        r'(.+?(?:株式会社|有限会社|合同会社))\s*(?:\n|$)',
        r'(?:株式会社|有限会社|合同会社)(.+?)\s*(?:\n|$)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None


def _extract_date(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    if not m:
        return None
    raw = m.group(1)
    # 2024年3月1日 → 2024-03-01
    raw = raw.replace("年", "-").replace("月", "-").replace("日", "")
    parts = [p for p in re.split(r'[/\-]', raw) if p]
    if len(parts) >= 2:
        y = parts[0]
        mo = parts[1].zfill(2)
        d = parts[2].zfill(2) if len(parts) >= 3 else "01"
        return f"{y}-{mo}-{d}"
    return raw


def _extract_amount(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def _extract_total(text: str) -> int | None:
    patterns = [
        r'(?:ご?請求(?:金額|額)|合計(?:金額)?|お支払[い]?(?:金額|額))\s*[:：]?\s*[¥￥]?\s*([\d,]+)',
        r'合計\s*[:：]?\s*[¥￥]?\s*([\d,]+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def _extract_hours(text: str) -> float | None:
    patterns = [
        r'(?:稼働時間|作業時間|工数)\s*[:：]?\s*([\d.]+)\s*(?:時間|[hH])',
        r'([\d.]+)\s*(?:時間|[hH])\s*(?:稼働|作業)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1))
    return None
