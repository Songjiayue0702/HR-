"""
文件解析工具
支持PDF和Word文档的文本提取
"""
import os
import PyPDF2
from docx import Document

# OCR功能（可选）- 使用PaddleOCR替代Tesseract
OCR_AVAILABLE = False
OCR_ENGINE = None

def init_ocr_engine(ocr_enabled=True, engine='paddleocr', use_gpu=False):
    """
    初始化OCR引擎
    
    Args:
        ocr_enabled: 是否启用OCR
        engine: OCR引擎类型 ('paddleocr' 或 'easyocr')
        use_gpu: 是否使用GPU加速
    """
    global OCR_AVAILABLE, OCR_ENGINE
    
    if not ocr_enabled:
        OCR_AVAILABLE = False
        OCR_ENGINE = None
        return
    
    if engine.lower() == 'paddleocr':
        try:
            from paddleocr import PaddleOCR
            OCR_AVAILABLE = True
            try:
                OCR_ENGINE = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=use_gpu)
                print("PaddleOCR初始化成功")
            except Exception as e:
                print(f"PaddleOCR初始化失败: {e}")
                OCR_AVAILABLE = False
                OCR_ENGINE = None
        except ImportError:
            print("警告: PaddleOCR未安装，尝试使用EasyOCR作为备选")
            # 如果PaddleOCR不可用，尝试使用EasyOCR作为备选
            try:
                import easyocr
                OCR_AVAILABLE = True
                try:
                    OCR_ENGINE = easyocr.Reader(['ch_sim', 'en'], gpu=use_gpu)
                    print("EasyOCR初始化成功（作为PaddleOCR的备选）")
                except Exception as e:
                    print(f"EasyOCR初始化失败: {e}")
                    OCR_AVAILABLE = False
                    OCR_ENGINE = None
            except ImportError:
                OCR_AVAILABLE = False
                OCR_ENGINE = None
                print("警告: OCR功能不可用，图片PDF可能无法正确解析。请安装 paddleocr 或 easyocr")
    elif engine.lower() == 'easyocr':
        try:
            import easyocr
            OCR_AVAILABLE = True
            try:
                OCR_ENGINE = easyocr.Reader(['ch_sim', 'en'], gpu=use_gpu)
                print("EasyOCR初始化成功")
            except Exception as e:
                print(f"EasyOCR初始化失败: {e}")
                OCR_AVAILABLE = False
                OCR_ENGINE = None
        except ImportError:
            OCR_AVAILABLE = False
            OCR_ENGINE = None
            print("警告: EasyOCR未安装，请运行: pip install easyocr")

# 延迟初始化，等待配置加载
# 在实际使用时，会通过 app.py 调用 init_ocr_engine

def clean_ocr_text(text):
    """
    清理OCR识别结果中的常见错误
    """
    if not text:
        return text
    
    # 移除常见的OCR错误字符
    # 替换常见的OCR识别错误
    replacements = {
        '0': 'O',  # 数字0误识别为字母O（在特定上下文中）
        '1': 'I',  # 数字1误识别为字母I（在特定上下文中）
        '□': '',   # 移除无法识别的字符标记
        '': '',   # 移除编码错误标记
    }
    
    # 清理连续的特殊字符
    import re
    # 移除连续的空白字符，保留单个空格或换行
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 移除行首行尾的空白
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    text = '\n'.join(cleaned_lines)
    
    return text

