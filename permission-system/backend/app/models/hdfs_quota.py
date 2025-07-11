from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.core.db import Base

class HdfsQuota(Base):
    __tablename__ = "hdfs_quotas"

    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String(100), nullable=False, index=True, unique=True)
    hdfs_quota = Column(Float, nullable=False, comment="HDFS quota in GB")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
