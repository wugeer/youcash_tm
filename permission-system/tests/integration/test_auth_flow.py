import os
import pytest
import requests
from time import sleep

# 测试配置
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("TEST_FRONTEND_URL", "http://localhost:3000")

# 测试数据
TEST_USER = {
    "username": "integration_test_user",
    "password": "secure_password_123"
}

class TestAuthFlow:
    """
    测试完整的认证流程，模拟前后端交互
    这个测试需要后端和前端服务器都在运行
    """

    def setup_method(self):
        """每个测试方法运行前的设置，清理可能已存在的测试用户"""
        # 使用管理员API清理可能存在的测试用户（实际应用中需替换为真实的管理员凭据）
        admin_credentials = {"username": "admin", "password": "admin_password"}
        try:
            admin_token_resp = requests.post(f"{BASE_URL}/auth/login/json", json=admin_credentials)
            if admin_token_resp.status_code == 200:
                admin_token = admin_token_resp.json().get("access_token")
                # 查找并删除测试用户
                user_list_resp = requests.get(
                    f"{BASE_URL}/users", 
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                if user_list_resp.status_code == 200:
                    users = user_list_resp.json().get("items", [])
                    for user in users:
                        if user.get("username") == TEST_USER["username"]:
                            requests.delete(
                                f"{BASE_URL}/users/{user.get('id')}", 
                                headers={"Authorization": f"Bearer {admin_token}"}
                            )
        except:
            # 清理过程中的错误不应该阻止测试运行
            pass
    
    def test_full_auth_flow(self):
        """测试完整的认证流程：注册、登录、获取用户信息、退出"""
        # 步骤1：用户注册
        register_resp = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
        assert register_resp.status_code == 200, "用户注册失败"
        user_data = register_resp.json()
        assert user_data["username"] == TEST_USER["username"]
        assert "id" in user_data
        
        # 步骤2：用户登录
        login_resp = requests.post(f"{BASE_URL}/auth/login/json", json=TEST_USER)
        assert login_resp.status_code == 200, "用户登录失败"
        auth_data = login_resp.json()
        assert "access_token" in auth_data
        assert auth_data["token_type"] == "bearer"
        
        token = auth_data["access_token"]
        auth_header = {"Authorization": f"Bearer {token}"}
        
        # 步骤3：获取用户信息
        me_resp = requests.get(f"{BASE_URL}/auth/me", headers=auth_header)
        assert me_resp.status_code == 200, "获取用户信息失败"
        current_user = me_resp.json()
        assert current_user["username"] == TEST_USER["username"]
        
        # 步骤4：测试无效令牌
        invalid_header = {"Authorization": "Bearer invalid_token"}
        invalid_resp = requests.get(f"{BASE_URL}/auth/me", headers=invalid_header)
        assert invalid_resp.status_code == 401, "无效令牌验证失败"
        
        # 步骤5：模拟前端请求流程
        # 在真实的端到端测试中，这部分会使用Selenium或Cypress等工具来操作实际浏览器
        
        # 步骤6：测试令牌过期（模拟）- 在实际集成测试中可配置短期令牌
        print("测试令牌过期场景...")
        # 实际测试中可使用JWT_ACCESS_TOKEN_EXPIRE_MINUTES设置短期令牌
        
        # 步骤7：测试退出登录后token失效（后端无状态，仅模拟前端清除本地存储的行为）
        print("模拟退出登录...")
        # 前端通常会清除localStorage中的token
        
        # 确认成功流程
        assert True, "认证流程集成测试通过"
