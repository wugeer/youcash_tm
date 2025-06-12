from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.db import get_db
from app.models.models import User, ColumnPermission
from app.schemas.schemas import (
    ColumnPermissionCreate, ColumnPermissionUpdate, ColumnPermissionOut,
    ColumnPermissionFilter, PaginatedResponse
)
from app.utils.helpers import get_paginated_results, check_unique_constraint, create_item, update_item, delete_item

router = APIRouter()

@router.post("/", response_model=ColumnPermissionOut)
def create_column_permission(
    *,
    db: Session = Depends(get_db),
    column_permission_in: ColumnPermissionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建列权限"""
    # 检查是否存在相同的权限记录
    constraint_fields = {
        "db_name": column_permission_in.db_name,
        "table_name": column_permission_in.table_name,
        "col_name": column_permission_in.col_name,
        "user_name": column_permission_in.user_name,
        "role_name": column_permission_in.role_name
    }
    
    if check_unique_constraint(db, ColumnPermission, constraint_fields):
        raise HTTPException(
            status_code=400,
            detail="相同的列权限记录已存在"
        )
    
    # 创建列权限记录
    column_permission = create_item(db, ColumnPermission, column_permission_in.dict())
    return column_permission

@router.get("/", response_model=PaginatedResponse)
def get_column_permissions(
    db: Session = Depends(get_db),
    db_name: Optional[str] = None,
    table_name: Optional[str] = None,
    col_name: Optional[str] = None,
    mask_type: Optional[str] = None,
    user_name: Optional[str] = None,
    role_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """获取列权限列表，支持过滤和分页"""
    filters = {
        "db_name": db_name,
        "table_name": table_name,
        "col_name": col_name,
        "mask_type": mask_type,
        "user_name": user_name,
        "role_name": role_name
    }
    
    # 移除None值
    filters = {k: v for k, v in filters.items() if v is not None}
    
    result = get_paginated_results(
        db, ColumnPermission, page=page, page_size=page_size, filters=filters
    )
    
    # 转换为JSON响应格式
    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "items": [ColumnPermissionOut.from_orm(item) for item in result["items"]]
    }

@router.get("/{permission_id}", response_model=ColumnPermissionOut)
def get_column_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取列权限"""
    column_permission = db.query(ColumnPermission).filter(ColumnPermission.id == permission_id).first()
    if not column_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="列权限不存在"
        )
    return column_permission

@router.put("/{permission_id}", response_model=ColumnPermissionOut)
def update_column_permission(
    *,
    permission_id: int,
    db: Session = Depends(get_db),
    column_permission_in: ColumnPermissionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新列权限"""
    # 检查记录是否存在
    column_permission = db.query(ColumnPermission).filter(ColumnPermission.id == permission_id).first()
    if not column_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="列权限不存在"
        )
    
    # 如果有任何字段有值，则检查唯一约束
    update_data = column_permission_in.dict(exclude_unset=True)
    if any(update_data.values()):
        # 构建约束检查字段
        constraint_fields = {}
        for field in ["db_name", "table_name", "col_name", "user_name", "role_name"]:
            if field in update_data and update_data[field] is not None:
                constraint_fields[field] = update_data[field]
            else:
                constraint_fields[field] = getattr(column_permission, field)
        
        if check_unique_constraint(db, ColumnPermission, constraint_fields, permission_id):
            raise HTTPException(
                status_code=400,
                detail="更新后的列权限与现有记录冲突"
            )
    
    # 更新记录
    updated_column_permission = update_item(db, ColumnPermission, permission_id, update_data)
    return updated_column_permission

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除列权限"""
    result = delete_item(db, ColumnPermission, permission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="列权限不存在"
        )
    return None