def extract_text_from_pdf_with_ocr(file_path):
    """
    使用OCR从PDF中提取文本（适用于图片PDF）
    """
    ocr_text = ""
    
    try:
        # 首先尝试使用pdf2image将PDF转换为图片
        try:
            from pdf2image import convert_from_path
            # 提高DPI以提高识别准确率
            images = convert_from_path(file_path, dpi=300)
        except ImportError:
            # 如果pdf2image不可用，尝试使用PyMuPDF
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(file_path)
                images = []
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    # 提高缩放比例以提高识别准确率（3x缩放）
                    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                    from PIL import Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # 图像预处理：增强对比度和清晰度
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)  # 增强对比度20%
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.1)  # 增强锐度10%
                    
                    images.append(img)
                pdf_doc.close()
            except ImportError:
                print("警告: 无法将PDF转换为图片，需要安装 pdf2image 或 PyMuPDF")
                return ""
        
        # 使用OCR识别每页图片
        for idx, image in enumerate(images):
            try:
                if OCR_ENGINE is None:
                    continue
                    
                # 判断OCR引擎类型
                if hasattr(OCR_ENGINE, 'ocr'):  # PaddleOCR
                    result = OCR_ENGINE.ocr(image, cls=True)
                    if result and result[0]:
                        page_text = '\n'.join([line[1][0] for line in result[0] if line])
                        ocr_text += page_text + "\n"
                elif hasattr(OCR_ENGINE, 'readtext'):  # EasyOCR
                    # EasyOCR需要numpy数组，转换PIL Image
                    import numpy as np
                    if hasattr(image, 'mode') and image.mode != 'RGB':
                        image = image.convert('RGB')
                    img_array = np.array(image)
                    
                    # EasyOCR参数优化：提高识别准确率
                    # 使用detail=1获取置信度，过滤低置信度结果
                    result = OCR_ENGINE.readtext(
                        img_array,
                        detail=1,  # 返回位置和置信度信息
                        paragraph=False,  # 不使用段落模式，提高准确率
                        width_ths=0.4,  # 降低字符宽度阈值，识别更多字符
                        height_ths=0.4,  # 降低字符高度阈值
                        allowlist=None,  # 允许所有字符
                        blocklist=''  # 不屏蔽任何字符
                    )
                    # 过滤低置信度的结果，但保留更多结果以提高召回率
                    if result:
                        # 对于置信度 > 0.5 的结果，直接使用
                        # 对于置信度 0.3-0.5 的结果，如果包含中文字符也使用
                        import re
                        filtered_result = []
                        for item in result:
                            if len(item) >= 3:
                                confidence = item[2]
                                text_item = item[1]
                                # 高置信度直接使用
                                if confidence > 0.5:
                                    filtered_result.append(text_item)
                                # 中等置信度但包含中文字符也使用
                                elif confidence > 0.25 and re.search(r'[\u4e00-\u9fa5]', text_item):
                                    filtered_result.append(text_item)
                            elif len(item) >= 2:
                                # 如果没有置信度信息，直接使用
                                filtered_result.append(item[1])
                        
                        if filtered_result:
                            result = filtered_result
                        else:
                            # 如果过滤后没有结果，使用所有结果
                            result = [item[1] if len(item) >= 2 else str(item) for item in result]
                    if result:
                        page_text = '\n'.join(result) if isinstance(result, list) else str(result)
                        ocr_text += page_text + "\n"
                        
            except Exception as e:
                print(f"OCR处理第{idx+1}页失败: {e}")
                continue
        
        # 清理OCR文本
        ocr_text = clean_ocr_text(ocr_text)
                
    except Exception as e:
        print(f"OCR处理失败: {e}")
        return ""
    
    return ocr_text.strip()

