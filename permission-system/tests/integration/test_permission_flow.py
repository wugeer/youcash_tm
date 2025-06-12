import os
import pytest
import requests
from time import sleep

# 测试配置
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("TEST_FRONTEND_URL", "http://localhost:3000")

# 测试数据
TEST_USER = {
    "username": "perm_test_user",
    "password": "secure_password_123"
}

TABLE_PERMISSION = {
    "db_name": "test_database",
    "table_name": "test_table",
    "user_name": "perm_test_user",
    "role_name": "analyst"
}

COLUMN_PERMISSION = {
    "db_name": "test_database",
    "table_name": "test_table",
    "col_name": "user_phone",
    "mask_type": "手机号",
    "user_name": "perm_test_user",
    "role_name": "analyst"
}

ROW_PERMISSION = {
    "db_name": "test_database",
    "table_name": "test_table",
    "row_filter": "department = 'IT'",
    "user_name": "perm_test_user",
    "role_name": "analyst"
}

class TestPermissionFlow:
    """测试完整的权限管理流程，包括表、列、行权限的创建、查询、更新和删除"""
    
    token = None
    table_permission_id = None
    column_permission_id = None
    row_permission_id = None
    
    @classmethod
    def setup_class(cls):
        """在所有测试之前创建测试用户并获取令牌"""
        # 注册测试用户
        register_resp = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
        if register_resp.status_code == 200:
            # 登录并获取令牌
            login_resp = requests.post(f"{BASE_URL}/auth/login/json", json=TEST_USER)
            if login_resp.status_code == 200:
                cls.token = login_resp.json().get("access_token")
    
    def get_auth_header(self):
        """获取带有认证令牌的请求头"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_01_table_permission_crud(self):
        """测试表权限的增删改查操作"""
        # 创建表权限
        create_resp = requests.post(
            f"{BASE_URL}/table-permissions",
            headers=self.get_auth_header(),
            json=TABLE_PERMISSION
        )
        assert create_resp.status_code == 200, "创建表权限失败"
        created_perm = create_resp.json()
        self.__class__.table_permission_id = created_perm["id"]
        
        # 获取表权限列表
        list_resp = requests.get(
            f"{BASE_URL}/table-permissions",
            headers=self.get_auth_header(),
            params={"db_name": TABLE_PERMISSION["db_name"]}
        )
        assert list_resp.status_code == 200, "获取表权限列表失败"
        list_data = list_resp.json()
        assert list_data["total"] > 0
        assert any(p["db_name"] == TABLE_PERMISSION["db_name"] for p in list_data["items"])
        
        # 获取单个表权限
        get_resp = requests.get(
            f"{BASE_URL}/table-permissions/{self.__class__.table_permission_id}",
            headers=self.get_auth_header()
        )
        assert get_resp.status_code == 200, "获取单个表权限失败"
        
        # 更新表权限
        updated_data = TABLE_PERMISSION.copy()
        updated_data["role_name"] = "manager"
        update_resp = requests.put(
            f"{BASE_URL}/table-permissions/{self.__class__.table_permission_id}",
            headers=self.get_auth_header(),
            json=updated_data
        )
        assert update_resp.status_code == 200, "更新表权限失败"
        updated_perm = update_resp.json()
        assert updated_perm["role_name"] == "manager"
    
    def test_02_column_permission_crud(self):
        """测试列权限的增删改查操作"""
        # 创建列权限
        create_resp = requests.post(
            f"{BASE_URL}/column-permissions",
            headers=self.get_auth_header(),
            json=COLUMN_PERMISSION
        )
        assert create_resp.status_code == 200, "创建列权限失败"
        created_perm = create_resp.json()
        self.__class__.column_permission_id = created_perm["id"]
        
        # 获取列权限列表
        list_resp = requests.get(
            f"{BASE_URL}/column-permissions",
            headers=self.get_auth_header(),
            params={
                "db_name": COLUMN_PERMISSION["db_name"],
                "table_name": COLUMN_PERMISSION["table_name"]
            }
        )
        assert list_resp.status_code == 200, "获取列权限列表失败"
        list_data = list_resp.json()
        assert list_data["total"] > 0
        
        # 获取单个列权限
        get_resp = requests.get(
            f"{BASE_URL}/column-permissions/{self.__class__.column_permission_id}",
            headers=self.get_auth_header()
        )
        assert get_resp.status_code == 200, "获取单个列权限失败"
        
        # 更新列权限
        updated_data = COLUMN_PERMISSION.copy()
        updated_data["mask_type"] = "身份证"
        update_resp = requests.put(
            f"{BASE_URL}/column-permissions/{self.__class__.column_permission_id}",
            headers=self.get_auth_header(),
            json=updated_data
        )
        assert update_resp.status_code == 200, "更新列权限失败"
        updated_perm = update_resp.json()
        assert updated_perm["mask_type"] == "身份证"
    
    def test_03_row_permission_crud(self):
        """测试行权限的增删改查操作"""
        # 创建行权限
        create_resp = requests.post(
            f"{BASE_URL}/row-permissions",
            headers=self.get_auth_header(),
            json=ROW_PERMISSION
        )
        assert create_resp.status_code == 200, "创建行权限失败"
        created_perm = create_resp.json()
        self.__class__.row_permission_id = created_perm["id"]
        
        # 获取行权限列表
        list_resp = requests.get(
            f"{BASE_URL}/row-permissions",
            headers=self.get_auth_header(),
            params={
                "db_name": ROW_PERMISSION["db_name"],
                "table_name": ROW_PERMISSION["table_name"]
            }
        )
        assert list_resp.status_code == 200, "获取行权限列表失败"
        list_data = list_resp.json()
        assert list_data["total"] > 0
        
        # 获取单个行权限
        get_resp = requests.get(
            f"{BASE_URL}/row-permissions/{self.__class__.row_permission_id}",
            headers=self.get_auth_header()
        )
        assert get_resp.status_code == 200, "获取单个行权限失败"
        
        # 更新行权限
        updated_data = ROW_PERMISSION.copy()
        updated_data["row_filter"] = "department = 'HR' AND salary > 5000"
        update_resp = requests.put(
            f"{BASE_URL}/row-permissions/{self.__class__.row_permission_id}",
            headers=self.get_auth_header(),
            json=updated_data
        )
        assert update_resp.status_code == 200, "更新行权限失败"
        updated_perm = update_resp.json()
        assert updated_perm["row_filter"] == "department = 'HR' AND salary > 5000"
    
    def test_04_permission_dependency(self):
        """测试权限之间的依赖关系，确保表权限、列权限、行权限能够正确关联"""
        # 这部分测试可以验证数据库中的外键约束和业务逻辑关系
        pass
    
    def test_05_permission_cleanup(self):
        """测试删除权限的操作"""
        # 删除行权限
        if self.__class__.row_permission_id:
            row_delete_resp = requests.delete(
                f"{BASE_URL}/row-permissions/{self.__class__.row_permission_id}",
                headers=self.get_auth_header()
            )
            assert row_delete_resp.status_code == 200, "删除行权限失败"
            
            # 验证删除成功
            get_resp = requests.get(
                f"{BASE_URL}/row-permissions/{self.__class__.row_permission_id}",
                headers=self.get_auth_header()
            )
            assert get_resp.status_code == 404, "行权限未成功删除"
        
        # 删除列权限
        if self.__class__.column_permission_id:
            col_delete_resp = requests.delete(
                f"{BASE_URL}/column-permissions/{self.__class__.column_permission_id}",
                headers=self.get_auth_header()
            )
            assert col_delete_resp.status_code == 200, "删除列权限失败"
            
            # 验证删除成功
            get_resp = requests.get(
                f"{BASE_URL}/column-permissions/{self.__class__.column_permission_id}",
                headers=self.get_auth_header()
            )
            assert get_resp.status_code == 404, "列权限未成功删除"
        
        # 删除表权限
        if self.__class__.table_permission_id:
            table_delete_resp = requests.delete(
                f"{BASE_URL}/table-permissions/{self.__class__.table_permission_id}",
                headers=self.get_auth_header()
            )
            assert table_delete_resp.status_code == 200, "删除表权限失败"
            
            # 验证删除成功
            get_resp = requests.get(
                f"{BASE_URL}/table-permissions/{self.__class__.table_permission_id}",
                headers=self.get_auth_header()
            )
            assert get_resp.status_code == 404, "表权限未成功删除"
