# Railway 部署 PDF/Word 解析优化说明

## 📋 概述

优化了PDF和Word文档解析功能，提升线上部署的准确度。实现了三级解析策略，确保在不同环境下都能获得最佳解析效果。

## 🔧 修改内容

### 1. requirements.txt - 固定版本

**更新内容：**
- 固定所有依赖版本，确保部署一致性
- 新增依赖：
  - `cryptography==41.0.7` - 加密功能
  - `PyMuPDF==1.23.26` - PDF文本提取（优先）
  - `pdfplumber==0.11.0` - PDF文本提取（备用）
  - `pytesseract==0.3.10` - OCR识别（最后手段）
  - `Pillow==10.2.0` - 图像处理
  - `nltk==3.8.1` - 自然语言处理
  - `certifi` - SSL证书

### 2. aptfile - 系统依赖

**创建 `aptfile` 文件（根目录）：**

```
poppler-utils          # PDF处理工具
libpoppler-cpp-dev     # PDF处理开发库
tesseract-ocr          # OCR引擎
tesseract-ocr-chi-sim  # 简体中文OCR
tesseract-ocr-chi-tra  # 繁体中文OCR
tesseract-ocr-eng      # 英文OCR
libjpeg-dev            # JPEG图像处理
libpng-dev             # PNG图像处理
libtiff-dev            # TIFF图像处理
ca-certificates        # SSL证书
openssl                # SSL/TLS支持
```

**说明：** Railway 会自动读取 `aptfile` 并在构建时安装这些系统依赖。

### 3. PDF解析函数 - 三级解析策略

**优化 `utils/file_parser.py` 中的 `extract_text_from_pdf()` 函数：**

#### 策略优先级：

1. **优先：PyMuPDF**（最快，适合文本PDF）
   - 直接提取PDF中的文本层
   - 保持页面顺序和结构
   - 适合大多数标准PDF文档

2. **备用：pdfplumber**（适合复杂布局）
   - 更好的表格和复杂布局处理
   - 适合包含表格、多栏布局的PDF

3. **最后：OCR**（扫描件处理）
   - 将PDF页面转换为图片
   - 使用Tesseract OCR识别
   - 支持中英文混合识别
   - 适合扫描件、图片PDF

#### 判断标准：

- 文本长度 >= 200字符
- 中文字符数量 >= 50个
- 中文字符占比 >= 10%
- 唯一字符数 >= 50

### 4. 启动时初始化

**在 `app.py` 开头添加 `initialize_app()` 函数：**

```python
def initialize_app():
    """应用启动时的初始化操作"""
    # 1. SSL上下文设置
    # 2. NLTK数据下载
    # 3. 检查PDF解析库
```

**功能：**
- SSL上下文设置（解决证书验证问题）
- NLTK数据自动下载（如果不存在）
- 检查并报告PDF解析库状态

### 5. 测试端点

**新增 `/test-parser` 端点：**

```http
POST /test-parser
Content-Type: application/json

{
  "file_path": "20251226_064645_xxx.pdf",
  "test_methods": ["PyMuPDF", "pdfplumber", "OCR"]
}
```

**功能：**
- 对比三种解析方法的效果
- 显示每种方法的文本长度、中文字符数
- 推荐最佳解析方法
- 提供文本预览

**响应示例：**
```json
{
  "success": true,
  "data": {
    "file_path": "xxx.pdf",
    "file_size": 123456,
    "methods": {
      "PyMuPDF": {
        "success": true,
        "text_length": 5000,
        "chinese_chars": 2000,
        "page_count": 3,
        "preview": "..."
      },
      "pdfplumber": {...},
      "OCR": {...}
    },
    "recommended_method": "PyMuPDF"
  }
}
```

## 🔐 环境变量配置

### Railway 环境变量设置

在 Railway 项目设置中添加以下环境变量：

#### 必需环境变量

1. **`ENCRYPTION_KEY`**（推荐）
   - 用于加密存储API密钥
   - 建议使用32字节的随机字符串
   - 生成方式：`python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **`SECRET_KEY`**（推荐）
   - Flask会话密钥
   - 生成方式：`python -c "import secrets; print(secrets.token_hex(32))"`

#### 可选环境变量

3. **`AI_ENABLED`**
   - 是否启用AI功能
   - 默认值：`true`

4. **`OPENAI_API_KEY`** / `AI_API_KEY`
   - AI API密钥
   - 用于AI解析和文本优化

5. **`AI_API_BASE`**
   - AI API基础URL
   - 如果使用OpenAI，可以留空

6. **`AI_MODEL`**
   - AI模型名称
   - 默认值：`gpt-3.5-turbo`

7. **`TESSDATA_PREFIX`**（可选）
   - Tesseract OCR数据路径
   - Railway会自动设置

## 📊 解析策略对比

| 方法 | 速度 | 准确度 | 适用场景 | 依赖 |
|------|------|--------|----------|------|
| PyMuPDF | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 文本PDF | 低 |
| pdfplumber | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 复杂布局PDF | 低 |
| OCR | ⭐⭐ | ⭐⭐⭐ | 扫描件/图片PDF | 高 |

## 🚀 部署步骤

### 1. 更新代码

```bash
git add .
git commit -m "优化PDF/Word解析功能"
git push
```

### 2. Railway 自动部署

Railway 会自动：
1. 读取 `aptfile` 并安装系统依赖
2. 读取 `requirements.txt` 并安装Python依赖
3. 执行应用启动初始化

### 3. 验证部署

1. **检查日志：** 查看应用启动日志，确认所有库已加载
2. **测试解析：** 使用 `/test-parser` 端点测试PDF解析
3. **上传测试：** 上传一个PDF文件，检查解析效果

## 🔍 故障排查

### 问题1: OCR不可用

**症状：** 日志显示 "pytesseract (OCR) 未安装"

**解决方案：**
- 确认 `aptfile` 中包含 `tesseract-ocr` 和相关语言包
- 确认 `requirements.txt` 中包含 `pytesseract==0.3.10`
- 重新部署应用

### 问题2: PDF解析失败

**症状：** 所有解析方法都返回空文本

**可能原因：**
- PDF是加密的
- PDF是纯图片格式
- 文件损坏

**解决方案：**
- 使用 `/test-parser` 端点测试
- 检查PDF是否加密
- 如果确实是图片PDF，确保AI API已配置

### 问题3: SSL证书错误

**症状：** 启动时SSL相关错误

**解决方案：**
- 确认 `certifi` 已安装
- 检查 `aptfile` 中是否包含 `ca-certificates`
- 重新部署应用

## 📈 性能优化建议

1. **优先使用PyMuPDF：** 最快且准确度较高
2. **避免OCR：** OCR速度慢，仅在必要时使用
3. **配置AI API：** 对于图片PDF，AI解析通常比OCR更准确
4. **缓存结果：** 对于相同文件，可以缓存解析结果

## 📝 测试建议

1. **本地测试：**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

2. **测试端点：**
   ```bash
   curl -X POST http://localhost:5000/test-parser \
     -H "Content-Type: application/json" \
     -d '{"file_path": "test.pdf"}'
   ```

3. **生产环境测试：**
   - 访问 `https://your-domain.com/test-parser`
   - 上传测试PDF文件
   - 查看解析结果对比

## 🔄 更新日志

- **2025-01-27:** 初始实现
  - 添加三级解析策略
  - 创建 aptfile
  - 添加测试端点
  - 优化启动初始化

---

**维护者：** 系统管理员  
**最后更新：** 2025-01-27

