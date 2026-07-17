# ============================================================
# VibeSport Backend - Fitness Router
# /api/fitness/*
# ============================================================
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import (
    FitnessLogCreate,
    FitnessLogUpdate,
    FitnessLogOut,
    FitnessStats,
    MessageResponse,
    PaginatedResponse,
)
from services.fitness_service import (
    create_fitness_log,
    get_fitness_logs,
    get_fitness_log,
    update_fitness_log,
    delete_fitness_log,
    get_fitness_stats,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/fitness", tags=["Fitness"])


# -----------------------------------------------------------
# POST /api/fitness
# -----------------------------------------------------------
@router.post("", response_model=FitnessLogOut, status_code=status.HTTP_201_CREATED)
def create(
    data: FitnessLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """录入健身记录 (F-09, F-10, F-11)."""
    try:
        log = create_fitness_log(db, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return log


# -----------------------------------------------------------
# GET /api/fitness
# -----------------------------------------------------------
@router.get("", response_model=PaginatedResponse)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    exercise_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取健身记录列表 (F-21). 分页 + 日期范围 + 运动类型筛选."""
    logs, total = get_fitness_logs(
        db, current_user.user_id, page, page_size, start_date, end_date, exercise_type
    )
    items = [FitnessLogOut.model_validate(log) for log in logs]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


# -----------------------------------------------------------
# GET /api/fitness/stats
# -----------------------------------------------------------
@router.get("/stats", response_model=FitnessStats)
def stats(
    period: str = Query("week", pattern="^(week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取健身频率统计 (F-19). period=week|month."""
    try:
        return get_fitness_stats(db, current_user.user_id, period)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------
# GET /api/fitness/{fitness_id}
# -----------------------------------------------------------
@router.get("/{fitness_id}", response_model=FitnessLogOut)
def get_one(
    fitness_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条健身记录."""
    log = get_fitness_log(db, fitness_id, current_user.user_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return log


# -----------------------------------------------------------
# PATCH /api/fitness/{fitness_id}
# -----------------------------------------------------------
@router.patch("/{fitness_id}", response_model=FitnessLogOut)
def update(
    fitness_id: str,
    data: FitnessLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑健身记录 (F-12)."""
    try:
        log = update_fitness_log(db, fitness_id, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return log


# -----------------------------------------------------------
# DELETE /api/fitness/{fitness_id}
# -----------------------------------------------------------
@router.delete("/{fitness_id}", response_model=MessageResponse)
def delete(
    fitness_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除健身记录 (F-12)."""
    try:
        delete_fitness_log(db, fitness_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return MessageResponse(message="记录已删除")
