#!/bin/bash

# 复制前端文件到Nginx静态文件目录
echo "Copying frontend files..."
cp -r /app/static/* /usr/share/nginx/html/

# 启动Nginx服务
echo "Starting Nginx service..."
nginx

# 检查Nginx是否成功启动
if [ $? -ne 0 ]; then
    echo "Failed to start Nginx service"
    exit 1
fi

# 启动后端服务
echo "Starting backend service..."
cd /app
uvicorn main:app --host 0.0.0.0 --port 8000
