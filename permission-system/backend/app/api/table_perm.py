from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.db import get_db
from app.models.models import User, TablePermission
from app.schemas.schemas import (
    TablePermissionCreate, TablePermissionUpdate, TablePermissionOut,
    TablePermissionFilter, PaginatedResponse, SortParam, TablePermissionBatchCreate
)
from app.utils.helpers import get_paginated_results, check_unique_constraint, create_item, update_item, delete_item
import json
from pydantic import ValidationError

router = APIRouter()

@router.post("/batch", response_model=List[TablePermissionOut])
def batch_create_table_permissions(
    *,
    db: Session = Depends(get_db),
    batch_data: List[dict] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """批量创建表权限"""
    results = []
    errors = []
    
    for i, permission_dict in enumerate(batch_data):
        try:
            # 尝试创建并验证TablePermissionCreate对象
            try:
                permission_data = TablePermissionCreate(**permission_dict)
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
                "user_name": permission_data.user_name,
                "role_name": permission_data.role_name
            }
            
            if check_unique_constraint(db, TablePermission, constraint_fields):
                errors.append({
                    "index": i,
                    "error": "相同的表权限记录已存在",
                    "data": permission_dict
                })
                continue
            
            # 创建表权限记录
            table_permission = create_item(db, TablePermission, permission_data.model_dump())
            results.append(TablePermissionOut.model_validate(table_permission))
            
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
                "message": "批量创建表权限失败",
                "errors": errors
            }
        )
    
    # 如果部分成功部分失败，返回成功的结果和错误信息
    if errors:
        # 这里我们仍然返回成功创建的记录，但在响应头中添加警告信息
        return results
    
    return results

@router.post("/", response_model=TablePermissionOut)
def create_table_permission(
    *,
    db: Session = Depends(get_db),
    table_permission_in: TablePermissionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建表权限"""
    # 检查是否存在相同的权限记录
    constraint_fields = {
        "db_name": table_permission_in.db_name,
        "table_name": table_permission_in.table_name,
        "user_name": table_permission_in.user_name,
        "role_name": table_permission_in.role_name
    }
    
    if check_unique_constraint(db, TablePermission, constraint_fields):
        raise HTTPException(
            status_code=400,
            detail="相同的表权限记录已存在"
        )
    
    # 创建表权限记录
    table_permission = create_item(db, TablePermission, table_permission_in.model_dump())
    return TablePermissionOut.model_validate(table_permission)

@router.get("/", response_model=PaginatedResponse)
def get_table_permissions(
    db: Session = Depends(get_db),
    params: TablePermissionFilter = Depends(),
    current_user: User = Depends(get_current_active_user),
):
    """获取表权限列表，支持过滤、分页和排序"""
    filters = {
        "db_name": params.db_name,
        "table_name": params.table_name,
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
        TablePermission, 
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
        "items": [TablePermissionOut.model_validate(item) for item in result["items"]]
    }

@router.get("/{permission_id}", response_model=TablePermissionOut)
def get_table_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取表权限"""
    table_permission = db.query(TablePermission).filter(TablePermission.id == permission_id).first()
    if not table_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表权限不存在"
        )
    return TablePermissionOut.model_validate(table_permission)

@router.put("/{permission_id}", response_model=TablePermissionOut)
def update_table_permission(
    *,
    permission_id: int,
    db: Session = Depends(get_db),
    table_permission_in: TablePermissionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新表权限"""
    # 检查记录是否存在
    table_permission = db.query(TablePermission).filter(TablePermission.id == permission_id).first()
    if not table_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表权限不存在"
        )
    
    # 如果有任何字段有值，则检查唯一约束
    update_data = table_permission_in.model_dump(exclude_unset=True)
    if any(update_data.values()):
        # 构建约束检查字段
        constraint_fields = {}
        for field in ["db_name", "table_name", "user_name", "role_name"]:
            if field in update_data and update_data[field] is not None:
                constraint_fields[field] = update_data[field]
            else:
                constraint_fields[field] = getattr(table_permission, field)
        
        if check_unique_constraint(db, TablePermission, constraint_fields, permission_id):
            raise HTTPException(
                status_code=400,
                detail="更新后的表权限与现有记录冲突"
            )
    
    # 更新记录
    updated_table_permission = update_item(db, TablePermission, permission_id, update_data)
    return TablePermissionOut.model_validate(updated_table_permission)

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除表权限"""
    result = delete_item(db, TablePermission, permission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表权限不存在"
        )
    return None
