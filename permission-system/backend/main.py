import uvicorn
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import API_V1_STR, BACKEND_CORS_ORIGINS

# 配置日志系统
def setup_logging():
    # 创建日志格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    import os
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'permission_system.log'))
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 配置应用日志记录器
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)
    
    # 关闭uvicorn的访问日志
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# 初始化日志系统
logger = setup_logging()

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

@app.on_event("startup")
async def startup_event():
    """FastAPI应用启动时的事件处理程序"""
    logger.info("权限管理系统 API启动...")
    logger.info(f"API版本前缀: {API_V1_STR}")
    logger.info(f"CORS配置: {BACKEND_CORS_ORIGINS}")

# 添加中间件记录所有API请求
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """API请求日志中间件"""
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    # 检查是否与权限同步相关
    is_sync_request = 'sync' in path
    if is_sync_request:
        logger.info(f"收到同步请求: {method} {path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response_status = response.status_code
    
    if is_sync_request or response_status >= 400:
        logger.info(f"请求完成: {method} {path} - 状态码: {response_status} - 处理时间: {process_time:.2f}ms")
    
    return response

@app.get("/")
def root():
    return {
        "message": "表权限管理系统API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
