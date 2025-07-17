from typing import List, Optional, Dict, Any
from fastapi import Body
from app.utils.youcash_ranger_v2 import run as ranger_run
from app.utils.sync_helpers import with_sync_retry
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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
import argparse

logger = logging.getLogger(__name__)

router = APIRouter()

def run_ranger_command(payload: dict) -> None:
    """执行Ranger命令的内部函数"""
    # 首先定义 policy_name，确保它在 try-except 块之外也可见
    policy_name = ""
    try:
        # 从payload中提取数据库和表名，生成一个唯一的策略名称
        # 确保所有必需的键都存在
        required_keys = ['db_name', 'table_name']
        # 检查是否为批量同步的特殊操作
        is_batch_sync_action = payload.get('action') == 'sync_all_row_permissions'

        if not is_batch_sync_action:
            if not all(key in payload and payload[key] is not None for key in required_keys):
                raise ValueError("Payload for Ranger command must include 'db_name' and 'table_name'")
            policy_name = f"row_filter_{payload['db_name']}_{payload['table_name']}_{payload.get('user_name', '')}_{payload.get('role_name', '')}".replace(' ', '_')

        # 准备CLI参数
        args = argparse.Namespace(
            command=payload.get('action', 'grant'),
            policy_type='row-filter',
            service=['cm_hive', 'doris'],
            catalog=['internal', 'cdp_hive'],
            database=payload.get('db_name'),
            table=payload.get('table_name'),
            row_filter=payload.get('row_filter', ''),
            users=[payload.get('user_name')] if payload.get('user_name') else [],
            groups=[],
            roles=[payload.get('role_name')] if payload.get('role_name') else [],
            name=policy_name,  # 使用生成的策略名称
            accesses=['select']
        )
        logger.debug(f"[行权限模块] 准备执行命令: {args}")
        ranger_run(args)        
        logger.info(f"[行权限模块] 命令执行成功")
    except Exception as e:
        error_msg = f"执行命令失败: {e}"
        logger.critical(f"[行权限模块] {error_msg}")
        # 确保错误信息能够传递到前端
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/batch", response_model=List[RowPermissionOut])
def batch_create_row_permissions(
    *,
    db: Session = Depends(get_db),
    batch_data: Any = Body(...),  # 使用Any类型和Body，以便接受多种格式
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
    
    # 兼容两种输入格式：对象和数组
    logger.info(f"[行权限模块] 接收到批量请求数据类型: {type(batch_data)}")
    
    # 检测输入格式
    if isinstance(batch_data, list):
        # 如果是数组格式，直接使用
        items = batch_data
        batch_sync = False
        logger.info(f"[行权限模块] 检测到数组格式，包含{len(items)}条数据")
    elif hasattr(batch_data, 'items') and hasattr(batch_data, 'batch_sync'):
        # 如果是已经验证的RowPermissionBatchCreate对象
        items = batch_data.items
        batch_sync = batch_data.batch_sync
        logger.info(f"[行权限模块] 检测到标准对象格式，包含{len(items)}条数据")
    elif isinstance(batch_data, dict) and 'items' in batch_data:
        # 如果是字典格式且包含items字段
        items = batch_data.get('items', [])
        batch_sync = batch_data.get('batch_sync', False)
        logger.info(f"[行权限模块] 检测到字典对象格式，包含{len(items)}条数据")
    else:
        # 其他格式则报错
        error_msg = f"[行权限模块] 不支持的输入格式: {type(batch_data)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 记录同步模式
    logger.info(f"[行权限模块] 批量创建行权限，同步模式: {'批量' if batch_sync else '逐条'}")
    
    for i, permission_item in enumerate(items):
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
                "row_filter": permission_data.row_filter,
                "user_name": permission_data.user_name,
                "role_name": permission_data.role_name
            }
            
            if check_unique_constraint(db, RowPermission, constraint_fields):
                # 格式化冲突详情用于错误消息
                conflict_details = ", ".join([f"{k}='{v}'" for k, v in constraint_fields.items() if v is not None])
                error_message = f"相同的行权限记录已存在: ({conflict_details})"
                errors.append({
                    "index": i,
                    "error": error_message,
                    "data": permission_dict
                })
                continue
            
            # 创建行权限记录
            row_permission = create_item(db, RowPermission, permission_data.model_dump())
            results.append(RowPermissionOut.model_validate(row_permission))
            
            # 根据同步模式决定如何操作
            if not batch_sync:
                # 逐条同步模式：直接同步并捕获错误
                try:
                    sync_single_row_permission(
                        row_permission.id,
                        db=db,
                        module_name="行权限模块",
                        action="批量创建-逐条同步"
                    )
                except HTTPException as http_exc:
                    # 如果同步失败，记录错误并删除已创建的记录
                    errors.append({
                        "index": i,
                        "error": f"同步失败: {http_exc.detail}",
                        "data": permission_dict
                    })
                    db.delete(row_permission)
                    db.commit()
                    # 从成功列表中移除
                    results.pop()
            else:
                # 批量同步模式下，收集ID以便后续一次性同步
                permissions_to_sync.append(row_permission.id)
            
        except Exception as e:
            errors.append({
                "index": index,
                "error": str(e),
                "data": permission_dict
            })
    
    # 如果有错误，回滚并返回错误信息
    if errors and not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"批量创建行-权限失败，共 {len(errors)} 个错误",
                "errors": errors
            }
        )
    
    # 如果部分成功部分失败，返回成功的结果和错误信息
    if errors:
        # 这里我们仍然返回成功创建的记录，但在响应头中添加警告信息
        return results
    
    # 如果使用批量同步模式且有成功创建的记录，直接调用批量同步函数
    if batch_sync and permissions_to_sync:
        try:
            logger.info(f"[行权限模块] 批量同步模式，开始同步 {len(permissions_to_sync)} 条记录")
            sync_all_row_permissions(db=db, permission_ids=permissions_to_sync)
        except HTTPException as http_exc:
            # 批量同步失败，将错误信息附加到errors列表，并回滚所有已创建的记录
            logger.error(f"[行权限模块] 批量同步失败，将回滚 {len(results)} 条已创建的记录。")
            errors.append({
                "index": "all",
                "error": f"批量同步失败: {http_exc.detail}",
                "data": permissions_to_sync
            })
            created_ids = [r.id for r in results]
            db.query(RowPermission).filter(RowPermission.id.in_(created_ids)).delete(synchronize_session=False)
            db.commit()
            # 清空成功结果
            results = []
            # 抛出包含所有错误的最终异常
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"批量操作因同步失败而终止: {http_exc.detail} (共 {len(errors)} 个错误)",
                    "errors": errors
                }
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
        "row_filter": row_permission_in.row_filter,
        "user_name": row_permission_in.user_name,
        "role_name": row_permission_in.role_name
    }
    
    if check_unique_constraint(db, RowPermission, constraint_fields):
        raise HTTPException(
            status_code=400,
            detail="相同的行权限记录已存在"
        )
    
    # 创建行权限记录
    row_permission = create_item(db, RowPermission, row_permission_in.model_dump())

    # 直接同步行权限，确保错误能立即反馈到前端
    try:
        sync_single_row_permission(
            row_permission.id,
            db=db,
            module_name="行权限模块",
            action="创建同步"
        )
    except HTTPException as http_exc:
        # 如果同步失败，删除刚刚创建的记录，并抛出异常
        db.delete(row_permission)
        db.commit()
        raise http_exc

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
        "row_filter": params.row_filter,
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
    update_data = row_permission_in.model_dump(exclude_unset=True)
    if any(update_data.values()):
        # 构建约束检查字段
        constraint_fields = {}
        for field in ["db_name", "table_name", "row_filter", "user_name", "role_name"]:
            if field in update_data and update_data[field] is not None:
                constraint_fields[field] = update_data[field]
            else:
                constraint_fields[field] = getattr(row_permission, field)
        
        if check_unique_constraint(db, RowPermission, constraint_fields, permission_id):
            raise HTTPException(
                status_code=400,
                detail="更新后的行权限与现有记录冲突"
            )
    
    # 在更新前对原始数据执行删除同步
    try:
        # 对原始数据执行删除同步
        logger.info(f"[行权限模块] 更新前对原始数据执行删除同步: ID={permission_id}")
        sync_delete_row_permission(
            permission_id=permission_id,
            db_name=row_permission.db_name,
            table_name=row_permission.table_name,
            row_filter=row_permission.row_filter,
            user_name=row_permission.user_name,
            role_name=row_permission.role_name
        )
    except Exception as e:
        # 如果删除同步失败，记录错误但不中断更新操作
        logger.error(f"[行权限模块] 更新前删除同步失败: {str(e)}")
    
    # 更新记录
    updated_row_permission = update_item(db, RowPermission, permission_id, update_data)
    
    # 直接同步行权限，确保错误能立即反馈到前端
    try:
        sync_single_row_permission(
            permission_id,
            db=db,
            module_name="行权限模块",
            action="更新同步"
        )
    except HTTPException as http_exc:
        # 将同步失败的错误直接抛出，以便前端捕获
        raise http_exc

    return updated_row_permission

