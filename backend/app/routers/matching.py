from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.matching import MatchingResult
from app.schemas.matching import MatchingRequest, MatchingResultResponse
from app.services.tier_eligibility import is_engineer_eligible
from app.auth.dependencies import get_current_user

router = APIRouter()


def calculate_match(project: Project, engineer: Engineer) -> tuple[float, float, bool, bool, bool]:
    """案件とエンジニアのマッチングスコアを計算する。"""
    project_skill_ids = {s.id for s in project.required_skills}
    engineer_skill_ids = {s.id for s in engineer.skills}
    if not project_skill_ids:
        skill_match_rate = 0.0
    else:
        skill_match_rate = len(project_skill_ids & engineer_skill_ids) / len(project_skill_ids)
    rate_match = (
        engineer.monthly_rate is not None
        and project.budget is not None
        and engineer.monthly_rate <= project.budget
    )
    availability_match = engineer.availability_status.value == "available"
    tier_eligible = is_engineer_eligible(engineer, project)
    if not tier_eligible:
        score = 0.0
    else:
        score = skill_match_rate * 0.5 + (0.25 if rate_match else 0) + (0.25 if availability_match else 0)
    return score, skill_match_rate, rate_match, availability_match, tier_eligible


@router.post("/run", summary="マッチング実行")
def run_matching(
    req: MatchingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")

    engineers = db.query(Engineer).filter(Engineer.is_active.is_(True)).all()
    if not engineers:
        return {"message": "対象エンジニアが見つかりません", "results": []}

    # 既存のマッチング結果を削除
    db.query(MatchingResult).filter(MatchingResult.project_id == req.project_id).delete()

    results = []
    for engineer in engineers:
        score, skill_match_rate, rate_match, availability_match, tier_eligible = calculate_match(project, engineer)
        result = MatchingResult(
            project_id=project.id,
            engineer_id=engineer.id,
            score=score,
            skill_match_rate=skill_match_rate,
            rate_match=rate_match,
            availability_match=availability_match,
            tier_eligible=tier_eligible,
        )
        db.add(result)
        results.append(result)

    db.commit()
    for r in results:
        db.refresh(r)

    # スコア降順にソート
    results.sort(key=lambda r: r.score, reverse=True)
    return {
        "message": f"{len(results)}件のマッチング結果を生成しました",
        "results": results,
    }


@router.get("/results", summary="マッチング結果一覧")
def list_matching_results(
    page: int = 1,
    per_page: int = 20,
    project_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MatchingResult)
    if project_id is not None:
        query = query.filter(MatchingResult.project_id == project_id)
    query = query.order_by(MatchingResult.score.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
