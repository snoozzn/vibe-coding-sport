# ============================================================
# VibeSport Backend - Pydantic Schemas
# 请求/响应模型校验
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# Auth
# ============================================================
class UserRegister(BaseModel):
    """用户注册请求."""
    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_digit(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一个字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class UserLogin(BaseModel):
    """用户登录请求."""
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """JWT Token 响应."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class UserOut(BaseModel):
    """用户信息输出 (不含密码)."""
    user_id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    target_weight_kg: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """用户信息更新."""
    username: Optional[str] = Field(None, min_length=2, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)
    target_weight_kg: Optional[Decimal] = Field(None, ge=20, le=500)


class ChangePassword(BaseModel):
    """修改密码."""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def new_password_complexity(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一个字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# ============================================================
# Running
# ============================================================
class RunningLogCreate(BaseModel):
    """创建跑步记录."""
    distance_km: Decimal = Field(..., gt=0, le=100, description="跑步距离 (km)")
    log_date: date = Field(default_factory=date.today, description="运动日期")
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("日期不能是未来日期")
        return v


class RunningLogUpdate(BaseModel):
    """更新跑步记录."""
    distance_km: Optional[Decimal] = Field(None, gt=0, le=100)
    log_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("日期不能是未来日期")
        return v


class RunningLogOut(BaseModel):
    """跑步记录输出."""
    log_id: str
    user_id: str
    distance_km: Decimal
    log_date: date
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Fitness
# ============================================================
class FitnessLogCreate(BaseModel):
    """创建健身记录."""
    exercise_type: str = Field(..., min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    reps_sets: Optional[str] = Field(None, max_length=50)
    log_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("日期不能是未来日期")
        return v

    @field_validator("reps_sets")
    @classmethod
    def check_at_least_one(cls, v: Optional[str], info) -> Optional[str]:
        """duration_minutes 和 reps_sets 至少填一个."""
        return v  # 全局校验在 service 层做, 这里只做字段级校验

    @field_validator("duration_minutes")
    @classmethod
    def check_duration_or_reps(cls, v: Optional[int], info) -> Optional[int]:
        """仅做字段级校验, 业务逻辑见 service."""
        return v


class FitnessLogUpdate(BaseModel):
    """更新健身记录."""
    exercise_type: Optional[str] = Field(None, min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    reps_sets: Optional[str] = Field(None, max_length=50)
    log_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("日期不能是未来日期")
        return v


class FitnessLogOut(BaseModel):
    """健身记录输出."""
    fitness_id: str
    user_id: str
    exercise_type: str
    duration_minutes: Optional[int] = None
    reps_sets: Optional[str] = None
    log_date: date
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Weight
# ============================================================
class WeightLogCreate(BaseModel):
    """创建体重记录."""
    weight_value: Decimal = Field(..., ge=20, le=500)
    unit: str = Field(default="kg", pattern="^(kg|lbs)$")
    log_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("日期不能是未来日期")
        return v


class WeightLogUpdate(BaseModel):
    """更新体重记录."""
    weight_value: Optional[Decimal] = Field(None, ge=20, le=500)
    unit: Optional[str] = Field(None, pattern="^(kg|lbs)$")
    log_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("log_date")
    @classmethod
    def date_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("日期不能是未来日期")
        return v


class WeightLogOut(BaseModel):
    """体重记录输出."""
    weight_id: str
    user_id: str
    weight_value: Decimal
    unit: str
    log_date: date
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# ExerciseType
# ============================================================
class ExerciseTypeOut(BaseModel):
    """运动类型输出."""
    type_id: int
    type_name: str
    is_preset: bool

    model_config = {"from_attributes": True}


class ExerciseTypeCreate(BaseModel):
    """创建自定义运动类型 (F-13)."""
    type_name: str = Field(..., min_length=1, max_length=100)


# ============================================================
# Analytics / 统计
# ============================================================
class RunningStats(BaseModel):
    """跑步统计."""
    total_km: float = 0.0
    avg_km: float = 0.0
    count: int = 0
    previous_total_km: float = 0.0
    trend_pct: Optional[float] = None  # 与上一周期对比的百分比


class FitnessStats(BaseModel):
    """健身统计."""
    total_sessions: int = 0
    total_minutes: int = 0
    type_distribution: dict[str, int] = {}


class WeightStats(BaseModel):
    """体重统计."""
    latest_weight: Optional[float] = None
    highest_weight: Optional[float] = None
    lowest_weight: Optional[float] = None
    latest_unit: str = "kg"
    data_points: int = 0


class DashboardData(BaseModel):
    """仪表盘总览 (F-17)."""
    today_running_km: float = 0.0
    week_fitness_count: int = 0
    latest_weight: Optional[float] = None
    latest_weight_unit: str = "kg"


# ============================================================
# 通用
# ============================================================
class MessageResponse(BaseModel):
    """通用消息响应."""
    message: str


class PaginatedResponse(BaseModel):
    """分页响应."""
    items: list
    total: int
    page: int
    page_size: int
