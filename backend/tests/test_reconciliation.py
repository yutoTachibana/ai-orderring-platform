import io

import pytest

from app.models.company import Company
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.quotation import Quotation
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.services.reconciliation import (
    _levenshtein_distance,
    _normalize_company_name,
    _similarity_ratio,
)


API = "/api/v1/reconciliation"


def _create_invoice_via_api(auth_client, db):
    """テスト用にcontract→invoiceを作成してinvoice_idを返す。"""
    co = Company(name="Test Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Test Project", client_company_id=co.id)
    db.add(p)
    db.flush()
    e = Engineer(full_name="Test Engineer", email="eng@test.com")
    db.add(e)
    db.flush()
    q = Quotation(project_id=p.id, engineer_id=e.id, unit_price=500000, estimated_hours=160, total_amount=500000)
    db.add(q)
    db.flush()
    o = Order(quotation_id=q.id, order_number="ORD-REC-001")
    db.add(o)
    db.commit()
    db.refresh(o)
    db.refresh(p)
    db.refresh(e)

    # Create contract via API
    res = auth_client.post("/api/v1/contracts", json={
        "order_id": o.id, "contract_number": "CON-REC-001",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 500000,
    })
    contract_id = res.json()["id"]

    # Create invoice via API
    res = auth_client.post("/api/v1/invoices", json={
        "contract_id": contract_id,
        "invoice_number": "INV-REC-001",
        "billing_month": "2026-04-01",
        "working_hours": 160,
        "base_amount": 500000,
        "tax_amount": 50000,
        "total_amount": 550000,
    })
    invoice_id = res.json()["id"]

    # Send invoice to make it matchable
    auth_client.post(f"/api/v1/invoices/{invoice_id}/send")
    return invoice_id


def test_list_payments_unauthenticated(client):
    response = client.get(API)
    assert response.status_code == 401


def test_list_payments_empty(auth_client):
    response = auth_client.get(API)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_summary_empty(auth_client):
    response = auth_client.get(f"{API}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_payments"] == 0
    assert data["matched"] == 0


def test_import_csv(auth_client):
    csv_content = "入金日,金額,振込人,参照番号\n2026-04-15,550000,テスト株式会社,REF-001\n2026-04-16,330000,サンプル商事,REF-002\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = auth_client.post(f"{API}/import", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2
    assert len(data["payments"]) == 2


def test_import_non_csv(auth_client):
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    response = auth_client.post(f"{API}/import", files=files)
    assert response.status_code == 400


def test_auto_match_no_data(auth_client):
    response = auth_client.post(f"{API}/match")
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_auto_match_with_data(auth_client, db):
    invoice_id = _create_invoice_via_api(auth_client, db)

    # Import payment matching the invoice amount
    csv_content = "入金日,金額,振込人,参照番号\n2026-04-15,550000,テスト株式会社,INV-REC-001\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    auth_client.post(f"{API}/import", files=files)

    # Run auto-match
    response = auth_client.post(f"{API}/match")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["status"] == "matched"
    assert results[0]["invoice_id"] == invoice_id


def test_manual_match(auth_client, db):
    invoice_id = _create_invoice_via_api(auth_client, db)

    # Import payment
    csv_content = "入金日,金額,振込人\n2026-04-15,550000,テスト\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = auth_client.post(f"{API}/import", files=files)
    payment_id = res.json()["payments"][0]["id"]

    # Manual match
    response = auth_client.post(f"{API}/{payment_id}/match", json={"invoice_id": invoice_id})
    assert response.status_code == 200
    assert response.json()["invoice_id"] == invoice_id


