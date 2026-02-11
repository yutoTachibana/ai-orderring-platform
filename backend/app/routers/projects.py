from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.skill_tag import SkillTag
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
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


@router.get("", summary="案件一覧")
def list_projects(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    client_company_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(Project)
    if status:
        base_query = base_query.filter(Project.status == status)
    if client_company_id is not None:
        base_query = base_query.filter(Project.client_company_id == client_company_id)
    total = base_query.count()
    items = base_query.options(
        joinedload(Project.client_company),
        joinedload(Project.required_skills),
    ).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{project_id}", response_model=ProjectResponse, summary="案件詳細")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")
    return project


@router.post("", response_model=ProjectResponse, status_code=201, summary="案件作成")
def create_project(
    req: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = req.model_dump(exclude={"skill_ids"})
    project = Project(**data)
    project.required_skills = _resolve_skills(db, req.skill_ids)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse, summary="案件更新")
def update_project(
    project_id: int,
    req: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    skill_ids = update_data.pop("skill_ids", None)
    for key, value in update_data.items():
        setattr(project, key, value)
    if skill_ids is not None:
        project.required_skills = _resolve_skills(db, skill_ids)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204, summary="案件削除")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません")
    db.delete(project)
    db.commit()
