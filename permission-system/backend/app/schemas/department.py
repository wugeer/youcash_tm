from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DepartmentBase(BaseModel):
    """部门基础模型"""
    name: str = Field(..., description="部门名称")
    description: Optional[str] = Field(None, description="部门描述")

class DepartmentCreate(DepartmentBase):
    """创建部门请求模型"""
    pass

class DepartmentUpdate(BaseModel):
    """更新部门请求模型"""
    name: Optional[str] = Field(None, description="部门名称")
    description: Optional[str] = Field(None, description="部门描述")

class DepartmentResponse(DepartmentBase):
    """部门响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
