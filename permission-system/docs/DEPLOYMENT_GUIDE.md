# 权限管理系统部署指南

本文档提供详细指导，帮助您将权限管理系统部署到各种生产环境。无论是传统服务器部署、Docker容器化部署还是云服务部署，本指南都将帮助您建立安全可靠的生产环境。

## 目录

- [系统要求](#系统要求)
- [准备工作](#准备工作)
- [传统服务器部署](#传统服务器部署)
- [Docker容器化部署](#Docker容器化部署)
- [云服务部署](#云服务部署)
- [环境变量配置](#环境变量配置)
- [数据库迁移](#数据库迁移)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [监控与日志](#监控与日志)
- [常见问题排解](#常见问题排解)

## 系统要求

### 后端要求
- Python 3.8+
- PostgreSQL 12+
- 2GB RAM (最小)，推荐4GB+
- 10GB可用磁盘空间

### 前端要求
- Node.js 16+
- npm 8+ 或 yarn 1.22+
- 任何现代Web服务器如Nginx或Apache

## 准备工作

1. 获取最新的代码库
   ```bash
   git clone https://your-repository-url/permission-system.git
   cd permission-system
   ```

2. 准备环境变量文件
   - 后端: 复制 `.env.example` 到 `.env` 并修改配置
   - 前端: 复制 `.env.production.example` 到 `.env.production` 并修改配置

## 传统服务器部署

### 后端部署

1. 创建并激活Python虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate
   ```

2. 安装依赖
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. 设置数据库
   ```bash
   # 创建PostgreSQL数据库
   sudo -u postgres psql
   CREATE DATABASE permission_system;
   CREATE USER permission_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE permission_system TO permission_user;
   \q
   
   # 执行数据库迁移
   cd backend
   alembic upgrade head
   ```

4. 配置系统服务
   创建系统服务文件 `/etc/systemd/system/permission-backend.service`:
   ```ini
   [Unit]
   Description=Permission System Backend
   After=network.target

   [Service]
   User=yourusername
   Group=yourgroup
   WorkingDirectory=/path/to/permission-system/backend
   Environment="PATH=/path/to/permission-system/backend/venv/bin"
   ExecStart=/path/to/permission-system/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

5. 启动服务
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start permission-backend
   sudo systemctl enable permission-backend
   ```

### 前端部署

1. 安装依赖
   ```bash
   cd frontend
   npm install
   ```

2. 构建生产版本
   ```bash
   npm run build
   ```

3. 配置Nginx服务器
   创建配置文件 `/etc/nginx/sites-available/permission-frontend`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/permission-system/frontend/build;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

4. 启用站点并重启Nginx
   ```bash
   sudo ln -s /etc/nginx/sites-available/permission-frontend /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Docker容器化部署

我们提供了Docker配置，简化部署流程：

1. 准备Docker环境
   确保已安装Docker和Docker Compose:
   ```bash
   docker --version
   docker-compose --version
   ```

2. 配置环境变量
   编辑 `.env` 文件设置环境变量

3. 使用Docker Compose启动服务
   ```bash
   docker-compose up -d
   ```

4. 验证服务状态
   ```bash
   docker-compose ps
   ```

### Docker Compose配置说明

`docker-compose.yml` 定义了三个服务：

- **db**: PostgreSQL数据库
- **backend**: FastAPI后端服务
- **frontend**: React前端服务（Nginx提供）

您可以根据需求修改容器资源限制和网络配置。

## 云服务部署

### AWS部署

1. **使用AWS Elastic Beanstalk部署**
   
   准备部署文件:
   ```bash
   # 创建Procfile
   echo "web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile
   
   # 创建.ebextensions配置
   mkdir -p .ebextensions
   ```
   
   创建 `.ebextensions/01_packages.config`:
   ```yaml
   packages:
     yum:
       postgresql-devel: []
       python3-devel: []
   ```
   
   使用AWS EB CLI部署:
   ```bash
   eb init -p python-3.8 permission-system
   eb create permission-system-env
   eb deploy
   ```

2. **使用AWS ECS (Elastic Container Service) 部署**
   
   - 创建ECR仓库并推送Docker镜像
   - 配置ECS任务定义和服务
   - 设置负载均衡器和自动扩展

### Azure部署

1. **使用Azure App Service部署**
   
   ```bash
   # 登录Azure
   az login
   
   # 创建资源组
   az group create --name permission-system-rg --location eastus
   
   # 创建App Service计划
   az appservice plan create --name permission-system-plan --resource-group permission-system-rg --sku B1
   
   # 创建Web应用
   az webapp create --name permission-system --resource-group permission-system-rg --plan permission-system-plan
   
   # 设置Python版本
   az webapp config set --name permission-system --resource-group permission-system-rg --python-version 3.8
   
   # 部署应用
   az webapp deploy --name permission-system --resource-group permission-system-rg --src-path ./backend
   ```

2. **使用Azure Kubernetes Service (AKS) 部署**
   
   - 创建AKS集群
   - 配置Kubernetes部署文件
   - 使用kubectl部署服务

## 环境变量配置

系统使用环境变量进行配置，以下是关键变量及其说明：

### 后端环境变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| DATABASE_URL | 数据库连接字符串 | postgresql://user:password@localhost/dbname |
| JWT_SECRET_KEY | JWT令牌签名密钥 | your-secret-key-here |
| JWT_ALGORITHM | JWT签名算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌有效期(分钟) | 10080 |
| CORS_ORIGINS | 允许的跨域来源 | http://localhost:3000,https://yourdomain.com |
| LOG_LEVEL | 日志级别 | info |
| ENVIRONMENT | 运行环境 | production |

### 前端环境变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| REACT_APP_API_BASE_URL | API基础URL | /api 或 https://api.yourdomain.com |
| REACT_APP_AUTH_TOKEN_NAME | 本地存储中的令牌名称 | auth_token |
| NODE_ENV | 运行环境 | production |

## 数据库迁移

数据库结构更新使用Alembic迁移工具：

1. 应用现有迁移
   ```bash
   cd backend
   alembic upgrade head
   ```

2. 创建新的迁移
   ```bash
   # 修改模型后生成迁移脚本
   alembic revision --autogenerate -m "描述更改内容"
   
   # 审核生成的迁移脚本
   # 应用迁移
   alembic upgrade head
   ```

3. 数据库备份策略
   建议配置定期备份PostgreSQL数据库：
   ```bash
   # 创建备份脚本
   pg_dump -U user_name database_name > backup_$(date +%Y%m%d).sql
   ```
   使用cron作业定期执行

## 安全配置

生产环境部署应强化安全措施：

1. **HTTPS配置**
   
   配置SSL证书，可使用Let's Encrypt获取免费证书：
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **防火墙设置**
   
   仅开放必要端口：
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```

3. **限制API访问**
   
   配置JWT令牌验证并限制API访问频率：
   ```python
   # 在FastAPI应用中添加限流中间件
   app.add_middleware(
       RateLimitingMiddleware,
       calls_limit=100,
       time_window=60
   )
   ```

4. **数据加密**
   
   确保敏感数据使用适当的加密方法存储和传输。

## 性能优化

1. **数据库索引优化**
   
   为频繁查询的字段添加索引：
   ```sql
   CREATE INDEX idx_table_permissions_db_table ON table_permissions(db_name, table_name);
   CREATE INDEX idx_column_permissions_table_col ON column_permissions(table_name, col_name);
   ```

2. **缓存机制**
   
   实现Redis缓存减轻数据库负担：
   ```bash
   # 安装Redis
   sudo apt install redis-server
   
   # 安装Python Redis客户端
   pip install redis
   ```

   添加缓存逻辑到API查询：
   ```python
   # 示例代码见backend/app/core/cache.py
   ```

3. **应用性能监控**
   
   使用APM工具如New Relic或Datadog监控应用性能。

## 监控与日志

1. **设置日志记录**
   
   配置集中式日志系统，如ELK Stack (Elasticsearch, Logstash, Kibana)：
   ```bash
   # 配置Filebeat收集日志
   sudo apt install filebeat
   
   # 配置filebeat.yml
   ```

2. **系统监控**
   
   设置系统监控如Prometheus + Grafana提供实时系统状态监控。
   
3. **告警机制**
   
   配置基于阈值的告警通知，当出现异常时通过Email或Slack通知。

## 常见问题排解

### 数据库连接问题

**症状**: 应用无法连接到数据库
**解决方案**:
1. 验证数据库服务正在运行
   ```bash
   sudo systemctl status postgresql
   ```
2. 检查连接字符串格式
3. 确认防火墙没有阻止连接
4. 验证数据库用户权限

### API 400/500错误

**症状**: API返回400或500错误
**解决方案**:
1. 检查应用日志中的详细错误信息
2. 验证请求格式和必填字段
3. 检查数据库约束冲突
4. 在开发环境重现问题进行调试

### 前端无法连接后端

**症状**: 前端显示无法连接后端API
**解决方案**:
1. 验证API服务正在运行
2. 检查CORS配置是否允许前端域名
3. 检查反向代理设置是否正确
4. 尝试直接访问API端点验证其可用性

### JWT认证失败

**症状**: 用户无法登录或API返回401错误
**解决方案**:
1. 检查JWT密钥配置是否与前端存储的匹配
2. 验证令牌未过期
3. 检查令牌格式是否正确
