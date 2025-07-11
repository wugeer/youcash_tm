#!/bin/bash

# 权限管理系统部署脚本
# 用于在目标环境中加载预构建的Docker镜像并启动容器

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的命令是否存在
check_commands() {
    info "检查必要的命令..."
    for cmd in docker gunzip; do
        if ! command -v $cmd &> /dev/null; then
            error "$cmd 命令未找到，请先安装"
            exit 1
        fi
    done
}

# 检查镜像文件是否存在
check_image_file() {
    if [ ! -f "$1" ]; then
        error "镜像文件 $1 不存在"
        exit 1
    fi
    info "镜像文件检查通过"
}

# 加载Docker镜像
load_image() {
    local image_file=$1
    info "加载Docker镜像 $image_file..."
    
    # 如果是压缩文件，先解压
    if [[ "$image_file" == *.gz ]]; then
        info "解压镜像文件..."
        gunzip -k "$image_file"
        image_file="${image_file%.gz}"
    fi
    
    docker load -i "$image_file"
    if [ $? -ne 0 ]; then
        error "加载镜像失败"
        exit 1
    fi
    info "镜像加载成功"
}

# 创建环境变量文件
create_env_file() {
    local db_host=$1
    info "创建环境变量文件..."
    if [ -f ".env" ]; then
        warn ".env文件已存在，将被备份为.env.bak"
        mv .env .env.bak
    fi
    
    cat > .env << EOF
# 数据库配置 - 使用外部PostgreSQL
POSTGRES_USER=permission_user
POSTGRES_PASSWORD=permission_pass
POSTGRES_DB=permission_system
DATABASE_URL=postgresql://permission_user:permission_pass@${db_host}:5432/permission_system

# JWT配置
JWT_SECRET_KEY=BKiPGiS9hbaAHc97aG7llxNB5k_48s1zLo1dmt8HfOI=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS配置
CORS_ORIGINS=["http://localhost:18000"]

# 其他配置
TZ=Asia/Shanghai
EOF
    
    info "环境变量文件创建成功"
}

# 启动容器
start_container() {
    local image_name=$1
    local db_location=$2
    info "启动容器..."
    
    # 检查是否已存在同名容器
    if docker ps -a | grep -q "permission-system"; then
        warn "已存在名为permission-system的容器，将停止并删除"
        docker stop permission-system > /dev/null 2>&1
        docker rm permission-system > /dev/null 2>&1
    fi
    
    # 准备启动命令
    local run_cmd="docker run -d \
      --name permission-system \
      --restart always \
      -p 18000:80"
      
    # 根据数据库位置决定是否添加host.docker.internal映射
    if [ "$db_location" = "host" ]; then
        run_cmd="$run_cmd \
      --add-host=host.docker.internal:host-gateway"
    fi
    
    # 添加环境变量和镜像名
    run_cmd="$run_cmd \
      --env-file .env \
      $image_name"
    
    # 执行命令
    eval $run_cmd
    
    if [ $? -ne 0 ]; then
        error "启动容器失败"
        exit 1
    fi
    info "容器启动成功"
}

# 初始化数据库
init_database() {
    info "初始化数据库..."
    info "等待容器完全启动..."
    sleep 5
    
    docker exec -it permission-system bash -c "cd /app && alembic upgrade head"
    if [ $? -ne 0 ]; then
        warn "数据库初始化可能失败，请检查日志"
    else
        info "数据库初始化成功"
    fi
}

# 显示部署信息
show_deployment_info() {
    local host_ip=$(hostname -I | awk '{print $1}')
    echo ""
    info "部署完成！"
    echo "=============================================="
    echo "应用访问地址: http://$host_ip:18000"
    echo "API文档: http://$host_ip:18000/docs"
    echo "=============================================="
    echo "查看容器日志: docker logs permission-system"
    echo "进入容器: docker exec -it permission-system bash"
    echo "重启容器: docker restart permission-system"
    echo "停止容器: docker stop permission-system"
    echo "=============================================="
}

# 主函数
main() {
    echo "=============================================="
    echo "权限管理系统部署脚本"
    echo "=============================================="
    
    if [ $# -lt 1 ]; then
        error "使用方法: $0 <镜像文件路径> [镜像名称:标签]"
        error "例如: $0 permission-system-image.tar.gz permission-system:latest"
        exit 1
    fi
    
    local image_file=$1
    local image_name=${2:-"permission-system:latest"}
    local db_location=${3:-"host"}
    
    check_commands
    check_image_file "$image_file"
    load_image "$image_file"
    create_env_file "$db_location"
    start_container "$image_name" "$db_location"
    init_database
    show_deployment_info
}

# 执行主函数
main "$@"
