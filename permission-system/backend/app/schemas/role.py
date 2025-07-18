from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")

class RoleCreate(RoleBase):
    """创建角色请求模型"""
    pass

class RoleUpdate(BaseModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")

class RoleResponse(RoleBase):
    """角色响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        
        # 字段别名映射，将数据库模型的role_name映射到响应模型的name
        fields = {
            'role_name': 'name',
        }
