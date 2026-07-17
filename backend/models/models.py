# ============================================================
# VibeSport Backend - SQLAlchemy 数据模型
# 对应 PRD §5 数据模型 & database/init.sql
# ============================================================
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime,
    Boolean, Text, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def gen_uuid() -> str:
    """生成 UUID v4 字符串."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """返回当前 UTC 时间 (与 MySQL CURRENT_TIMESTAMP 对齐)."""
    return datetime.utcnow()


# -----------------------------------------------------------
# User
# -----------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id          = Column(String(36), primary_key=True, default=gen_uuid)
    username         = Column(String(20), nullable=False, unique=True)
    email            = Column(String(255), nullable=False, unique=True)
    password_hash    = Column(String(255), nullable=False)
    avatar_url       = Column(String(500), nullable=True)
    target_weight_kg = Column(Numeric(5, 1), nullable=True)
    login_attempts   = Column(Integer, nullable=False, default=0)
    locked_until     = Column(DateTime, nullable=True)
    created_at       = Column(DateTime, nullable=False, default=now_utc)
    updated_at       = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    # 关联
    running_logs  = relationship("RunningLog",  back_populates="user", cascade="all, delete-orphan")
    fitness_logs  = relationship("FitnessLog",  back_populates="user", cascade="all, delete-orphan")
    weight_logs   = relationship("WeightLog",   back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.user_id} username={self.username}>"


# -----------------------------------------------------------
# RunningLog
# -----------------------------------------------------------
class RunningLog(Base):
    __tablename__ = "running_logs"

    log_id      = Column(String(36), primary_key=True, default=gen_uuid)
    user_id     = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    distance_km = Column(Numeric(5, 1), nullable=False)
    log_date    = Column(Date, nullable=False)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime, nullable=False, default=now_utc)

    user = relationship("User", back_populates="running_logs")

    __table_args__ = (
        Index("idx_running_user_date", "user_id", "log_date"),
        Index("idx_running_date", "log_date"),
    )

    def __repr__(self) -> str:
        return f"<RunningLog {self.log_id} {self.distance_km}km @ {self.log_date}>"


# -----------------------------------------------------------
# FitnessLog
# -----------------------------------------------------------
class FitnessLog(Base):
    __tablename__ = "fitness_logs"

    fitness_id       = Column(String(36), primary_key=True, default=gen_uuid)
    user_id          = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    exercise_type    = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    reps_sets        = Column(String(50), nullable=True)
    log_date         = Column(Date, nullable=False)
    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime, nullable=False, default=now_utc)

    user = relationship("User", back_populates="fitness_logs")

    __table_args__ = (
        Index("idx_fitness_user_date", "user_id", "log_date"),
        Index("idx_fitness_type", "exercise_type"),
        Index("idx_fitness_date", "log_date"),
    )

    def __repr__(self) -> str:
        return f"<FitnessLog {self.fitness_id} {self.exercise_type} @ {self.log_date}>"


# -----------------------------------------------------------
# WeightLog
# -----------------------------------------------------------
class WeightLog(Base):
    __tablename__ = "weight_logs"

    weight_id    = Column(String(36), primary_key=True, default=gen_uuid)
    user_id      = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    weight_value = Column(Numeric(5, 1), nullable=False)
    unit         = Column(String(3), nullable=False, default="kg")
    log_date     = Column(Date, nullable=False)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime, nullable=False, default=now_utc)

    user = relationship("User", back_populates="weight_logs")

    __table_args__ = (
        Index("idx_weight_user_date", "user_id", "log_date"),
        Index("idx_weight_date", "log_date"),
    )

    def __repr__(self) -> str:
        return f"<WeightLog {self.weight_id} {self.weight_value}{self.unit} @ {self.log_date}>"


# -----------------------------------------------------------
# ExerciseType (预设运动类型)
# -----------------------------------------------------------
class ExerciseType(Base):
    __tablename__ = "exercise_types"

    type_id    = Column(Integer, primary_key=True, autoincrement=True)
    type_name  = Column(String(100), nullable=False, unique=True)
    is_preset  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)

    def __repr__(self) -> str:
        return f"<ExerciseType {self.type_id} {self.type_name}>"
