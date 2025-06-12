# 表权限管理系统

## 项目概述

表权限管理系统是一个基于FastAPI和React的全栈应用，用于管理数据库表的访问权限，包括表级、字段级和行级权限。系统支持多用户角色，权限申请与撤销，数据过滤与分页等功能。

## 系统特点

- **多级权限控制**：支持表级、字段级和行级权限管理
- **字段脱敏**：支持多种字段脱敏类型（手机号、身份证、银行卡号等）
- **灵活的行级过滤**：通过SQL条件表达式进行行级数据过滤
- **用户认证与授权**：JWT令牌认证，基于角色的权限控制
- **响应式设计**：适配不同设备尺寸的用户界面
- **完整的CRUD操作**：支持权限的创建、读取、更新和删除

## 技术栈

### 后端

- **语言**：Python 3.12
- **Web框架**：FastAPI
- **ORM**：SQLAlchemy
- **数据库**：PostgreSQL
- **迁移工具**：Alembic
- **认证**：JWT, Bcrypt

### 前端

- **语言**：JavaScript (ES6+)
- **框架**：React 18
- **UI库**：Ant Design 5.0
- **路由**：React Router v6
- **HTTP客户端**：Axios
- **状态管理**：React Context API

## 目录结构

```
permission-system/
├── backend/               # 后端代码
│   ├── alembic/           # 数据库迁移文件
│   ├── app/               # 应用代码
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心功能（配置、DB、安全）
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic模式
│   │   └── utils/         # 辅助工具
│   ├── tests/             # 单元测试
│   └── main.py            # 应用入口
├── frontend/              # 前端代码
│   ├── public/            # 静态资源
│   ├── src/               # 源代码
│   │   ├── api/           # API服务
│   │   ├── components/    # React组件
│   │   ├── context/       # React上下文
│   │   ├── pages/         # 页面组件
│   │   └── utils/         # 辅助工具
│   └── package.json       # 依赖配置
└── README.md              # 项目说明
```

## 快速开始

### 前置条件

- Python 3.12
- Node.js 18+
- PostgreSQL 14+

### 后端安装和运行

1. 克隆仓库并进入目录
   ```bash
   git clone <repository-url>
   cd permission-system/backend
   ```

2. 创建并激活Python虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量，创建.env文件
   ```
   DATABASE_URL=postgresql://postgres:password@localhost/permission_system
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_DAYS=7
   CORS_ORIGINS=["http://localhost:3000"]
   ```

5. 运行数据库迁移
   ```bash
   alembic upgrade head
   ```

6. 启动应用
   ```bash
   uvicorn main:app --reload
   ```

### 前端安装和运行

1. 进入前端目录
   ```bash
   cd permission-system/frontend
   ```

2. 安装依赖
   ```bash
   npm install
   ```

3. 启动开发服务器
   ```bash
   npm start
   ```

4. 浏览器访问
   ```
   http://localhost:3000
   ```

## 系统功能

### 用户认证

- 用户注册
- 用户登录
- JWT认证
- 密码哈希加密

### 表权限管理

- 创建表权限
- 管理表权限列表
- 过滤和分页查询
- 编辑和删除表权限

### 字段权限管理

- 创建字段权限
- 配置字段脱敏类型
- 管理字段权限列表
- 过滤和分页查询
- 编辑和删除字段权限

### 行权限管理

- 创建行级过滤条件
- 管理行权限列表
- 过滤和分页查询
- 编辑和删除行权限

## 测试

### 后端测试

```bash
cd backend
pytest
```

### 前端测试

```bash
cd frontend
npm test
```

## 部署

系统可以部署在任何支持Python和Node.js的环境中。推荐的部署选项包括：

- Docker容器化部署
- AWS/Azure/GCP云服务
- 传统服务器部署

## 许可证

本项目采用MIT许可证

## 联系方式

如有问题或建议，请联系项目维护者。
