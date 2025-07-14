from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form, BackgroundTasks, status
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

from app.utils.sync_helpers import with_sync_retry
logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import HdfsQuota, User
from app.api.auth import get_current_active_user
from app.schemas.schemas import (
    HdfsQuotaCreate, 
    HdfsQuotaUpdate, 
    HdfsQuotaOut, 
    HdfsQuotaFilter,
    PaginatedResponse
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from pydantic import BaseModel, RootModel
from typing import Dict, Any

# 批量导入请求和响应模型
class HdfsQuotaBatchItem(BaseModel):
    db_name: str
    hdfs_quota: float
    
class HdfsQuotaBatchRequest(BaseModel):
    items: List[HdfsQuotaBatchItem]
    batch_sync: bool = False  # 添加批量同步选项，默认为逻条同步
    
class BatchImportResponse(BaseModel):
    total: int
    success: int
    failed: int
    failed_records: List[Dict[str, Any]] = []
    
router = APIRouter()

# 预执行命令
def run_pre_save_command(payload: dict) -> None:
    # 记录执行参数
    logger.info(f"[HDFS配额模块] 执行命令参数: {payload}")
    
    cmd = ["python", "example_cli.py", json.dumps(payload)]
    try:
        logger.debug(f"[HDFS配额模块] 准备执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        logger.info(f"[HDFS配额模块] 命令执行结果: 返回码={result.returncode}, 输出={result.stdout.strip()}, 错误={result.stderr.strip()}")
        
        if result.returncode != 0:
            logger.error(f"[HDFS配额模块] 预执行命令失败: {result.stderr.strip() or '未知错误'}")
            raise HTTPException(status_code=400, detail=f"预执行命令失败: {result.stderr.strip() or '未知错误'}")
        logger.info(f"[HDFS配额模块] 命令执行成功")
    except FileNotFoundError:
        # 未找到脚本时直接抛错
        logger.critical(f"[HDFS配额模块] 脚本文件不存在: example_cli.py")
        raise HTTPException(status_code=500, detail="预执行命令脚本不存在")


@router.post("", response_model=HdfsQuotaOut)
def create_hdfs_quota(
    hdfs_quota: HdfsQuotaCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建新的HDFS配额记录，并自动执行同步操作"""
    try:
        db_hdfs_quota = HdfsQuota(
            db_name=hdfs_quota.db_name,
            hdfs_quota=hdfs_quota.hdfs_quota
        )
        db.add(db_hdfs_quota)
        db.commit()
        db.refresh(db_hdfs_quota)
        
        # 添加同步任务到后台执行
        logger.info(f"[HDFS配额模块] 添加同步任务: 新建配额记录 ID={db_hdfs_quota.id}")
        background_tasks.add_task(
            sync_single_hdfs_quota,
            db_hdfs_quota.id,
            db=db
        )
        
        return db_hdfs_quota
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"数据库名 '{hdfs_quota.db_name}' 的配额记录已存在"
        )


@router.get("", response_model=PaginatedResponse)
def get_hdfs_quotas(
    filter_params: HdfsQuotaFilter = Depends(),
    db: Session = Depends(get_db)
):
    """获取HDFS配额列表，支持筛选和排序"""
    query = db.query(HdfsQuota)
    
    # 应用过滤条件
    if filter_params.db_name:
        query = query.filter(HdfsQuota.db_name.ilike(f"%{filter_params.db_name}%"))
    
    # 计算总数
    total = query.count()
    
    # 应用排序
    sort_field = filter_params.sort_field
    sort_order = filter_params.sort_order
    
    
    # 定义前端字段名与模型属性的映射
    field_mapping = {
        'db_name': 'db_name',
        'hdfs_quota': 'hdfs_quota',
        'created_at': 'created_at',
        'updated_at': 'updated_at'
    }
    
    # 如果sort_field存在于映射中，则使用映射的属性名
    mapped_field = field_mapping.get(sort_field)
    
    if sort_field and mapped_field and hasattr(HdfsQuota, mapped_field):
        sort_column = getattr(HdfsQuota, mapped_field)
        if sort_order == "descend":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        # 默认按创建时间排序
        query = query.order_by(desc(HdfsQuota.created_at))
    
    # 分页
    db_items = query.offset((filter_params.page - 1) * filter_params.page_size) \
                .limit(filter_params.page_size) \
                .all()
    
    # 将SQLAlchemy对象转换为Pydantic对象
    items = [HdfsQuotaOut.model_validate(item) for item in db_items]
    
    return {
        "total": total,
        "page": filter_params.page,
        "page_size": filter_params.page_size,
        "items": items
    }


@router.get("/{hdfs_quota_id}", response_model=HdfsQuotaOut)
def get_hdfs_quota(hdfs_quota_id: int, db: Session = Depends(get_db)):
    """获取指定ID的HDFS配额记录"""
    db_hdfs_quota = db.query(HdfsQuota).filter(HdfsQuota.id == hdfs_quota_id).first()
    if not db_hdfs_quota:
        raise HTTPException(
            status_code=404,
            detail=f"ID为 {hdfs_quota_id} 的配额记录不存在"
        )
    return db_hdfs_quota


@router.put("/{hdfs_quota_id}", response_model=HdfsQuotaOut)
def update_hdfs_quota(
    hdfs_quota_id: int, 
    hdfs_quota: HdfsQuotaUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """更新指定ID的HDFS配额记录"""
    db_hdfs_quota = db.query(HdfsQuota).filter(HdfsQuota.id == hdfs_quota_id).first()
    if not db_hdfs_quota:
        raise HTTPException(
            status_code=404,
            detail=f"ID为 {hdfs_quota_id} 的配额记录不存在"
        )
    
    # 更新数据
    update_data = hdfs_quota.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_hdfs_quota, key, value)
    
    try:
        db.commit()
        db.refresh(db_hdfs_quota)
        
        # 添加同步任务到后台执行
        logger.info(f"[HDFS配额模块] 添加同步任务: 更新配额记录 ID={db_hdfs_quota.id}")
        background_tasks.add_task(
            sync_single_hdfs_quota,
            db_hdfs_quota.id,
            db=db
        )
        
        return db_hdfs_quota
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"数据库名 '{hdfs_quota.db_name}' 的配额记录已存在"
        )


def sync_delete_hdfs_quota(*, quota_id: int, db_name: str):
    """同步删除HDFS配额
    
    参数:
        quota_id: 配额记录ID
        db_name: 数据库名称
    """
    try:
        # 准备删除同步参数
        # 使用现有的"sync_single_hdfs_quota"操作，并添加is_delete标志
        payload = {
            "action": "sync_single_hdfs_quota",
            "id": quota_id,
            "db_name": db_name,
            "hdfs_quota": 0,  # 设置为0，表示删除
            "is_delete": True  # 添加删除标志
        }
            
        # 记录同步请求
        logger.info(f"[HDFS配额模块] 同步删除HDFS配额: ID={quota_id}, 数据库=[{db_name}]")
        
        # 执行同步命令
        run_pre_save_command(payload)
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"[HDFS配额模块] 同步删除HDFS配额失败 ID={quota_id}: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.delete("/{hdfs_quota_id}")
def delete_hdfs_quota(
    hdfs_quota_id: int, 
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user)
):
    """删除HDFS配额记录并同步到外部系统"""
    # 先获取配额记录详情，用于后续同步
    db_hdfs_quota = db.query(HdfsQuota).filter(HdfsQuota.id == hdfs_quota_id).first()
    if not db_hdfs_quota:
        raise HTTPException(status_code=404, detail="HDFS配额记录不存在")
    
    # 保存必要的同步信息
    db_name = db_hdfs_quota.db_name
    
    # 执行删除操作
    db.delete(db_hdfs_quota)
    db.commit()
    
    # 添加同步任务到后台执行
    logger.info(f"[HDFS配额模块] 添加删除同步任务: HDFS配额记录 ID={hdfs_quota_id}")
    if background_tasks:
        background_tasks.add_task(
            sync_delete_hdfs_quota,
            quota_id=hdfs_quota_id,
            db_name=db_name
        )
    
    return {"message": "删除成功"}


@router.post("/sync", response_model=dict)
def sync_hdfs_quotas(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """同步所有HDFS配额
    
    自动遍历数据库中的所有HDFS配额记录，并依次执行同步操作
    """
    # 查询所有HDFS配额记录
    all_hdfs_quotas = db.query(HdfsQuota).all()
    total_count = len(all_hdfs_quotas)
    
    logger.info(f"[HDFS配额模块] 开始同步所有HDFS配额，共{total_count}条记录")
    
    if total_count == 0:
        logger.warning("[HDFS配额模块] 无配额记录可同步")
        return {"message": "sync ok", "total": 0, "synced": 0}
    
    # 先通知CLI脚本开始批量同步操作
    batch_payload = {
        "action": "sync_hdfs_quotas",
        "total": total_count
    }
    run_pre_save_command(batch_payload)
    
    # 记录成功和失败的同步操作
    success_count = 0
    failed_records = []
    
    # 依次同步每条记录
    for index, quota in enumerate(all_hdfs_quotas):
        try:
            # 准备同步参数
            payload = {
                "action": "sync_single_hdfs_quota",
                "id": quota.id,
                "db_name": quota.db_name,
                "hdfs_quota": quota.hdfs_quota
            }
            
            # 记录同步请求
            logger.info(f"[HDFS配额模块] 同步记录 {index+1}/{total_count}: ID={quota.id}, 数据库={quota.db_name}, 配额={quota.hdfs_quota}")
            
            # 执行同步命令
            run_pre_save_command(payload)
            success_count += 1
            
        except Exception as e:
            logger.error(f"[HDFS配额模块] 同步记录 ID={quota.id} 失败: {str(e)}")
            failed_records.append({
                "id": quota.id,
                "db_name": quota.db_name,
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

@router.post("/sync/{quota_id}", response_model=dict)
@with_sync_retry(max_attempts=3, retry_delay=2)
def sync_single_hdfs_quota(
    quota_id: int,
    *,
    db: Session = Depends(get_db),
    module_name: str = "HDFS配额模块",
    action: str = "同步"
):
    """同步单个HDFS配额
    
    根据配额ID获取db_name和hdfs_quota参数并进行同步
    """
    # 检查配额记录是否存在
    hdfs_quota_record = db.query(HdfsQuota).filter(HdfsQuota.id == quota_id).first()
    if not hdfs_quota_record:
        raise HTTPException(status_code=404, detail="HDFS配额记录不存在")
    
    # 准备同步参数
    payload = {
        "action": "sync_single_hdfs_quota", 
        "id": quota_id,
        "db_name": hdfs_quota_record.db_name,
        "hdfs_quota": hdfs_quota_record.hdfs_quota
    }
    
    # 记录同步请求
    logger.info(f"[HDFS配额模块] 收到单条同步请求: {payload}")
    
    # 执行同步命令
    run_pre_save_command(payload)
    return {
        "message": "sync ok", 
        "id": quota_id, 
        "db_name": hdfs_quota_record.db_name, 
        "hdfs_quota": hdfs_quota_record.hdfs_quota
    }

@router.post("/batch-import", response_model=BatchImportResponse)
def batch_import_hdfs_quotas(
    batch_data: HdfsQuotaBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量导入HDFS配额记录
    
    批量导入HDFS配额记录，每条记录包含：
    - db_name: 数据库名，不能为空
    - hdfs_quota: HDFS配额(GB)，必须是正数
    
    所有成功导入的记录会自动执行同步操作
    """
    # 结果统计
    result = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "failed_records": []
    }
    
    # 记录需要同步的配额ID列表
    quotas_to_sync = []
    
    try:
        # 获取数据列表
        items = batch_data.items
        result["total"] = len(items)
        
        # 获取同步方式
        batch_sync = batch_data.batch_sync
        
        # 处理每一条记录
        for index, item in enumerate(items):
            try:
                # 数据验证
                if not item.db_name or not item.db_name.strip():
                    result["failed"] += 1
                    result["failed_records"].append({
                        "row": index + 1, 
                        "error": "数据库名不能为空",
                        "data": {"db_name": item.db_name, "hdfs_quota": item.hdfs_quota}
                    })
                    continue
                
                if item.hdfs_quota <= 0:
                    result["failed"] += 1
                    result["failed_records"].append({
                        "row": index + 1, 
                        "error": "HDFS配额必须是大于0的数值",
                        "data": {"db_name": item.db_name, "hdfs_quota": item.hdfs_quota}
                    })
                    continue
                
                # 检查是否已存在
                existing = db.query(HdfsQuota).filter(HdfsQuota.db_name == item.db_name).first()
                
                if existing:
                    # 如果已存在，更新配额值
                    existing.hdfs_quota = item.hdfs_quota
                    # 记录需要同步的ID
                    quotas_to_sync.append(existing.id)
                else:
                    # 否则添加新记录
                    db_hdfs_quota = HdfsQuota(
                        db_name=item.db_name,
                        hdfs_quota=item.hdfs_quota
                    )
                    db.add(db_hdfs_quota)
                    db.flush() # 获取新记录的ID
                    quotas_to_sync.append(db_hdfs_quota.id)
                
                result["success"] += 1
                
            except IntegrityError:
                db.rollback()
                result["failed"] += 1
                result["failed_records"].append({
                    "row": index + 1, 
                    "error": f"数据库名'{item.db_name}'的配额记录已存在",
                    "data": {"db_name": item.db_name, "hdfs_quota": item.hdfs_quota}
                })
            except Exception as e:
                result["failed"] += 1
                result["failed_records"].append({
                    "row": index + 1, 
                    "error": str(e),
                    "data": {"db_name": item.db_name, "hdfs_quota": item.hdfs_quota}
                })
        
        # 提交所有成功的更改
        db.commit()
        
        # 对成功导入的记录添加同步任务
        if quotas_to_sync:
            logger.info(f"[HDFS配额模块] 批量导入后添加同步任务，共 {len(quotas_to_sync)} 条记录，同步方式: {'批量' if batch_sync else '逐条'}")
            
            if batch_sync and quotas_to_sync:
                # 批量同步模式 - 添加一个后台任务执行所有配额的同步
                background_tasks.add_task(
                    sync_hdfs_quotas,
                    db=db
                )
            else:
                # 逻条同步模式 - 为每条记录添加一个同步任务
                for quota_id in quotas_to_sync:
                    background_tasks.add_task(
                        sync_single_hdfs_quota,
                        quota_id,
                        db=db
                    )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
        
    return result
