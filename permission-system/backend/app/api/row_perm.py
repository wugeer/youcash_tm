from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, BackgroundTasks
from app.utils.sync_helpers import with_sync_retry
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.db import get_db
from app.models.models import User, RowPermission
from app.schemas.schemas import (
    RowPermissionCreate, RowPermissionUpdate, RowPermissionOut,
    RowPermissionFilter, PaginatedResponse, RowPermissionBatchCreate
)
from app.utils.helpers import get_paginated_results, check_unique_constraint, create_item, update_item, delete_item
import json
from pydantic import ValidationError
import subprocess
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------- 预执行 CLI 命令的占位函数 -----------------

def run_pre_save_command(payload: dict) -> None:
    """在真正保存权限前调用 CLI（argparse）命令。

    当前仅为占位实现，后续可将 `cmd` 修改为实际脚本及参数。
    如果命令返回非 0，则抛出 HTTPException 400 阻止保存。
    """
    # 记录执行参数
    logger.info(f"[行权限模块] 执行命令参数: {payload}")
    
    # TODO: 根据业务需要修改命令及参数
    cmd = ["python", "example_cli.py", json.dumps(payload)]
    try:
        logger.debug(f"[行权限模块] 准备执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        logger.info(f"[行权限模块] 命令执行结果: 返回码={result.returncode}, 输出={result.stdout.strip()}, 错误={result.stderr.strip()}")
        
        if result.returncode != 0:
            logger.error(f"[行权限模块] 预执行命令失败: {result.stderr.strip() or '未知错误'}")
            raise HTTPException(
                status_code=400,
                detail=f"预执行命令失败: {result.stderr.strip() or '未知错误'}"
            )
        logger.info(f"[行权限模块] 命令执行成功")
    except FileNotFoundError:
        # 未找到脚本时直接抛错，提醒后端开发者
        logger.critical(f"[行权限模块] 脚本文件不存在: example_cli.py")
        raise HTTPException(status_code=500, detail="预执行命令脚本不存在，请实现 run_pre_save_command")

@router.post("/batch", response_model=List[RowPermissionOut])
def batch_create_row_permissions(
    *,
    db: Session = Depends(get_db),
    batch_data: RowPermissionBatchCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """批量创建行权限
    
    批量创建行权限记录，可选批量同步模式
    - batch_sync=True: 所有记录一次性同步（适合大批量导入）
    - batch_sync=False: 逐条同步（默认模式）
    """
    results = []
    errors = []
    permissions_to_sync = []
    batch_sync = batch_data.batch_sync
    
    # 记录同步模式
    logger.info(f"[行权限模块] 批量创建行权限，同步模式: {'批量' if batch_sync else '逐条'}")
    
    for i, permission_item in enumerate(batch_data.items):
        try:
            # 尝试创建并验证RowPermissionCreate对象
            try:
                permission_data = RowPermissionCreate.model_validate(permission_item)
                permission_dict = permission_data.model_dump()
            except ValidationError as ve:
                errors.append({
                    "index": i,
                    "error": f"数据验证失败: {str(ve)}",
                    "data": permission_item.dict() if hasattr(permission_item, 'dict') else permission_item
                })
                continue
                
            # 检查是否存在相同的权限记录
            constraint_fields = {
                "db_name": permission_data.db_name,
                "table_name": permission_data.table_name,
                "user_name": permission_data.user_name,
                "role_name": permission_data.role_name
            }
            
            if check_unique_constraint(db, RowPermission, constraint_fields):
                errors.append({
                    "index": i,
                    "error": "相同的行权限记录已存在",
                    "data": permission_dict
                })
                continue
            
            # 创建行权限记录
            row_permission = create_item(db, RowPermission, permission_data.model_dump())
            results.append(RowPermissionOut.model_validate(row_permission))
            
            # 如果使用逐条同步模式，则为每条记录添加单独的同步任务
            if not batch_sync:
                logger.info(f"[行权限模块] 添加单独同步任务: 批量导入权限记录 ID={row_permission.id}")
                background_tasks.add_task(
                    sync_single_row_permission,
                    row_permission.id,
                    db=db
                )
            else:
                # 批量同步模式下，收集ID以便后续一次性同步
                permissions_to_sync.append(row_permission.id)
            
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
                "message": "批量创建行权限失败",
                "errors": errors
            }
        )
    
    # 如果部分成功部分失败，返回成功的结果和错误信息
    if errors:
        # 这里我们仍然返回成功创建的记录，但在响应头中添加警告信息
        return results
    
    # 如果使用批量同步模式且有成功创建的记录，启动批量同步任务
    if batch_sync and permissions_to_sync:
        total_to_sync = len(permissions_to_sync)
        logger.info(f"[行权限模块] 批量同步模式，添加批量同步任务，共{total_to_sync}条记录")
        background_tasks.add_task(
            sync_all_row_permissions,
            db=db
        )
    
    return results

