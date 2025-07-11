from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 与用户角色关联表的关系
    roles = relationship("UserRole", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 与用户角色关联表的关系
    users = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 与用户和角色的关系
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    
    # 确保用户和角色的组合是唯一的
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
    )


class TablePermission(Base):
    __tablename__ = "table_permissions"

    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    user_name = Column(String(50), nullable=True, index=True)  # Changed here
    role_name = Column(String(50), nullable=True, index=True)  # Changed here
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 确保db_name, table_name, user_name, role_name的组合是唯一的
    __table_args__ = (
        UniqueConstraint('db_name', 'table_name', 'user_name', 'role_name', name='unique_table_permission'),
    )


class ColumnPermission(Base):
    __tablename__ = "column_permissions"

    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    col_name = Column(String(100), nullable=False, index=True)
    mask_type = Column(String(50), nullable=False)
    user_name = Column(String(50), nullable=True, index=True)
    role_name = Column(String(50), nullable=True, index=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 确保mask_type的值在规定范围内
    __table_args__ = (
        CheckConstraint(
            mask_type.in_(['手机号', '身份证', '银行卡号', '座机号', '姓名', '原文']),
            name='check_mask_type'
        ),
        # 确保db_name, table_name, col_name, user_name, role_name的组合是唯一的
        UniqueConstraint('db_name', 'table_name', 'col_name', 'user_name', 'role_name', name='unique_column_permission'),
    )


class RowPermission(Base):
    __tablename__ = "row_permissions"

    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    row_filter = Column(Text, nullable=False)
    user_name = Column(String(50), nullable=True, index=True)
    role_name = Column(String(50), nullable=True, index=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 确保db_name, table_name, user_name, role_name的组合是唯一的
    __table_args__ = (
        UniqueConstraint('db_name', 'table_name', 'user_name', 'role_name', name='unique_row_permission'),
    )


class HdfsQuota(Base):
    __tablename__ = "hdfs_quotas"

    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String(100), nullable=False, index=True, unique=True)
    hdfs_quota = Column(Float, nullable=False, comment="HDFS quota in GB")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
