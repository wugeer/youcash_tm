# 前后端合并Docker部署指南

本文档提供了使用单一Docker容器部署权限管理系统的详细步骤。

## 系统架构

该系统使用单一Docker容器运行：

- **合并服务 (app)**：包含基于FastAPI的Python后端和基于React的前端应用，通过Nginx提供服务
- 系统使用外部PostgreSQL数据库（非Docker容器）

## 前置条件

- 安装Docker (20.10.0+)
- 安装Docker Compose (2.0.0+)
- 确保18000端口未被占用
- 已安装并配置好PostgreSQL数据库（非Docker容器）

## 部署步骤

### 1. 准备外部PostgreSQL数据库

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

### 2. 配置环境变量

项目根目录下已提供`.env`文件，需要更新数据库连接信息以匹配您的外部PostgreSQL数据库：

```bash
# 编辑环境变量
nano .env
```

确保`DATABASE_URL`变量指向您的外部PostgreSQL数据库，例如：
```
DATABASE_URL=postgresql://permission_user:permission_pass@host.docker.internal:5432/permission_system
```

### 3. 构建并启动服务

```bash
# 使用合并的Docker Compose配置构建并启动容器
docker-compose -f docker-compose.combined.yml up -d --build
```

首次构建可能需要几分钟时间，请耐心等待。

### 4. 初始化数据库（首次部署）

```bash
# 进入容器
docker exec -it permission-system bash

# 运行数据库迁移
cd /app
alembic upgrade head

# 退出容器
exit
```

注意：确保外部PostgreSQL数据库已经启动并可以从容器中访问。

### 5. 访问应用

- 应用访问地址：http://localhost:18000
- API文档：http://localhost:18000/docs

## 维护指南

### 查看日志

```bash
# 查看容器日志
docker logs permission-system

# 实时查看日志
docker logs -f permission-system
```

### 重启服务

```bash
# 重启容器
docker-compose -f docker-compose.combined.yml restart
```

### 停止服务

```bash
# 停止容器
docker-compose -f docker-compose.combined.yml down
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.combined.yml up -d --build
```

## 常见问题

1. **无法连接到数据库**
   - 检查外部PostgreSQL数据库是否正常运行：`pg_isready -h localhost -p 5432`
   - 检查数据库连接配置是否正确：`.env`文件中的`DATABASE_URL`
   - 确保容器可以通过`host.docker.internal`访问主机的PostgreSQL

2. **应用无法访问**
   - 检查容器是否正常运行：`docker ps`
   - 检查容器日志：`docker logs permission-system`
   - 确保18000端口未被占用：`netstat -tulpn | grep 18000`

3. **前端无法访问后端API**
   - 检查Nginx配置是否正确
   - 检查后端服务是否在容器内正常运行：`docker exec -it permission-system ps aux | grep uvicorn`
