FROM nginx:stable-alpine

# 安装所需的调试和网络工具
RUN apk add --no-cache bash gettext curl iputils busybox-extras iproute2 bind-tools

# 复制前端构建文件和配置
COPY build/ /usr/share/nginx/html

# 保存nginx.conf到多个位置，确保入口脚本能找到
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 同时保存一份到/app目录作为备份
RUN mkdir -p /app
COPY nginx.conf /app/

# 复制入口脚本并设置执行权限
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# 创建配置目录，确保所有必要的路径存在
RUN mkdir -p /etc/nginx/sites-enabled

# 将默认模板复制到其他可能的位置以兼容不同的Nginx配置
RUN cp /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default || true

EXPOSE 80

# 使用入口脚本
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
