import os
from pydantic import PostgresDsn
from dotenv import load_dotenv
from typing import Any, Dict, Optional

# 加载环境变量
load_dotenv()

# 获取环境变量或使用默认值
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/permission_db"
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# API前缀
API_V1_STR = "/api/v1"

# CORS设置
# 注意: 在FastAPI中不建议同时使用通配符"*"和特定域名，有可能导致CORS错误

# 生产环境中根据需要选择一种配置方式:

# 方式1: 显式列出所有允许的源
# 一定要包含前端Docker容器的实际访问地址
# 例如: http://192.168.1.100:38080
SPECIFIC_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:13000",
    "http://localhost:8080",
    # 添加实际前端访问地址 - 注意这里一定要用实际IP
    # 这应该与浏览器地址栏中的地址精确匹配
    "http://192.168.122.141:38080",  # 替换为实际IP和端口
]

# 方式2: 允许所有源 (只在开发环境使用)
ALLOW_ALL = True  # 在生产环境中设为 False

# 根据选择设置最终CORS配置
if ALLOW_ALL:
    # 使用通配符允许所有源(开发环境)
    BACKEND_CORS_ORIGINS = ["*"]
else:
    # 使用特定源列表(生产环境推荐)
    BACKEND_CORS_ORIGINS = SPECIFIC_ORIGINS

# 数据库配置
SQLALCHEMY_DATABASE_URI = DATABASE_URL
