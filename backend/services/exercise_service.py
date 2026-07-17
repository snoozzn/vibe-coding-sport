# ============================================================
# VibeSport Backend - ExerciseType Service
# 运动类型预设管理
# ============================================================
from sqlalchemy.orm import Session

from models.models import ExerciseType


def get_all_exercise_types(db: Session) -> list[ExerciseType]:
    """获取全部运动类型 (预设 + 自定义)."""
    return db.query(ExerciseType).order_by(ExerciseType.is_preset.desc(), ExerciseType.type_id.asc()).all()


def get_preset_exercise_types(db: Session) -> list[ExerciseType]:
    """获取系统预设运动类型."""
    return (
        db.query(ExerciseType)
        .filter(ExerciseType.is_preset == True)
        .order_by(ExerciseType.type_id.asc())
        .all()
    )


def create_custom_type(db: Session, type_name: str) -> ExerciseType:
    """创建自定义运动类型 (F-13)."""
    existing = db.query(ExerciseType).filter(ExerciseType.type_name == type_name).first()
    if existing:
        raise ValueError(f"运动类型 '{type_name}' 已存在")

    ex_type = ExerciseType(type_name=type_name, is_preset=False)
    db.add(ex_type)
    db.commit()
    db.refresh(ex_type)
    return ex_type
