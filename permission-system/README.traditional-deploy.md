# 权限管理系统传统部署指南

本文档提供了在不使用Docker的情况下，直接在服务器上部署权限管理系统的详细步骤。




## 系统要求

- 操作系统：Linux（推荐Ubuntu 20.04/22.04或CentOS 8）
- Python 3.9+（推荐3.12）
- Node.js 16+（推荐22）
- PostgreSQL 12+（推荐14）
- Nginx 1.18+

## 部署流程概述

1. 准备服务器环境
2. 部署PostgreSQL数据库
3. 部署后端服务
4. 部署前端应用
5. 配置Nginx
6. 启动服务

## 详细部署步骤

### 1. 准备服务器环境

#### 安装基础工具

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git curl wget build-essential libpq-dev

# CentOS/RHEL
sudo dnf update
sudo dnf install -y git curl wget gcc gcc-c++ postgresql-devel
```

#### 安装Python

```bash
# Ubuntu/Debian
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# CentOS/RHEL
sudo dnf install -y python3.12 python3.12-devel

# 创建软链接（如果需要）
sudo ln -sf /usr/bin/python3.12 /usr/bin/python3
sudo ln -sf /usr/bin/pip3.12 /usr/bin/pip3
```

#### 安装Node.js

```bash
# 使用NVM安装Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
```

#### 安装Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo dnf install -y nginx
```

### 2. 部署PostgreSQL数据库

#### 安装PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# CentOS/RHEL
sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
```

#### 启动PostgreSQL服务

```bash
# Ubuntu/Debian
sudo systemctl enable postgresql
sudo systemctl start postgresql

# CentOS/RHEL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### 创建数据库和用户

```bash
# 切换到postgres用户
sudo -i -u postgres

# 创建数据库和用户
psql -c "CREATE USER permission_user WITH PASSWORD 'permission_pass';"
psql -c "CREATE DATABASE permission_system;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE permission_system TO permission_user;"

# 退出postgres用户
exit
```

### 3. 部署后端服务

#### 获取代码

```bash
# 克隆代码仓库（如果使用Git）
git clone <repository-url> /opt/permission-system
cd /opt/permission-system

# 或者，上传项目文件到服务器
# 使用scp, rsync等工具
```

#### 创建Python虚拟环境

```bash
# 创建虚拟环境
cd /opt/permission-system/backend
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量

```bash
# 创建.env文件
cat > .env << EOF
# 数据库配置
POSTGRES_USER=permission_user
POSTGRES_PASSWORD=permission_pass
POSTGRES_DB=permission_system
DATABASE_URL=postgresql://permission_user:permission_pass@localhost:5432/permission_system

# JWT配置
JWT_SECRET_KEY=BKiPGiS9hbaAHc97aG7llxNB5k_48s1zLo1dmt8HfOI=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS配置
CORS_ORIGINS=["http://localhost:18000"]

# 其他配置
TZ=Asia/Shanghai
EOF
```

#### 运行数据库迁移

```bash
# 确保在虚拟环境中
cd /opt/permission-system/backend
source venv/bin/activate

# 运行迁移
alembic upgrade head
```

#### 创建系统服务

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/permission-backend.service > /dev/null << EOF
[Unit]
Description=Permission System Backend
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/permission-system/backend
ExecStart=/opt/permission-system/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
Environment="PATH=/opt/permission-system/backend/venv/bin"
EnvironmentFile=/opt/permission-system/backend/.env

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl enable permission-backend
sudo systemctl start permission-backend
```

### 4. 部署前端应用

#### 构建前端

```bash
# 进入前端目录
cd /opt/permission-system/frontend

# 安装依赖
npm ci

# 构建生产版本
NODE_ENV=production npm run build
```

#### 配置前端环境变量（如果需要）

如果前端需要环境变量，可以在构建前创建`.env`文件：

```bash
# 创建前端环境变量文件
cat > .env << EOF
REACT_APP_API_URL=http://your-domain.com/api
EOF

# 然后重新构建
npm run build
```

### 5. 配置Nginx

#### 创建Nginx配置文件

```bash
# 创建Nginx配置
sudo tee /etc/nginx/sites-available/permission-system.conf > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或IP

    # 前端静态文件
    location / {
        root /opt/permission-system/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # API文档
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# 启用站点配置
sudo ln -sf /etc/nginx/sites-available/permission-system.conf /etc/nginx/sites-enabled/

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 配置防火墙（如果需要）

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 6. 启动所有服务

```bash
# 启动PostgreSQL（如果尚未启动）
sudo systemctl start postgresql

# 启动后端服务
sudo systemctl start permission-backend

# 启动Nginx
sudo systemctl start nginx
```

## 验证部署

访问以下URL验证应用是否正常运行：
- 应用访问地址：http://your-domain.com
- API文档：http://your-domain.com/docs

## 维护指南

### 查看日志

```bash
# 查看后端日志
sudo journalctl -u permission-backend

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 重启服务

```bash
# 重启后端
sudo systemctl restart permission-backend

# 重启Nginx
sudo systemctl restart nginx

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### 更新应用

#### 更新后端

```bash
# 进入后端目录
cd /opt/permission-system/backend

# 拉取最新代码（如果使用Git）
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 重启服务
sudo systemctl restart permission-backend
```

#### 更新前端

```bash
# 进入前端目录
cd /opt/permission-system/frontend

# 拉取最新代码（如果使用Git）
git pull

# 安装依赖
npm ci

# 构建生产版本
NODE_ENV=production npm run build

# 不需要重启Nginx，因为静态文件已更新
```

## 常见问题

### 1. 后端服务无法启动

检查以下几点：
- Python虚拟环境是否正确激活
- 依赖是否完全安装
- 环境变量是否正确设置
- 数据库连接是否正常
- 查看日志：`sudo journalctl -u permission-backend`

### 2. 前端无法访问后端API

检查以下几点：
- Nginx配置是否正确
- 后端服务是否正常运行
- CORS配置是否正确
- 查看Nginx日志：`sudo tail -f /var/log/nginx/error.log`

### 3. 数据库连接问题

检查以下几点：
- PostgreSQL服务是否运行：`sudo systemctl status postgresql`
- 数据库用户和权限是否正确设置
- 防火墙是否允许数据库连接
- 数据库连接字符串是否正确

## 性能优化建议

1. **配置Nginx缓存**：为静态资源添加缓存头
2. **使用Gunicorn**：替代Uvicorn作为生产WSGI服务器
3. **配置PostgreSQL**：根据服务器内存调整PostgreSQL配置
4. **添加HTTPS**：使用Let's Encrypt配置SSL证书
5. **监控系统**：添加Prometheus/Grafana监控
