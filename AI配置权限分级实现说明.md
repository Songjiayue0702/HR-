# AI配置权限分级实现说明

## 📋 概述

实现了权限分级的AI配置管理系统，支持管理员设置全局持久化配置和用户设置个人临时配置。

## 🏗️ 架构设计

### 配置优先级

1. **用户session配置**（最高优先级）- 临时配置，登出失效
2. **管理员全局配置**（中等优先级）- 持久化存储在数据库
3. **环境变量配置**（最低优先级）- 默认配置

### 数据存储

- **全局配置：** 存储在 `global_ai_config` 表（加密存储API密钥）
- **用户配置：** 存储在 Flask session（临时，登出失效）

## 📝 修改内容

### 1. models.py - 新增数据模型

**新增 `GlobalAIConfig` 模型类：**

```python
class GlobalAIConfig(Base):
    """全局AI配置数据模型（管理员设置）"""
    __tablename__ = 'global_ai_config'
    
    # 配置字段
    ai_enabled: bool          # 是否启用AI
    ai_api_key: str            # API密钥（加密存储）
    ai_api_base: str           # API基础URL
    ai_model: str              # AI模型
    
    # 操作记录
    created_by: str            # 创建者
    updated_by: str            # 最后更新者
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**特性：**
- 单例模式（只保留一条记录）
- API密钥加密存储
- 操作记录追踪

### 2. utils/encryption.py - 加密工具

**新增加密工具模块：**

- `encrypt_value(value: str) -> str` - 加密字符串
- `decrypt_value(encrypted_value: str) -> str` - 解密字符串
- `get_encryption_key()` - 获取加密密钥（从环境变量 `ENCRYPTION_KEY`）

**加密方式：**
- 使用 Fernet 对称加密
- 密钥从环境变量 `ENCRYPTION_KEY` 获取
- 如果未设置，使用默认密钥（仅开发环境）

### 3. app.py - 核心修改

#### 3.1 辅助函数

**`get_effective_ai_config()`**
- 获取当前有效的AI配置
- 按优先级合并：用户session > 全局配置 > 环境变量
- 返回配置字典

**`create_ai_extractor(ai_config=None)`**
- 创建AI提取器实例
- 如果 `ai_config` 为 `None`，使用 `get_effective_ai_config()`
- 检查AI是否启用和API密钥是否有效

#### 3.2 管理员全局配置API

**GET `/api/admin/ai-config`**
- 获取全局AI配置
- 需要 `@admin_required` 装饰器
- 返回配置信息（API密钥可选返回）

**POST `/api/admin/ai-config`**
- 设置全局AI配置
- 需要 `@admin_required` 装饰器
- API密钥自动加密存储
- 记录操作者信息

**POST `/api/admin/ai-config/test`**
- 测试全局AI配置连接
- 需要 `@admin_required` 装饰器
- 执行简单测试并返回结果

#### 3.3 用户个人配置API

**GET `/api/user/ai-config`**
- 获取用户个人AI配置
- 需要 `@login_required` 装饰器
- 从session读取配置

**POST `/api/user/ai-config`**
- 设置用户个人AI配置
- 需要 `@login_required` 装饰器
- 存储在session中（临时）

**DELETE `/api/user/ai-config`**
- 清除用户个人AI配置
- 需要 `@login_required` 装饰器
- 从session删除配置

**POST `/api/user/ai-config/test`**
- 测试用户个人AI配置连接
- 需要 `@login_required` 装饰器
- 使用当前有效配置测试

#### 3.4 现有AI使用函数修改

**`process_resume_async(resume_id, file_path)`**
- 异步任务使用全局配置（不依赖session）
- 优先级：全局配置 > 环境变量
- 使用 `create_ai_extractor()` 创建提取器

**`analyze_interview_doc(interview_id)`**
- 使用 `get_effective_ai_config()` 获取配置
- 使用 `create_ai_extractor()` 创建提取器
- 支持用户临时配置覆盖

**`analyze_resume_match(resume_id)`**
- 使用 `get_effective_ai_config()` 获取配置
- 使用 `create_ai_extractor()` 创建提取器
- 支持用户临时配置覆盖

## 🔐 安全特性

### API密钥加密存储

- 管理员配置的API密钥使用 Fernet 对称加密
- 加密密钥从环境变量 `ENCRYPTION_KEY` 获取
- 数据库存储的是加密后的值

### 权限控制

- 管理员配置API需要管理员权限（`@admin_required`）
- 用户配置API需要登录权限（`@login_required`）
- 配置读取遵循优先级，用户无法直接访问全局配置的密钥

## 📊 数据库迁移

### 创建表

运行 `init_database()` 会自动创建 `global_ai_config` 表：

```python
from models import init_database
init_database()
```

### 表结构

```sql
CREATE TABLE global_ai_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_enabled INTEGER DEFAULT 1,
    ai_api_key TEXT,
    ai_api_base VARCHAR(500),
    ai_model VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    created_at DATETIME,
    updated_at DATETIME
);
```

## 🔧 环境变量

### 必需环境变量

**`ENCRYPTION_KEY`**（推荐设置）
- 用于加密存储API密钥
- 建议使用32字节的随机字符串
- 如果未设置，使用默认密钥（不安全，仅开发环境）

### 可选环境变量（默认配置）

- `AI_ENABLED` - 是否启用AI（默认：true）
- `OPENAI_API_KEY` / `AI_API_KEY` - API密钥
- `AI_API_BASE` - API基础URL
- `AI_MODEL` - AI模型（默认：gpt-3.5-turbo）

## 📖 API使用示例

### 管理员设置全局配置

```javascript
// 设置全局配置
POST /api/admin/ai-config
{
  "ai_enabled": true,
  "ai_api_key": "sk-xxx",
  "ai_api_base": "https://api.openai.com/v1",
  "ai_model": "gpt-4"
}

