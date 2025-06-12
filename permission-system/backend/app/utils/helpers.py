from typing import Dict, Any, List, TypeVar, Generic, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from pydantic import BaseModel

T = TypeVar('T')

def filter_query(query, model, filters: Dict[str, Any]):
    """根据过滤条件筛选查询"""
    for key, value in filters.items():
        if hasattr(model, key) and value is not None:
            if isinstance(value, str) and value.strip():
                query = query.filter(getattr(model, key).ilike(f"%{value}%"))
            elif value is not None:
                query = query.filter(getattr(model, key) == value)
    return query

def get_paginated_results(
    db: Session, 
    model: Any, 
    page: int = 1, 
    page_size: int = 10, 
    filters: Dict[str, Any] = None
):
    """获取分页结果"""
    if page <= 0:
        page = 1
    if page_size <= 0:
        page_size = 10
    
    query = db.query(model)
    
    if filters:
        query = filter_query(query, model, filters)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }

def check_unique_constraint(
    db: Session, 
    model: Any, 
    constraint_fields: Dict[str, Any], 
    id_value: Optional[int] = None
):
    """检查唯一约束是否冲突"""
    query = db.query(model)
    
    # 构建过滤条件
    filters = []
    for field, value in constraint_fields.items():
        if hasattr(model, field) and value is not None:
            filters.append(getattr(model, field) == value)
    
    # 如果有ID值，则排除当前记录(用于更新操作)
    if id_value is not None and hasattr(model, 'id'):
        query = query.filter(and_(*filters, model.id != id_value))
    else:
        query = query.filter(and_(*filters))
    
    # 检查是否存在记录
    if query.first():
        return True
    return False

def create_item(db: Session, model, data):
    """通用创建记录函数"""
    db_item = model(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, model, id: int, data: Dict[str, Any]):
    """通用更新记录函数"""
    db_item = db.query(model).filter(model.id == id).first()
    if not db_item:
        return None
    
    for key, value in data.items():
        if value is not None and hasattr(db_item, key):
            setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, model, id: int):
    """通用删除记录函数"""
    db_item = db.query(model).filter(model.id == id).first()
    if not db_item:
        return False
    
    db.delete(db_item)
    db.commit()
    return True
