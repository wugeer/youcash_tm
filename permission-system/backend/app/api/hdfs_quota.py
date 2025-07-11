from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.models.models import HdfsQuota
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
    
class HdfsQuotaBatchRequest(RootModel):
    root: List[HdfsQuotaBatchItem]
    
class BatchImportResponse(BaseModel):
    total: int
    success: int
    failed: int
    failed_records: List[Dict[str, Any]] = []
    
router = APIRouter()


@router.post("", response_model=HdfsQuotaOut)
def create_hdfs_quota(hdfs_quota: HdfsQuotaCreate, db: Session = Depends(get_db)):
    """创建新的HDFS配额记录"""
    try:
        db_hdfs_quota = HdfsQuota(
            db_name=hdfs_quota.db_name,
            hdfs_quota=hdfs_quota.hdfs_quota
        )
        db.add(db_hdfs_quota)
        db.commit()
        db.refresh(db_hdfs_quota)
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
    
    print(f"DEBUG: sort_field={sort_field}, sort_order={sort_order}")
    
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
        print(f"DEBUG: 排序字段匹配成功: {mapped_field}")
        sort_column = getattr(HdfsQuota, mapped_field)
        if sort_order == "descend":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        # 默认按创建时间排序
        print(f"DEBUG: 使用默认排序: created_at desc")
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
        return db_hdfs_quota
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"数据库名 '{hdfs_quota.db_name}' 的配额记录已存在"
        )


@router.delete("/{hdfs_quota_id}")
def delete_hdfs_quota(hdfs_quota_id: int, db: Session = Depends(get_db)):
    """删除HDFS配额记录"""
    db_hdfs_quota = db.query(HdfsQuota).filter(HdfsQuota.id == hdfs_quota_id).first()
    if not db_hdfs_quota:
        raise HTTPException(status_code=404, detail="HDFS配额记录不存在")

    db.delete(db_hdfs_quota)
    db.commit()
    return {"message": "删除成功"}


@router.post("/batch-import", response_model=BatchImportResponse)
def batch_import_hdfs_quotas(
    batch_data: HdfsQuotaBatchRequest,
    db: Session = Depends(get_db)
):
    """批量导入HDFS配额记录
    
    批量导入HDFS配额记录，每条记录包含：
    - db_name: 数据库名，不能为空
    - hdfs_quota: HDFS配额(GB)，必须是正数
    """
    # 结果统计
    result = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "failed_records": []
    }
    
    try:
        # 获取数据列表
        items = batch_data.root
        result["total"] = len(items)
        
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
                else:
                    # 否则添加新记录
                    db_hdfs_quota = HdfsQuota(
                        db_name=item.db_name,
                        hdfs_quota=item.hdfs_quota
                    )
                    db.add(db_hdfs_quota)
                
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
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
        
    return result
