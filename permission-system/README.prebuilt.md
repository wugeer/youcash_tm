# 预构建镜像部署指南

本文档提供了如何预先构建Docker镜像，然后将其部署到其他环境的详细步骤。

## 部署流程概述

1. 在开发环境中构建Docker镜像
2. 将镜像保存为文件并传输到目标环境
3. 在目标环境中加载镜像并启动容器
4. 初始化数据库并验证应用

## 详细步骤

### 1. 在开发环境中构建镜像

```bash
# 进入项目目录
cd permission-system

# 构建Docker镜像
docker build -t permission-system:latest -f Dockerfile.combined .
```

### 2. 保存镜像为文件

```bash
# 将镜像保存为tar文件
docker save permission-system:latest -o permission-system-image.tar

# 压缩tar文件以减小体积（可选）
gzip permission-system-image.tar
```

### 3. 传输镜像到目标环境

```bash
# 使用scp传输（示例）
scp permission-system-image.tar.gz user@target-server:/path/to/destination/

# 或使用其他文件传输方式
# - 云存储服务（如AWS S3, Google Cloud Storage等）
# - 物理存储设备
# - 文件共享服务
```

### 4. 在目标环境中准备部署

#### 4.1 准备PostgreSQL数据库

确保目标环境中已安装并启动PostgreSQL数据库：

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

#### 4.2 创建环境配置文件

在目标环境中创建`.env`文件：

```bash
# 创建.env文件
cat > .env << EOF
# 数据库配置 - 使用外部PostgreSQL
POSTGRES_USER=permission_user
POSTGRES_PASSWORD=permission_pass
POSTGRES_DB=permission_system
DATABASE_URL=postgresql://permission_user:permission_pass@host.docker.internal:5432/permission_system

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

### 5. 加载镜像并启动容器

```bash
# 如果镜像是压缩的，先解压
gunzip permission-system-image.tar.gz

# 加载Docker镜像
docker load -i permission-system-image.tar

# 确认镜像已加载
docker images | grep permission-system

# 创建并启动容器
docker run -d \
  --name permission-system \
  --restart always \
  -p 18000:80 \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  permission-system:latest
```

### 6. 初始化数据库

```bash
# 进入容器
docker exec -it permission-system bash

# 运行数据库迁移
cd /app
alembic upgrade head

# 退出容器
exit
```

### 7. 验证部署

访问以下URL验证应用是否正常运行：
- 应用访问地址：http://[服务器IP]:18000
- API文档：http://[服务器IP]:18000/docs

## 维护操作

### 查看容器日志

```bash
# 查看容器日志
docker logs permission-system

# 实时查看日志
docker logs -f permission-system
```

### 重启容器

```bash
# 重启容器
docker restart permission-system
```

### 停止和删除容器

```bash
# 停止容器
docker stop permission-system

# 删除容器
docker rm permission-system
```

### 更新镜像（新版本部署）

当有新版本时，重复上述步骤1-3构建并传输新镜像，然后在目标环境中执行：

```bash
# 停止并删除旧容器
docker stop permission-system
docker rm permission-system

# 加载新镜像
docker load -i new-permission-system-image.tar

# 启动新容器
docker run -d \
  --name permission-system \
  --restart always \
  -p 18000:80 \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  permission-system:latest

# 如有需要，执行数据库迁移
docker exec -it permission-system bash
cd /app
alembic upgrade head
exit
```

## 常见问题

### 1. 容器无法连接到数据库

确保：
- PostgreSQL服务已启动并监听在5432端口
- 数据库用户和权限配置正确
- 容器可以通过`host.docker.internal`访问主机
- 防火墙未阻止容器访问主机的5432端口

### 2. 容器启动但应用无法访问

检查：
- 容器日志：`docker logs permission-system`
- 确保18000端口未被占用：`netstat -tulpn | grep 18000`
- 防火墙是否允许18000端口的访问

### 3. 数据库迁移失败

可能原因：
- 数据库连接信息不正确
- 数据库用户权限不足
- 数据库架构已经存在但不兼容

解决方法：
- 检查环境变量中的数据库连接字符串
- 确保数据库用户有足够权限
- 考虑重新创建数据库（如果是全新部署）