def extract_text_from_pdf(file_path):
    """
    从PDF文件提取文本
    支持文本PDF和图片PDF（OCR）
    
    策略：
    1. 文本PDF：直接使用PyPDF2提取，完全按照OCR更新前的逻辑（不进行任何OCR判断）
    2. 图片PDF：使用OCR识别
    """
    text = ""
    
    try:
        # 首先尝试直接提取文本（OCR更新前的逻辑）
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text and isinstance(page_text, str) and page_text.strip():
                    text += page_text + "\n"
        
        text_stripped = text.strip()
        
        # 判断是否为文本PDF的标准（OCR更新前的判断逻辑）
        # 1. 文本长度 >= 200字符
        # 2. 中文字符数量 >= 50个
        # 3. 中文字符占比 >= 10%
        # 4. 不是编码字符串（唯一字符数 >= 50）
        import re
        is_text_pdf = False
        if text_stripped:
            total_chars = len(text_stripped)
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text_stripped))
            unique_chars = len(set(text_stripped))
            chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
            
            # 判断是否为文本PDF
            if total_chars >= 200 and chinese_chars >= 50 and chinese_ratio >= 0.1 and unique_chars >= 50:
                is_text_pdf = True
                # 文本PDF：直接返回，不进行任何OCR相关处理（OCR更新前的逻辑）
                return text_stripped
        
        # 如果不是文本PDF，检查是否为编码字符串
        is_encoded_string = False
        if text_stripped:
            unique_chars = len(set(text_stripped))
            # 如果唯一字符少于50个，且文本长度大于100，可能是编码字符串
            if unique_chars < 50 and len(text_stripped) > 100:
                is_encoded_string = True
                print(f"检测到编码字符串（唯一字符: {unique_chars}），尝试使用OCR")
        
        # 对于图片PDF（文本太少或编码字符串），使用OCR
        if (len(text_stripped) < 200 or is_encoded_string) and OCR_AVAILABLE and OCR_ENGINE:
            try:
                ocr_text = extract_text_from_pdf_with_ocr(file_path)
                if ocr_text:
                    # 检查OCR文本质量
                    ocr_chinese = len(re.findall(r'[\u4e00-\u9fa5]', ocr_text))
                    ocr_has_content = ocr_chinese >= 20 or \
                                      bool(re.search(r'(姓名|性别|年龄|手机|邮箱|学校|专业|工作|教育)', ocr_text))
                    
                    if is_encoded_string:
                        # 如果是编码字符串，只要OCR有内容就使用
                        if ocr_has_content:
                            text = ocr_text
                            print(f"使用OCR替换编码字符串，OCR文本长度: {len(text)} 字符，中文字符: {ocr_chinese}")
                    elif not text_stripped:
                        # 如果直接提取没有文本，使用OCR结果
                        if ocr_has_content:
                            text = ocr_text
                            print(f"使用OCR提取文本（直接提取无文本），长度: {len(text)} 字符，中文字符: {ocr_chinese}")
                    else:
                        # 如果直接提取有少量文本，比较质量
                        direct_chinese = len(re.findall(r'[\u4e00-\u9fa5]', text_stripped))
                        if ocr_chinese > direct_chinese * 1.5:  # OCR中文字符数明显更多
                            text = ocr_text
                            print(f"使用OCR提取文本（OCR质量更好），OCR中文字符: {ocr_chinese} vs 直接提取: {direct_chinese}")
            except Exception as e:
                print(f"OCR处理失败: {e}")
                # 如果OCR失败，返回已提取的文本（如果有）
        
    except Exception as e:
        raise Exception(f"PDF解析失败: {str(e)}")
    
    return text if text else ""

def extract_text_from_word(file_path):
    """
    从Word文档提取文本
    支持 .docx 格式，提取段落和表格中的内容
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise Exception(f"文件不存在: {file_path}")
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.doc':
        raise Exception("不支持旧的 .doc 格式，请将文件转换为 .docx 格式后再上传")
    
    try:
        # 使用绝对路径，避免路径问题
        abs_path = os.path.abspath(file_path)
        doc = Document(abs_path)
        text = ""
        
        # 提取段落文本
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        # 提取表格中的文本
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    text += " | ".join(row_text) + "\n"
        
        # 如果没有提取到任何文本，可能是文件格式问题
        if not text.strip():
            raise Exception("无法从Word文档中提取文本，文件可能已损坏或格式不正确（可能是加密的文档）")
        
        return text.strip()
    except Exception as e:
        error_msg = str(e)
        # 提供更友好的错误提示
        if "cannot open" in error_msg.lower() or "permission" in error_msg.lower():
            raise Exception(f"无法打开文件，请检查文件是否被其他程序占用或没有读取权限: {error_msg}")
        elif "not a zip file" in error_msg.lower() or "bad zipfile" in error_msg.lower():
            raise Exception(f"文件格式错误，.docx 文件应该是有效的 ZIP 格式。请确认文件是否损坏: {error_msg}")
        else:
            raise Exception(f"Word文档解析失败: {error_msg}")

def extract_text(file_path):
    """
    根据文件类型自动选择解析方法
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.doc', '.docx']:
        return extract_text_from_word(file_path)
    else:
        raise Exception(f"不支持的文件格式: {file_ext}")

