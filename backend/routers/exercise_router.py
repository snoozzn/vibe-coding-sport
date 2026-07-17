# ============================================================
# VibeSport Backend - ExerciseType Router
# /api/exercise-types/*
# ============================================================
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.models import User
from schemas.schemas import (
    ExerciseTypeOut,
    ExerciseTypeCreate,
    MessageResponse,
)
from services.exercise_service import (
    get_all_exercise_types,
    get_preset_exercise_types,
    create_custom_type,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/exercise-types", tags=["Exercise Types"])


# -----------------------------------------------------------
# GET /api/exercise-types
# -----------------------------------------------------------
@router.get("", response_model=list[ExerciseTypeOut])
def list_all(
    preset_only: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
):
    """
    获取运动类型列表.
    - preset_only=False: 返回全部 (预设 + 自定义)
    - preset_only=True:  仅返回预设15种
    """
    if preset_only:
        types = get_preset_exercise_types(db)
    else:
        types = get_all_exercise_types(db)
    return types


# -----------------------------------------------------------
# POST /api/exercise-types
# -----------------------------------------------------------
@router.post("", response_model=ExerciseTypeOut, status_code=status.HTTP_201_CREATED)
def create_custom(
    data: ExerciseTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加自定义运动类型 (F-13). 需登录."""
    try:
        ex_type = create_custom_type(db, data.type_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return ex_type
