"""請求書PDF取り込み: PDFからテキスト抽出・データ構造化"""
from pathlib import Path


class InvoicePDFProcessor:
    """PDF請求書を解析してデータを抽出"""

    def extract_from_pdf(self, file_path: str) -> dict:
        """PDFからテキストを抽出し、構造化データに変換"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber がインストールされていません")

        data = {
            "invoice_number": None,
            "vendor_name": None,
            "billing_date": None,
            "due_date": None,
            "subtotal": None,
            "tax": None,
            "total": None,
            "line_items": [],
            "raw_text": "",
        }

        with pdfplumber.open(str(path)) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"

                # テーブル抽出
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row and len(row) >= 3:
                            data["line_items"].append({
                                "description": row[0],
                                "quantity": row[1] if len(row) > 1 else None,
                                "amount": row[-1],
                            })

            data["raw_text"] = full_text
            data = self._extract_fields(data, full_text)

        return data

    def _extract_fields(self, data: dict, text: str) -> dict:
        """テキストからフィールドを抽出 (簡易パターンマッチ)"""
        import re

        # 請求書番号
        m = re.search(r'請求(?:書)?(?:番号|No\.?)\s*[:：]?\s*(\S+)', text)
        if m:
            data["invoice_number"] = m.group(1)

        # 合計金額
        m = re.search(r'合計\s*[:：]?\s*[¥￥]?\s*([\d,]+)', text)
        if m:
            data["total"] = int(m.group(1).replace(",", ""))

        # 税額
        m = re.search(r'(?:消費税|税額)\s*[:：]?\s*[¥￥]?\s*([\d,]+)', text)
        if m:
            data["tax"] = int(m.group(1).replace(",", ""))

        return data
