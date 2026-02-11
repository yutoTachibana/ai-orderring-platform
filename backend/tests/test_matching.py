from app.models.company import Company
from app.models.project import Project, SubcontractingTierLimit
from app.models.engineer import Engineer, EmploymentType
from app.models.skill_tag import SkillTag


API = "/api/v1/matching"


def _setup(db):
    co = Company(name="Test Client", company_type="client")
    db.add(co)
    db.flush()
    skill = SkillTag(name="Python", category="language")
    db.add(skill)
    db.flush()
    p = Project(name="Test Project", client_company_id=co.id, budget=800000)
    p.required_skills = [skill]
    db.add(p)
    db.flush()
    e1 = Engineer(full_name="Good Match", email="good@test.com", monthly_rate=700000, is_active=True)
    e1.skills = [skill]
    db.add(e1)
    db.flush()
    e2 = Engineer(full_name="No Match", email="no@test.com", monthly_rate=700000, is_active=True)
    db.add(e2)
    db.commit()
    db.refresh(p)
    return p, e1, e2


def test_run_matching_unauthenticated(client):
    response = client.post(f"{API}/run", json={"project_id": 1})
    assert response.status_code == 401


def test_run_matching_project_not_found(auth_client):
    response = auth_client.post(f"{API}/run", json={"project_id": 99999})
    assert response.status_code == 404


def test_run_matching_success(auth_client, db):
    p, e1, e2 = _setup(db)
    response = auth_client.post(f"{API}/run", json={"project_id": p.id})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "results" in data
    assert len(data["results"]) >= 1


def test_run_matching_no_engineers(auth_client, db):
    co = Company(name="Empty Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Empty Project", client_company_id=co.id, budget=500000)
    db.add(p)
    db.commit()
    db.refresh(p)
    response = auth_client.post(f"{API}/run", json={"project_id": p.id})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0


def test_list_results_empty(auth_client):
    response = auth_client.get(f"{API}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_matching_score_order(auth_client, db):
    co = Company(name="Score Client", company_type="client")
    db.add(co)
    db.flush()
    s1 = SkillTag(name="Python2", category="language")
    s2 = SkillTag(name="JavaScript2", category="language")
    db.add_all([s1, s2])
    db.flush()
    p = Project(name="Multi-Skill", client_company_id=co.id, budget=1000000)
    p.required_skills = [s1, s2]
    db.add(p)
    db.flush()
    e1 = Engineer(full_name="Perfect", email="perfect@test.com", monthly_rate=600000, is_active=True)
    e1.skills = [s1, s2]
    db.add(e1)
    db.flush()
    e2 = Engineer(full_name="Partial", email="partial@test.com", monthly_rate=600000, is_active=True)
    e2.skills = [s1]
    db.add(e2)
    db.commit()
    db.refresh(p)

    response = auth_client.post(f"{API}/run", json={"project_id": p.id})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 2
    # Results should be ordered by score descending
    for i in range(len(results) - 1):
        assert results[i]["score"] >= results[i + 1]["score"]


# ---------------------------------------------------------------------------
# Tier eligibility in matching
# ---------------------------------------------------------------------------


def test_matching_ineligible_engineer_score_zero(auth_client, db):
    """商流不適格エンジニアは score=0, tier_eligible=False になる"""
    co = Company(name="Tier Client", company_type="client")
    db.add(co)
    db.flush()
    ses_co = Company(name="SES Partner", company_type="ses")
    db.add(ses_co)
    db.flush()
    skill = SkillTag(name="Go", category="language")
    db.add(skill)
    db.flush()
    p = Project(
        name="Proper Only",
        client_company_id=co.id,
        budget=1000000,
        subcontracting_tier_limit=SubcontractingTierLimit.proper_only,
    )
    p.required_skills = [skill]
    db.add(p)
    db.flush()
    # 適格エンジニア（プロパー）
    e_proper = Engineer(
        full_name="Proper Dev",
        email="proper@test.com",
        monthly_rate=800000,
        employment_type=EmploymentType.proper,
        is_active=True,
    )
    e_proper.skills = [skill]
    db.add(e_proper)
    db.flush()
    # 不適格エンジニア（フリーランス）
    e_fl = Engineer(
        full_name="FL Dev",
        email="fl@test.com",
        monthly_rate=800000,
        employment_type=EmploymentType.freelancer,
        is_active=True,
    )
    e_fl.skills = [skill]
    db.add(e_fl)
    db.commit()
    db.refresh(p)

    response = auth_client.post(f"{API}/run", json={"project_id": p.id})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 2

    # Find each engineer's result
    proper_result = next(r for r in results if r["engineer_id"] == e_proper.id)
    fl_result = next(r for r in results if r["engineer_id"] == e_fl.id)

    assert proper_result["tier_eligible"] is True
    assert proper_result["score"] > 0

    assert fl_result["tier_eligible"] is False
    assert fl_result["score"] == 0.0


def test_matching_no_restriction_all_eligible(auth_client, db):
    """制限なし案件では全エンジニアが tier_eligible=True"""
    co = Company(name="Free Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Free Project", client_company_id=co.id, budget=1000000)
    db.add(p)
    db.flush()
    e = Engineer(
        full_name="Any Dev",
        email="any@test.com",
        monthly_rate=800000,
        employment_type=EmploymentType.freelancer,
        is_active=True,
    )
    db.add(e)
    db.commit()
    db.refresh(p)

    response = auth_client.post(f"{API}/run", json={"project_id": p.id})
    assert response.status_code == 200
    results = response.json()["results"]
    for r in results:
        assert r["tier_eligible"] is True
