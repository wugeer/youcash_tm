from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.db import get_db
from app.models.ldap_user import LdapUser
from app.schemas.ldap_user import (
    LdapUserCreate, LdapUserUpdate, LdapUserResponse, 
    LdapUserImport, LdapUserFilter, LdapUserCreateResponse
)
from app.utils.ldap_ranger import YoucashUtils
from app.utils.ldap3_script import LDAPConnection, LDAPUserManager, LDAPGroupManager
import os
import logging
import argparse
from datetime import datetime
import csv
from io import StringIO
import tempfile

logger = logging.getLogger(__name__)
router = APIRouter()

# 从环境变量中获取LDAP配置
LDAP_SERVER = os.getenv("LDAP_SERVER", "").split(",") if os.getenv("LDAP_SERVER") else []
USER_DN = os.getenv("LDAP_USER_DN", "")
DEFAULT_PASSWORD = os.getenv("LDAP_DEFAULT_PASSWORD", "")

def get_ldap_connection():
    """获取LDAP连接"""
    try:
        return LDAPConnection(LDAP_SERVER, USER_DN, DEFAULT_PASSWORD)
    except Exception as e:
        logger.error(f"LDAP连接失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LDAP连接失败: {str(e)}")

import string
import random
import base64

@router.post("/", response_model=LdapUserCreateResponse, status_code=status.HTTP_201_CREATED, summary="创建LDAP用户")
def create_ldap_user(
    user: LdapUserCreate,
    db: Session = Depends(get_db)
) -> LdapUserCreateResponse:
    """创建LDAP用户，自动生成随机密码"""
    # 检查用户是否已存在
    db_user = db.query(LdapUser).filter(LdapUser.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户已存在")
    
    try:
        # 生成8位随机密码，包含字母、数字和特殊字符
        if not user.password:  # 如果没有提供密码，则生成随机密码
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(8))
        else:
            password = user.password
            
        # 对密码进行Base64编码
        encoded_password = base64.b64encode(password.encode()).decode()
        
        # [临时禁用] 跳过实际的LDAP用户创建，直接操作数据库
        # connection = get_ldap_connection()
        # user_manager = LDAPUserManager(connection.connection)
        # group_manager = LDAPGroupManager(connection.connection)
        
        # # 创建参数
        # args = argparse.Namespace(
        #     command='create_user',
        #     user=user.username,
        #     password=password,  # 使用原始密码创建LDAP用户
        #     department_name=user.department_name,
        #     roles=[user.role_name],
        #     quota=user.hdfs_quota
        # )
        
        # # 调用LDAP工具创建用户
        # from app.utils.ldap_ranger import run
        # run(args)
        
        # 在本地数据库中保存用户信息，使用Base64编码的密码
        db_user = LdapUser(
            username=user.username,
            password=encoded_password,  # 存储Base64编码后的密码
            role_name=user.role_name,
            department_name=user.department_name,
            hdfs_quota=user.hdfs_quota,
            description=user.description
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 手动构造用户响应数据，避免序列化错误
        # 先将数据库对象转换为字典
        user_dict = {
            "id": db_user.id,
            "username": db_user.username,
            "role_name": db_user.role_name,
            "department_name": db_user.department_name,
            "hdfs_quota": db_user.hdfs_quota,
            "description": db_user.description,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at
        }
        
        # 使用字典创建LdapUserResponse对象
        user_response = LdapUserResponse(**user_dict)
        
        # 返回用户信息和原始密码（仅在创建时返回一次）
        return LdapUserCreateResponse(
            user=user_response,
            raw_password=password if not user.password else None
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建LDAP用户失败: {str(e)}")

@router.get("/ldap-users/", response_model=Dict[str, Any])
def get_ldap_users(
    username: Optional[str] = None,
    role_name: Optional[str] = None,
    department_name: Optional[str] = None,
    hdfs_quota_min: Optional[float] = None,
    hdfs_quota_max: Optional[float] = None,
    order_by: Optional[str] = None,
    order_desc: bool = False,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """获取LDAP用户列表，支持筛选和排序"""
    query = db.query(LdapUser)
    
    # 应用筛选条件
    if username:
        query = query.filter(LdapUser.username.ilike(f"%{username}%"))
    if role_name:
        query = query.filter(LdapUser.role_name.ilike(f"%{role_name}%"))
    if department_name:
        query = query.filter(LdapUser.department_name.ilike(f"%{department_name}%"))
    if hdfs_quota_min is not None:
        query = query.filter(LdapUser.hdfs_quota >= hdfs_quota_min)
    if hdfs_quota_max is not None:
        query = query.filter(LdapUser.hdfs_quota <= hdfs_quota_max)
    
    # 计算总记录数
    total = query.count()
    
    # 应用排序
    if order_by:
        column = getattr(LdapUser, order_by, None)
        if column is not None:
            query = query.order_by(column.desc() if order_desc else column.asc())
    
    # 应用分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 获取原始数据库对象列表
    users = query.all()
    
    # 手动转换每个数据库对象为Pydantic模型
    serialized_users = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "role_name": user.role_name,
            "department_name": user.department_name,
            "hdfs_quota": user.hdfs_quota,
            "description": user.description,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        serialized_users.append(LdapUserResponse(**user_dict))
    
    return {
        "items": serialized_users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.get("/ldap-users/roles")
def get_ldap_roles(
    db: Session = Depends(get_db)
):
    """获取所有角色名"""
    try:
        # 获取数据库中所有不同的角色名
        roles = db.query(LdapUser.role_name).distinct().all()
        return {"roles": [role[0] for role in roles]}
    except Exception as e:
        logger.error(f"获取角色名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色名失败: {str(e)}")

@router.get("/ldap-users/departments")
def get_ldap_departments(
    db: Session = Depends(get_db)
):
    """获取所有部门名"""
    try:
        # 获取数据库中所有不同的部门名
        departments = db.query(LdapUser.department_name).distinct().all()
        return {"departments": [dept[0] for dept in departments]}
    except Exception as e:
        logger.error(f"获取部门名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取部门名失败: {str(e)}")

@router.get("/ldap-users/{user_id}", response_model=LdapUserResponse)
def get_ldap_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取LDAP用户详情"""
    user = db.query(LdapUser).filter(LdapUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    # 手动转换为Pydantic模型
    user_dict = {
        "id": user.id,
        "username": user.username,
        "role_name": user.role_name,
        "department_name": user.department_name,
        "hdfs_quota": user.hdfs_quota,
        "description": user.description,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    return LdapUserResponse(**user_dict)

@router.put("/ldap-users/{user_id}", response_model=LdapUserResponse)
def update_ldap_user(
    user_id: int,
    user_update: LdapUserUpdate,
    db: Session = Depends(get_db)
):
    """更新LDAP用户"""
    db_user = db.query(LdapUser).filter(LdapUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        update_data = user_update.dict(exclude_unset=True)
        password = update_data.pop("password", None)
        
        # 更新数据库中的用户信息
        for key, value in update_data.items():
            if value is not None:
                setattr(db_user, key, value)
        
        # 如果需要更新密码
        if password:
            # 调用LDAP工具更新密码
            args = argparse.Namespace(
                command='change_password',
                user=db_user.username,
                new_password=password
            )
            from app.utils.ldap_ranger import run
            run(args)
        
        # 如果更新了配额
        if "hdfs_quota" in update_data:
            # 调用HDFS工具更新配额
            util_obj = YoucashUtils(db_user.username, db_user.username)
            util_obj.set_hdfs_space_quota(db_user.hdfs_quota)
        
        db.commit()
        db.refresh(db_user)
        return db_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新LDAP用户失败: {str(e)}")

@router.delete("/ldap-users/{user_id}")
def delete_ldap_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除LDAP用户"""
    db_user = db.query(LdapUser).filter(LdapUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        username = db_user.username
        
        # 调用LDAP工具删除用户
        args = argparse.Namespace(
            command='delete_user',
            user=username
        )
        from app.utils.ldap_ranger import run
        run(args)
        
        # 从数据库中删除用户信息
        db.delete(db_user)
        db.commit()
        
        return {"message": f"用户 {username} 已成功删除"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除LDAP用户失败: {str(e)}")

@router.post("/ldap-users/{user_id}/sync")
def sync_ldap_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """同步单个LDAP用户"""
    db_user = db.query(LdapUser).filter(LdapUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 调用LDAP工具同步用户
        connection = get_ldap_connection()
        user_manager = LDAPUserManager(connection.connection)
        
        # 检查LDAP中是否存在该用户
        ldap_user = user_manager.search_user(db_user.username)
        if not ldap_user:
            # 如果LDAP中不存在，则创建
            args = argparse.Namespace(
                command='create_user',
                user=db_user.username,
                password=DEFAULT_PASSWORD,  # 使用默认密码
                department_name=db_user.department_name,
                roles=[db_user.role_name],
                quota=db_user.hdfs_quota
            )
            from app.utils.ldap_ranger import run
            run(args)
        else:
            # 如果LDAP中存在，则更新配额
            util_obj = YoucashUtils(db_user.username, db_user.username)
            util_obj.set_hdfs_space_quota(db_user.hdfs_quota)
        
        return {"message": f"用户 {db_user.username} 已成功同步"}
        
    except Exception as e:
        logger.error(f"同步LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步LDAP用户失败: {str(e)}")

@router.post("/ldap-users/sync-all")
def sync_all_ldap_users(
    db: Session = Depends(get_db)
):
    """同步所有LDAP用户"""
    try:
        # 获取所有数据库中的用户
        db_users = db.query(LdapUser).all()
        
        # 获取LDAP中的所有用户
        connection = get_ldap_connection()
        user_manager = LDAPUserManager(connection.connection)
        ldap_users = user_manager.search_user_all(['uid'])
        ldap_usernames = [entry.uid.value for entry in ldap_users] if ldap_users else []
        
        sync_results = {
            "total": len(db_users),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # 遍历数据库用户，同步到LDAP
        for db_user in db_users:
            try:
                if db_user.username not in ldap_usernames:
                    # 如果LDAP中不存在，则创建
                    args = argparse.Namespace(
                        command='create_user',
                        user=db_user.username,
                        password=DEFAULT_PASSWORD,  # 使用默认密码
                        department_name=db_user.department_name,
                        roles=[db_user.role_name],
                        quota=db_user.hdfs_quota
                    )
                    from app.utils.ldap_ranger import run
                    run(args)
                else:
                    # 如果LDAP中存在，则更新配额
                    util_obj = YoucashUtils(db_user.username, db_user.username)
                    util_obj.set_hdfs_space_quota(db_user.hdfs_quota)
                
                sync_results["success"] += 1
                sync_results["details"].append({
                    "username": db_user.username,
                    "status": "success"
                })
                
            except Exception as e:
                sync_results["failed"] += 1
                sync_results["details"].append({
                    "username": db_user.username,
                    "status": "failed",
                    "error": str(e)
                })
        
        return sync_results
        
    except Exception as e:
        logger.error(f"同步所有LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步所有LDAP用户失败: {str(e)}")

@router.post("/ldap-users/import")
def import_ldap_users(
    file_content: str = Body(...),
    db: Session = Depends(get_db)
):
    """从CSV文件导入LDAP用户"""
    try:
        csv_file = StringIO(file_content)
        reader = csv.DictReader(csv_file)
        
        import_results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for row in reader:
            import_results["total"] += 1
            try:
                # 检查必填字段
                required_fields = ["username", "password", "role_name", "department_name"]
                for field in required_fields:
                    if field not in row or not row[field]:
                        raise ValueError(f"缺少必填字段: {field}")
                
                # 检查用户是否已存在
                db_user = db.query(LdapUser).filter(LdapUser.username == row["username"]).first()
                if db_user:
                    raise ValueError(f"用户已存在: {row['username']}")
                
                # 创建LDAP用户
                hdfs_quota = float(row.get("hdfs_quota", 100))
                args = argparse.Namespace(
                    command='create_user',
                    user=row["username"],
                    password=row["password"],
                    department_name=row["department_name"],
                    roles=[row["role_name"]],
                    quota=hdfs_quota
                )
                
                # 调用LDAP工具创建用户
                from app.utils.ldap_ranger import run
                run(args)
                
                # 在本地数据库中保存用户信息
                db_user = LdapUser(
                    username=row["username"],
                    password="******",  # 不保存明文密码
                    role_name=row["role_name"],
                    department_name=row["department_name"],
                    hdfs_quota=hdfs_quota,
                    description=row.get("description", "")
                )
                db.add(db_user)
                db.commit()
                
                import_results["success"] += 1
                import_results["details"].append({
                    "username": row["username"],
                    "status": "success"
                })
                
            except Exception as e:
                db.rollback()
                import_results["failed"] += 1
                import_results["details"].append({
                    "username": row.get("username", "未知"),
                    "status": "failed",
                    "error": str(e)
                })
        
        return import_results
        
    except Exception as e:
        logger.error(f"导入LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入LDAP用户失败: {str(e)}")

@router.post("/ldap-users/export")
def export_ldap_users(
    filter_params: LdapUserFilter,
    db: Session = Depends(get_db)
):
    """导出LDAP用户为CSV文件"""
    try:
        query = db.query(LdapUser)
        
        # 应用筛选条件
        if filter_params.username:
            query = query.filter(LdapUser.username.ilike(f"%{filter_params.username}%"))
        if filter_params.role_name:
            query = query.filter(LdapUser.role_name.ilike(f"%{filter_params.role_name}%"))
        if filter_params.department_name:
            query = query.filter(LdapUser.department_name.ilike(f"%{filter_params.department_name}%"))
        if filter_params.hdfs_quota_min is not None:
            query = query.filter(LdapUser.hdfs_quota >= filter_params.hdfs_quota_min)
        if filter_params.hdfs_quota_max is not None:
            query = query.filter(LdapUser.hdfs_quota <= filter_params.hdfs_quota_max)
        
        # 应用排序
        if filter_params.order_by:
            column = getattr(LdapUser, filter_params.order_by, None)
            if column is not None:
                query = query.order_by(column.desc() if filter_params.order_desc else column.asc())
        
        # 获取数据
        users = query.all()
        
        # 创建CSV内容
        csv_output = StringIO()
        fieldnames = ["username", "role_name", "department_name", "hdfs_quota", "created_at", "updated_at", "description"]
        writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
        writer.writeheader()
        
        for user in users:
            writer.writerow({
                "username": user.username,
                "role_name": user.role_name,
                "department_name": user.department_name,
                "hdfs_quota": user.hdfs_quota,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "",
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else "",
                "description": user.description or ""
            })
        
        return {"content": csv_output.getvalue()}
        
    except Exception as e:
        logger.error(f"导出LDAP用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出LDAP用户失败: {str(e)}")

