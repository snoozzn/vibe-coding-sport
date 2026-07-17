# ============================================================
# VibeSport Backend - Weight Router
# /api/weight/*
# ============================================================
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import (
    WeightLogCreate,
    WeightLogUpdate,
    WeightLogOut,
    WeightStats,
    MessageResponse,
    PaginatedResponse,
)
from services.weight_service import (
    create_weight_log,
    get_weight_logs,
    get_weight_log,
    update_weight_log,
    delete_weight_log,
    get_weight_stats,
    get_weight_trend,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/weight", tags=["Weight"])


# -----------------------------------------------------------
# POST /api/weight
# -----------------------------------------------------------
@router.post("", response_model=WeightLogOut, status_code=status.HTTP_201_CREATED)
def create(
    data: WeightLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """录入体重记录 (F-14, F-15)."""
    try:
        log = create_weight_log(db, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return log


# -----------------------------------------------------------
# GET /api/weight
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
    """获取体重记录列表 (F-21). 分页 + 日期范围筛选."""
    logs, total = get_weight_logs(
        db, current_user.user_id, page, page_size, start_date, end_date
    )
    items = [WeightLogOut.model_validate(log) for log in logs]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


# -----------------------------------------------------------
# GET /api/weight/stats
# -----------------------------------------------------------
@router.get("/stats", response_model=WeightStats)
def stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取体重统计摘要 (F-20)."""
    return get_weight_stats(db, current_user.user_id)


# -----------------------------------------------------------
# GET /api/weight/trend
# -----------------------------------------------------------
@router.get("/trend")
def trend(
    days: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取体重变化趋势 (F-20 折线图数据)."""
    return get_weight_trend(db, current_user.user_id, days)


# -----------------------------------------------------------
# GET /api/weight/{weight_id}
# -----------------------------------------------------------
@router.get("/{weight_id}", response_model=WeightLogOut)
def get_one(
    weight_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条体重记录."""
    log = get_weight_log(db, weight_id, current_user.user_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return log


# -----------------------------------------------------------
# PATCH /api/weight/{weight_id}
# -----------------------------------------------------------
@router.patch("/{weight_id}", response_model=WeightLogOut)
def update(
    weight_id: str,
    data: WeightLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑体重记录 (F-16)."""
    try:
        log = update_weight_log(db, weight_id, current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return log


# -----------------------------------------------------------
# DELETE /api/weight/{weight_id}
# -----------------------------------------------------------
@router.delete("/{weight_id}", response_model=MessageResponse)
def delete(
    weight_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除体重记录 (F-16)."""
    try:
        delete_weight_log(db, weight_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return MessageResponse(message="记录已删除")