def sync_all_row_permissions(*, db: Session, permission_ids: List[int] = None):
    """同步所有或指定的行权限

    - 如果提供了 permission_ids，则只同步这些记录。
    - 如果未提供，则同步数据库中所有的行权限记录。
    - 在同步失败时，会抛出 HTTPException。
    """
    if permission_ids:
        permissions_to_sync = db.query(RowPermission).filter(RowPermission.id.in_(permission_ids)).all()
        log_message = f"开始同步指定的 {len(permissions_to_sync)} 条行权限记录"
    else:
        permissions_to_sync = db.query(RowPermission).all()
        log_message = f"开始同步所有行权限，共{len(permissions_to_sync)}条记录"

    total_count = len(permissions_to_sync)
    logger.info(f"[行权限模块] {log_message}")

    if total_count == 0:
        logger.warning("[行权限模块] 无行权限记录可同步")
        return

    success_count = 0
    failed_records = []

    for index, perm in enumerate(permissions_to_sync):
        try:
            payload = {
                "action": "grant",
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "row_filter": perm.row_filter,
                "user_name": perm.user_name,
                "role_name": perm.role_name
            }
            logger.info(f"[行权限模块] 同步记录 {index + 1}/{total_count}: ID={perm.id}")
            # run_ranger_command(payload)
            success_count += 1
        except Exception as e:
            error_detail = getattr(e, 'detail', str(e))
            logger.error(f"[行权限模块] 同步记录 ID={perm.id} 失败: {error_detail}")
            failed_records.append({
                "id": perm.id,
                "db_name": perm.db_name,
                "table_name": perm.table_name,
                "error": error_detail
            })

    if failed_records:
        error_summary = {
            "message": "批量同步操作完成，但部分记录失败。",
            "total": total_count,
            "succeeded": success_count,
            "failed": len(failed_records),
            "errors": failed_records
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_summary
        )
    logger.info(f"[行权限模块] 批量同步操作完成，成功 {success_count} 条，失败 {len(failed_records)} 条")
    return {
        "message": "批量同步操作完成",
        "total": total_count,
        "succeeded": success_count,
        "failed": 0,
        "errors": []
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
        "action": "grant",
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
    run_ranger_command(payload)
    
    # 返回同步结果及关键字段信息
    return {
        "message": "sync ok",
        "id": permission_id,
        "db_name": row_permission.db_name,
        "table_name": row_permission.table_name,
        "user_name": row_permission.user_name,
        "role_name": row_permission.role_name
    }

def sync_delete_row_permission(*, permission_id: int, db_name: str, table_name: str, row_filter: str, user_name: Optional[str] = None, role_name: Optional[str] = None):
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
            "action": "revoke",
            "id": permission_id,
            "db_name": db_name,
            "table_name": table_name,
            "row_filter": row_filter,
            "user_name": user_name,
            "role_name": role_name
        }
            
        # 记录同步请求
        logger.info(f"[行权限模块] 同步删除行权限: ID={permission_id}, 数据库=[{db_name}], 表=[{table_name}], 用户=[{user_name}], 角色=[{role_name}]")
        
        # 执行同步命令
        run_ranger_command(payload)
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
    row_filter = permission.row_filter
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
            row_filter=row_filter,
            user_name=user_name,
            role_name=role_name
        )
    
    return None
