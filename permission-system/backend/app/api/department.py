from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Department
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[DepartmentResponse])
def get_departments(
    name: Optional[str] = Query(None, description="按部门名称筛选"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """获取所有部门"""
    try:
        query = db.query(Department)
        if name:
            query = query.filter(Department.name.contains(name))
        departments = query.offset(skip).limit(limit).all()
        return departments
    except Exception as e:
        logger.error(f"获取部门列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取部门列表失败: {str(e)}")

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    """获取部门详情"""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if department is None:
            raise HTTPException(status_code=404, detail="部门不存在")
        return department
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取部门详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取部门详情失败: {str(e)}")

@router.post("/", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    """创建新部门"""
    try:
        # 检查部门是否已存在
        db_department = db.query(Department).filter(Department.name == department.name).first()
        if db_department:
            raise HTTPException(status_code=400, detail="部门名已存在")
        
        # 创建新部门
        db_department = Department(
            name=department.name,
            description=department.description
        )
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        return db_department
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建部门失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建部门失败: {str(e)}")

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, department: DepartmentUpdate, db: Session = Depends(get_db)):
    """更新部门"""
    try:
        # 查找部门
        db_department = db.query(Department).filter(Department.id == department_id).first()
        if db_department is None:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 检查名称是否已被其他部门使用
        if department.name:
            existing_department = db.query(Department).filter(Department.name == department.name, Department.id != department_id).first()
            if existing_department:
                raise HTTPException(status_code=400, detail="部门名已存在")
        
        # 更新部门
        if department.name:
            db_department.name = department.name
        if department.description is not None:
            db_department.description = department.description
        
        db.commit()
        db.refresh(db_department)
        return db_department
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新部门失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新部门失败: {str(e)}")

@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    """删除部门"""
    try:
        # 查找部门
        db_department = db.query(Department).filter(Department.id == department_id).first()
        if db_department is None:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 删除部门
        db.delete(db_department)
        db.commit()
        return {"message": "部门删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除部门失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除部门失败: {str(e)}")
