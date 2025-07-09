from pydantic import BaseModel, Field, validator, root_validator, ValidationError
from typing import Optional, List, Literal
import json
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
        from_attributes = True

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
        from_attributes = True

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
        from_attributes = True

# Token相关模式
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 表权限相关模式
class TablePermissionBase(BaseModel):
    db_name: str = Field(..., description="数据库名", max_length=100)
    table_name: str = Field(..., description="表名", max_length=100)
    user_name: Optional[str] = Field(None, description="用户名", max_length=50)
    role_name: Optional[str] = Field(None, description="角色名", max_length=50)

    @root_validator(skip_on_failure=True)
    def check_user_or_role_present(cls, values):
        user_name, role_name = values.get('user_name'), values.get('role_name')
        # db_name and table_name are required by Field(...)
        # Pydantic's own validation will catch their absence before this validator runs (due to skip_on_failure=True).
        if not user_name and not role_name:
            raise ValueError('用户名和角色名至少需要提供一个')
        return values
        
# 批量导入表权限的Schema
class TablePermissionBatchCreate(BaseModel):
    items: List[TablePermissionBase]

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
        from_attributes = True

# 列权限相关模式
class ColumnPermissionBase(BaseModel):
    db_name: str = Field(..., max_length=100)
    table_name: str = Field(..., max_length=100)
    col_name: str = Field(..., max_length=100)
    mask_type: str = Field(..., max_length=50)
    user_name: Optional[str] = Field(None, description="用户名", max_length=50)
    role_name: Optional[str] = Field(None, description="角色名", max_length=50)
    
    @root_validator(skip_on_failure=True)
    def check_user_or_role_present(cls, values):
        user_name, role_name = values.get('user_name'), values.get('role_name')
        if not user_name and not role_name:
            raise ValueError('用户名和角色名至少需要提供一个')
        return values

    @validator('mask_type')
    def validate_mask_type(cls, v):
        valid_types = ['手机号', '身份证', '银行卡号', '座机号', '姓名', '原文']
        if v not in valid_types:
            raise ValueError(f'mask_type必须是以下类型之一: {", ".join(valid_types)}')
        return v

# 批量导入字段权限的Schema
class ColumnPermissionBatchCreate(BaseModel):
    items: List[ColumnPermissionBase]

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
        from_attributes = True

# 行权限相关模式
class RowPermissionBase(BaseModel):
    db_name: str = Field(..., max_length=100)
    table_name: str = Field(..., max_length=100)
    row_filter: str
    user_name: Optional[str] = Field(None, description="用户名", max_length=50)
    role_name: Optional[str] = Field(None, description="角色名", max_length=50)

    @root_validator(skip_on_failure=True)
    def check_user_or_role_present(cls, values):
        user_name, role_name = values.get('user_name'), values.get('role_name')
        if not user_name and not role_name:
            raise ValueError('用户名和角色名至少需要提供一个')
        return values

# 批量导入行权限的Schema
class RowPermissionBatchCreate(BaseModel):
    items: List[RowPermissionBase]

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
        from_attributes = True

# 分页响应
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List

# 查询过滤器
class SortParam(BaseModel):
    field: str
    order: Literal['ascend', 'descend']

class TablePermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10
    sorters: Optional[List[SortParam]] = None
    # 添加单独的排序字段和排序方向参数
    sort_field: Optional[str] = None
    sort_order: Optional[Literal['ascend', 'descend']] = None

    @validator("sorters", pre=True)
    def transform_sort_param(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid sort parameter format")
        return v

class ColumnPermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    col_name: Optional[str] = None
    mask_type: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10
    sorters: Optional[List[SortParam]] = None
    # 添加单独的排序字段和排序方向参数
    sort_field: Optional[str] = None
    sort_order: Optional[Literal['ascend', 'descend']] = None


class RowPermissionFilter(BaseModel):
    db_name: Optional[str] = None
    table_name: Optional[str] = None
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    page: int = 1
    page_size: int = 10
    sorters: Optional[List[SortParam]] = None
    # 添加单独的排序字段和排序方向参数
    sort_field: Optional[str] = None
    sort_order: Optional[Literal['ascend', 'descend']] = None
    
    @validator("sorters", pre=True)
    def transform_row_sort_param(cls, v):
        if isinstance(v, str):
            try:
                return [SortParam(**item) for item in json.loads(v)]
            except (json.JSONDecodeError, ValidationError):
                return None
        return v
