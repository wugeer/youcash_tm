from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.db import Base

class LdapUser(Base):
    """LDAP用户模型"""
    __tablename__ = "ldap_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, index=True, unique=True)
    password = Column(String(255), nullable=False)
    role_name = Column(String(100), nullable=False, index=True)
    department_name = Column(String(100), nullable=False, index=True)
    hdfs_quota = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    description = Column(Text, nullable=True)
    
    def to_dict(self):
        """将对象转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "role_name": self.role_name,
            "department_name": self.department_name,
            "hdfs_quota": self.hdfs_quota,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "description": self.description
        }
