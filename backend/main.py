# ============================================================
# VibeSport Backend - FastAPI 主入口
# Python 3.11+ / FastAPI / SQLAlchemy / MySQL
# ============================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------------------------------------
# App 初始化
# -----------------------------------------------------------
app = FastAPI(
    title="VibeSport API",
    description="运动打卡追踪 App 后端服务 — PRD v1.0.0",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# -----------------------------------------------------------
# CORS — v1.0 允许所有来源 (后续收紧)
# -----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------
# 注册路由
# -----------------------------------------------------------
from routers.auth_router import router as auth_router
from routers.running_router import router as running_router
from routers.fitness_router import router as fitness_router
from routers.weight_router import router as weight_router
from routers.exercise_router import router as exercise_router
from routers.dashboard_router import router as dashboard_router

app.include_router(auth_router)
app.include_router(running_router)
app.include_router(fitness_router)
app.include_router(weight_router)
app.include_router(exercise_router)
app.include_router(dashboard_router)


# -----------------------------------------------------------
# 健康检查
# -----------------------------------------------------------
@app.get("/api/health", tags=["Health"])
def health_check():
    """健康检查端点."""
    from database.connection import engine
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
    }


# -----------------------------------------------------------
# 开发服务器入口
# -----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
