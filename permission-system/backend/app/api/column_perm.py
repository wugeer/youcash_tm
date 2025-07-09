from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.db import get_db
from app.models.models import User, ColumnPermission
from app.schemas.schemas import (
    ColumnPermissionCreate, ColumnPermissionUpdate, ColumnPermissionOut,
    ColumnPermissionFilter, PaginatedResponse, ColumnPermissionBatchCreate
)
from app.utils.helpers import get_paginated_results, check_unique_constraint, create_item, update_item, delete_item
import json
from pydantic import ValidationError

router = APIRouter()

@router.post("/batch", response_model=List[ColumnPermissionOut])
def batch_create_column_permissions(
    *,
    db: Session = Depends(get_db),
    batch_data: List[dict] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """批量创建字段权限"""
    results = []
    errors = []
    
    for i, permission_dict in enumerate(batch_data):
        try:
            # 尝试创建并验证ColumnPermissionCreate对象
            try:
                permission_data = ColumnPermissionCreate(**permission_dict)
            except ValidationError as ve:
                errors.append({
                    "index": i,
                    "error": f"数据验证失败: {str(ve)}",
                    "data": permission_dict
                })
                continue
                
            # 检查是否存在相同的权限记录
            constraint_fields = {
                "db_name": permission_data.db_name,
                "table_name": permission_data.table_name,
                "col_name": permission_data.col_name,
                "user_name": permission_data.user_name,
                "role_name": permission_data.role_name
            }
            
            if check_unique_constraint(db, ColumnPermission, constraint_fields):
                errors.append({
                    "index": i,
                    "error": "相同的字段权限记录已存在",
                    "data": permission_dict
                })
                continue
            
            # 创建字段权限记录
            column_permission = create_item(db, ColumnPermission, permission_data.model_dump())
            results.append(ColumnPermissionOut.model_validate(column_permission))
            
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e),
                "data": permission_dict
            })
    
    # 如果有错误，回滚并返回错误信息
    if errors and not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "批量创建字段权限失败",
                "errors": errors
            }
        )
    
    # 如果部分成功部分失败，返回成功的结果和错误信息
    if errors:
        # 这里我们仍然返回成功创建的记录，但在响应头中添加警告信息
        return results
    
    return results

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
    params: ColumnPermissionFilter = Depends(),
    current_user: User = Depends(get_current_active_user),
):
    # 添加调试日志
    print("DEBUG: 接收到的排序参数:", params.sorters)
    """获取列权限列表，支持过滤、分页和排序"""
    filters = {
        "db_name": params.db_name,
        "table_name": params.table_name,
        "col_name": params.col_name,
        "mask_type": params.mask_type,
        "user_name": params.user_name,
        "role_name": params.role_name
    }
    
    # 移除None值
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # 处理排序参数 - 优先使用单独的排序字段和排序方向参数
    sorters_list = None
    if params.sort_field and params.sort_order:
        print(f"DEBUG: 使用单独的排序参数: {params.sort_field}, {params.sort_order}")
        sorters_list = [{'field': params.sort_field, 'order': params.sort_order}]
    elif params.sorters:
        print(f"DEBUG: 使用sorters参数: {params.sorters}")
        sorters_list = [s.model_dump() for s in params.sorters]

    result = get_paginated_results(
        db, 
        ColumnPermission, 
        page=params.page, 
        page_size=params.page_size, 
        filters=filters,
        sorters=sorters_list
    )
    
    # 转换为JSON响应格式
    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "items": [ColumnPermissionOut.model_validate(item) for item in result["items"]]
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
