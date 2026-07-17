# ============================================================
# VibeSport Backend - Dashboard Router
# /api/dashboard/*
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import DashboardData
from services.dashboard_service import get_dashboard
from utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# -----------------------------------------------------------
# GET /api/dashboard
# -----------------------------------------------------------
@router.get("", response_model=DashboardData)
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取仪表盘总览 (F-17)."""
    return get_dashboard(db, current_user.user_id)
