# OCR功能安装说明

## 概述

本系统已升级OCR功能，使用 **PaddleOCR** 或 **EasyOCR** 替代原来的 Tesseract OCR。新方案具有以下优势：

- ✅ **无需安装系统级软件**（如Tesseract）
- ✅ **中文识别准确率更高**
- ✅ **安装简单，只需pip安装**
- ✅ **支持中英文混合识别**

## 安装步骤

### 方案一：使用 PaddleOCR（推荐）

PaddleOCR 对中文识别准确率最高，推荐使用。

```bash
# 安装 PaddlePaddle（CPU版本）
pip install paddlepaddle

# 安装 PaddleOCR
pip install paddleocr
```

**注意**：首次运行时会自动下载模型文件（约100MB），请确保网络畅通。

### 方案二：使用 EasyOCR（备选）

如果 PaddleOCR 安装失败，可以使用 EasyOCR 作为备选：

```bash
pip install easyocr
```

**注意**：首次运行时会自动下载模型文件（约500MB），请确保网络畅通。

### PDF转图片依赖

OCR需要先将PDF转换为图片。系统已包含 PyMuPDF（无需额外依赖），但也可以使用 pdf2image：

#### 使用 PyMuPDF（推荐，已包含在requirements.txt中）

无需额外安装，系统已自动使用。

#### 使用 pdf2image（可选）

如果需要使用 pdf2image，需要安装 poppler：

**Windows:**
1. 下载 poppler: https://github.com/oschwartz10612/poppler-windows/releases
2. 解压并添加到系统PATH环境变量
3. 安装Python包: `pip install pdf2image`

**Linux:**
```bash
sudo apt-get install poppler-utils
pip install pdf2image
```

**macOS:**
```bash
brew install poppler
pip install pdf2image
```

## 配置说明

在 `config.py` 中可以配置OCR相关选项：

```python
# OCR配置
OCR_ENABLED = True  # 是否启用OCR
OCR_ENGINE = 'paddleocr'  # 可选: 'paddleocr' 或 'easyocr'
OCR_USE_GPU = False  # 是否使用GPU加速（需要安装GPU版本的PaddlePaddle）
```

也可以通过环境变量配置：

```bash
export OCR_ENABLED=true
export OCR_ENGINE=paddleocr
export OCR_USE_GPU=false
```

## 使用说明

1. **自动检测**：系统会自动检测PDF是否为图片格式
2. **自动切换**：如果直接提取文本失败或文本过少（<100字符），会自动使用OCR
3. **无需手动操作**：OCR功能完全自动化，用户无需干预

## 常见问题

### Q1: OCR识别速度慢？

**A:** 首次运行需要下载模型，之后会快很多。如果仍然慢，可以：
- 使用GPU加速（需要安装GPU版本的PaddlePaddle）
- 减少PDF页数
- 降低图片分辨率（修改 `dpi=200` 参数）

### Q2: 识别准确率不高？

**A:** 可以尝试：
- 使用 PaddleOCR（中文识别更准确）
- 确保PDF图片清晰
- 检查PDF是否倾斜（PaddleOCR支持自动矫正）

### Q3: 不想使用OCR功能？

**A:** 在 `config.py` 中设置 `OCR_ENABLED = False`，系统将跳过OCR处理。

### Q4: 安装失败？

**A:** 
- 检查Python版本（建议3.7+）
- 确保pip已更新：`pip install --upgrade pip`
- 如果网络问题，可以使用国内镜像：
  ```bash
  pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

## 性能对比

| OCR引擎 | 中文准确率 | 英文准确率 | 速度 | 模型大小 | 系统依赖 |
|---------|-----------|-----------|------|---------|---------|
| PaddleOCR | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~100MB | 无 |
| EasyOCR | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~500MB | 无 |
| Tesseract | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~50MB | 需要安装 |

## 更新日志

- **2024-11**: 升级OCR功能，使用PaddleOCR/EasyOCR替代Tesseract
- 改进PDF转图片逻辑，支持PyMuPDF和pdf2image两种方案
- 添加OCR配置选项，支持灵活配置

