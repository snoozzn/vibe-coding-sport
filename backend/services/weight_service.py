# ============================================================
# VibeSport Backend - Weight Service
# 体重记录 CRUD + 统计
# ============================================================
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import WeightLog
from schemas.schemas import WeightLogCreate, WeightLogUpdate, WeightStats


# -----------------------------------------------------------
# CRUD
# -----------------------------------------------------------
def create_weight_log(db: Session, user_id: str, data: WeightLogCreate) -> WeightLog:
    """创建体重记录."""
    log = WeightLog(
        user_id=user_id,
        weight_value=data.weight_value,
        unit=data.unit,
        log_date=data.log_date,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_weight_logs(
    db: Session,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[WeightLog], int]:
    """分页查询用户体重记录."""
    query = db.query(WeightLog).filter(WeightLog.user_id == user_id)

    if start_date:
        query = query.filter(WeightLog.log_date >= start_date)
    if end_date:
        query = query.filter(WeightLog.log_date <= end_date)

    total = query.count()
    logs = (
        query
        .order_by(WeightLog.log_date.desc(), WeightLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return logs, total


def get_weight_log(db: Session, weight_id: str, user_id: str) -> WeightLog | None:
    """获取单条体重记录."""
    return (
        db.query(WeightLog)
        .filter(WeightLog.weight_id == weight_id, WeightLog.user_id == user_id)
        .first()
    )


def update_weight_log(
    db: Session, weight_id: str, user_id: str, data: WeightLogUpdate
) -> WeightLog:
    """更新体重记录."""
    log = get_weight_log(db, weight_id, user_id)
    if log is None:
        raise ValueError("记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log


def delete_weight_log(db: Session, weight_id: str, user_id: str) -> None:
    """删除体重记录."""
    log = get_weight_log(db, weight_id, user_id)
    if log is None:
        raise ValueError("记录不存在")
    db.delete(log)
    db.commit()


# -----------------------------------------------------------
# 统计 (F-20)
# -----------------------------------------------------------
def get_weight_stats(db: Session, user_id: str) -> WeightStats:
    """获取体重统计摘要（全部历史数据）."""
    # 最新一条
    latest = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.log_date.desc(), WeightLog.created_at.desc())
        .first()
    )

    # 所有记录
    agg = (
        db.query(
            func.max(WeightLog.weight_value).label("max_w"),
            func.min(WeightLog.weight_value).label("min_w"),
            func.count(WeightLog.weight_id).label("cnt"),
        )
        .filter(WeightLog.user_id == user_id)
        .first()
    )

    return WeightStats(
        latest_weight=float(latest.weight_value) if latest else None,
        highest_weight=float(agg.max_w) if agg.max_w else None,
        lowest_weight=float(agg.min_w) if agg.min_w else None,
        latest_unit=latest.unit if latest else "kg",
        data_points=agg.cnt or 0,
    )


def get_weight_trend(db: Session, user_id: str, days: int = 90) -> list[dict]:
    """获取体重变化趋势数据（折线图用）."""
    from datetime import timedelta

    start_date = date.today() - timedelta(days=days)

    logs = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == user_id,
            WeightLog.log_date >= start_date,
        )
        .order_by(WeightLog.log_date.asc())
        .all()
    )

    return [
        {
            "date": str(log.log_date),
            "weight": float(log.weight_value),
            "unit": log.unit,
        }
        for log in logs
    ]
