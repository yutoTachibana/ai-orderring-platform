"""Tests for tier eligibility logic (subcontracting tier constraints)."""

import pytest

from app.models.company import Company
from app.models.engineer import Engineer, EmploymentType
from app.models.project import Project, SubcontractingTierLimit
from app.services.tier_eligibility import (
    get_engineer_tier,
    is_engineer_eligible,
    validate_engineer_eligibility,
)


# ---------------------------------------------------------------------------
# get_engineer_tier
# ---------------------------------------------------------------------------


def test_tier_proper(db):
    """プロパー → tier 0"""
    e = Engineer(full_name="Proper", email="p@t.com", employment_type=EmploymentType.proper)
    db.add(e)
    db.commit()
    db.refresh(e)
    assert get_engineer_tier(e) == 0


def test_tier_first_tier_proper(db):
    """一社先プロパー → tier 1"""
    e = Engineer(full_name="FTP", email="ftp@t.com", employment_type=EmploymentType.first_tier_proper)
    db.add(e)
    db.commit()
    db.refresh(e)
    assert get_engineer_tier(e) == 1


def test_tier_freelancer_no_company(db):
    """所属企業なしフリーランス → tier 1"""
    e = Engineer(full_name="FL", email="fl@t.com", employment_type=EmploymentType.freelancer)
    db.add(e)
    db.commit()
    db.refresh(e)
    assert get_engineer_tier(e) == 1


def test_tier_first_tier_freelancer(db):
    """一社先個人事業主 → tier 2"""
    e = Engineer(full_name="FTF", email="ftf@t.com", employment_type=EmploymentType.first_tier_freelancer)
    db.add(e)
    db.commit()
    db.refresh(e)
    assert get_engineer_tier(e) == 2


def test_tier_freelancer_with_company(db):
    """所属企業ありフリーランス → tier 2"""
    co = Company(name="Partner Corp", company_type="ses")
    db.add(co)
    db.flush()
    e = Engineer(
        full_name="FL Partner",
        email="flp@t.com",
        employment_type=EmploymentType.freelancer,
        company_id=co.id,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    assert get_engineer_tier(e) == 2


# ---------------------------------------------------------------------------
# is_engineer_eligible – all combinations (5 tiers x 5 limits)
# ---------------------------------------------------------------------------


def _make_project(db, limit):
    co = Company(name="Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Test", client_company_id=co.id, subcontracting_tier_limit=limit)
    db.add(p)
    db.flush()
    return p


def _make_engineer(db, employment_type, with_company=False):
    company_id = None
    if with_company:
        co = Company(name="SES Co", company_type="ses")
        db.add(co)
        db.flush()
        company_id = co.id
    e = Engineer(full_name="Eng", email="e@t.com", employment_type=employment_type, company_id=company_id)
    db.add(e)
    db.flush()
    return e


# --- proper_only (tier == 0) ---

def test_proper_only_tier0(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.proper)
    assert is_engineer_eligible(e, p) is True


def test_proper_only_first_tier_proper(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.first_tier_proper)
    assert is_engineer_eligible(e, p) is False


def test_proper_only_tier1(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.freelancer)
    assert is_engineer_eligible(e, p) is False


def test_proper_only_first_tier_freelancer(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.first_tier_freelancer)
    assert is_engineer_eligible(e, p) is False


def test_proper_only_tier2(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    assert is_engineer_eligible(e, p) is False


# --- first_tier (tier <= 1) ---

def test_first_tier_tier0(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.proper)
    assert is_engineer_eligible(e, p) is True


def test_first_tier_first_tier_proper(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.first_tier_proper)
    assert is_engineer_eligible(e, p) is True


def test_first_tier_tier1(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.freelancer)
    assert is_engineer_eligible(e, p) is True


def test_first_tier_first_tier_freelancer(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.first_tier_freelancer)
    assert is_engineer_eligible(e, p) is False


def test_first_tier_tier2(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    assert is_engineer_eligible(e, p) is False


# --- second_tier (tier <= 2) ---

def test_second_tier_tier0(db):
    p = _make_project(db, SubcontractingTierLimit.second_tier)
    e = _make_engineer(db, EmploymentType.proper)
    assert is_engineer_eligible(e, p) is True


def test_second_tier_first_tier_proper(db):
    p = _make_project(db, SubcontractingTierLimit.second_tier)
    e = _make_engineer(db, EmploymentType.first_tier_proper)
    assert is_engineer_eligible(e, p) is True


def test_second_tier_tier1(db):
    p = _make_project(db, SubcontractingTierLimit.second_tier)
    e = _make_engineer(db, EmploymentType.freelancer)
    assert is_engineer_eligible(e, p) is True


def test_second_tier_first_tier_freelancer(db):
    p = _make_project(db, SubcontractingTierLimit.second_tier)
    e = _make_engineer(db, EmploymentType.first_tier_freelancer)
    assert is_engineer_eligible(e, p) is True


def test_second_tier_tier2(db):
    p = _make_project(db, SubcontractingTierLimit.second_tier)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    assert is_engineer_eligible(e, p) is True


# --- no_restriction ---

def test_no_restriction_tier0(db):
    p = _make_project(db, SubcontractingTierLimit.no_restriction)
    e = _make_engineer(db, EmploymentType.proper)
    assert is_engineer_eligible(e, p) is True


def test_no_restriction_tier1(db):
    p = _make_project(db, SubcontractingTierLimit.no_restriction)
    e = _make_engineer(db, EmploymentType.freelancer)
    assert is_engineer_eligible(e, p) is True


def test_no_restriction_tier2(db):
    p = _make_project(db, SubcontractingTierLimit.no_restriction)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    assert is_engineer_eligible(e, p) is True


# --- None (制限なし) ---

def test_none_limit_tier0(db):
    p = _make_project(db, None)
    e = _make_engineer(db, EmploymentType.proper)
    assert is_engineer_eligible(e, p) is True


def test_none_limit_tier1(db):
    p = _make_project(db, None)
    e = _make_engineer(db, EmploymentType.freelancer)
    assert is_engineer_eligible(e, p) is True


def test_none_limit_tier2(db):
    p = _make_project(db, None)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    assert is_engineer_eligible(e, p) is True


# ---------------------------------------------------------------------------
# validate_engineer_eligibility
# ---------------------------------------------------------------------------


def test_validate_eligible_no_error(db):
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.proper)
    validate_engineer_eligibility(e, p)  # no exception


def test_validate_ineligible_raises(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.freelancer)
    with pytest.raises(ValueError, match="商流制約違反"):
        validate_engineer_eligibility(e, p)


def test_validate_error_message_contains_info(db):
    p = _make_project(db, SubcontractingTierLimit.proper_only)
    e = _make_engineer(db, EmploymentType.freelancer, with_company=True)
    with pytest.raises(ValueError, match="プロパーのみ"):
        validate_engineer_eligibility(e, p)


def test_validate_second_tier_rejects_none(db):
    """second_tier は全員許可（tier <= 2）なので、ここでは proper_only で first_tier_freelancer を検証"""
    p = _make_project(db, SubcontractingTierLimit.first_tier)
    e = _make_engineer(db, EmploymentType.first_tier_freelancer)
    with pytest.raises(ValueError, match="商流制約違反"):
        validate_engineer_eligibility(e, p)
