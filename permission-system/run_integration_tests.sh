#!/bin/bash

# 确保使用Python 3.13
echo "=== 使用Python 3.13运行集成测试 ==="
echo "Python版本："
./venv/bin/python3 --version

# 设置环境变量
export TEST_API_URL="http://localhost:8000"
export TEST_FRONTEND_URL="http://localhost:3000"

# 运行集成测试
echo "=== 开始运行认证流程测试 ==="
./venv/bin/python -m pytest tests/integration/test_auth_flow.py -v

echo "=== 开始运行权限流程测试 ==="
./venv/bin/python -m pytest tests/integration/test_permission_flow.py -v
