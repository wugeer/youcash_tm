#!/bin/sh

# 默认API地址
API_URL=${API_URL:-"http://localhost:8000/api/v1"}

# 从 API_URL 中提取主机名/IP
# 例如从 http://192.168.1.10:38000/api/v1 中提取 192.168.1.10
API_HOST=$(echo $API_URL | sed -E 's|^http(s)?://([^:/]+).*$|\2|')
echo "Extracted API_HOST: $API_HOST"

# 如果提取失败或为空，使用容器的特殊网络配置
if [ -z "$API_HOST" ] || [ "$API_HOST" = "localhost" ]; then
    # 在Docker中，localhost指容器自身，需要使用主机网络
    # 使用host.docker.internal指向Docker宿主机（在支持的环境中）
    API_HOST="host.docker.internal"
    echo "Using Docker special network name: $API_HOST"
    
    # 如果Linux系统，可能需要使用容器网络IP
    if [ ! -f /etc/host.docker.internal ]; then
        # 使用默认网关作为API_HOST
        API_HOST=$(ip route | grep default | awk '{print $3}')
        echo "Linux environment, using default gateway: $API_HOST"
    fi
fi

# 替换前端配置文件中的API URL
# 使用相对路径，因为Nginx代理会处理
echo "window.APP_CONFIG = { API_URL: \"/api/v1\" };" > /usr/share/nginx/html/config.js
echo "API URL set to: /api/v1 (using proxy)"

# 找到所有的Nginx配置文件并进行替换
for NGINX_CONF in /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default
do
    if [ -f "$NGINX_CONF" ]; then
        echo "Updating Nginx config file: $NGINX_CONF"
        # 先搜索是否包含 API_HOST 占位符
        if grep -q "API_HOST" "$NGINX_CONF"; then
            sed -i "s|http://API_HOST:38000|http://$API_HOST:38000|g" "$NGINX_CONF"
            echo "Updated proxy_pass in $NGINX_CONF to: http://$API_HOST:38000"
        fi
        cat "$NGINX_CONF"
    fi
done

# 复制nginx.conf到正确位置
# 如果自定义nginx.conf已存在
# 因为docker映像在构建时可能将nginx.conf放在其他位置
if [ -f "/app/nginx.conf" ]; then
    echo "Found custom nginx.conf in /app, copying to /etc/nginx/conf.d/default.conf"
    # 先替换API_HOST
    sed "s|http://API_HOST:38000|http://$API_HOST:38000|g" /app/nginx.conf > /etc/nginx/conf.d/default.conf
    echo "Copied and updated nginx.conf"
    cat /etc/nginx/conf.d/default.conf
fi

# 用于调试连接的网络测试
echo "Network connectivity test:"
ping -c 1 $API_HOST || echo "Cannot ping $API_HOST (expected in container)"
echo "Attempting curl to backend API:"
curl -v "http://$API_HOST:38000/api/v1" || echo "Could not connect to backend API"

# 尝试使用不同的方法连接到后端API
echo "Trying alternate connection methods..."

# 提取API_URL中的端口（默认38000）
API_PORT=$(echo $API_URL | grep -o ':[0-9]\+' | grep -o '[0-9]\+' || echo "38000")
echo "Using API port: $API_PORT"

# 尝试不同的网络配置
echo "\nTrying node IP directly (if provided in API_URL)..."
NODE_IP=$(echo $API_URL | sed -E 's|^http(s)?://([^:/]+).*$|\2|')
if [ "$NODE_IP" != "localhost" ] && [ "$NODE_IP" != "$API_HOST" ]; then
    curl -v "http://$NODE_IP:$API_PORT/api/v1" || echo "Could not connect using node IP"
    # 如果成功连接，使用这个IP
    if curl -s -o /dev/null -w "%{http_code}" "http://$NODE_IP:$API_PORT/api/v1" | grep -qv "000"; then
        API_HOST=$NODE_IP
        echo "Successfully connected to $API_HOST:$API_PORT! Using this address."
        # 更新所有Nginx配置
        for NGINX_CONF in /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default; do
            if [ -f "$NGINX_CONF" ]; then
                sed -i "s|http://[^:]*:38000|http://$API_HOST:$API_PORT|g" "$NGINX_CONF"
            fi
        done
    fi
fi

echo "\nTrying Docker host network..."
# 通过DNS名称host.docker.internal尝试访问Docker主机
if curl -s -o /dev/null -w "%{http_code}" "http://host.docker.internal:$API_PORT/api/v1" | grep -qv "000"; then
    API_HOST="host.docker.internal"
    echo "Successfully connected to host.docker.internal! Using this address."
    # 更新所有Nginx配置
    for NGINX_CONF in /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default; do
        if [ -f "$NGINX_CONF" ]; then
            sed -i "s|http://[^:]*:38000|http://$API_HOST:$API_PORT|g" "$NGINX_CONF"
        fi
    done
fi

# 最后使用实际的后端节点IP（直接指定）
echo "\nTrying backend IP specified in environment..."
BACKEND_IP=${BACKEND_IP:-"192.168.122.141"} # 这是后端实际运行的IP
if [ -n "$BACKEND_IP" ]; then
    echo "Testing connection to specified backend IP: $BACKEND_IP:$API_PORT"
    if curl -s -o /dev/null -w "%{http_code}" "http://$BACKEND_IP:$API_PORT/api/v1" | grep -qv "000"; then
        API_HOST=$BACKEND_IP
        echo "Successfully connected to $BACKEND_IP! Using this address."
        # 更新所有Nginx配置
        for NGINX_CONF in /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default; do
            if [ -f "$NGINX_CONF" ]; then
                sed -i "s|http://[^:]*:38000|http://$API_HOST:$API_PORT|g" "$NGINX_CONF"
            fi
        done
    else
        echo "Could not connect to specified backend IP: $BACKEND_IP"
    fi
fi

# 显示最终使用的API主机
echo "\nFinal API host configuration:"
echo "API_HOST = $API_HOST"
echo "API_PORT = $API_PORT"

# 显示最终的Nginx配置
echo "\nFinal Nginx configuration:"
cat /etc/nginx/conf.d/default.conf                                                                                                                                                                                                                
# 执行CMD
exec "$@"
