from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.engineer import Engineer, AvailabilityStatus
from app.models.project import Project
from app.models.skill_tag import SkillTag
from app.schemas.engineer import EngineerCreate, EngineerUpdate, EngineerResponse
from app.services.tier_eligibility import is_engineer_eligible
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter()


def _resolve_skills(db: Session, skill_ids: list[int]) -> list[SkillTag]:
    """スキルIDリストからSkillTagオブジェクトリストを取得する。"""
    if not skill_ids:
        return []
    skills = db.query(SkillTag).filter(SkillTag.id.in_(skill_ids)).all()
    if len(skills) != len(skill_ids):
        found_ids = {s.id for s in skills}
        missing = [sid for sid in skill_ids if sid not in found_ids]
        raise HTTPException(status_code=400, detail=f"存在しないスキルIDです: {missing}")
    return skills


@router.get("", summary="エンジニア一覧")
def list_engineers(
    page: int = 1,
    per_page: int = 20,
    availability_status: str | None = None,
    company_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Engineer).options(joinedload(Engineer.skills), joinedload(Engineer.company))
    if availability_status:
        query = query.filter(Engineer.availability_status == availability_status)
    if company_id is not None:
        query = query.filter(Engineer.company_id == company_id)
    if search:
        query = query.filter(Engineer.full_name.ilike(f"%{search}%"))
    total = db.query(Engineer).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [EngineerResponse.model_validate(e) for e in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/eligible", summary="適格エンジニア一覧")
def list_eligible_engineers(
    project_id: int,
    page: int = 1,
    per_page: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """案件の再委託制限に基づき、選択可能なエンジニアのみ返す。"""
    from fastapi import HTTPException

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")
    engineers = (
        db.query(Engineer)
        .options(joinedload(Engineer.skills), joinedload(Engineer.company))
        .filter(Engineer.is_active.is_(True))
        .all()
    )
    eligible = [e for e in engineers if is_engineer_eligible(e, project)]
    total = len(eligible)
    start = (page - 1) * per_page
    items = eligible[start : start + per_page]
    return {
        "items": [EngineerResponse.model_validate(e) for e in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }


@router.get("/{engineer_id}", response_model=EngineerResponse, summary="エンジニア詳細")
def get_engineer(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")
    return engineer


@router.post("", response_model=EngineerResponse, status_code=201, summary="エンジニア作成")
def create_engineer(
    req: EngineerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = req.model_dump(exclude={"skill_ids"})
    engineer = Engineer(**data)
    engineer.skills = _resolve_skills(db, req.skill_ids)
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer


@router.put("/{engineer_id}", response_model=EngineerResponse, summary="エンジニア更新")
def update_engineer(
    engineer_id: int,
    req: EngineerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    skill_ids = update_data.pop("skill_ids", None)
    for key, value in update_data.items():
        setattr(engineer, key, value)
    if skill_ids is not None:
        engineer.skills = _resolve_skills(db, skill_ids)
    db.commit()
    db.refresh(engineer)
    return engineer


@router.delete("/{engineer_id}", status_code=204, summary="エンジニア削除")
def delete_engineer(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")
    db.delete(engineer)
    db.commit()
