# 用户管理 API — 产品需求文档

## 概述

本系统为用户管理模块，提供用户的增删改查接口。

基础 URL: `http://localhost:8000`

## API 端点

### 1. 获取用户列表

- **路径**: `/api/users`
- **方法**: GET
- **描述**: 分页获取用户列表，支持按用户名模糊搜索
- **查询参数**:
  - `page`: integer, 默认 1, 页码
  - `size`: integer, 默认 20, 每页数量, 最大 100
  - `keyword`: string, 可选, 搜索关键字
- **响应体**: 用户列表及分页信息

### 2. 创建用户

- **路径**: `/api/users`
- **方法**: POST
- **描述**: 注册新用户
- **请求体**:
  - `username`: string, 必填, 用户名, 长度 3-50
  - `email`: email, 必填, 邮箱地址
  - `password`: string, 必填, 密码, 最小长度 8
  - `age`: integer, 可选, 年龄, 范围 1-150
  - `bio`: string, 可选, 个人简介, 最大长度 500
- **响应体**: 创建的用户信息（不含密码）

### 3. 获取单个用户

- **路径**: `/api/users/{user_id}`
- **方法**: GET
- **描述**: 根据 ID 获取用户详情
- **路径参数**:
  - `user_id`: uuid, 必填, 用户唯一标识
- **响应体**: 用户详细信息

### 4. 更新用户

- **路径**: `/api/users/{user_id}`
- **方法**: PUT
- **描述**: 更新用户资料
- **路径参数**:
  - `user_id`: uuid, 必填, 用户唯一标识
- **请求体**:
  - `username`: string, 可选, 用户名, 长度 3-50
  - `email`: email, 可选, 邮箱
  - `age`: integer, 可选, 年龄, 范围 1-150
  - `bio`: string, 可选, 个人简介, 最大长度 500
- **响应体**: 更新后的用户信息

### 5. 删除用户

- **路径**: `/api/users/{user_id}`
- **方法**: DELETE
- **描述**: 删除指定用户（软删除）
- **路径参数**:
  - `user_id`: uuid, 必填, 用户唯一标识
- **响应状态**: 204

## 数据库实体

### users 表

| 列名 | 类型 | 约束 |
|------|------|------|
| id | UUID | PRIMARY KEY, NOT NULL |
| username | VARCHAR(50) | NOT NULL, UNIQUE |
| email | VARCHAR(320) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| age | INTEGER | NULL |
| bio | VARCHAR(500) | NULL |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

索引: `idx_users_email ON users(email)`, `idx_users_username ON users(username)`