@router.post("/", response_model=RowPermissionOut)
def create_row_permission(
    *,
    db: Session = Depends(get_db),
    row_permission_in: RowPermissionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """创建行权限并自动执行同步"""
    # 检查是否存在相同的权限记录
    constraint_fields = {
        "db_name": row_permission_in.db_name,
        "table_name": row_permission_in.table_name,
        "user_name": row_permission_in.user_name,
        "role_name": row_permission_in.role_name
    }
    
    if check_unique_constraint(db, RowPermission, constraint_fields):
        raise HTTPException(
            status_code=400,
            detail="相同的行权限记录已存在"
        )
    
    # 预执行 CLI 命令
    run_pre_save_command(row_permission_in.model_dump())
    # 创建行权限记录
    row_permission = create_item(db, RowPermission, row_permission_in.model_dump())
    
    # 添加同步任务到后台执行
    logger.info(f"[行权限模块] 添加同步任务: 新建权限记录 ID={row_permission.id}")
    background_tasks.add_task(
        sync_single_row_permission,
        row_permission.id,
        db=db
    )
    
    return RowPermissionOut.model_validate(row_permission)

@router.get("/", response_model=PaginatedResponse)
def get_row_permissions(
    db: Session = Depends(get_db),
    params: RowPermissionFilter = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """获取行权限列表，支持过滤、分页和排序"""
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
        RowPermission, 
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
        "items": [RowPermissionOut.from_orm(item) for item in result["items"]]
    }

@router.get("/{permission_id}", response_model=RowPermissionOut)
def get_row_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据ID获取行权限"""
    row_permission = db.query(RowPermission).filter(RowPermission.id == permission_id).first()
    if not row_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行权限不存在"
        )
    return row_permission

@router.put("/{permission_id}", response_model=RowPermissionOut)
def update_row_permission(
    *,
    permission_id: int,
    db: Session = Depends(get_db),
    row_permission_in: RowPermissionUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """更新行权限"""
    # 检查记录是否存在
    row_permission = db.query(RowPermission).filter(RowPermission.id == permission_id).first()
    if not row_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行权限不存在"
        )
    
    # 如果有任何字段有值，则检查唯一约束
    update_data = row_permission_in.dict(exclude_unset=True)
    if any(update_data.values()):
        # 构建约束检查字段
        constraint_fields = {}
        for field in ["db_name", "table_name", "user_name", "role_name"]:
            if field in update_data and update_data[field] is not None:
                constraint_fields[field] = update_data[field]
            else:
                constraint_fields[field] = getattr(row_permission, field)
        
        if check_unique_constraint(db, RowPermission, constraint_fields, permission_id):
            raise HTTPException(
                status_code=400,
                detail="更新后的行权限与现有记录冲突"
            )
    
    # 预执行 CLI 命令
    run_pre_save_command({**update_data, "id": permission_id})
    # 更新记录
    updated_row_permission = update_item(db, RowPermission, permission_id, update_data)
    
    # 添加同步任务到后台执行
    logger.info(f"[行权限模块] 添加同步任务: 更新权限记录 ID={permission_id}")
    background_tasks.add_task(
        sync_single_row_permission,
        permission_id,
        db=db
    )
    
    return updated_row_permission

def sync_all_row_permissions(*, db: Session):
    """同步所有行权限的内部函数，可以被后台任务调用
    
    参数:
        db: 数据库会话（关键字参数）
    """
    # 查询所有行权限记录
    all_row_permissions = db.query(RowPermission).all()
    total_count = len(all_row_permissions)
    
    logger.info(f"[行权限模块] 开始同步所有行权限，共{total_count}条记录")
    
    if total_count == 0:
        logger.warning("[行权限模块] 无行权限记录可同步")
        return {"message": "sync ok", "total": 0, "synced": 0}
    
    # 先通知CLI脚本开始批量同步操作
    batch_payload = {
        "action": "sync_row_permissions",
        "total": total_count
    }
    run_pre_save_command(batch_payload)
    
    # 记录成功和失败的同步操作
    success_count = 0
    failed_records = []
    
    # 依次同步每条记录
    for index, perm in enumerate(all_row_permissions):
        try:
            # 准备同步参数
            payload = {
                "action": "sync_single_row_permission",
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "row_filter": perm.row_filter,
                "user_name": perm.user_name,
                "role_name": perm.role_name
            }
            
            # 记录同步请求
            logger.info(f"[行权限模块] 同步记录 {index+1}/{total_count}: ID={perm.id}, 数据库=[{perm.db_name}], 表=[{perm.table_name}], 用户=[{perm.user_name}], 角色=[{perm.role_name}]")
            
            # 执行同步命令
            run_pre_save_command(payload)
            success_count += 1
            
        except Exception as e:
            logger.error(f"[行权限模块] 同步记录 ID={perm.id} 失败: {str(e)}")
            failed_records.append({
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "error": str(e)
            })
    
    # 返回同步结果摘要
    return {
        "message": "sync completed", 
        "total": total_count, 
        "synced": success_count,
        "failed": len(failed_records),
        "failed_records": failed_records[:10] if failed_records else []  # 最多显示10条失败记录
    }

@router.post("/sync", response_model=dict)
def sync_row_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """同步所有行权限API端点
    
    自动遍历数据库中的所有行权限记录，并依次执行同步操作
    """
    return sync_all_row_permissions(db=db)

@router.post("/sync/{permission_id}", response_model=dict)
@with_sync_retry(max_attempts=3, retry_delay=2)
def sync_single_row_permission(
    permission_id: int,
    *,
    db: Session = Depends(get_db),
    module_name: str = "行权限模块",
    action: str = "同步"
):
    """同步单个行权限记录
    
    传递关键字段：数据库名、表名、行筛选条件、用户名、角色名
    """
    # 检查权限记录是否存在
    row_permission = db.query(RowPermission).filter(RowPermission.id == permission_id).first()
    if not row_permission:
        raise HTTPException(status_code=404, detail="行权限记录不存在")
    
    # 准备同步参数，包含所有关键字段
    payload = {
        "action": "sync_single_row_permission",
        "id": permission_id,
        "db_name": row_permission.db_name,
        "table_name": row_permission.table_name,
        "row_filter": row_permission.row_filter,
        "user_name": row_permission.user_name,
        "role_name": row_permission.role_name
    }
    
    # 记录同步请求
    logger.info(f"[行权限模块] 同步单条记录: ID={permission_id}, 数据库=[{row_permission.db_name}], 表=[{row_permission.table_name}], 用户=[{row_permission.user_name}], 角色=[{row_permission.role_name}]")
    
    # 执行同步命令
    run_pre_save_command(payload)
    
    # 返回同步结果及关键字段信息
    return {
        "message": "sync ok",
        "id": permission_id,
        "db_name": row_permission.db_name,
        "table_name": row_permission.table_name,
        "user_name": row_permission.user_name,
        "role_name": row_permission.role_name
    }

def sync_delete_row_permission(*, permission_id: int, db_name: str, table_name: str, user_name: Optional[str] = None, role_name: Optional[str] = None):
    """同步删除行权限
    
    参数:
        permission_id: 权限记录ID
        db_name: 数据库名称
        table_name: 表名称
        user_name: 用户名（可选）
        role_name: 角色名（可选）
    """
    try:
        # 准备删除同步参数
        payload = {
            "action": "sync_delete_row_permission",
            "id": permission_id,
            "db_name": db_name,
            "table_name": table_name
        }
        
        # 添加可选参数
        if user_name:
            payload["user_name"] = user_name
        if role_name:
            payload["role_name"] = role_name
            
        # 记录同步请求
        logger.info(f"[行权限模块] 同步删除行权限: ID={permission_id}, 数据库=[{db_name}], 表=[{table_name}], 用户=[{user_name}], 角色=[{role_name}]")
        
        # 执行同步命令
        run_pre_save_command(payload)
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"[行权限模块] 同步删除行权限失败 ID={permission_id}: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_row_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user)
):
    """删除行权限并同步到外部系统"""
    # 先获取权限记录详情，用于后续同步
    permission = db.query(RowPermission).filter(RowPermission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行权限不存在"
        )
    
    # 保存必要的同步信息
    db_name = permission.db_name
    table_name = permission.table_name
    user_name = permission.user_name
    role_name = permission.role_name
    
    # 执行删除操作
    result = delete_item(db, RowPermission, permission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除行权限失败"
        )
    
    # 添加同步任务到后台执行
    logger.info(f"[行权限模块] 添加删除同步任务: 行权限记录 ID={permission_id}")
    if background_tasks:
        background_tasks.add_task(
            sync_delete_row_permission,
            permission_id=permission_id,
            db_name=db_name,
            table_name=table_name,
            user_name=user_name,
            role_name=role_name
        )
    
    return None
