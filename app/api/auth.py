from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.deps import get_db
from ..core.security import create_access_token
from ..schemas.user import Token, UserCreate, UserOut
from ..services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if user_service.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已被注册")
    if user_service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    return user_service.create_user(db, data)


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = user_service.authenticate_user(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.username))
