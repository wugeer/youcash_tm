# 表权限管理系统部署文档

## 系统架构

本系统采用前后端分离架构：
- 前端：基于 Nginx 容器化部署
- 后端：基于 FastAPI 本地部署
- 数据库：PostgreSQL

## 部署方案

本文档详细说明了如何通过前端容器部署、后端本地部署的方式运行表权限管理系统。

### 一、环境要求

#### 前端环境要求
- Docker 19.03+
- 开放端口：8080（可根据需要调整）

#### 后端环境要求
- Python 3.12+（推荐使用 Mamba 或 Conda 环境）
- PostgreSQL 12+
- 开放端口：8000（后端 API 服务）

### 二、数据库准备

1. 确保 PostgreSQL 数据库已运行（示例中使用的是容器化的 PostgreSQL）

2. 创建所需的数据库和用户
   ```sql
   CREATE DATABASE permission_system;
   CREATE USER permission_user WITH PASSWORD 'permission_pass';
   GRANT ALL PRIVILEGES ON DATABASE permission_system TO permission_user;
   ```

### 三、后端部署

#### 1. 准备 Python 环境

使用标准 venv 创建虚拟环境（离线部署推荐）：
```bash
# 创建虚拟环境
python -m venv permission_venv

# 激活虚拟环境
# Linux/macOS
source permission_venv/bin/activate
# Windows
# permission_venv\Scripts\activate

# 验证环境
python --version
```

或者使用 Mamba/Conda（可选）：
```bash
# 激活 Python 环境
eval "$(micromamba shell hook --shell fish)" && micromamba activate py312
```

#### 2. 安装依赖包

```bash
cd /path/to/permission-system/backend
pip install -r requirements.txt
```

#### 3. 配置后端

查看并确认 `app/core/config.py` 中的配置是否正确：
- 数据库连接字符串
- CORS 设置
- API 前缀等

确保 CORS 配置允许前端访问：
```python
# app/core/config.py
BACKEND_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:13000",
    "http://172.17.0.1:8080",  # Docker 容器访问
    # 其他允许的源
]
```

#### 4. 启动后端服务

```bash
cd /path/to/permission-system/backend
# 激活虚拟环境
source permission_venv/bin/activate

# 开发环境启动（自动重载）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境启动（多进程）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

说明：
- `--workers N`：启动N个工作进程，建议设置为CPU核心数的2倍
- `--reload`：开发环境中开启代码变更自动重载
- 生产环境建议使用`gunicorn`作为进程管理器：
  ```bash
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
  ```

### 四、前端容器部署

#### 1. 构建前端 Docker 镜像

确保前端代码已经构建完毕（存在 build 目录）。

```bash
cd /path/to/permission-system/frontend
docker build -t permission-system-frontend .
```

#### 2. 运行前端容器

```bash
docker run -d -p 38000:80 -e API_URL="http://172.17.0.1:8000/api/v1" --name permission-frontend permission-system-frontend
```

参数说明：
- `-d`：后台运行
- `-p 38000:80`：将容器的 80 端口映射到宿主机的 38000 端口
- `-e API_URL="http://172.17.0.1:8000/api/v1"`：设置后端 API 地址
  - `172.17.0.1` 是 Docker 容器访问宿主机的默认地址
- `--name permission-frontend`：容器名称

### 五、验证部署

1. 访问前端：http://localhost:38000
2. 使用以下凭据登录：
   - 用户名：admin
   - 密码：admin123

### 六、常见问题处理

#### 1. 登录失败

如果登录失败，可能是以下原因：
- 后端服务未正常启动
- 数据库连接问题
- 用户不存在或密码错误
- 前端 API_URL 配置不正确

可以通过以下方式排查：
```bash
# 检查后端服务状态
ps aux | grep uvicorn

# 检查数据库连接
psql -U postgres -h localhost -c "SELECT 1;"

# 检查前端容器 API 配置
docker exec permission-frontend cat /usr/share/nginx/html/config.js

# 重置管理员用户密码（如需要）
python -c "from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; from app.core.config import SQLALCHEMY_DATABASE_URI; from app.models.models import User; from app.core.security import get_password_hash; engine = create_engine(SQLALCHEMY_DATABASE_URI); SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine); db = SessionLocal(); admin = db.query(User).filter(User.username == 'admin').first(); admin.password_hash = get_password_hash('admin123'); admin.is_admin = True; db.commit(); db.close(); print('管理员密码已重置');"
```

#### 2. 端口冲突

如果端口已被占用：
```bash
# 查找占用端口的进程
lsof -i:8000
# 或
lsof -i:8080

# 终止进程
kill -15 <PID>
```

#### 3. 容器无法访问主机

如果前端容器无法访问宿主机上的后端服务：
- 尝试使用宿主机的实际 IP 地址替代 172.17.0.1
- 确认防火墙设置允许访问

```bash
# 获取宿主机 IP
ip addr show

# 使用实际 IP 重启容器
docker rm -f permission-frontend
docker run -d -p 38000:80 -e API_URL="http://<实际IP>:8000/api/v1" --name permission-frontend permission-system-frontend
```

### 七、离线安装准备

对于离线环境，需要提前准备以下资源：

1. **Python 包离线安装**：
   ```bash
   # 在联网环境下载依赖
   pip download -r requirements.txt -d ./offline_packages
   
   # 将 offline_packages 目录复制到目标机器后
   # 1. 创建并激活虚拟环境
   python -m venv permission_venv
   source permission_venv/bin/activate  # Linux/macOS
   
   # 2. 安装依赖
   pip install --no-index --find-links=./offline_packages -r requirements.txt
   ```

2. **Docker 镜像离线迁移**：
   ```bash
   # 在联网环境保存镜像
   docker save -o permission-frontend.tar permission-system-frontend
   
   # 将 tar 文件复制到目标机器后，执行
   docker load -i permission-frontend.tar
   ```

3. **PostgreSQL 数据库导出/导入**（如需迁移数据）：
   ```bash
   # 导出
   pg_dump -U postgres permission_system > permission_system.sql
   
   # 导入
   psql -U postgres -d permission_system -f permission_system.sql
   ```

### 八、完整部署脚本

以下是一键部署的脚本示例（需根据实际环境调整）：

```bash
#!/bin/bash

# 1. 创建并激活 Python 虚拟环境
cd /path/to/permission-system/backend
python -m venv permission_venv
source permission_venv/bin/activate  # Linux/macOS
# permission_venv\Scripts\activate  # Windows

# 2. 部署后端
pip install -r requirements.txt
# 使用多进程运行后端（生产环境）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 3. 部署前端
cd /path/to/permission-system/frontend
docker build -t permission-system-frontend .
docker rm -f permission-frontend 2>/dev/null || true
docker run -d -p 38000:80 -e API_URL="http://172.17.0.1:8000/api/v1" --name permission-frontend permission-system-frontend

echo "部署完成！请访问 http://localhost:38000"
```

### 九、备注

- 生产环境部署时，应考虑使用更安全的配置
- 应定期备份数据库数据
- 如需要高可用部署，可考虑使用容器编排工具如 Kubernetes
- 本文档适用于开发和测试环境，生产环境可能需要进一步配置
