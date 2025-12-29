# Cloudflare Workers 依赖替换总结

## 📋 不兼容库清单

### ❌ 必须移除的库

| 库名 | 原因 | 影响 |
|------|------|------|
| **Flask** | Workers不需要Web框架 | 已移除，使用原生fetch API |
| **Werkzeug** | Flask依赖 | 已移除 |
| **flask-cors** | Flask扩展 | 已移除，Workers原生支持CORS |
| **sqlalchemy** | ORM框架 | 已移除，使用D1原生SQL |

### ⚠️ 需要替换的库

| 库名 | 不兼容原因 | 替代方案 | 状态 |
|------|-----------|---------|------|
| **python-docx** | 可能依赖系统库 | ✅ 纯Python实现（zipfile+xml） | 已完成 |
| **openpyxl** | 有C扩展 | ✅ CSV格式导出 | 已完成 |
| **reportlab** | 有C扩展 | ⚠️ 客户端生成PDF或外部服务 | 待处理 |
| **pymupdf** | 有C扩展 | ⚠️ AI API处理或外部服务 | 待处理 |
| **requests** | 同步HTTP库 | ✅ Workers原生fetch | 已完成 |
| **openai** | 可能不兼容 | ✅ 原生fetch API调用 | 已完成 |

## ✅ 已完成的替代方案

### 1. Word文档解析 ✅

**文件**：`utils/file_parser_cf.py`

**特点**：
- 纯Python实现（zipfile + xml.etree.ElementTree）
- 支持.docx格式
- 提取段落、表格、页眉页脚
- 完全兼容Workers环境

**使用示例**：
```python
from utils.file_parser_cf import extract_text_from_word

# file_data是bytes类型
text = extract_text_from_word(file_data)
```

### 2. Excel导出 → CSV导出 ✅

**文件**：`utils/export_cf.py`

**特点**：
- 使用Python标准库csv模块
- CSV可以在Excel中打开
- 支持中文（添加UTF-8 BOM）
- 文件体积更小

**使用示例**：
```python
from utils.export_cf import export_resumes_to_csv

csv_data = export_resumes_to_csv(resumes_list)
return Response(csv_data, headers={
    'Content-Type': 'text/csv; charset=utf-8',
    'Content-Disposition': 'attachment; filename="resumes.csv"'
})
```

### 3. AI API调用 ✅

**文件**：`utils/ai_extractor_cf.py`

**特点**：
- 使用Workers原生fetch API
- 完全异步，性能更好
- 支持所有兼容OpenAI API的服务
- 无需额外依赖

**使用示例**：
```python
from utils.ai_extractor_cf import AIExtractor

extractor = AIExtractor(
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# 在Worker中调用时传入fetch函数
result = await extractor.extract_with_ai(text, fetch_func=fetch)
```

## ⚠️ 待处理的方案

### 1. PDF文本提取

**问题**：pymupdf有C扩展，可能不兼容

**推荐方案**：
1. **使用AI API处理PDF**（推荐）
   - 将PDF转换为图片发送给AI API
   - AI API可以处理图片PDF和文本PDF
   - 实现简单，准确率高

2. **使用外部PDF解析服务**
   - 通过HTTP API调用外部服务
   - 需要额外的服务成本

3. **测试pymupdf在Workers中的可用性**
   - 如果可用，继续使用
   - 如果不可用，使用方案1或2

### 2. PDF生成

**问题**：reportlab有C扩展，不兼容

**推荐方案**：
1. **客户端生成PDF**（推荐）
   - 使用JavaScript库（如jsPDF）在浏览器生成
   - 服务器只提供数据
   - 无需服务器资源

2. **返回HTML格式**
   - 生成格式化的HTML
   - 用户使用浏览器打印功能保存为PDF
   - 简单但格式控制有限

3. **使用外部PDF生成服务**
   - 通过HTTP API调用外部服务
   - 需要额外的服务成本

## 📝 更新的文件

### 新增文件

1. **utils/file_parser_cf.py** - Word文档解析（纯Python）
2. **utils/ai_extractor_cf.py** - AI调用（使用fetch API）
3. **utils/export_cf.py** - CSV导出（替代Excel）

### 修改文件

1. **cf-requirements.txt** - 移除了所有不兼容的依赖

## 🔄 代码迁移指南

### 文件解析

**原代码**：
```python
from utils.file_parser import extract_text
text = extract_text(file_path)  # 需要文件路径
```

**新代码**：
```python
from utils.file_parser_cf import extract_text
text = extract_text(file_data, filename)  # 使用文件数据（bytes）
```

### Excel导出

**原代码**：
```python
from utils.export import export_resumes_to_excel
wb = export_resumes_to_excel(resume)
wb.save('resume.xlsx')
```

**新代码**：
```python
from utils.export_cf import export_resumes_to_csv
csv_data = export_resumes_to_csv([resume])
return Response(csv_data, headers={
    'Content-Type': 'text/csv; charset=utf-8',
    'Content-Disposition': 'attachment; filename="resumes.csv"'
})
```

### AI调用

**原代码**：
```python
from utils.ai_extractor import AIExtractor
extractor = AIExtractor(api_key="...")
result = extractor.extract_with_ai(text)  # 同步调用
```

**新代码**：
```python
from utils.ai_extractor_cf import AIExtractor
extractor = AIExtractor(api_key="...")
result = await extractor.extract_with_ai(text, fetch_func=fetch)  # 异步调用
```

## ✅ 最终依赖清单

**cf-requirements.txt** 已更新为：

```
# Cloudflare Workers Python 依赖
# 只包含纯Python库，无C扩展

# 注意：Workers Python运行时已经内置了大部分标准库
# 可能不需要额外的依赖

# 如果pymupdf在Workers中可用，可以添加：
# pymupdf==1.23.8
```

## 🧪 测试建议

1. **本地测试**：
   ```bash
   wrangler dev
   ```

2. **测试Word解析**：
   - 测试各种.docx文件格式
   - 验证表格、页眉页脚提取

3. **测试CSV导出**：
   - 在Excel中打开CSV，验证中文显示
   - 验证数据完整性

4. **测试AI调用**：
   - 测试各种AI服务（OpenAI、DeepSeek等）
   - 验证异步调用性能

5. **测试PDF处理**：
   - 如果pymupdf不可用，测试AI API处理PDF
   - 验证PDF文本提取准确性

## 📌 关键注意事项

1. **所有新代码都使用异步API**（async/await）
2. **文件操作使用bytes而不是文件路径**
3. **使用Workers原生fetch API替代requests**
4. **CSV格式替代Excel，功能足够但格式简单**
5. **PDF处理建议使用AI API或外部服务**

## 🎯 总结

✅ **已完成**：
- Word文档解析（纯Python）
- CSV导出（替代Excel）
- AI调用（使用fetch API）

⚠️ **待处理**：
- PDF文本提取（建议使用AI API）
- PDF生成（建议客户端生成）

📦 **依赖清理**：
- 移除了所有不兼容的库
- 只保留必要的标准库
- Workers环境可能无需额外依赖





