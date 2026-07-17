# ============================================================
# VibeSport Backend - Fitness Service
# 健身记录 CRUD + 统计
# ============================================================
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import FitnessLog
from schemas.schemas import FitnessLogCreate, FitnessLogUpdate, FitnessStats


# -----------------------------------------------------------
# CRUD
# -----------------------------------------------------------
def create_fitness_log(db: Session, user_id: str, data: FitnessLogCreate) -> FitnessLog:
    """创建健身记录."""
    if data.duration_minutes is None and data.reps_sets is None:
        raise ValueError("duration_minutes 和 reps_sets 至少填写一项")

    log = FitnessLog(
        user_id=user_id,
        exercise_type=data.exercise_type,
        duration_minutes=data.duration_minutes,
        reps_sets=data.reps_sets,
        log_date=data.log_date,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_fitness_logs(
    db: Session,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    start_date: date | None = None,
    end_date: date | None = None,
    exercise_type: str | None = None,
) -> tuple[list[FitnessLog], int]:
    """分页查询用户健身记录."""
    query = db.query(FitnessLog).filter(FitnessLog.user_id == user_id)

    if start_date:
        query = query.filter(FitnessLog.log_date >= start_date)
    if end_date:
        query = query.filter(FitnessLog.log_date <= end_date)
    if exercise_type:
        query = query.filter(FitnessLog.exercise_type == exercise_type)

    total = query.count()
    logs = (
        query
        .order_by(FitnessLog.log_date.desc(), FitnessLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return logs, total


def get_fitness_log(db: Session, fitness_id: str, user_id: str) -> FitnessLog | None:
    """获取单条健身记录."""
    return (
        db.query(FitnessLog)
        .filter(FitnessLog.fitness_id == fitness_id, FitnessLog.user_id == user_id)
        .first()
    )


def update_fitness_log(
    db: Session, fitness_id: str, user_id: str, data: FitnessLogUpdate
) -> FitnessLog:
    """更新健身记录."""
    log = get_fitness_log(db, fitness_id, user_id)
    if log is None:
        raise ValueError("记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log


def delete_fitness_log(db: Session, fitness_id: str, user_id: str) -> None:
    """删除健身记录."""
    log = get_fitness_log(db, fitness_id, user_id)
    if log is None:
        raise ValueError("记录不存在")
    db.delete(log)
    db.commit()


# -----------------------------------------------------------
# 统计 (F-19)
# -----------------------------------------------------------
def get_fitness_stats(
    db: Session,
    user_id: str,
    period: str = "week",
) -> FitnessStats:
    """获取健身频率统计."""
    from datetime import timedelta

    today = date.today()

    if period == "week":
        start = today - timedelta(days=today.weekday())
    elif period == "month":
        start = today.replace(day=1)
    else:
        raise ValueError(f"不支持的统计周期: {period}")

    # 总计
    agg = (
        db.query(
            func.count(FitnessLog.fitness_id).label("total_sessions"),
            func.coalesce(func.sum(FitnessLog.duration_minutes), 0).label("total_minutes"),
        )
        .filter(
            FitnessLog.user_id == user_id,
            FitnessLog.log_date >= start,
            FitnessLog.log_date <= today,
        )
        .first()
    )

    # 类型分布
    type_dist = (
        db.query(
            FitnessLog.exercise_type,
            func.count(FitnessLog.fitness_id).label("cnt"),
        )
        .filter(
            FitnessLog.user_id == user_id,
            FitnessLog.log_date >= start,
            FitnessLog.log_date <= today,
        )
        .group_by(FitnessLog.exercise_type)
        .all()
    )

    return FitnessStats(
        total_sessions=agg.total_sessions,
        total_minutes=int(agg.total_minutes),
        type_distribution={row.exercise_type: row.cnt for row in type_dist},
    )
