from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import SQLALCHEMY_DATABASE_URI

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,  # 连接池预检查
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    pool_recycle=3600,   # 连接回收时间（秒）
    echo=False           # SQL回显，生产环境关闭
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 获取数据库会话的依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
