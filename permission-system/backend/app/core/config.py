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
BACKEND_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:13000",
]

# 数据库配置
SQLALCHEMY_DATABASE_URI = DATABASE_URL
