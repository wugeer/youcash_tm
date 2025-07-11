from fastapi import APIRouter, Depends, HTTPException, Query, Body
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

router = APIRouter(
    prefix="/hdfs-quotas",
    tags=["hdfs-quotas"]
)


@router.post("/", response_model=HdfsQuotaOut)
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


@router.get("/", response_model=PaginatedResponse)
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
    
    if sort_field and hasattr(HdfsQuota, sort_field):
        sort_column = getattr(HdfsQuota, sort_field)
        if sort_order == "descend":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    else:
        # 默认按创建时间排序
        query = query.order_by(desc(HdfsQuota.created_at))
    
    # 分页
    items = query.offset((filter_params.page - 1) * filter_params.page_size) \
                .limit(filter_params.page_size) \
                .all()
    
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
    """删除指定ID的HDFS配额记录"""
    db_hdfs_quota = db.query(HdfsQuota).filter(HdfsQuota.id == hdfs_quota_id).first()
    if not db_hdfs_quota:
        raise HTTPException(
            status_code=404,
            detail=f"ID为 {hdfs_quota_id} 的配额记录不存在"
        )
    
    db.delete(db_hdfs_quota)
    db.commit()
    
    return {"detail": "配额记录已成功删除"}
