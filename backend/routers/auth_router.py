# ============================================================
# VibeSport Backend - Auth Router
# /api/auth/*
# ============================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserOut,
    UserUpdate,
    ChangePassword,
    MessageResponse,
)
from services.auth_service import (
    register_user,
    login_user,
    get_user_profile,
    update_user_profile,
    change_password,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# -----------------------------------------------------------
# POST /api/auth/register
# -----------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """用户注册 (F-01). 注册成功后直接返回 JWT (自动登录)."""
    try:
        user = register_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    # 注册成功, 直接签发 token
    from utils.security import create_access_token

    token = create_access_token(data={"sub": user.user_id})
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        username=user.username,
    )


# -----------------------------------------------------------
# POST /api/auth/login
# -----------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """用户登录 (F-02). 邮箱 + 密码. 5次失败锁定15分钟."""
    try:
        result = login_user(db, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(**result)


# -----------------------------------------------------------
# GET /api/auth/me
# -----------------------------------------------------------
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息."""
    return current_user


# -----------------------------------------------------------
# PATCH /api/auth/me
# -----------------------------------------------------------
@router.patch("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新个人信息 (F-04)."""
    try:
        user = update_user_profile(db, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


# -----------------------------------------------------------
# POST /api/auth/change-password
# -----------------------------------------------------------
@router.post("/change-password", response_model=MessageResponse)
def change_pwd(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码."""
    try:
        change_password(db, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="密码已更新")