// 测试配置
POST /api/admin/ai-config/test
{
  "ai_enabled": true,
  "ai_api_key": "sk-xxx",
  "ai_api_base": "https://api.openai.com/v1",
  "ai_model": "gpt-4"
}
```

### 用户设置个人配置

```javascript
// 设置个人配置（临时）
POST /api/user/ai-config
{
  "ai_enabled": true,
  "ai_api_key": "sk-xxx",
  "ai_api_base": "https://api.deepseek.com",
  "ai_model": "deepseek-chat"
}

// 清除个人配置
DELETE /api/user/ai-config

// 测试配置
POST /api/user/ai-config/test
{
  "ai_enabled": true,
  "ai_api_key": "sk-xxx",
  "ai_api_base": "https://api.deepseek.com",
  "ai_model": "deepseek-chat"
}
```

## 🎯 使用场景

### 场景1：管理员设置全局配置

1. 管理员登录系统
2. 访问管理员配置页面
3. 设置全局AI配置（API密钥、模型等）
4. 配置自动加密存储到数据库
5. 所有用户默认使用此配置

### 场景2：用户临时使用不同配置

1. 用户登录系统
2. 访问个人设置页面
3. 设置个人AI配置（覆盖全局配置）
4. 配置存储在session中
5. 用户的所有AI操作使用个人配置
6. 登出后配置失效，恢复使用全局配置

### 场景3：异步任务使用全局配置

1. 用户上传简历
2. 系统启动异步解析任务
3. 异步任务使用全局配置（不依赖session）
4. 确保任务执行时配置可用

## ⚠️ 注意事项

1. **加密密钥：** 生产环境必须设置 `ENCRYPTION_KEY` 环境变量
2. **配置优先级：** 用户配置会覆盖全局配置，但仅对当前session有效
3. **异步任务：** 异步任务使用全局配置，不支持用户临时配置
4. **配置测试：** 建议在设置配置后先测试连接
5. **密钥安全：** API密钥加密存储，但前端传输时仍需使用HTTPS

## 🔄 迁移步骤

1. **更新代码：** 拉取最新代码
2. **设置环境变量：** 设置 `ENCRYPTION_KEY`
3. **初始化数据库：** 运行 `init_database()` 创建新表
4. **设置全局配置：** 管理员通过API设置全局配置
5. **测试功能：** 测试AI功能是否正常工作

## 📚 相关文件

- `models.py` - 数据模型定义
- `app.py` - 主应用和API接口
- `utils/encryption.py` - 加密工具
- `utils/ai_extractor.py` - AI提取器（使用配置）

---

**实现完成时间：** 2025-01-27  
**版本：** v1.0.0

