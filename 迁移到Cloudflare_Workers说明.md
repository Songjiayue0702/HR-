# 迁移到Cloudflare Workers说明

## 已完成的工作

### 1. 依赖检查与替换 ✅
- **修改了 `requirements.txt`**：将 `PyPDF2==3.0.1` 替换为 `pymupdf==1.23.8`
- **修改了 `utils/file_parser.py`**：将PyPDF2替换为pymupdf（fitz），简化了PDF文本提取逻辑

### 2. 创建适配层 ✅

#### D1数据库适配器 (`d1_adapter.py`)
- 提供了类似SQLAlchemy的接口，将ORM操作转换为D1 SQL操作
- 实现了以下功能：
  - Resume（简历）的CRUD操作
  - User（用户）的CRUD操作
  - Position（岗位）的CRUD操作
  - Interview（面试）的CRUD操作
  - 密码哈希和验证功能
  - JSON字段的自动序列化/反序列化

#### R2存储适配器 (`r2_storage.py`)
- 提供了类似本地文件系统的接口
- 实现了以下功能：
  - 文件上传到R2
  - 文件下载 from R2
  - 文件删除
  - 文件存在性检查
  - 文件列表
  - 统一的FileStorageAdapter类，管理uploads和exports两个存储桶

### 3. 创建Worker主入口 (`worker.py`) ✅
- 将Flask应用的核心逻辑迁移为Cloudflare Worker
- 实现了以下路由：
  - `/api/login` - 用户登录
  - `/api/logout` - 用户登出
  - `/api/current-user` - 获取当前用户信息
  - `/api/education-levels` - 获取教育层级选项
  - `/api/upload` - 文件上传（需要登录）
  - `/api/resumes` - 获取简历列表
  - `/api/resumes/<id>` - 获取简历详情
- 实现了Session管理（使用Cookie）
- 实现了权限装饰器（`require_login`、`require_admin`）
- 添加了CORS支持

## 配置文件

### `wrangler.toml`
已配置：
- Worker名称：`x12523.site`
- 主入口：`worker.py`
- D1数据库绑定：`DB`（数据库名：`zhaopinxitong`）
- R2存储桶绑定：
  - `UPLOADS_BUCKET`（桶名：`resume-uploads`）
  - `EXPORTS_BUCKET`（桶名：`resume-exports`）

## 注意事项

### 1. Cloudflare Workers Python运行时
- Workers使用Python运行时，但某些标准库可能不可用
- 某些依赖（如`werkzeug`）可能需要替换为纯Python实现
- 文件上传的multipart/form-data处理可能需要根据实际运行时调整

### 2. 异步处理
- 原Flask应用中的`process_resume_async`使用线程处理，Workers不支持线程
- 需要使用以下替代方案之一：
  - **Cloudflare Queues**：将任务放入队列，由另一个Worker处理
  - **Durable Objects**：使用Durable Objects处理长时间运行的任务
  - **定时任务**：使用Cron Triggers定期处理pending状态的简历

### 3. Session管理
- 当前实现使用Cookie存储session，安全性较低
- 建议使用以下方案之一：
  - **Workers KV**：存储session数据
  - **D1数据库**：在数据库中存储session
  - **JWT Token**：使用JWT token进行身份验证

### 4. 静态文件
- 原Flask应用使用本地`static`和`templates`目录
- Workers中建议使用：
  - **Cloudflare Pages**：将静态文件部署到Pages
  - **R2存储桶**：将静态文件存储在R2，通过Worker提供访问
  - **外部CDN**：使用其他CDN服务

### 5. 数据库迁移
- 需要将SQLite数据库迁移到D1
- 可以使用以下方法：
  - 使用`wrangler d1 execute`命令执行SQL脚本
  - 使用D1的Web UI导入数据
  - 编写迁移脚本，从SQLite导出数据并导入D1

### 6. 依赖兼容性
- 某些依赖可能不兼容Workers环境：
  - `reportlab`（PDF生成）：可能需要替换为其他库或使用外部服务
  - `openpyxl`（Excel处理）：需要确认是否支持Workers环境
  - `python-docx`（Word处理）：需要确认是否支持Workers环境

## 下一步工作

1. **测试Worker**：
   - 使用`wrangler dev`本地测试
   - 部署到Cloudflare并测试各个功能

2. **完善路由**：
   - 实现所有API路由（目前只实现了部分）
   - 添加错误处理和日志记录

3. **数据库迁移**：
   - 创建D1数据库表结构
   - 迁移现有数据

4. **异步任务处理**：
   - 实现简历解析的异步处理机制
   - 配置Queue或Durable Objects

5. **静态文件部署**：
   - 将前端静态文件部署到Pages或R2
   - 配置Worker路由到静态文件

6. **Session优化**：
   - 实现更安全的Session管理
   - 添加Session过期机制

7. **错误处理**：
   - 添加全局错误处理
   - 添加日志记录和监控

## 部署命令

```bash
# 本地开发
wrangler dev

# 部署到生产环境
wrangler deploy

# 执行数据库迁移
wrangler d1 execute zhaopinxitong --file=./schema.sql

# 查看日志
wrangler tail
```

## 参考文档

- [Cloudflare Workers Python文档](https://developers.cloudflare.com/workers/languages/python/)
- [Cloudflare D1文档](https://developers.cloudflare.com/d1/)
- [Cloudflare R2文档](https://developers.cloudflare.com/r2/)
- [Cloudflare Queues文档](https://developers.cloudflare.com/queues/)

