from fastapi import APIRouter
from app.api import auth, table_perm, column_perm, row_perm, hdfs_quota, ldap_user, role, department

api_router = APIRouter()

# 添加各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(table_perm.router, prefix="/table-permissions", tags=["table-permissions"])
api_router.include_router(column_perm.router, prefix="/column-permissions", tags=["column-permissions"])
api_router.include_router(row_perm.router, prefix="/row-permissions", tags=["row-permissions"])
api_router.include_router(hdfs_quota.router, prefix="/hdfs-quotas", tags=["hdfs-quotas"])
api_router.include_router(ldap_user.router, prefix="/ldap", tags=["ldap-users"])
api_router.include_router(role.router, prefix="/roles", tags=["roles"])
api_router.include_router(department.router, prefix="/departments", tags=["departments"])