def test_confirm_match(auth_client, db):
    invoice_id = _create_invoice_via_api(auth_client, db)

    # Import and auto-match
    csv_content = "入金日,金額,振込人,参照番号\n2026-04-15,550000,テスト,INV-REC-001\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = auth_client.post(f"{API}/import", files=files)
    payment_id = res.json()["payments"][0]["id"]
    auth_client.post(f"{API}/match")

    # Confirm
    response = auth_client.post(f"{API}/{payment_id}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Verify invoice is now paid
    inv_res = auth_client.get(f"/api/v1/invoices/{invoice_id}")
    assert inv_res.json()["status"] == "paid"


def test_unmatch_payment(auth_client, db):
    invoice_id = _create_invoice_via_api(auth_client, db)

    csv_content = "入金日,金額,振込人\n2026-04-15,550000,テスト\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = auth_client.post(f"{API}/import", files=files)
    payment_id = res.json()["payments"][0]["id"]

    # Manual match then unmatch
    auth_client.post(f"{API}/{payment_id}/match", json={"invoice_id": invoice_id})
    response = auth_client.post(f"{API}/{payment_id}/unmatch")
    assert response.status_code == 200

    # Verify payment is unmatched again
    list_res = auth_client.get(API)
    p = [x for x in list_res.json()["items"] if x["id"] == payment_id][0]
    assert p["status"] == "unmatched"
    assert p["invoice_number"] is None


def test_unmatch_confirmed_fails(auth_client, db):
    invoice_id = _create_invoice_via_api(auth_client, db)

    csv_content = "入金日,金額,振込人,参照番号\n2026-04-15,550000,テスト,INV-REC-001\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = auth_client.post(f"{API}/import", files=files)
    payment_id = res.json()["payments"][0]["id"]
    auth_client.post(f"{API}/match")
    auth_client.post(f"{API}/{payment_id}/confirm")

    # Try to unmatch confirmed
    response = auth_client.post(f"{API}/{payment_id}/unmatch")
    assert response.status_code == 400


def test_list_with_status_filter(auth_client):
    csv_content = "入金日,金額,振込人\n2026-04-15,100000,A\n2026-04-16,200000,B\n"
    files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    auth_client.post(f"{API}/import", files=files)

    response = auth_client.get(f"{API}?status=unmatched")
    assert response.status_code == 200
    assert response.json()["total"] == 2


# ---------------------------------------------------------------------------
# Unit tests for fuzzy matching helpers
# ---------------------------------------------------------------------------


class TestLevenshteinDistance:
    """Tests for _levenshtein_distance()."""

    def test_identical_strings(self):
        assert _levenshtein_distance("abc", "abc") == 0

    def test_empty_strings(self):
        assert _levenshtein_distance("", "") == 0

    def test_one_empty(self):
        assert _levenshtein_distance("abc", "") == 3
        assert _levenshtein_distance("", "abc") == 3

    def test_single_insertion(self):
        assert _levenshtein_distance("abc", "abcd") == 1

    def test_single_deletion(self):
        assert _levenshtein_distance("abcd", "abc") == 1

    def test_single_substitution(self):
        assert _levenshtein_distance("abc", "axc") == 1

    def test_completely_different(self):
        assert _levenshtein_distance("abc", "xyz") == 3

    def test_japanese_katakana(self):
        # ソリューション vs ソリユーシヨン (missing prolonged marks / small kana)
        dist = _levenshtein_distance("ソリューション", "ソリユーシヨン")
        assert dist > 0  # They are different
        assert dist <= 3  # But not hugely different


class TestSimilarityRatio:
    """Tests for _similarity_ratio()."""

    def test_identical(self):
        assert _similarity_ratio("テスト", "テスト") == 1.0

    def test_empty_strings(self):
        assert _similarity_ratio("", "") == 1.0

    def test_completely_different(self):
        ratio = _similarity_ratio("abc", "xyz")
        assert ratio == 0.0

    def test_similar_strings(self):
        ratio = _similarity_ratio("テックソリューション", "テックソリユーシヨン")
        assert 0.5 <= ratio <= 1.0  # reasonably similar

    def test_range_is_zero_to_one(self):
        ratio = _similarity_ratio("hello", "world")
        assert 0.0 <= ratio <= 1.0


class TestNormalizeCompanyName:
    """Tests for _normalize_company_name()."""

    def test_strip_kabushiki_kaisha(self):
        result = _normalize_company_name("株式会社テックソリューション")
        assert "株式会社" not in result
        assert "テックソリューション" in result or "テックソリューション" in _normalize_company_name("テックソリューション")

    def test_strip_kabu_prefix(self):
        # カ） is a common half-width prefix in bank transfers
        result = _normalize_company_name("カ）テックソリューション")
        assert result == _normalize_company_name("テックソリューション")

    def test_strip_yuugen_kaisha(self):
        result = _normalize_company_name("有限会社テスト商事")
        assert "有限会社" not in result

    def test_remove_spaces(self):
        result = _normalize_company_name("テック ソリューション")
        assert " " not in result

    def test_empty_string(self):
        assert _normalize_company_name("") == ""

    def test_uppercase_latin(self):
        result = _normalize_company_name("abc Corp")
        assert "ABC" in result

    def test_normalized_names_match(self):
        """Bank transfer name カ）テックソリユーシヨン should normalize close to 株式会社テックソリューション."""
        bank_name = _normalize_company_name("カ）テックソリユーシヨン")
        company_name = _normalize_company_name("株式会社テックソリューション")
        # After stripping prefixes, the core names should be similar
        ratio = _similarity_ratio(bank_name, company_name)
        assert ratio >= 0.5, f"Expected ratio >= 0.5, got {ratio} ('{bank_name}' vs '{company_name}')"


class TestFuzzyMatchingIntegration:
    """Tests verifying fuzzy matching flows through to match results."""

    def test_fuzzy_match_katakana_variations(self):
        """カ）テックソリユーシヨン should fuzzy-match 株式会社テックソリューション after normalization."""
        bank_payer = "カ）テックソリユーシヨン"
        company = "株式会社テックソリューション"

        norm_payer = _normalize_company_name(bank_payer)
        norm_company = _normalize_company_name(company)

        # After removing prefixes they should be similar
        ratio = _similarity_ratio(norm_payer, norm_company)
        # This should be at least 0.5 (10-point fuzzy match threshold)
        assert ratio >= 0.5, f"ratio={ratio}, payer='{norm_payer}', company='{norm_company}'"

    def test_exact_after_normalization(self):
        """Same core name with different legal entity prefix should normalize to identical."""
        name_a = _normalize_company_name("（株）テスト商事")
        name_b = _normalize_company_name("株式会社テスト商事")
        assert name_a == name_b

    def test_score_returned_in_match_results(self, auth_client, db):
        """auto_match should return 'score' key in each result dict."""
        invoice_id = _create_invoice_via_api(auth_client, db)

        csv_content = "入金日,金額,振込人,参照番号\n2026-04-15,550000,テスト株式会社,INV-REC-001\n"
        files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        auth_client.post(f"{API}/import", files=files)

        response = auth_client.post(f"{API}/match")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) >= 1
        for result in results:
            assert "score" in result, "Each match result must include a 'score' key"
            assert isinstance(result["score"], (int, float))

    def test_score_returned_for_unmatched(self, auth_client):
        """Even unmatched payments should have a score in the result."""
        csv_content = "入金日,金額,振込人\n2026-04-15,999999,不明な振込人\n"
        files = {"file": ("payments.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        auth_client.post(f"{API}/import", files=files)

        response = auth_client.post(f"{API}/match")
        assert response.status_code == 200
        results = response.json()["results"]
        for result in results:
            assert "score" in result
