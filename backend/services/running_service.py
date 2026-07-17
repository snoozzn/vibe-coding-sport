# ============================================================
# VibeSport Backend - Running Service
# 跑步记录 CRUD + 统计
# ============================================================
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import RunningLog
from schemas.schemas import RunningLogCreate, RunningLogUpdate, RunningStats


# -----------------------------------------------------------
# CRUD
# -----------------------------------------------------------
def create_running_log(db: Session, user_id: str, data: RunningLogCreate) -> RunningLog:
    """创建跑步记录."""
    log = RunningLog(
        user_id=user_id,
        distance_km=data.distance_km,
        log_date=data.log_date,
        notes=data.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_running_logs(
    db: Session,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[RunningLog], int]:
    """分页查询用户跑步记录, 支持日期范围筛选."""
    query = db.query(RunningLog).filter(RunningLog.user_id == user_id)

    if start_date:
        query = query.filter(RunningLog.log_date >= start_date)
    if end_date:
        query = query.filter(RunningLog.log_date <= end_date)

    total = query.count()
    logs = (
        query
        .order_by(RunningLog.log_date.desc(), RunningLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return logs, total


def get_running_log(db: Session, log_id: str, user_id: str) -> RunningLog | None:
    """获取单条跑步记录."""
    return (
        db.query(RunningLog)
        .filter(RunningLog.log_id == log_id, RunningLog.user_id == user_id)
        .first()
    )


def update_running_log(
    db: Session, log_id: str, user_id: str, data: RunningLogUpdate
) -> RunningLog:
    """更新跑步记录."""
    log = get_running_log(db, log_id, user_id)
    if log is None:
        raise ValueError("记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(log, key, value)

    db.commit()
    db.refresh(log)
    return log


def delete_running_log(db: Session, log_id: str, user_id: str) -> None:
    """删除跑步记录."""
    log = get_running_log(db, log_id, user_id)
    if log is None:
        raise ValueError("记录不存在")
    db.delete(log)
    db.commit()


# -----------------------------------------------------------
# 统计 (F-18)
# -----------------------------------------------------------
def get_running_stats(
    db: Session,
    user_id: str,
    period: str = "week",  # week | month
) -> RunningStats:
    """获取指定周期的跑步统计.

    period="week": 本周 vs 上周
    period="month": 本月 vs 上月
    """
    today = date.today()

    if period == "week":
        # 本周一 ~ 今天
        week_start = today - timedelta(days=today.weekday())
        current_start = week_start
        current_end = today

        # 上周一 ~ 上周日
        prev_start = week_start - timedelta(days=7)
        prev_end = week_start - timedelta(days=1)

    elif period == "month":
        # 本月 1 日 ~ 今天
        current_start = today.replace(day=1)
        current_end = today

        # 上月 1 日 ~ 上月最后一天
        if today.month == 1:
            prev_start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            prev_start = today.replace(month=today.month - 1, day=1)
        # 上月最后一天 = 本月 1 日前一天
        prev_end = current_start - timedelta(days=1)

    else:
        raise ValueError(f"不支持的统计周期: {period}")

    # 当前周期
    current = (
        db.query(
            func.coalesce(func.sum(RunningLog.distance_km), 0).label("total"),
            func.coalesce(func.avg(RunningLog.distance_km), 0).label("avg"),
            func.count(RunningLog.log_id).label("count"),
        )
        .filter(
            RunningLog.user_id == user_id,
            RunningLog.log_date >= current_start,
            RunningLog.log_date <= current_end,
        )
        .first()
    )

    # 上一周期
    previous = (
        db.query(
            func.coalesce(func.sum(RunningLog.distance_km), 0).label("total"),
        )
        .filter(
            RunningLog.user_id == user_id,
            RunningLog.log_date >= prev_start,
            RunningLog.log_date <= prev_end,
        )
        .first()
    )

    current_total = float(current.total or 0)
    previous_total = float(previous.total or 0)

    # 趋势百分比
    if previous_total > 0:
        trend_pct = round((current_total - previous_total) / previous_total * 100, 1)
    else:
        trend_pct = None

    return RunningStats(
        total_km=round(current_total, 1),
        avg_km=round(float(current.avg or 0), 1),
        count=current.count,
        previous_total_km=round(previous_total, 1),
        trend_pct=trend_pct,
    )
