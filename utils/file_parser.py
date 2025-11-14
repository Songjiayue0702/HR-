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
    保持文本结构和上下文位置信息
    """
    if not text:
        return text
    
    import re
    
    # 保留页面分隔标记（如果存在）
    page_markers = []
    if '--- 第' in text and '页 ---' in text:
        # 提取并保留页面标记
        page_marker_pattern = r'--- 第\d+页 ---'
        page_markers = re.findall(page_marker_pattern, text)
        # 临时替换页面标记，避免被清理
        for i, marker in enumerate(page_markers):
            text = text.replace(marker, f'__PAGE_MARKER_{i}__', 1)
    
    # 修复常见的OCR识别错误（但保留上下文）
    # 修复年份中的O应该是0（如"2O25" -> "2025"）
    text = re.sub(r'([12])O(\d{3})', r'\g<1>0\2', text)  # 修复年份中的O -> 0
    text = re.sub(r'(\d{4})\.O(\d)', r'\1.0\2', text)  # 修复月份中的O -> 0
    
    # 修复邮箱中的常见OCR错误（如"@4q.com"应该是"@qq.com"）
    text = re.sub(r'@4q\.com', '@qq.com', text, flags=re.IGNORECASE)
    text = re.sub(r'@(\d+)q\.com', r'@qq.com', text, flags=re.IGNORECASE)
    
    # 移除无法识别的字符标记，但保留必要的标点
    text = re.sub(r'[□¡¿\u200b\u200c\u200d\ufeff]', '', text)  # 移除OCR无法识别的字符标记和零宽字符
    
    # 清理连续的特殊字符，但保留换行结构
    text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符合并为单个空格
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # 超过3个换行符的合并为3个（保留段落分隔）
    
    # 移除行首行尾的空白，但保留空行（用于段落分隔）
    lines = text.split('\n')
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        line_stripped = line.strip()
        if line_stripped:
            cleaned_lines.append(line_stripped)
            prev_empty = False
        elif not prev_empty:
            # 保留单个空行作为段落分隔
            cleaned_lines.append('')
            prev_empty = True
    
    text = '\n'.join(cleaned_lines)
    
    # 恢复页面标记
    if page_markers:
        for i, marker in enumerate(page_markers):
            text = text.replace(f'__PAGE_MARKER_{i}__', marker, 1)
    
    return text

def extract_text_from_pdf_with_ocr(file_path):
    """
    使用OCR从PDF中提取文本（适用于图片PDF）
    保持页面顺序和位置信息
    """
    ocr_text_pages = []  # 存储每页OCR结果，保持页面顺序
    
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
        
        total_pages = len(images)
        
        # 使用OCR识别每页图片（保持页面顺序）
        for idx, image in enumerate(images):
            try:
                if OCR_ENGINE is None:
                    continue
                
                page_num = idx + 1
                page_text = ""
                    
                # 判断OCR引擎类型
                if hasattr(OCR_ENGINE, 'ocr'):  # PaddleOCR
                    result = OCR_ENGINE.ocr(image, cls=True)
                    if result and result[0]:
                        # PaddleOCR返回的结果包含位置信息
                        # 提取X和Y坐标，按从上到下、从左到右排序
                        items_with_pos = []
                        for line in result[0]:
                            if line and len(line) >= 2:
                                text_content = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                                # 获取位置信息（边界框的四个点）
                                if len(line) >= 2 and isinstance(line[0], (list, tuple)) and len(line[0]) >= 4:
                                    # line[0] 是位置信息，包含4个点 [左上, 右上, 右下, 左下]
                                    bbox = line[0]
                                    # 计算左上角坐标（X, Y）
                                    x_pos = bbox[0][0] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    y_pos = bbox[0][1] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    # 计算行高（用于判断是否在同一行）
                                    if len(bbox) >= 2 and isinstance(bbox[1], (list, tuple)):
                                        height = abs(bbox[1][1] - bbox[0][1]) if len(bbox[1]) >= 2 else 0
                                    else:
                                        height = 0
                                    items_with_pos.append((y_pos, x_pos, height, text_content))
                                else:
                                    items_with_pos.append((0, 0, 0, text_content))
                        
                        # 按位置排序：先按Y坐标（从上到下），然后按X坐标（从左到右）
                        # 对于Y坐标相近的文本（在同一行），按X坐标排序
                        if items_with_pos:
                            # 计算平均行高，用于判断是否在同一行
                            heights = [item[2] for item in items_with_pos if item[2] > 0]
                            avg_height = sum(heights) / len(heights) if heights else 20
                            line_tolerance = avg_height * 0.5  # 行高容差：同一行的Y坐标差异不超过平均行高的50%
                            
                            # 先按Y坐标排序
                            items_with_pos.sort(key=lambda x: x[0])
                            
                            # 对于Y坐标相近的文本（在同一行），按X坐标排序
                            sorted_items = []
                            current_line = []
                            current_y = None
                            
                            for y, x, h, text in items_with_pos:
                                if current_y is None or abs(y - current_y) <= line_tolerance:
                                    # 同一行或第一行
                                    current_line.append((y, x, h, text))
                                    current_y = y if current_y is None else (current_y + y) / 2  # 更新当前行的平均Y坐标
                                else:
                                    # 新的一行，先对上一行按X坐标排序
                                    current_line.sort(key=lambda x: x[1])  # 按X坐标排序
                                    sorted_items.extend([item[3] for item in current_line])
                                    # 开始新行
                                    current_line = [(y, x, h, text)]
                                    current_y = y
                            
                            # 处理最后一行
                            if current_line:
                                current_line.sort(key=lambda x: x[1])  # 按X坐标排序
                                sorted_items.extend([item[3] for item in current_line])
                            
                            page_text = '\n'.join([text for text in sorted_items if text.strip()])
                        else:
                            page_text = ""
                elif hasattr(OCR_ENGINE, 'readtext'):  # EasyOCR
                    # EasyOCR需要numpy数组，转换PIL Image
                    import numpy as np
                    if hasattr(image, 'mode') and image.mode != 'RGB':
                        image = image.convert('RGB')
                    img_array = np.array(image)
                    
                    # EasyOCR参数优化：提高识别准确率
                    # 使用detail=1获取置信度和位置信息
                    result = OCR_ENGINE.readtext(
                        img_array,
                        detail=1,  # 返回位置和置信度信息
                        paragraph=False,  # 不使用段落模式，保持行结构
                        width_ths=0.4,  # 降低字符宽度阈值，识别更多字符
                        height_ths=0.4,  # 降低字符高度阈值
                        allowlist=None,  # 允许所有字符
                        blocklist=''  # 不屏蔽任何字符
                    )
                    # 过滤低置信度的结果，但保留更多结果以提高召回率
                    # 同时保持位置信息以维护上下文顺序（从上到下，从左到右）
                    if result:
                        import re
                        # 存储文本和位置信息（Y坐标，X坐标，行高，文本，置信度）
                        text_items_with_pos = []
                        for item in result:
                            if len(item) >= 3:
                                confidence = item[2]
                                text_item = item[1]
                                # 获取位置信息（边界框）
                                bbox = item[0] if len(item) >= 1 else None
                                if bbox and isinstance(bbox, list) and len(bbox) >= 4:
                                    # bbox格式：[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                                    # 计算左上角坐标
                                    x_pos = bbox[0][0] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    y_pos = bbox[0][1] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    # 计算行高
                                    if len(bbox) >= 2 and isinstance(bbox[1], (list, tuple)) and len(bbox[1]) >= 2:
                                        height = abs(bbox[1][1] - bbox[0][1])
                                    else:
                                        height = 0
                                    
                                    # 高置信度直接使用
                                    if confidence > 0.5:
                                        text_items_with_pos.append((y_pos, x_pos, height, text_item, confidence))
                                    # 中等置信度但包含中文字符也使用
                                    elif confidence > 0.25 and re.search(r'[\u4e00-\u9fa5]', text_item):
                                        text_items_with_pos.append((y_pos, x_pos, height, text_item, confidence))
                            elif len(item) >= 2:
                                # 如果没有置信度信息，直接使用
                                bbox = item[0] if len(item) >= 1 else None
                                if bbox and isinstance(bbox, list) and len(bbox) >= 4:
                                    x_pos = bbox[0][0] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    y_pos = bbox[0][1] if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) >= 2 else 0
                                    height = abs(bbox[1][1] - bbox[0][1]) if len(bbox) >= 2 and isinstance(bbox[1], (list, tuple)) and len(bbox[1]) >= 2 else 0
                                    text_items_with_pos.append((y_pos, x_pos, height, item[1], 1.0))
                                else:
                                    text_items_with_pos.append((0, 0, 0, item[1], 1.0))
                        
                        if text_items_with_pos:
                            # 计算平均行高，用于判断是否在同一行
                            heights = [item[2] for item in text_items_with_pos if item[2] > 0]
                            avg_height = sum(heights) / len(heights) if heights else 20
                            line_tolerance = avg_height * 0.5  # 行高容差：同一行的Y坐标差异不超过平均行高的50%
                            
                            # 先按Y坐标排序（从上到下）
                            text_items_with_pos.sort(key=lambda x: x[0])
                            
                            # 对于Y坐标相近的文本（在同一行），按X坐标排序（从左到右）
                            sorted_items = []
                            current_line = []
                            current_y = None
                            
                            for y, x, h, text, conf in text_items_with_pos:
                                if current_y is None or abs(y - current_y) <= line_tolerance:
                                    # 同一行或第一行
                                    current_line.append((y, x, h, text, conf))
                                    current_y = y if current_y is None else (current_y + y) / 2  # 更新当前行的平均Y坐标
                                else:
                                    # 新的一行，先对上一行按X坐标排序
                                    current_line.sort(key=lambda x: x[1])  # 按X坐标排序
                                    sorted_items.extend([item[3] for item in current_line])
                                    # 开始新行
                                    current_line = [(y, x, h, text, conf)]
                                    current_y = y
                            
                            # 处理最后一行
                            if current_line:
                                current_line.sort(key=lambda x: x[1])  # 按X坐标排序
                                sorted_items.extend([item[3] for item in current_line])
                            
                            page_text = '\n'.join([text for text in sorted_items if text.strip()])
                        else:
                            # 如果过滤后没有结果，使用所有结果
                            page_text = '\n'.join([item[1] if len(item) >= 2 else str(item) for item in result])
                    elif result:
                        page_text = '\n'.join(result) if isinstance(result, list) else str(result)
                    else:
                        page_text = ""
                
                # 如果提取到页面文本，添加到结果中
                if page_text and page_text.strip():
                    # 保持页面分隔，便于后续解析时识别上下文位置
                    if total_pages > 1:
                        ocr_text_pages.append(f"--- 第{page_num}页 ---\n{page_text.strip()}")
                    else:
                        ocr_text_pages.append(page_text.strip())
                        
            except Exception as e:
                print(f"OCR处理第{idx+1}页失败: {e}")
                continue
        
        # 合并所有页面文本，保持页面顺序
        ocr_text = "\n\n".join(ocr_text_pages)
        
        # 清理OCR文本（但保持基本结构）
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
    1. 文本PDF：直接使用PyPDF2提取，保持页面顺序和结构
    2. 图片PDF：使用OCR识别，保持位置信息
    """
    text = ""
    page_texts = []  # 存储每页文本，保持页面顺序
    
    try:
        # 首先尝试直接提取文本（保持页面顺序和结构）
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text and isinstance(page_text, str):
                    # 清理每页文本，但保持基本结构
                    page_text_cleaned = page_text.strip()
                    if page_text_cleaned:
                        # 保持页面分隔，便于后续解析时识别上下文位置
                        # 在页面之间添加明确的分隔符（仅在多页时）
                        if total_pages > 1:
                            page_texts.append(f"--- 第{page_num}页 ---\n{page_text_cleaned}")
                        else:
                            page_texts.append(page_text_cleaned)
            
            # 合并所有页面文本，保持顺序
            text = "\n\n".join(page_texts)
        
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
        
        # 提取段落文本（保持原有顺序和结构）
        paragraph_count = 0
        for paragraph in doc.paragraphs:
            para_text = paragraph.text.strip()
            if para_text:
                text += para_text + "\n"
                paragraph_count += 1
        
        # 提取表格中的文本（保持表格结构，便于后续解析）
        table_count = 0
        for table in doc.tables:
            table_count += 1
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    # 使用空格分隔，保持表格内容的可读性
                    text += " ".join(row_text) + "\n"
        
        # 尝试提取页眉和页脚（可能包含重要信息）
        try:
            for section in doc.sections:
                # 提取页眉
                if section.header:
                    for paragraph in section.header.paragraphs:
                        header_text = paragraph.text.strip()
                        if header_text and len(header_text) > 1:
                            # 页眉信息放在文本开头
                            text = header_text + "\n" + text
                # 提取页脚
                if section.footer:
                    for paragraph in section.footer.paragraphs:
                        footer_text = paragraph.text.strip()
                        if footer_text and len(footer_text) > 1:
                            # 页脚信息放在文本末尾
                            text += "\n" + footer_text
        except Exception as e:
            # 页眉页脚提取失败不影响主流程
            pass
        
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
