# ============================================================
# VibeSport Backend - Auth Service
# 用户注册、登录、个人信息管理
# ============================================================
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.models import User
from schemas.schemas import UserRegister, UserUpdate, ChangePassword
from utils.security import hash_password, verify_password, create_access_token
from config import settings


# -----------------------------------------------------------
# 注册
# -----------------------------------------------------------
def register_user(db: Session, data: UserRegister) -> User:
    """注册新用户. 返回创建成功的 User 对象."""
    # 检查邮箱是否已注册
    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        raise ValueError("该邮箱已被注册")

    # 检查用户名是否已占用
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise ValueError("该用户名已被占用")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------------------------------------
# 登录
# -----------------------------------------------------------
def login_user(db: Session, email: str, password: str) -> dict:
    """用户登录. 返回 JWT token 和用户信息.

    业务规则 (PRD F-01):
    - 连续失败 ≥ 5 次 → 锁定 15 分钟
    - 登录成功后清零失败计数
    """
    user = db.query(User).filter(User.email == email).first()

    # 用户不存在
    if user is None:
        raise ValueError("邮箱或密码错误")

    # 检查是否被锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        raise ValueError(f"账号已锁定，请 {remaining} 分钟后重试")

    # 校验密码
    if not verify_password(password, user.password_hash):
        # 增加失败计数
        user.login_attempts = (user.login_attempts or 0) + 1
        if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
        db.commit()
        raise ValueError("邮箱或密码错误")

    # 登录成功: 清零失败计数
    user.login_attempts = 0
    user.locked_until = None
    db.commit()

    # 生成 JWT
    token = create_access_token(data={"sub": user.user_id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
    }


# -----------------------------------------------------------
# 个人信息
# -----------------------------------------------------------
def get_user_profile(db: Session, user_id: str) -> User:
    """获取用户信息."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise ValueError("用户不存在")
    return user


def update_user_profile(db: Session, user_id: str, data: UserUpdate) -> User:
    """更新用户信息."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise ValueError("用户不存在")

    update_data = data.model_dump(exclude_unset=True)

    # 如果修改用户名, 检查是否重复
    if "username" in update_data:
        existing = db.query(User).filter(
            User.username == update_data["username"],
            User.user_id != user_id,
        ).first()
        if existing:
            raise ValueError("该用户名已被占用")

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user_id: str, data: ChangePassword) -> None:
    """修改密码."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise ValueError("用户不存在")

    if not verify_password(data.old_password, user.password_hash):
        raise ValueError("原密码错误")

    user.password_hash = hash_password(data.new_password)
    db.commit()
