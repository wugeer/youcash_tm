from typing import List, Optional, Any
from fastapi import Body
import argparse
from app.utils.youcash_ranger_v2 import run as ranger_run

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.utils.sync_helpers import with_sync_retry
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.core.db import get_db
from app.models.models import User, ColumnPermission
from app.schemas.schemas import (
    ColumnPermissionCreate, ColumnPermissionUpdate, ColumnPermissionOut,
    ColumnPermissionFilter, PaginatedResponse, ColumnPermissionBatchCreate
)
from app.utils.helpers import get_paginated_results, check_unique_constraint, create_item, update_item, delete_item
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def run_ranger_command(payload: dict):
    # 记录执行参数
    logger.info(f"[字段权限模块] 执行命令参数: {payload}")

    if payload['action'] == 'sync_column_permission':
        logger.info(f"[字段权限模块] 开始同步{payload['total']}条字段权限")
        return

    try:
        args = argparse.Namespace(
            command=payload['action'],
            policy_type="mask",
            service=['cm_hive', 'doris'],
            catalog=['internal', 'cdp_hive'],
            database=payload['db_name'],
            table=payload['table_name'],
            columns=[payload['col_name']],
            mask_type=payload['mask_type'],
            users=[payload['user_name']],
            groups=[],
            roles=[payload['role_name']],
            name=None,  # 添加缺失的name属性
            accesses=['select']  # 添加缺失的accesses属性，默认为select权限
        )
        logger.debug(f"[字段权限模块] 准备执行命令: {args}")
        ranger_run(args)
        logger.info(f"[字段权限模块] 命令执行成功")
    except Exception as e:
        # 未找到脚本时直接抛错
        logger.critical(f"[字段权限模块] 执行命令失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行命令失败: {e}")
    

@router.post("/batch", response_model=List[ColumnPermissionOut])
def batch_create_column_permissions(
    *,
    db: Session = Depends(get_db),
    batch_data: Any = Body(...),  # 使用Any类型和Body，以便接受多种格式
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """批量创建字段权限
    
    批量创建字段权限记录，可选批量同步模式
    - batch_sync=True: 所有记录一次性同步（适合大批量导入）
    - batch_sync=False: 逐条同步（默认模式）
    """
    results = []
    errors = []
    permissions_to_sync = []
    
    # 兼容两种输入格式：对象和数组
    logger.info(f"[字段权限模块] 接收到批量请求数据类型: {type(batch_data)}")
    
    # 检测输入格式
    if isinstance(batch_data, list):
        # 如果是数组格式，直接使用
        items = batch_data
        batch_sync = False
        logger.info(f"[字段权限模块] 检测到数组格式，包含{len(items)}条数据")
    elif hasattr(batch_data, 'items') and hasattr(batch_data, 'batch_sync'):
        # 如果是已经验证的ColumnPermissionBatchCreate对象
        items = batch_data.items
        batch_sync = batch_data.batch_sync
        logger.info(f"[字段权限模块] 检测到标准对象格式，包含{len(items)}条数据")
    elif isinstance(batch_data, dict) and 'items' in batch_data:
        # 如果是字典格式且包含items字段
        items = batch_data.get('items', [])
        batch_sync = batch_data.get('batch_sync', False)
        logger.info(f"[字段权限模块] 检测到字典对象格式，包含{len(items)}条数据")
    else:
        # 其他格式则报错
        error_msg = f"[字段权限模块] 不支持的输入格式: {type(batch_data)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 记录同步模式
    logger.info(f"[字段权限模块] 批量创建字段权限，同步模式: {'批量' if batch_sync else '逐条'}")
    
    for i, permission_item in enumerate(items):
        try:
            # 尝试创建并验证ColumnPermissionCreate对象
            try:
                permission_data = ColumnPermissionCreate.model_validate(permission_item)
                permission_dict = permission_data.model_dump()
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
                "mask_type": permission_data.mask_type,
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
            
            # 根据同步模式处理同步任务
            if not batch_sync:
                # 逐条同步模式，立即添加同步任务
                logger.info(f"[字段权限模块] 逐条同步模式: 添加同步任务，ID={column_permission.id}")
                background_tasks.add_task(
                    sync_single_column_permission,
                    column_permission.id,
                    db=db
                )
            else:
                # 批量同步模式，收集权限ID以便后续批量同步
                permissions_to_sync.append(column_permission.id)
                logger.info(f"[字段权限模块] 批量同步模式: 收集权限ID={column_permission.id}")
            
            
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e),
                "data": permission_item.model_dump() if hasattr(permission_item, 'model_dump') else permission_item.dict()
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
    
    # 如果使用批量同步模式且有成功创建的记录，启动批量同步任务
    if batch_sync and permissions_to_sync:
        total_to_sync = len(permissions_to_sync)
        logger.info(f"[字段权限模块] 批量同步模式，添加批量同步任务，共{total_to_sync}条记录")
        background_tasks.add_task(
            sync_all_column_permissions,
            db=db
        )
    
    return results

