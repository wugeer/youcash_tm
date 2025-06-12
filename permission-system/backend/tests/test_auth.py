import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.security import create_access_token
from app.models.models import User
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

# 测试用例
def test_create_user():
    # 创建用户
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login():
    # 先创建用户
    client.post(
        "/auth/register",
        json={"username": "logintest", "password": "password123"},
    )
    
    # 登录
    response = client.post(
        "/auth/login/json",
        json={"username": "logintest", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password():
    # 先创建用户
    client.post(
        "/auth/register",
        json={"username": "wrongpasstest", "password": "password123"},
    )
    
    # 使用错误密码登录
    response = client.post(
        "/auth/login/json",
        json={"username": "wrongpasstest", "password": "wrongpassword"},
    )
    assert response.status_code == 401

def test_get_current_user():
    # 先创建用户
    user_response = client.post(
        "/auth/register",
        json={"username": "currentusertest", "password": "password123"},
    )
    user_data = user_response.json()
    
    # 登录获取token
    login_response = client.post(
        "/auth/login/json",
        json={"username": "currentusertest", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    # 获取当前用户
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentusertest"
    assert data["id"] == user_data["id"]

def test_unauthorized_access():
    # 尝试未授权访问当前用户API
    response = client.get("/auth/me")
    assert response.status_code == 401
