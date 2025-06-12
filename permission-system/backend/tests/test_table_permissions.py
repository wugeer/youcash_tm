import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.security import create_access_token
from app.models.models import User, TablePermission
from main import app

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 设置测试数据库
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 替换应用中的数据库依赖
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 测试数据和辅助函数
test_user = {"username": "tablepermtest", "password": "password123"}
test_table_perm = {
    "db_name": "testdb",
    "table_name": "test_table",
    "user_name": "tablepermtest",
    "role_name": "analyst"
}

def create_user_and_get_token():
    # 创建用户
    client.post("/auth/register", json=test_user)
    # 登录
    login_response = client.post(
        "/auth/login/json",
        json={"username": test_user["username"], "password": test_user["password"]},
    )
    return login_response.json()["access_token"]

# 测试用例
def test_create_table_permission():
    token = create_user_and_get_token()
    response = client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"},
        json=test_table_perm,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["db_name"] == test_table_perm["db_name"]
    assert data["table_name"] == test_table_perm["table_name"]
    assert "id" in data

def test_get_table_permissions():
    token = create_user_and_get_token()
    # 先创建一个表权限
    client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"},
        json=test_table_perm,
    )
    
    # 获取表权限列表
    response = client.get(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["total"] > 0

def test_get_table_permission_by_id():
    token = create_user_and_get_token()
    # 先创建一个表权限
    create_response = client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"},
        json=test_table_perm,
    )
    perm_id = create_response.json()["id"]
    
    # 通过ID获取表权限
    response = client.get(
        f"/table-permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == perm_id
    assert data["db_name"] == test_table_perm["db_name"]
    assert data["table_name"] == test_table_perm["table_name"]

def test_update_table_permission():
    token = create_user_and_get_token()
    # 先创建一个表权限
    create_response = client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"},
        json=test_table_perm,
    )
    perm_id = create_response.json()["id"]
    
    # 更新表权限
    updated_perm = test_table_perm.copy()
    updated_perm["table_name"] = "updated_table"
    response = client.put(
        f"/table-permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=updated_perm,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == perm_id
    assert data["table_name"] == "updated_table"

def test_delete_table_permission():
    token = create_user_and_get_token()
    # 先创建一个表权限
    create_response = client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {token}"},
        json=test_table_perm,
    )
    perm_id = create_response.json()["id"]
    
    # 删除表权限
    response = client.delete(
        f"/table-permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # 确认已删除
    get_response = client.get(
        f"/table-permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404
