import os
import time
import json
import random
import string
import concurrent.futures
import requests
from statistics import mean, median, stdev
from datetime import datetime

# 配置参数
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
ADMIN_USER = {"username": "admin", "password": "admin123"}
TEST_USERS = 50  # 测试用户数量
CONCURRENT_USERS = 10  # 并发用户数
OPERATIONS_PER_USER = 20  # 每个用户操作次数

# 测试数据生成
DB_NAMES = ["prod", "test", "dev", "staging"]
TABLE_PREFIXES = ["user", "order", "product", "transaction", "customer"]
ROLE_NAMES = ["analyst", "developer", "manager", "viewer", "admin"]
MASK_TYPES = ["手机号", "身份证", "银行卡号", "座机号", "姓名", "原文"]
COLUMN_NAMES = ["id", "name", "phone", "email", "address", "age", "salary"]

# 测试结果存储
results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "config": {
        "test_users": TEST_USERS,
        "concurrent_users": CONCURRENT_USERS,
        "operations_per_user": OPERATIONS_PER_USER
    },
    "metrics": {
        "auth": {},
        "table_permissions": {},
        "column_permissions": {},
        "row_permissions": {}
    },
    "errors": []
}

# 辅助函数
def random_string(length=8):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_table():
    """生成随机表名"""
    prefix = random.choice(TABLE_PREFIXES)
    suffix = random_string(4)
    return f"{prefix}_{suffix}"

def random_row_filter():
    """生成随机行过滤条件"""
    conditions = [
        "department = 'IT'",
        "age > 30",
        "salary > 5000",
        "status = 'active'",
        "create_time > '2024-01-01'"
    ]
    return random.choice(conditions)

def register_test_user(username, password):
    """注册测试用户"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username, "password": password}
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            return {"success": True, "duration": duration}
        else:
            return {"success": False, "error": response.text, "duration": duration}
    except Exception as e:
        return {"success": False, "error": str(e), "duration": 0}

def login_user(username, password):
    """登录用户并获取令牌"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/auth/login/json",
            json={"username": username, "password": password}
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"success": True, "token": token, "duration": duration}
        else:
            return {"success": False, "error": response.text, "duration": duration}
    except Exception as e:
        return {"success": False, "error": str(e), "duration": 0}

