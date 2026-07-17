# ============================================================
# VibeSport Backend - Dashboard Service
# 仪表盘总览 (F-17)
# ============================================================
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import RunningLog, FitnessLog, WeightLog
from schemas.schemas import DashboardData


def get_dashboard(db: Session, user_id: str) -> DashboardData:
    """获取仪表盘总览数据."""
    today = date.today()

    # 今日跑步距离
    today_running = (
        db.query(func.coalesce(func.sum(RunningLog.distance_km), 0))
        .filter(RunningLog.user_id == user_id, RunningLog.log_date == today)
        .scalar()
    )

    # 本周健身次数
    week_start = today - timedelta(days=today.weekday())
    week_fitness = (
        db.query(func.count(FitnessLog.fitness_id))
        .filter(
            FitnessLog.user_id == user_id,
            FitnessLog.log_date >= week_start,
            FitnessLog.log_date <= today,
        )
        .scalar()
    )

    # 最新体重
    latest_weight = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id)
        .order_by(WeightLog.log_date.desc(), WeightLog.created_at.desc())
        .first()
    )

    return DashboardData(
        today_running_km=round(float(today_running or 0), 1),
        week_fitness_count=week_fitness or 0,
        latest_weight=float(latest_weight.weight_value) if latest_weight else None,
        latest_weight_unit=latest_weight.unit if latest_weight else "kg",
    )
