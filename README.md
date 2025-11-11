# 智能简历数据库系统

基于网页的智能简历信息提取与管理平台，支持PDF和Word文档的自动解析、关键信息提取、外部API验证和数据导出功能。

## 功能特性

- ✅ 支持PDF（文本/图片）和Word文档上传
- ✅ 自动提取关键信息（姓名、性别、年龄、学历、学校、专业等）
- ✅ 集成外部API验证（企查查、学校名录、专业名录）
- ✅ 数据展示、搜索、筛选和排序
- ✅ 支持简历记录的查看、编辑与删除（含批量删除）
- ✅ 单个和批量数据导出（Excel格式）
- ✅ 现代化的Web界面

## 技术栈

- **后端**: Python Flask
- **数据库**: SQLite
- **文件解析**: PyPDF2, python-docx, pytesseract (OCR)
- **数据导出**: openpyxl
- **前端**: HTML5, CSS3, JavaScript (原生)

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装OCR依赖（可选，用于图片PDF识别）

**Windows:**
- 下载并安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- 安装时选择中文语言包

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

### 3. 配置外部API（可选）

编辑 `config.py` 文件，填入实际的API密钥和URL：

```python
QICHACHA_API_KEY = 'your_api_key'
SCHOOL_API_URL = 'your_school_api_url'
MAJOR_API_URL = 'your_major_api_url'
```

如果没有配置API，系统仍可正常运行，但不会进行公司/学校/专业的标准化验证。

## 运行系统

```bash
python app.py
```

系统将在 `http://localhost:5000` 启动。

## 使用说明

### 上传简历

1. 点击上传区域或拖拽文件到上传区域
2. 支持的文件格式：`.pdf`, `.doc`, `.docx`
3. 文件大小限制：10MB
4. 上传后系统会自动解析简历内容

### 查看和管理简历

- **搜索**: 在搜索框输入姓名、学校或专业进行搜索
- **筛选**: 使用性别、学历下拉菜单进行筛选
- **排序**: 点击表头进行升序/降序排序
- **查看详情**: 点击"查看"按钮查看完整的简历信息

### 导出数据

- **单个导出**: 在详情页面点击"下载此简历"按钮
- **批量导出**: 勾选多个简历后点击"导出选中"
- **全部导出**: 点击"导出全部"按钮

## 项目结构

```
简历上传/
├── app.py                 # Flask主应用
├── config.py              # 配置文件
├── models.py              # 数据模型
├── requirements.txt       # Python依赖
├── README.md             # 说明文档
├── utils/                # 工具函数
│   ├── file_parser.py    # 文件解析
│   ├── info_extractor.py # 信息提取
│   ├── api_integration.py # API集成
│   └── export.py         # 数据导出
├── templates/            # HTML模板
│   └── index.html
├── static/               # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/              # 上传文件存储
├── exports/              # 导出文件存储
└── database.db           # SQLite数据库（自动生成）
```

## API接口说明

### 上传简历
- **POST** `/api/upload`
- 参数: `file` (文件)

### 获取简历列表
- **GET** `/api/resumes`
- 参数: `page`, `per_page`, `search`, `gender`, `education`, `sort_by`, `sort_order`

### 获取简历详情
- **GET** `/api/resumes/<id>`

### 更新简历信息
- **PUT** `/api/resumes/<id>`
- Body: JSON格式的简历数据

### 导出单个简历
- **GET** `/api/export/<id>`

### 批量导出
- **POST** `/api/export/batch`
- Body: `{"resume_ids": [1, 2, 3]}`

## 注意事项

1. **OCR功能**: 如果系统检测到图片PDF，会自动使用OCR识别。首次使用可能需要下载语言包。

2. **API限制**: 外部API调用可能有限制，建议配置实际的API密钥以获得最佳体验。

3. **数据存储**: 系统使用SQLite数据库，所有数据存储在本地 `database.db` 文件中。

4. **文件存储**: 上传的文件存储在 `uploads/` 目录，导出文件存储在 `exports/` 目录。

## 开发说明

### 扩展信息提取规则

编辑 `utils/info_extractor.py` 文件，可以自定义信息提取规则。

### 添加新的API集成

编辑 `utils/api_integration.py` 文件，添加新的API验证方法。

### 自定义导出格式

编辑 `utils/export.py` 文件，可以修改导出的Excel格式和字段。

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。

