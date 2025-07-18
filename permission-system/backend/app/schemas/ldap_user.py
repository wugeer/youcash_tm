from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class LdapUserBase(BaseModel):
    """LDAP用户基本信息模式"""
    username: str = Field(..., description="用户名")
    role_name: str = Field(..., description="角色名")
    department_name: str = Field(..., description="部门名")
    hdfs_quota: float = Field(..., description="HDFS配额(GB)")
    description: Optional[str] = Field(None, description="描述信息")

class LdapUserCreate(LdapUserBase):
    """创建LDAP用户的请求模式，密码字段可选，如果不提供则自动生成随机密码"""
    password: Optional[str] = Field(None, description="密码，可选字段，不提供则系统自动生成随机密码")

class LdapUserUpdate(BaseModel):
    """更新LDAP用户的请求模式"""
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    role_name: Optional[str] = Field(None, description="角色名")
    department_name: Optional[str] = Field(None, description="部门名")
    hdfs_quota: Optional[float] = Field(None, description="HDFS配额(GB)")
    description: Optional[str] = Field(None, description="描述信息")

class LdapUserInDB(LdapUserBase):
    """数据库中的LDAP用户模式"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LdapUserResponse(LdapUserInDB):
    """API响应中的LDAP用户模式"""
    class Config:
        from_attributes = True

class LdapUserCreateResponse(BaseModel):
    """创建LDAP用户后的响应模式"""
    user: LdapUserResponse = Field(..., description="创建成功的用户信息")
    raw_password: Optional[str] = Field(None, description="用户的明文密码，仅在创建时返回一次")

class LdapUserImport(BaseModel):
    """批量导入LDAP用户的请求模式"""
    users: List[LdapUserCreate] = Field(..., description="要导入的用户列表")

class LdapUserFilter(BaseModel):
    """LDAP用户筛选条件模式"""
    username: Optional[str] = Field(None, description="用户名筛选")
    role_name: Optional[str] = Field(None, description="角色名筛选")
    department_name: Optional[str] = Field(None, description="部门名筛选")
    hdfs_quota_min: Optional[float] = Field(None, description="最小HDFS配额")
    hdfs_quota_max: Optional[float] = Field(None, description="最大HDFS配额")
    order_by: Optional[str] = Field(None, description="排序字段")
    order_desc: Optional[bool] = Field(False, description="是否降序排序")
    page: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页条数")
