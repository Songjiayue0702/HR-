"""
文件解析工具
支持PDF和Word文档的文本提取
"""
import os
import PyPDF2
from docx import Document

# OCR功能（可选）
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("警告: OCR功能不可用，图片PDF可能无法正确解析")

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
                if page_text.strip():
                    text += page_text + "\n"
        
        # 如果提取的文本太少，可能是图片PDF，使用OCR（如果可用）
        if len(text.strip()) < 100 and OCR_AVAILABLE:
            try:
                images = convert_from_path(file_path, dpi=200)
                ocr_text = ""
                for image in images:
                    ocr_text += pytesseract.image_to_string(image, lang='chi_sim+eng') + "\n"
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
            except Exception as e:
                print(f"OCR处理失败: {e}")
                # 如果OCR失败，返回已提取的文本
        
    except Exception as e:
        raise Exception(f"PDF解析失败: {str(e)}")
    
    return text

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

