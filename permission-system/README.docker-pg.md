# PostgreSQL在Docker中部署指南

本文档提供了如何在Docker容器中部署PostgreSQL，并将其与权限管理系统容器连接的详细步骤。

## 方案概述

有三种方式可以将权限管理系统与Docker容器中的PostgreSQL连接：

1. 使用Docker自定义网络
2. 使用Docker Compose
3. 使用容器IP地址

下面将详细介绍这三种方式。

## 方案一：使用Docker自定义网络

### 1. 创建Docker网络

```bash
# 创建一个名为permission-network的网络
docker network create permission-network
```

### 2. 启动PostgreSQL容器

```bash
# 启动PostgreSQL容器并连接到网络
docker run -d \
  --name permission-postgres \
  --restart always \
  --network permission-network \
  -e POSTGRES_USER=permission_user \
  -e POSTGRES_PASSWORD=permission_pass \
  -e POSTGRES_DB=permission_system \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:14
```

### 3. 创建环境变量文件

```bash
# 创建.env文件，注意数据库主机名使用容器名
cat > .env << EOF
# 数据库配置 - 使用Docker容器中的PostgreSQL
POSTGRES_USER=permission_user
POSTGRES_PASSWORD=permission_pass
POSTGRES_DB=permission_system
DATABASE_URL=postgresql://permission_user:permission_pass@permission-postgres:5432/permission_system

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

### 4. 启动应用容器

```bash
# 启动应用容器并连接到同一网络
docker run -d \
  --name permission-system \
  --restart always \
  --network permission-network \
  -p 18000:80 \
  --env-file .env \
  permission-system:latest
```

### 5. 初始化数据库

```bash
# 进入容器
docker exec -it permission-system bash

# 运行数据库迁移
cd /app
alembic upgrade head

# 退出容器
exit
```

## 方案二：使用Docker Compose

### 1. 创建Docker Compose文件

创建一个名为`docker-compose.pg.yml`的文件：

```bash
cat > docker-compose.pg.yml << EOF
version: '3.8'

services:
  app:
    image: permission-system:latest
    container_name: permission-system
    restart: always
    ports:
      - "18000:80"
    depends_on:
      - db
    environment:
      - POSTGRES_USER=permission_user
      - POSTGRES_PASSWORD=permission_pass
      - POSTGRES_DB=permission_system
      - DATABASE_URL=postgresql://permission_user:permission_pass@db:5432/permission_system
      - JWT_SECRET_KEY=BKiPGiS9hbaAHc97aG7llxNB5k_48s1zLo1dmt8HfOI=
      - JWT_ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_DAYS=7
      - CORS_ORIGINS=["http://localhost:18000"]
      - TZ=Asia/Shanghai

  db:
    image: postgres:14
    container_name: permission-postgres
    restart: always
    environment:
      - POSTGRES_USER=permission_user
      - POSTGRES_PASSWORD=permission_pass
      - POSTGRES_DB=permission_system
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF
```

### 2. 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.pg.yml up -d

# 运行数据库迁移
docker exec -it permission-system bash -c "cd /app && alembic upgrade head"
```

## 方案三：使用容器IP地址

### 1. 启动PostgreSQL容器

```bash
# 启动PostgreSQL容器
docker run -d \
  --name permission-postgres \
  --restart always \
  -e POSTGRES_USER=permission_user \
  -e POSTGRES_PASSWORD=permission_pass \
  -e POSTGRES_DB=permission_system \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:14
```

### 2. 获取PostgreSQL容器IP地址

```bash
# 获取PostgreSQL容器IP地址
PG_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' permission-postgres)
echo "PostgreSQL容器IP地址: $PG_IP"
```

### 3. 创建环境变量文件

```bash
# 创建.env文件，使用PostgreSQL容器IP
cat > .env << EOF
# 数据库配置 - 使用Docker容器中的PostgreSQL
POSTGRES_USER=permission_user
POSTGRES_PASSWORD=permission_pass
POSTGRES_DB=permission_system
DATABASE_URL=postgresql://permission_user:permission_pass@${PG_IP}:5432/permission_system

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

### 4. 启动应用容器

```bash
# 启动应用容器
docker run -d \
  --name permission-system \
  --restart always \
  -p 18000:80 \
  --env-file .env \
  permission-system:latest
```

### 5. 初始化数据库

```bash
# 进入容器
docker exec -it permission-system bash

# 运行数据库迁移
cd /app
alembic upgrade head

# 退出容器
exit
```

## 方案比较

1. **Docker网络方案**：
   - 优点：简单易用，容器可以通过名称相互访问
   - 缺点：需要手动创建网络和容器

2. **Docker Compose方案**：
   - 优点：配置集中，一键启动所有服务
   - 缺点：需要额外学习Docker Compose

3. **容器IP方案**：
   - 优点：不需要创建网络
   - 缺点：容器重启后IP可能会变化

## 推荐方案

对于生产环境，推荐使用**Docker Compose方案**，因为它提供了最简单和最可靠的方式来管理多个相关容器。

对于快速测试，可以使用**Docker网络方案**，它提供了良好的平衡，既简单又相对可靠。
