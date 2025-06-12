from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# 用户相关模式
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# 角色相关模式
class RoleBase(BaseModel):
    role_name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# 用户角色相关模式
class UserRoleCreate(BaseModel):
    user_id: int
    role_id: int

class UserRoleOut(BaseModel):
    id: int
    user_id: int
    role_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Token相关模式
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 表权限相关模式
class TablePermissionBase(BaseModel):
    db_name: str = Field(..., max_length=100)
    table_name: str = Field(..., max_length=100)
    user_name: str = Field(..., max_length=50)
    role_name: str = Field(..., max_length=50)

class TablePermissionCreate(TablePermissionBase):
    pass

class TablePermissionUpdate(BaseModel):
    db_name: Optional[str] = Field(None, max_length=100)
    table_name: Optional[str] = Field(None, max_length=100)
    user_name: Optional[str] = Field(None, max_length=50)
    role_name: Optional[str] = Field(None, max_length=50)

class TablePermissionOut(TablePermissionBase):
    id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

# 列权限相关模式
class ColumnPermissionBase(BaseModel):
    db_name: str = Field(..., max_length=100)
    table_name: str = Field(..., max_length=100)
    col_name: str = Field(..., max_length=100)
    mask_type: str = Field(..., max_length=50)
    user_name: str = Field(..., max_length=50)
    role_name: str = Field(..., max_length=50)
    
    @validator('mask_type')
    def validate_mask_type(cls, v):
        valid_types = ['手机号', '身份证', '银行卡号', '座机号', '姓名', '原文']
        if v not in valid_types:
            raise ValueError(f'mask_type必须是以下类型之一: {", ".join(valid_types)}')
        return v

class ColumnPermissionCreate(ColumnPermissionBase):
    pass

class ColumnPermissionUpdate(BaseModel):
    db_name: Optional[str] = Field(None, max_length=100)
    table_name: Optional[str] = Field(None, max_length=100)
    col_name: Optional[str] = Field(None, max_length=100)
    mask_type: Optional[str] = Field(None, max_length=50)
    user_name: Optional[str] = Field(None, max_length=50)
    role_name: Optional[str] = Field(None, max_length=50)
    
    @validator('mask_type')
    def validate_mask_type(cls, v):
        if v is None:
            return v
        valid_types = ['手机号', '身份证', '银行卡号', '座机号', '姓名', '原文']
        if v not in valid_types:
            raise ValueError(f'mask_type必须是以下类型之一: {", ".join(valid_types)}')
        return v

class ColumnPermissionOut(ColumnPermissionBase):
    id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

# 行权限相关模式
class RowPermissionBase(BaseModel):
    db_name: str = Field(..., max_length=100)
    table_name: str = Field(..., max_length=100)
    row_filter: str
    user_name: str = Field(..., max_length=50)
    role_name: str = Field(..., max_length=50)

class RowPermissionCreate(RowPermissionBase):
    pass

class RowPermissionUpdate(BaseModel):
    db_name: Optional[str] = Field(None, max_length=100)
    table_name: Optional[str] = Field(None, max_length=100)
    row_filter: Optional[str] = None
    user_name: Optional[str] = Field(None, max_length=50)
    role_name: Optional[str] = Field(None, max_length=50)

class RowPermissionOut(RowPermissionBase):
    id: int
    create_time: datetime
    
    class Config:
        orm_mode = True

# 分页响应
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List

# 查询过滤器
class TablePermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10

class ColumnPermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    col_name: Optional[str] = None
    mask_type: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10

class RowPermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10
