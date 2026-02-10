from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginResponse, UserResponse
from app.auth.utils import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="ログイン")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )
    return LoginResponse(access_token=create_access_token(user.id))


@router.post("/signup", response_model=UserResponse, status_code=201, summary="ユーザー登録")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")
    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse, summary="現在のユーザー情報")
def me(current_user: User = Depends(get_current_user)):
    return current_user
