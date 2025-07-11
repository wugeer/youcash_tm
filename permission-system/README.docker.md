# Docker部署指南

本文档提供了使用Docker部署权限管理系统的详细步骤。

## 系统架构

该系统使用Docker Compose编排以下两个服务：

1. **后端服务 (backend)**：基于FastAPI的Python应用
2. **前端服务 (frontend)**：基于React的Web应用，通过Nginx提供服务

系统使用外部PostgreSQL数据库（非Docker容器）

## 前置条件

- 安装Docker (20.10.0+)
- 安装Docker Compose (2.0.0+)
- 确保18000和18182端口未被占用
- 已安装并配置好PostgreSQL数据库（非Docker容器）

## 部署步骤

### 1. 克隆代码库

```bash
git clone <repository-url>
cd permission-system
```

### 2. 准备外部PostgreSQL数据库

在部署Docker容器前，需要准备好外部PostgreSQL数据库：

```bash
# 登录到PostgreSQL
psql -U postgres

# 创建数据库和用户
CREATE USER permission_user WITH PASSWORD 'permission_pass';
CREATE DATABASE permission_system;
GRANT ALL PRIVILEGES ON DATABASE permission_system TO permission_user;

# 退出
\q
```

### 3. 配置环境变量

项目根目录下已提供`.env`文件，需要更新数据库连接信息以匹配您的外部PostgreSQL数据库：

```bash
# 编辑环境变量
nano .env
```

确保`DATABASE_URL`变量指向您的外部PostgreSQL数据库，例如：
```
DATABASE_URL=postgresql://permission_user:permission_pass@host.docker.internal:5432/permission_system
```

### 4. 构建并启动服务

```bash
# 构建镜像并启动容器
docker-compose up -d --build
```

首次构建可能需要几分钟时间，请耐心等待。

### 5. 初始化数据库（首次部署）

```bash
# 进入后端容器
docker exec -it permission-backend bash

# 运行数据库迁移
alembic upgrade head

# 退出容器
exit
```

注意：确保外部PostgreSQL数据库已经启动并可以从容器中访问。

### 6. 访问应用

- 前端应用：http://localhost:18000
- 后端API文档：http://localhost:18000/docs 或 http://localhost:18182/docs

## 维护指南

### 查看日志

```bash
# 查看所有服务的日志
docker-compose logs

# 查看特定服务的日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用，会删除数据库数据）
docker-compose down -v
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 数据备份与恢复

### 备份数据库

```bash
docker exec -t permission-db pg_dump -U permission_user permission_system > backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

### 恢复数据库

```bash
cat backup_file.sql | docker exec -i permission-db psql -U permission_user -d permission_system
```

## 常见问题

1. **无法连接到数据库**
   - 检查外部PostgreSQL数据库是否正常运行：`pg_isready -h localhost -p 5432`
   - 检查数据库连接配置是否正确：`.env`文件中的`DATABASE_URL`
   - 确保容器可以通过`host.docker.internal`访问主机的PostgreSQL

2. **前端无法访问后端API**
   - 检查后端服务是否正常运行：`docker-compose ps`
   - 检查Nginx配置是否正确：`frontend/nginx.conf`

3. **容器启动失败**
   - 查看详细错误日志：`docker-compose logs`
   - 检查端口是否被占用：`netstat -tulpn | grep -E '8000|80|5432'`
