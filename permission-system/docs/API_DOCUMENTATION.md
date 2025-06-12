# API 文档

本文档详细介绍表权限管理系统的API接口。

## 目录

1. [认证接口](#认证接口)
2. [表权限接口](#表权限接口)
3. [字段权限接口](#字段权限接口)
4. [行权限接口](#行权限接口)
5. [通用参数](#通用参数)
6. [错误处理](#错误处理)

## 基础URL

所有API都基于以下基础URL:

```
http://localhost:8000
```

## 认证接口

### 用户注册

**请求**:
```
POST /auth/register
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean",
  "is_admin": "boolean"
}
```

### 用户登录

**请求**:
```
POST /auth/login/json
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "access_token": "string",
  "token_type": "string"
}
```

### 获取当前用户信息

**请求**:
```
GET /auth/me
```

**需要认证**: 是（JWT令牌）

**响应**:
```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean",
  "is_admin": "boolean"
}
```

### 创建管理员用户

**请求**:
```
POST /auth/create-admin
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean",
  "is_admin": "boolean"
}
```

## 表权限接口

### 获取表权限列表

**请求**:
```
GET /table-permissions
```

**需要认证**: 是（JWT令牌）

**查询参数**:
- `page`: 页码（默认为1）
- `page_size`: 每页条数（默认为10）
- `db_name`: 数据库名（可选）
- `table_name`: 表名（可选）
- `user_name`: 用户名（可选）
- `role_name`: 角色名（可选）

**响应**:
```json
{
  "items": [
    {
      "id": "integer",
      "db_name": "string",
      "table_name": "string",
      "user_name": "string",
      "role_name": "string",
      "create_time": "datetime",
      "update_time": "datetime"
    }
  ],
  "total": "integer"
}
```

### 获取单个表权限

**请求**:
```
GET /table-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 表权限ID

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 创建表权限

**请求**:
```
POST /table-permissions
```

**需要认证**: 是（JWT令牌）

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 更新表权限

**请求**:
```
PUT /table-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 表权限ID

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 删除表权限

**请求**:
```
DELETE /table-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 表权限ID

**响应**:
```json
{
  "detail": "表权限删除成功"
}
```

## 字段权限接口

### 获取字段权限列表

**请求**:
```
GET /column-permissions
```

**需要认证**: 是（JWT令牌）

**查询参数**:
- `page`: 页码（默认为1）
- `page_size`: 每页条数（默认为10）
- `db_name`: 数据库名（可选）
- `table_name`: 表名（可选）
- `col_name`: 字段名（可选）
- `mask_type`: 脱敏类型（可选）
- `user_name`: 用户名（可选）
- `role_name`: 角色名（可选）

**响应**:
```json
{
  "items": [
    {
      "id": "integer",
      "db_name": "string",
      "table_name": "string",
      "col_name": "string",
      "mask_type": "string",
      "user_name": "string",
      "role_name": "string",
      "create_time": "datetime",
      "update_time": "datetime"
    }
  ],
  "total": "integer"
}
```

### 获取单个字段权限

**请求**:
```
GET /column-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 字段权限ID

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "col_name": "string",
  "mask_type": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 创建字段权限

**请求**:
```
POST /column-permissions
```

**需要认证**: 是（JWT令牌）

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "col_name": "string",
  "mask_type": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**注**: `mask_type` 必须是以下值之一: "手机号", "身份证", "银行卡号", "座机号", "姓名", "原文"

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "col_name": "string",
  "mask_type": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 更新字段权限

**请求**:
```
PUT /column-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 字段权限ID

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "col_name": "string",
  "mask_type": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**注**: `mask_type` 必须是以下值之一: "手机号", "身份证", "银行卡号", "座机号", "姓名", "原文"

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "col_name": "string",
  "mask_type": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 删除字段权限

**请求**:
```
DELETE /column-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 字段权限ID

**响应**:
```json
{
  "detail": "字段权限删除成功"
}
```

## 行权限接口

### 获取行权限列表

**请求**:
```
GET /row-permissions
```

**需要认证**: 是（JWT令牌）

**查询参数**:
- `page`: 页码（默认为1）
- `page_size`: 每页条数（默认为10）
- `db_name`: 数据库名（可选）
- `table_name`: 表名（可选）
- `user_name`: 用户名（可选）
- `role_name`: 角色名（可选）

**响应**:
```json
{
  "items": [
    {
      "id": "integer",
      "db_name": "string",
      "table_name": "string",
      "row_filter": "string",
      "user_name": "string",
      "role_name": "string",
      "create_time": "datetime",
      "update_time": "datetime"
    }
  ],
  "total": "integer"
}
```

### 获取单个行权限

**请求**:
```
GET /row-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 行权限ID

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "row_filter": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 创建行权限

**请求**:
```
POST /row-permissions
```

**需要认证**: 是（JWT令牌）

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "row_filter": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "row_filter": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 更新行权限

**请求**:
```
PUT /row-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 行权限ID

**请求体**:
```json
{
  "db_name": "string",
  "table_name": "string",
  "row_filter": "string",
  "user_name": "string",
  "role_name": "string"
}
```

**响应**:
```json
{
  "id": "integer",
  "db_name": "string",
  "table_name": "string",
  "row_filter": "string",
  "user_name": "string",
  "role_name": "string",
  "create_time": "datetime",
  "update_time": "datetime"
}
```

### 删除行权限

**请求**:
```
DELETE /row-permissions/{id}
```

**需要认证**: 是（JWT令牌）

**路径参数**:
- `id`: 行权限ID

**响应**:
```json
{
  "detail": "行权限删除成功"
}
```

## 通用参数

### 分页参数

以下参数适用于所有列表接口:

- `page`: 页码，从1开始
- `page_size`: 每页条数，默认10条

### 排序参数

- `sort_by`: 排序字段
- `order`: 排序方向，可选值 "asc" 或 "desc"

## 错误处理

系统使用HTTP状态码和统一的错误响应格式:

```json
{
  "detail": "错误描述"
}
```

### 常见状态码

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权（未提供令牌或令牌无效）
- `403`: 权限不足
- `404`: 资源不存在
- `409`: 资源冲突（如唯一性约束冲突）
- `422`: 请求体验证错误
- `500`: 服务器内部错误
