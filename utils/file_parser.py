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

def extract_text_from_pdf_with_ocr(file_path):
    """
    使用OCR从PDF中提取文本（适用于图片PDF）
    """
    ocr_text = ""
    
    try:
        # 首先尝试使用pdf2image将PDF转换为图片
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=200)
        except ImportError:
            # 如果pdf2image不可用，尝试使用PyMuPDF
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(file_path)
                images = []
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放
                    from PIL import Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
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
                    result = OCR_ENGINE.readtext(image)
                    if result:
                        page_text = '\n'.join([item[1] for item in result])
                        ocr_text += page_text + "\n"
                        
            except Exception as e:
                print(f"OCR处理第{idx+1}页失败: {e}")
                continue
                
    except Exception as e:
        print(f"OCR处理失败: {e}")
        return ""
    
    return ocr_text.strip()

def extract_text_from_pdf(file_path):
    """
    从PDF文件提取文本
    支持文本PDF和图片PDF（OCR）
    """
    text = ""
    
    try:
        # 首先尝试直接提取文本
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text and isinstance(page_text, str) and page_text.strip():
                    text += page_text + "\n"
        
        # 如果提取的文本太少（少于100字符），可能是图片PDF，使用OCR（如果可用）
        text_stripped = text.strip()
        if len(text_stripped) < 100 and OCR_AVAILABLE and OCR_ENGINE:
            try:
                ocr_text = extract_text_from_pdf_with_ocr(file_path)
                if ocr_text and len(ocr_text.strip()) > len(text_stripped):
                    text = ocr_text
                    print(f"使用OCR成功提取文本，长度: {len(text)} 字符")
                elif not text_stripped and ocr_text:
                    # 如果直接提取没有文本，即使OCR文本较短也使用
                    text = ocr_text
                    print(f"使用OCR提取文本（直接提取无文本），长度: {len(text)} 字符")
            except Exception as e:
                print(f"OCR处理失败: {e}")
                # 如果OCR失败，返回已提取的文本（如果有）
        
    except Exception as e:
        raise Exception(f"PDF解析失败: {str(e)}")
    
    return text if text else ""

def extract_text_from_word(file_path):
    """
    从Word文档提取文本
    """
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Word文档解析失败: {str(e)}")

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