@router.post("/", response_model=ColumnPermissionOut)
def create_column_permission(
    *,
    db: Session = Depends(get_db),
    column_permission_in: ColumnPermissionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """创建列权限并自动执行同步"""
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
    column_permission = create_item(db, ColumnPermission, column_permission_in.model_dump())
    
    # 添加同步任务到后台执行
    logger.info(f"[字段权限模块] 添加同步任务: 新建权限记录 ID={column_permission.id}")
    background_tasks.add_task(
        sync_single_column_permission,
        column_permission.id,
        db=db
    )
    
    return ColumnPermissionOut.model_validate(column_permission)

@router.get("/", response_model=PaginatedResponse)
def get_column_permissions(
    db: Session = Depends(get_db),
    params: ColumnPermissionFilter = Depends(),
    current_user: User = Depends(get_current_active_user),
):
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
        sorters_list = [{'field': params.sort_field, 'order': params.sort_order}]
    elif params.sorters:
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
    background_tasks: BackgroundTasks,
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
    
    # 在更新前对原始数据执行删除同步
    try:
        # 对原始数据执行删除同步
        logger.info(f"[字段权限模块] 更新前对原始数据执行删除同步: ID={permission_id}")
        sync_delete_column_permission(
            permission_id=permission_id,
            db_name=column_permission.db_name,
            table_name=column_permission.table_name,
            column_name=column_permission.col_name,
            mask_type=column_permission.mask_type,
            user_name=column_permission.user_name,
            role_name=column_permission.role_name
        )
    except Exception as e:
        # 如果删除同步失败，记录错误但不中断更新操作
        logger.error(f"[字段权限模块] 更新前删除同步失败: {str(e)}")
    
    # 更新记录
    updated_column_permission = update_item(db, ColumnPermission, permission_id, update_data)
    
    # 添加同步任务到后台执行
    logger.info(f"[字段权限模块] 添加同步任务: 更新权限记录 ID={permission_id}")
    background_tasks.add_task(
        sync_single_column_permission,
        permission_id,
        db=db
    )
    
    return updated_column_permission

def sync_all_column_permissions(*, db: Session):
    """同步所有字段权限的内部函数，可以被后台任务调用
    
    参数:
        db: 数据库会话（关键字参数）
    """
    # 查询所有字段权限记录
    all_column_permissions = db.query(ColumnPermission).all()
    total_count = len(all_column_permissions)
    
    logger.info(f"[字段权限模块] 开始同步所有字段权限，共{total_count}条记录")
    
    if total_count == 0:
        logger.warning("[字段权限模块] 无字段权限记录可同步")
        return {"message": "sync ok", "total": 0, "synced": 0}
    
    # 先通知CLI脚本开始批量同步操作
    batch_payload = {
        "action": "sync_column_permissions",
        "total": total_count
    }
    run_ranger_command(batch_payload)
    
    # 记录成功和失败的同步操作
    success_count = 0
    failed_records = []
    
    # 依次同步每条记录
    for index, perm in enumerate(all_column_permissions):
        try:
            # 准备同步参数
            payload = {
                "action": "grant",
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "col_name": perm.col_name,
                "mask_type": perm.mask_type,
                "user_name": perm.user_name,
                "role_name": perm.role_name
            }
            
            # 记录同步请求
            logger.info(f"[字段权限模块] 同步记录 {index+1}/{total_count}: ID={perm.id}, 数据库=[{perm.db_name}], 表=[{perm.table_name}], 字段=[{perm.col_name}], 用户=[{perm.user_name}], 角色=[{perm.role_name}]")
            
            # 执行同步命令
            run_ranger_command(payload)
            success_count += 1
            
        except Exception as e:
            logger.error(f"[字段权限模块] 同步记录 ID={perm.id} 失败: {str(e)}")
            failed_records.append({
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "col_name": perm.col_name,
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
def sync_column_permissions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """同步所有字段权限API端点
    
    自动遍历数据库中的所有字段权限记录，并依次执行同步操作
    """
    return sync_all_column_permissions(db=db)

@router.post("/sync/{permission_id}", response_model=dict)
@with_sync_retry(max_attempts=1, retry_delay=2)
def sync_single_column_permission(
    permission_id: int,
    *,
    db: Session = Depends(get_db),
    module_name: str = "字段权限模块",
    action: str = "同步"
):
    """同步单个字段权限记录
    
    传递关键字段：数据库名、表名、字段名、脱敏类型、用户名、角色名
    """
    # 检查权限记录是否存在
    column_permission = db.query(ColumnPermission).filter(ColumnPermission.id == permission_id).first()
    if not column_permission:
        raise HTTPException(status_code=404, detail="字段权限记录不存在")
    
    # 准备同步参数，包含所有关键字段
    payload = {
        "action": "grant",
        "id": permission_id,
        "db_name": column_permission.db_name,
        "table_name": column_permission.table_name,
        "col_name": column_permission.col_name,
        "mask_type": column_permission.mask_type,
        "user_name": column_permission.user_name,
        "role_name": column_permission.role_name
    }
    
    # 记录同步请求
    logger.info(f"[字段权限模块] 同步单条记录: ID={permission_id}, 数据库=[{column_permission.db_name}], 表=[{column_permission.table_name}], 字段=[{column_permission.col_name}], 脱敏=[{column_permission.mask_type}]")
    
    # 执行同步命令
    run_ranger_command(payload)
    
    # 返回同步结果及关键字段信息
    return {
        "message": "sync ok",
        "id": permission_id,
        "db_name": column_permission.db_name,
        "table_name": column_permission.table_name,
        "col_name": column_permission.col_name,
        "mask_type": column_permission.mask_type,
        "user_name": column_permission.user_name,
        "role_name": column_permission.role_name
    }

def sync_delete_column_permission(*, permission_id: int, db_name: str, table_name: str, column_name: str, mask_type: str, user_name: Optional[str] = None, role_name: Optional[str] = None):
    """同步删除列权限
    
    参数:
        permission_id: 权限记录ID
        db_name: 数据库名称
        table_name: 表名称
        column_name: 列名称
        mask_type: 脱敏类型
        user_name: 用户名（可选）
        role_name: 角色名（可选）
    """
    try:
        # 准备删除同步参数
        payload = {
            "action": "revoke",
            "id": permission_id,
            "db_name": db_name,
            "table_name": table_name,
            "col_name": column_name,
            "mask_type": mask_type,
            "user_name": user_name,
            "role_name": role_name
        }
        
        # 记录同步请求
        logger.info(f"[列权限模块] 同步删除列权限: ID={permission_id}, 数据库=[{db_name}], 表=[{table_name}], 列=[{column_name}], 脱敏=[{mask_type}], 用户=[{user_name}], 角色=[{role_name}]")
        
        # 执行同步命令
        run_ranger_command(payload)
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"[列权限模块] 同步删除列权限失败 ID={permission_id}: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user)
):
    """删除列权限并同步到外部系统"""
    # 先获取权限记录详情，用于后续同步
    permission = db.query(ColumnPermission).filter(ColumnPermission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="列权限不存在"
        )
    
    # 保存必要的同步信息
    db_name = permission.db_name
    table_name = permission.table_name
    column_name = permission.col_name
    mask_type = permission.mask_type
    user_name = permission.user_name
    role_name = permission.role_name
    
    # 执行删除操作
    result = delete_item(db, ColumnPermission, permission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除列权限失败"
        )
    
    # 添加同步任务到后台执行
    logger.info(f"[列权限模块] 添加删除同步任务: 列权限记录 ID={permission_id}")
    if background_tasks:
        background_tasks.add_task(
            sync_delete_column_permission,
            permission_id=permission_id,
            db_name=db_name,
            table_name=table_name,
            column_name=column_name,
            mask_type=mask_type,
            user_name=user_name,
            role_name=role_name
        )
    
    return None
