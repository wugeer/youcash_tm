import requests
import json

# 定义API地址
login_url = "http://localhost:8000/api/v1/auth/login/json"

# 定义测试用户凭据
credentials = {
    "username": "admin",  # 替换为您的用户名
    "password": "1qaz@WSX"  # 替换为您的密码
}

# 发送请求
response = requests.post(login_url, json=credentials)

# 打印响应
print(f"Status Code: {response.status_code}")
print("Response Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")
print("\nResponse Body:")
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)

# 如果成功登录，尝试使用令牌获取用户信息
if response.status_code == 200:
    token = response.json().get("access_token")
    me_url = "http://localhost:8000/api/v1/auth/me"
    me_response = requests.get(
        me_url,
        headers={"Authorization": f"Bearer {token}"}
    )
    print("\n\nUser Info Request:")
    print(f"Status Code: {me_response.status_code}")
    try:
        print(json.dumps(me_response.json(), indent=2))
    except:
        print(me_response.text)
