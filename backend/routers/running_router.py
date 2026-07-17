# ============================================================
# VibeSport Backend - Running Router
# /api/running/*
# ============================================================
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import (
    RunningLogCreate,
    RunningLogUpdate,
    RunningLogOut,
    RunningStats,
    MessageResponse,
    PaginatedResponse,
)
from services.running_service import (
    create_running_log,
    get_running_logs,
    get_running_log,
    update_running_log,
    delete_running_log,
    get_running_stats,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/running", tags=["Running"])


# -----------------------------------------------------------
# POST /api/running
# -----------------------------------------------------------
@router.post("", response_model=RunningLogOut, status_code=status.HTTP_201_CREATED)
def create(
    data: RunningLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """录入跑步记录 (F-05, F-06, F-07)."""
    try:
        log = create_running_log(db, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return log


# -----------------------------------------------------------
# GET /api/running
# -----------------------------------------------------------
@router.get("", response_model=PaginatedResponse)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取跑步记录列表 (F-21). 分页 + 日期范围筛选."""
    logs, total = get_running_logs(
        db, current_user.user_id, page, page_size, start_date, end_date
    )
    items = [RunningLogOut.model_validate(log) for log in logs]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


# -----------------------------------------------------------
# GET /api/running/stats
# -----------------------------------------------------------
@router.get("/stats", response_model=RunningStats)
def stats(
    period: str = Query("week", pattern="^(week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取跑步统计 (F-18). period=week|month."""
    try:
        return get_running_stats(db, current_user.user_id, period)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------
# GET /api/running/{log_id}
# -----------------------------------------------------------
@router.get("/{log_id}", response_model=RunningLogOut)
def get_one(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条跑步记录."""
    log = get_running_log(db, log_id, current_user.user_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return log


# -----------------------------------------------------------
# PATCH /api/running/{log_id}
# -----------------------------------------------------------
@router.patch("/{log_id}", response_model=RunningLogOut)
def update(
    log_id: str,
    data: RunningLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑跑步记录 (F-08)."""
    try:
        log = update_running_log(db, log_id, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return log


# -----------------------------------------------------------
# DELETE /api/running/{log_id}
# -----------------------------------------------------------
@router.delete("/{log_id}", response_model=MessageResponse)
def delete(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除跑步记录 (F-08)."""
    try:
        delete_running_log(db, log_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return MessageResponse(message="记录已删除")
