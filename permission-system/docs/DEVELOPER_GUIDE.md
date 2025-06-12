# 开发者指南

## 目录

1. [系统架构](#系统架构)
2. [后端开发指南](#后端开发指南)
3. [前端开发指南](#前端开发指南)
4. [数据库设计](#数据库设计)
5. [认证与授权](#认证与授权)
6. [测试指南](#测试指南)
7. [代码风格与规范](#代码风格与规范)
8. [常见问题与解决方案](#常见问题与解决方案)

## 系统架构

表权限管理系统采用前后端分离架构，基于RESTful API进行通信。

### 后端架构

- **FastAPI框架**：高性能异步API框架
- **SQLAlchemy ORM**：对象关系映射
- **Pydantic**：数据验证和序列化
- **JWT认证**：基于JSON Web Tokens的用户认证
- **依赖注入**：便于测试和维护
- **中间件**：处理CORS、认证等横切关注点

### 前端架构

- **React** + **Hooks**：组件化UI开发
- **Context API**：全局状态管理（认证状态）
- **React Router**：路由控制与导航
- **Axios**：HTTP请求与拦截器
- **Ant Design**：UI组件库

### 数据流

1. 用户通过前端界面发起请求
2. Axios拦截器添加认证令牌
3. 请求发送到FastAPI后端
4. 后端依赖处理认证和权限验证
5. 业务逻辑处理（CRUD操作）
6. 响应返回给前端
7. 前端渲染数据或处理错误

## 后端开发指南

### 项目结构

```
backend/
├── alembic/                # 数据库迁移
├── app/
│   ├── api/                # API路由
│   │   ├── deps.py         # 依赖函数
│   │   ├── endpoints/      # 各模块API实现
│   │   │   ├── auth.py     # 认证相关API
│   │   │   ├── column_permissions.py   # 字段权限API
│   │   │   ├── row_permissions.py      # 行权限API
│   │   │   └── table_permissions.py    # 表权限API
│   │   └── routers.py      # 路由注册
│   │
│   ├── core/                # 核心配置
│   │   ├── config.py       # 系统配置类
│   │   ├── db.py           # 数据库连接
│   │   └── security.py     # 认证和安全
│   │
│   ├── models/              # 数据库模型
│   │   └── models.py       # SQLAlchemy模型
│   │
│   └── schemas/             # Pydantic模式
│       ├── auth.py         # 认证相关模式
│       ├── column_permission.py   # 字段权限模式
│       ├── row_permission.py      # 行权限模式
│       └── table_permission.py    # 表权限模式
│
├── tests/                   # 单元测试
├── main.py                  # 应用入口
└── requirements.txt         # 依赖列表
```

### 添加新功能

要添加新功能，请按照以下步骤：

1. **创建数据库模型**：在`app/models/models.py`中
2. **创建Pydantic模式**：在`app/schemas/`目录下
3. **实现API端点**：在`app/api/endpoints/`中创建新文件
4. **注册路由**：在`app/api/routers.py`中添加路由
5. **创建数据库迁移**：`alembic revision -m "Add new feature"`
6. **应用迁移**：`alembic upgrade head`
7. **编写测试**：在`tests/`目录中

### 依赖注入

FastAPI使用依赖注入模式来处理共享逻辑。主要依赖位于`app/api/deps.py`中：

```python
# 获取当前用户
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # ...验证令牌并返回用户...

# 检查是否是管理员
def get_current_admin_user(current_user: User = Depends(get_current_user)):
    # ...检查管理员权限...
```

在API端点中使用依赖：

```python
@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    # 只有认证用户可访问
    return {"message": "Welcome, authenticated user"}
```

## 前端开发指南

### 项目结构

```
frontend/
├── public/                # 静态资源
├── src/
│   ├── api/               # API服务
│   │   ├── auth.js        # 认证API
│   │   ├── tablePermission.js  # 表权限API
│   │   ├── columnPermission.js  # 字段权限API
│   │   ├── rowPermission.js  # 行权限API
│   │   └── axios.js       # Axios配置
│   │
│   ├── components/         # 可复用组件
│   │   ├── layout/        # 布局组件
│   │   └── common/        # 通用组件
│   │
│   ├── context/            # React上下文
│   │   └── AuthContext.js  # 认证状态管理
│   │
│   ├── pages/              # 页面组件
│   │   ├── auth/          # 认证相关页面
│   │   ├── tablePermission/  # 表权限页面
│   │   ├── columnPermission/  # 字段权限页面
│   │   └── rowPermission/  # 行权限页面
│   │
│   ├── utils/              # 工具函数
│   │
│   ├── App.js              # 应用根组件
│   └── index.js            # 入口文件
│
├── package.json            # 依赖配置
└── setupProxy.js           # 开发代理配置
```

### 添加新页面

要添加新页面，请按照以下步骤：

1. 在`src/pages/`中创建新目录和页面组件
2. 在`src/App.js`的路由配置中注册页面
3. 如果需要，在`src/api/`目录下创建API服务
4. 更新导航组件以添加新页面链接

### 状态管理

系统使用React Context API进行状态管理：

```javascript
// 使用认证上下文
import { useAuth } from '../context/AuthContext';

function MyComponent() {
  const { user, login, logout } = useAuth();
  
  // 使用认证状态和方法
}
```

### API调用

使用Axios进行API调用：

```javascript
import { createTablePermission } from '../api/tablePermission';

async function handleSubmit(values) {
  try {
    const response = await createTablePermission(values);
    // 处理响应
  } catch (error) {
    // 处理错误
  }
}
```

## 数据库设计

### 实体关系图

```
┌───────────┐       ┌────────────────┐       ┌────────────────────┐
│   User    │       │ TablePermission │       │  ColumnPermission  │
├───────────┤       ├────────────────┤       ├────────────────────┤
│ id        │       │ id             │       │ id                 │
│ username  │       │ db_name        │       │ db_name            │
│ password  │       │ table_name     │       │ table_name         │
│ is_active │       │ user_name      │       │ col_name           │
│ is_admin  │       │ role_name      │       │ mask_type          │
└───────────┘       │ create_time    │       │ user_name          │
                    │ update_time    │       │ role_name          │
                    └────────────────┘       │ create_time        │
                                             │ update_time        │
                                             └────────────────────┘
                                             
                    ┌────────────────┐
                    │  RowPermission │
                    ├────────────────┤
                    │ id             │
                    │ db_name        │
                    │ table_name     │
                    │ row_filter     │
                    │ user_name      │
                    │ role_name      │
                    │ create_time    │
                    │ update_time    │
                    └────────────────┘
```

### 主要表及关系

- **User**: 用户表，存储认证信息
- **TablePermission**: 表权限信息
- **ColumnPermission**: 字段权限和脱敏信息
- **RowPermission**: 行权限过滤条件

## 认证与授权

### JWT认证流程

1. 用户登录（提供用户名和密码）
2. 服务器验证凭据，生成JWT令牌
3. 前端存储令牌（localStorage）
4. 前端请求带上令牌认证头：`Authorization: Bearer {token}`
5. 后端验证令牌，确认用户身份

### 权限检查

- 表/字段/行权限API验证当前用户是否有权限
- 不同操作可能需要不同级别的权限（普通用户/管理员）

## 测试指南

### 后端测试

后端使用pytest进行测试：

```bash
cd backend
pytest
```

#### 测试结构

- `tests/conftest.py`: 测试治具和共享资源
- `tests/test_*.py`: 按功能模块组织的测试用例

#### 编写测试

```python
def test_create_table_permission(client, test_user_token):
    # 准备测试数据
    test_data = {...}
    
    # 发送请求
    response = client.post(
        "/table-permissions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json=test_data
    )
    
    # 断言响应
    assert response.status_code == 200
    data = response.json()
    assert data["db_name"] == test_data["db_name"]
    # ...更多断言...
```

### 前端测试

前端使用Jest和React Testing Library进行测试：

```bash
cd frontend
npm test
```

#### 测试结构

- `src/__tests__/*.test.js`: 按组件组织的测试用例

#### 编写测试

```javascript
test('表单提交 - 成功创建', async () => {
  // 准备测试数据和Mock
  const submitForm = jest.fn().mockResolvedValue({ id: 1, ...mockData });
  
  // 渲染组件
  render(<Form onSubmit={submitForm} />);
  
  // 填写表单
  fireEvent.change(screen.getByLabelText('名称'), { target: { value: 'test' } });
  
  // 提交表单
  fireEvent.click(screen.getByRole('button', { name: '保存' }));
  
  // 断言
  await waitFor(() => {
    expect(submitForm).toHaveBeenCalledWith(expect.objectContaining({
      name: 'test'
    }));
  });
});
```

## 代码风格与规范

### 后端代码规范

- 遵循PEP 8标准
- 使用类型提示（Type Hints）
- 使用Pydantic进行数据验证
- 文档字符串格式：Google风格

### 前端代码规范

- 使用ES6+语法
- 使用函数组件和Hooks
- 命名约定：
  - 组件文件：PascalCase
  - 工具/服务：camelCase
- 使用PropTypes或TypeScript类型注释

## 常见问题与解决方案

### 跨域问题

前端开发时通过`setupProxy.js`解决跨域:

```javascript
module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      pathRewrite: {
        '^/api': '',
      },
    })
  );
};
```

### 认证问题

如果遇到认证失败，检查：

1. 令牌是否过期
2. 令牌是否正确添加到请求头
3. 用户是否有权限执行操作

### 数据库迁移错误

解决数据库迁移错误的步骤：

1. 检查当前迁移状态：`alembic current`
2. 如果迁移历史有问题：`alembic stamp head`重置到最新版本
3. 创建新迁移：`alembic revision --autogenerate -m "message"`
4. 应用迁移：`alembic upgrade head`
