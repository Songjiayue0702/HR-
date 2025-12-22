# Cloudflare 部署指南

## ⚠️ 重要说明

**您的项目是 Flask Python 后端应用，而 Cloudflare Workers 不支持 Python。**

Cloudflare Workers 只支持：
- JavaScript/TypeScript
- WebAssembly (WASM)
- 不支持 Python、Java、Go 等语言

## 📋 项目结构分析

您的项目结构：
```
项目根目录/
├── app.py                 # Flask 后端应用（Python）
├── config.py              # 配置文件
├── models.py              # 数据模型
├── requirements.txt       # Python 依赖
├── utils/                 # Python 工具函数
├── static/                # 静态资源
├── templates/             # HTML 模板
├── uploads/               # 上传文件存储
└── database.db            # SQLite 数据库
```

这是一个**完整的 Flask 后端应用**，不是前端静态站点。

## 🎯 部署方案选择

### 方案一：使用支持 Python 的云平台（推荐）

#### 1. Railway（推荐）
- ✅ 支持 Python Flask
- ✅ 自动部署
- ✅ 免费额度充足
- ✅ 简单易用

**部署步骤：**
1. 访问 https://railway.app
2. 连接 GitHub 仓库
3. 选择 Python 模板
4. Railway 会自动检测 `requirements.txt` 和 `app.py`
5. 设置环境变量（AI API 密钥等）
6. 部署完成

**需要创建的文件：**
```bash
# Procfile（告诉 Railway 如何启动应用）
web: python app.py
```

#### 2. Render
- ✅ 支持 Python Flask
- ✅ 免费套餐可用
- ✅ 自动 HTTPS

**部署步骤：**
1. 访问 https://render.com
2. 创建新的 Web Service
3. 连接 GitHub 仓库
4. 设置构建命令：`pip install -r requirements.txt`
5. 设置启动命令：`python app.py`
6. 设置环境变量
7. 部署

#### 3. Fly.io
- ✅ 支持 Python
- ✅ 全球边缘部署
- ✅ 免费额度

**部署步骤：**
1. 安装 Fly CLI：`curl -L https://fly.io/install.sh | sh`
2. 登录：`fly auth login`
3. 初始化：`fly launch`
4. 部署：`fly deploy`

**需要创建 `fly.toml`：**
```toml
app = "your-app-name"
primary_region = "iad"

[build]

[env]
  PORT = "5000"

[[services]]
  internal_port = 5000
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

#### 4. Heroku
- ✅ 支持 Python
- ⚠️ 免费套餐已取消，需要付费

### 方案二：Cloudflare Pages + Functions（有限支持）

Cloudflare Pages Functions 支持 Python，但有以下限制：
- ⚠️ 仅支持边缘函数（Edge Functions）
- ⚠️ 不支持完整的 Flask 应用
- ⚠️ 不支持 SQLite 数据库（需要使用 Cloudflare D1）
- ⚠️ 不支持文件上传存储（需要使用 R2）

**如果您想使用 Cloudflare，需要：**
1. 重构应用为 Cloudflare Pages Functions
2. 使用 Cloudflare D1 数据库（而不是 SQLite）
3. 使用 Cloudflare R2 存储文件（而不是本地 uploads 目录）
4. 重写所有路由为 Cloudflare Functions

**这需要大量重构工作，不推荐。**

### 方案三：分离前后端（高级）

如果您坚持使用 Cloudflare：
1. **前端**：部署到 Cloudflare Pages（静态文件）
2. **后端**：部署到支持 Python 的平台（Railway、Render 等）
3. 配置 CORS 允许跨域请求

## 🚀 推荐部署方案：Railway

### 步骤 1：准备部署文件

创建 `Procfile`：
```bash
web: python app.py
```

创建 `runtime.txt`（可选，指定 Python 版本）：
```
python-3.11
```

### 步骤 2：修改 app.py 以支持生产环境

在 `app.py` 末尾修改启动代码：

```python
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port, use_reloader=False)
```

### 步骤 3：配置环境变量

在 Railway/Render 等平台设置以下环境变量：
- `OPENAI_API_KEY` 或 `AI_API_KEY` 或 `DEEPSEEK_API_KEY`
- `AI_MODEL`（可选，默认：gpt-3.5-turbo）
- `AI_API_BASE`（可选）
- `SECRET_KEY`（Flask session 密钥）
- `PORT`（Railway 会自动设置）

### 步骤 4：部署到 Railway

1. 访问 https://railway.app
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择您的仓库
5. Railway 会自动检测 Python 项目
6. 在 Settings → Variables 中添加环境变量
7. 等待部署完成

### 步骤 5：配置自定义域名（可选）

1. 在 Railway 项目设置中添加自定义域名
2. Railway 会自动配置 SSL 证书

## 📝 部署前检查清单

- [ ] 确保 `requirements.txt` 包含所有依赖
- [ ] 创建 `Procfile`（Railway/Render）
- [ ] 修改 `app.py` 支持环境变量（PORT、HOST）
- [ ] 设置所有必需的环境变量
- [ ] 确保数据库路径使用相对路径（`./database.db`）
- [ ] 确保上传目录使用相对路径（`./uploads`）
- [ ] 测试本地运行：`python app.py`

## 🔧 常见问题

### Q: 为什么不能直接部署到 Cloudflare Workers？
A: Cloudflare Workers 只支持 JavaScript/TypeScript，不支持 Python。

### Q: 数据库文件怎么办？
A: SQLite 数据库文件会保存在服务器上。如果需要持久化，考虑：
- 使用 PostgreSQL（Railway/Render 都提供）
- 使用 Cloudflare D1（如果使用 Cloudflare）
- 定期备份数据库文件

### Q: 文件上传存储怎么办？
A: 上传的文件会保存在服务器的 `uploads/` 目录。如果需要更好的存储：
- 使用对象存储（AWS S3、Cloudflare R2）
- 使用数据库存储（BLOB）

### Q: 如何迁移到 PostgreSQL？
A: 修改 `models.py` 中的数据库连接：
```python
# 从 SQLite
DATABASE_URL = 'sqlite:///database.db'

# 改为 PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
```

## 📚 相关资源

- Railway 文档：https://docs.railway.app
- Render 文档：https://render.com/docs
- Fly.io 文档：https://fly.io/docs
- Cloudflare Workers 文档：https://developers.cloudflare.com/workers/

## 🎯 推荐方案总结

**最佳选择：Railway**
- ✅ 最简单
- ✅ 免费额度充足
- ✅ 自动部署
- ✅ 支持 Python Flask

**备选方案：Render**
- ✅ 免费套餐
- ✅ 简单易用
- ⚠️ 免费实例会休眠

**不推荐：Cloudflare Workers**
- ❌ 不支持 Python
- ❌ 需要大量重构