class LoadTester:
    """负载测试器"""
    
    def __init__(self):
        self.tokens = {}
        self.created_resources = {
            "table_permissions": [],
            "column_permissions": [],
            "row_permissions": []
        }
        
    def setup_users(self):
        """创建测试用户并登录获取令牌"""
        print(f"创建 {TEST_USERS} 个测试用户...")
        register_times = []
        login_times = []
        
        for i in range(TEST_USERS):
            username = f"perftest_user_{i}_{random_string()}"
            password = f"Perftest@{random_string(12)}"
            
            # 注册用户
            reg_result = register_test_user(username, password)
            if reg_result["success"]:
                register_times.append(reg_result["duration"])
                
                # 登录用户
                login_result = login_user(username, password)
                if login_result["success"]:
                    self.tokens[username] = login_result["token"]
                    login_times.append(login_result["duration"])
                else:
                    results["errors"].append(f"登录用户 {username} 失败: {login_result.get('error')}")
            else:
                results["errors"].append(f"注册用户 {username} 失败: {reg_result.get('error')}")
        
        # 记录认证指标
        if register_times:
            results["metrics"]["auth"]["register"] = {
                "avg": mean(register_times),
                "median": median(register_times),
                "min": min(register_times),
                "max": max(register_times),
                "stdev": stdev(register_times) if len(register_times) > 1 else 0
            }
        
        if login_times:
            results["metrics"]["auth"]["login"] = {
                "avg": mean(login_times),
                "median": median(login_times),
                "min": min(login_times),
                "max": max(login_times),
                "stdev": stdev(login_times) if len(login_times) > 1 else 0
            }
        
        print(f"成功创建和登录了 {len(self.tokens)} 个测试用户")
    
    def create_table_permission(self, token):
        """创建表权限"""
        try:
            table_name = random_table()
            db_name = random.choice(DB_NAMES)
            role_name = random.choice(ROLE_NAMES)
            
            data = {
                "db_name": db_name,
                "table_name": table_name,
                "user_name": random_string(),
                "role_name": role_name
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/table-permissions",
                headers={"Authorization": f"Bearer {token}"},
                json=data
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                perm_id = response.json().get("id")
                self.created_resources["table_permissions"].append(perm_id)
                return {"success": True, "id": perm_id, "duration": duration}
            else:
                return {"success": False, "error": response.text, "duration": duration}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": 0}
    
    def create_column_permission(self, token):
        """创建字段权限"""
        try:
            table_name = random_table()
            db_name = random.choice(DB_NAMES)
            role_name = random.choice(ROLE_NAMES)
            col_name = random.choice(COLUMN_NAMES)
            mask_type = random.choice(MASK_TYPES)
            
            data = {
                "db_name": db_name,
                "table_name": table_name,
                "col_name": col_name,
                "mask_type": mask_type,
                "user_name": random_string(),
                "role_name": role_name
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/column-permissions",
                headers={"Authorization": f"Bearer {token}"},
                json=data
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                perm_id = response.json().get("id")
                self.created_resources["column_permissions"].append(perm_id)
                return {"success": True, "id": perm_id, "duration": duration}
            else:
                return {"success": False, "error": response.text, "duration": duration}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": 0}
    
    def create_row_permission(self, token):
        """创建行权限"""
        try:
            table_name = random_table()
            db_name = random.choice(DB_NAMES)
            role_name = random.choice(ROLE_NAMES)
            row_filter = random_row_filter()
            
            data = {
                "db_name": db_name,
                "table_name": table_name,
                "row_filter": row_filter,
                "user_name": random_string(),
                "role_name": role_name
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/row-permissions",
                headers={"Authorization": f"Bearer {token}"},
                json=data
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                perm_id = response.json().get("id")
                self.created_resources["row_permissions"].append(perm_id)
                return {"success": True, "id": perm_id, "duration": duration}
            else:
                return {"success": False, "error": response.text, "duration": duration}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": 0}
    
    def query_permissions(self, token):
        """查询权限列表，带分页和过滤"""
        try:
            endpoints = [
                "/table-permissions",
                "/column-permissions",
                "/row-permissions"
            ]
            
            endpoint = random.choice(endpoints)
            page = random.randint(1, 5)
            page_size = random.choice([10, 20, 50])
            
            params = {
                "page": page,
                "page_size": page_size
            }
            
            # 添加随机过滤条件
            if random.choice([True, False]):
                params["db_name"] = random.choice(DB_NAMES)
            
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            duration = time.time() - start_time
            
            category = endpoint.split("/")[1]  # 提取权限类别
            
            if response.status_code == 200:
                return {
                    "success": True, 
                    "category": category,
                    "duration": duration,
                    "count": len(response.json().get("items", []))
                }
            else:
                return {
                    "success": False, 
                    "category": category,
                    "error": response.text, 
                    "duration": duration
                }
        except Exception as e:
            return {"success": False, "error": str(e), "duration": 0}
    
    def run_user_operations(self, username):
        """执行单个用户的操作"""
        if username not in self.tokens:
            return {"username": username, "error": "无效的用户名，找不到令牌"}
        
        token = self.tokens[username]
        operations = []
        
        for _ in range(OPERATIONS_PER_USER):
            # 随机选择操作类型
            op_type = random.choice(["create_table", "create_column", "create_row", "query"])
            
            if op_type == "create_table":
                result = self.create_table_permission(token)
                operations.append({"type": "create_table", "result": result})
            elif op_type == "create_column":
                result = self.create_column_permission(token)
                operations.append({"type": "create_column", "result": result})
            elif op_type == "create_row":
                result = self.create_row_permission(token)
                operations.append({"type": "create_row", "result": result})
            elif op_type == "query":
                result = self.query_permissions(token)
                operations.append({"type": "query", "result": result})
        
        return {"username": username, "operations": operations}
    
    def run_concurrent_load_test(self):
        """并发执行用户操作"""
        if not self.tokens:
            print("没有可用的测试用户，无法执行负载测试")
            return
        
        print(f"开始执行并发负载测试，{CONCURRENT_USERS}个并发用户，每个执行{OPERATIONS_PER_USER}次操作...")
        usernames = list(self.tokens.keys())
        selected_users = random.sample(usernames, min(CONCURRENT_USERS, len(usernames)))
        
        # 使用线程池执行并发操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            future_to_user = {executor.submit(self.run_user_operations, user): user for user in selected_users}
            user_results = []
            
            for future in concurrent.futures.as_completed(future_to_user):
                user = future_to_user[future]
                try:
                    data = future.result()
                    user_results.append(data)
                except Exception as e:
                    user_results.append({"username": user, "error": str(e)})
        
        # 分析结果
        self.analyze_results(user_results)
    
    def analyze_results(self, user_results):
        """分析测试结果并生成报告"""
        # 按操作类型收集耗时
        durations = {
            "table_permissions": {"create": [], "query": []},
            "column_permissions": {"create": [], "query": []},
            "row_permissions": {"create": [], "query": []}
        }
        
        success_count = 0
        failure_count = 0
        
        for user_result in user_results:
            if "operations" not in user_result:
                continue
                
            for op in user_result["operations"]:
                op_type = op["type"]
                result = op["result"]
                
                if result.get("success"):
                    success_count += 1
                    
                    if op_type == "create_table":
                        durations["table_permissions"]["create"].append(result["duration"])
                    elif op_type == "create_column":
                        durations["column_permissions"]["create"].append(result["duration"])
                    elif op_type == "create_row":
                        durations["row_permissions"]["create"].append(result["duration"])
                    elif op_type == "query":
                        category = result.get("category", "")
                        if category in durations:
                            durations[category]["query"].append(result["duration"])
                else:
                    failure_count += 1
                    error = result.get("error", "未知错误")
                    results["errors"].append(f"{op_type} 操作失败: {error}")
        
        # 计算各操作类型的统计指标
        for category in durations:
            results["metrics"][category]["create"] = self.calculate_stats(durations[category]["create"])
            results["metrics"][category]["query"] = self.calculate_stats(durations[category]["query"])
        
        # 添加总体统计
        results["summary"] = {
            "total_operations": success_count + failure_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0
        }
        
        # 保存结果到文件
        self.save_results()
    
    def calculate_stats(self, values):
        """计算统计指标"""
        if not values:
            return {
                "count": 0,
                "avg": 0,
                "median": 0,
                "min": 0,
                "max": 0,
                "stdev": 0,
                "p95": 0,
                "p99": 0
            }
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "avg": mean(values),
            "median": median(values),
            "min": min(values),
            "max": max(values),
            "stdev": stdev(values) if len(values) > 1 else 0,
            "p95": sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 0 else 0,
            "p99": sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 0 else 0
        }
    
    def save_results(self):
        """保存测试结果到文件"""
        filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"测试结果已保存到 {filepath}")
        
        # 打印摘要
        print("\n===== 性能测试摘要 =====")
        print(f"总操作数: {results['summary']['total_operations']}")
        print(f"成功率: {results['summary']['success_rate']:.2%}")
        
        if "table_permissions" in results["metrics"] and "create" in results["metrics"]["table_permissions"]:
            tp_create = results["metrics"]["table_permissions"]["create"]
            if tp_create and "avg" in tp_create:
                print(f"表权限创建平均耗时: {tp_create['avg']:.4f}秒")
        
        if "column_permissions" in results["metrics"] and "create" in results["metrics"]["column_permissions"]:
            cp_create = results["metrics"]["column_permissions"]["create"]
            if cp_create and "avg" in cp_create:
                print(f"列权限创建平均耗时: {cp_create['avg']:.4f}秒")
        
        if "row_permissions" in results["metrics"] and "create" in results["metrics"]["row_permissions"]:
            rp_create = results["metrics"]["row_permissions"]["create"]
            if rp_create and "avg" in rp_create:
                print(f"行权限创建平均耗时: {rp_create['avg']:.4f}秒")
        
        if results["errors"]:
            print(f"\n发生了 {len(results['errors'])} 个错误")

def main():
    """主函数"""
    print("开始性能测试...")
    start_time = time.time()
    
    tester = LoadTester()
    tester.setup_users()
    tester.run_concurrent_load_test()
    
    total_time = time.time() - start_time
    print(f"\n测试完成! 总耗时: {total_time:.2f}秒")

if __name__ == "__main__":
    main()
