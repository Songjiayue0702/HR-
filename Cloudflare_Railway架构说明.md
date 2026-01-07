# Cloudflare D1 + Railway 架构实现说明

## 📋 概述

已实现支持 Cloudflare D1 和 Railway 架构的双数据库 Flask 应用，具备自动降级、统一接口和完整的监控功能。

## 🏗️ 架构设计

### 1. 双数据库支持

**优先级：**
1. **Cloudflare D1**（优先）- 通过环境变量检测
2. **SQLite**（降级方案）- 自动切换

**自动检测逻辑：**
- 检查环境变量：`CF_ACCOUNT_ID`、`CF_D1_DATABASE_ID`、`CF_API_TOKEN`
- 检查全局 `DB` 对象（Cloudflare Workers 环境）
- 如果 D1 不可用，自动降级到 SQLite

### 2. DatabaseManager 类

**位置：** `database_manager.py`

**核心功能：**
- 统一数据库连接管理
- 自动选择数据库类型
- 提供统一的 `execute()` 接口
- 连接测试和状态查询

**主要方法：**
```python
- initialize()          # 初始化数据库连接
- get_session()         # 获取数据库会话（SQLite）
- execute(sql, params)  # 执行 SQL（统一接口）
- test_connection()     # 测试连接
- get_status()          # 获取状态信息
```

## 🛣️ 新增路由

### 1. `/` - 系统状态首页
- **功能：** 展示架构和数据库状态
- **返回：** HTML 页面（`status.html`）
- **内容：**
  - 数据库类型和状态
  - 连接测试结果
  - 环境变量配置
  - 快速导航链接

### 2. `/health` - 健康检查
- **功能：** Railway 健康检查端点
- **方法：** GET
- **返回：** JSON
```json
{
  "status": "healthy",
  "database": "connected",
  "db_type": "sqlite",
  "timestamp": "2025-01-27T..."
}
```

### 3. `/api/status` - API 状态信息
- **功能：** 获取完整的系统状态
- **方法：** GET
- **返回：** JSON
- **内容：**
  - 应用信息
  - 数据库状态
  - 环境变量配置

### 4. `/init-db` - 初始化数据库
- **功能：** 手动初始化数据库表
- **方法：** GET/POST
- **返回：** JSON
- **用途：** 首次部署或重置数据库

### 5. `/test-d1` - 测试数据库连接
- **功能：** 测试当前数据库连接
- **方法：** GET
- **返回：** JSON
- **内容：** 连接测试结果和错误信息

### 6. `/env-check` - 环境变量检查
- **功能：** 检查环境变量配置
- **方法：** GET
- **返回：** JSON
- **内容：**
  - 所有环境变量状态
  - 配置检查结果
  - 配置建议

## 🔧 环境变量

### Railway 必需
- `PORT` - Railway 自动设置
- `HOST` - 可选，默认 `0.0.0.0`

### Cloudflare D1
- `CF_ACCOUNT_ID` - Cloudflare 账户 ID
- `CF_D1_DATABASE_ID` - D1 数据库 ID
- `CF_API_TOKEN` - Cloudflare API Token

### Cloudflare R2
- `CF_R2_ACCOUNT_ID` - R2 账户 ID
- `CF_R2_ACCESS_KEY_ID` - R2 访问密钥 ID
- `CF_R2_SECRET_ACCESS_KEY` - R2 密钥
- `CF_R2_BUCKET_NAME` - R2 存储桶名称

### 其他
- `SECRET_KEY` - Flask 密钥（建议设置）
- `DATABASE_PATH` - SQLite 数据库路径（可选）
- `DEBUG` - 调试模式（生产环境建议 False）

## 🚀 部署流程

### Railway 部署

1. **连接 GitHub 仓库**
2. **设置环境变量：**
   - `PORT` - Railway 自动设置
   - `SECRET_KEY` - 生成随机密钥
   - 其他可选变量

3. **部署后验证：**
   - 访问 `https://your-app.railway.app/health`
   - 访问 `https://your-app.railway.app/` 查看状态
   - 访问 `https://your-app.railway.app/env-check` 检查配置

### Cloudflare Workers 部署

1. **配置 D1 数据库**
2. **设置环境变量**
3. **部署 Workers**
4. **验证连接**

## 📊 错误处理

### 数据库连接失败
- **行为：** 应用仍能启动
- **日志：** 详细的错误信息
- **降级：** 自动切换到 SQLite

### 初始化失败
- **行为：** 记录警告，继续启动
- **恢复：** 可通过 `/init-db` 手动初始化

## 🔍 调试功能

### 日志输出
- 数据库初始化过程
- 连接测试结果
- 错误详细信息

### 状态监控
- 实时数据库状态
- 连接测试
- 环境变量检查

## 📝 代码兼容性

### 现有代码兼容
- `get_db_session()` 函数保持兼容
- 现有路由无需修改
- 数据库操作透明切换

### 新功能使用
```python
from database_manager import get_database_manager

# 获取数据库管理器
db_manager = get_database_manager()

# 获取状态
status = db_manager.get_status()

# 测试连接
result = db_manager.test_connection()

# 执行 SQL（统一接口）
db_manager.execute("SELECT * FROM resumes")
```

## 🎯 使用建议

1. **首次部署：**
   - 访问 `/` 查看系统状态
   - 访问 `/init-db` 初始化数据库
   - 访问 `/env-check` 检查配置

2. **日常监控：**
   - Railway 自动调用 `/health` 端点
   - 定期检查 `/api/status` 获取详细状态

3. **故障排查：**
   - 查看 `/test-d1` 连接测试结果
   - 检查 `/env-check` 环境变量配置
   - 查看应用日志

## ⚠️ 注意事项

1. **D1 数据库：** 需要在 Cloudflare Workers 环境中才能完全使用
2. **SQLite 降级：** 在非 Workers 环境中自动使用 SQLite
3. **环境变量：** 敏感信息（如 API Token）不要提交到代码库
4. **端口配置：** Railway 会自动设置 PORT，无需手动配置

## 🔄 更新日志

- **2025-01-27:** 初始实现
  - 添加 DatabaseManager 类
  - 实现双数据库支持
  - 添加所有必需路由
  - 实现错误处理和日志

---

**维护者：** 系统管理员
**最后更新：** 2025-01-27

