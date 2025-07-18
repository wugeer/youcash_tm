from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Role
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def get_roles(
    name: Optional[str] = Query(None, description="按角色名称筛选"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """获取所有角色"""
    try:
        query = db.query(Role)
        
        # 如果提供了名称，则进行模糊搜索
        if name:
            query = query.filter(Role.role_name.contains(name))
            
        roles = query.offset(skip).limit(limit).all()
        
        # 手动处理字段映射
        result = []
        for role in roles:
            role_dict = {
                'id': role.id,
                'name': role.role_name,  # 将role_name映射到name字段
                'description': role.description,
                'created_at': role.created_at,
                'updated_at': role.updated_at
            }
            result.append(role_dict)
            
        return result
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """获取角色详情"""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role is None:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 手动处理字段映射
        role_dict = {
            'id': role.id,
            'name': role.role_name,  # 将role_name映射到name字段
            'description': role.description,
            'created_at': role.created_at,
            'updated_at': role.updated_at
        }
        return role_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色详情失败: {str(e)}")


@router.post("/", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """创建新角色"""
    try:
        # 检查角色是否已存在
        db_role = db.query(Role).filter(Role.role_name == role.name).first()
        if db_role:
            raise HTTPException(status_code=400, detail="角色名已存在")
        
        # 创建新角色
        db_role = Role(
            role_name=role.name,
            description=role.description
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        
        # 手动处理字段映射
        role_dict = {
            'id': db_role.id,
            'name': db_role.role_name,  # 将role_name映射到name字段
            'description': db_role.description,
            'created_at': db_role.created_at,
            'updated_at': db_role.updated_at
        }
        return role_dict
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建角色失败: {str(e)}")


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    """更新角色"""
    try:
        # 查找角色
        db_role = db.query(Role).filter(Role.id == role_id).first()
        if db_role is None:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 检查名称是否已被其他角色使用
        if role.name:
            existing_role = db.query(Role).filter(Role.role_name == role.name, Role.id != role_id).first()
            if existing_role:
                raise HTTPException(status_code=400, detail="角色名已存在")
        
        # 更新角色
        if role.name:
            db_role.role_name = role.name
        if role.description is not None:
            db_role.description = role.description
        
        db.commit()
        db.refresh(db_role)
        
        # 手动处理字段映射
        role_dict = {
            'id': db_role.id,
            'name': db_role.role_name,  # 将role_name映射到name字段
            'description': db_role.description,
            'created_at': db_role.created_at,
            'updated_at': db_role.updated_at
        }
        return role_dict
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新角色失败: {str(e)}")


@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """删除角色"""
    try:
        # 查找角色
        db_role = db.query(Role).filter(Role.id == role_id).first()
        if db_role is None:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 删除角色
        db.delete(db_role)
        db.commit()
        return {"message": "角色删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除角色失败: {str(e)}")
