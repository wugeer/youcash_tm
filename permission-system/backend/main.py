import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import API_V1_STR, BACKEND_CORS_ORIGINS

# 创建FastAPI应用
app = FastAPI(
    title="表权限管理系统",
    description="提供表级、字段级和行级权限管理的API",
    version="1.0.0",
)

# 设置CORS中间件
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 包含所有API路由
app.include_router(api_router, prefix=API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "表权限管理系统API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
