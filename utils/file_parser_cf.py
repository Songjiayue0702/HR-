"""
文件解析工具 - Cloudflare Workers版本
纯Python实现，不依赖C扩展
"""
import re
import zipfile
import io
import xml.etree.ElementTree as ET


def clean_text(text):
    """
    清理文本中的常见错误
    保持文本结构和上下文位置信息
    """
    if not text:
        return text
    
    # 保留页面分隔标记（如果存在）
    page_markers = []
    if '--- 第' in text and '页 ---' in text:
        # 提取并保留页面标记
        page_marker_pattern = r'--- 第\d+页 ---'
        page_markers = re.findall(page_marker_pattern, text)
        # 临时替换页面标记，避免被清理
        for i, marker in enumerate(page_markers):
            text = text.replace(marker, f'__PAGE_MARKER_{i}__', 1)
    
    # 修复常见的文本识别错误
    # 修复年份中的O应该是0（如"2O25" -> "2025"）
    text = re.sub(r'([12])O(\d{3})', r'\g<1>0\2', text)  # 修复年份中的O -> 0
    text = re.sub(r'(\d{4})\.O(\d)', r'\1.0\2', text)  # 修复月份中的O -> 0
    
    # 修复邮箱中的常见错误（如"@4q.com"应该是"@qq.com"）
    text = re.sub(r'@4q\.com', '@qq.com', text, flags=re.IGNORECASE)
    text = re.sub(r'@(\d+)q\.com', r'@qq.com', text, flags=re.IGNORECASE)
    
    # 移除无法识别的字符标记，但保留必要的标点
    text = re.sub(r'[□¡¿\u200b\u200c\u200d\ufeff]', '', text)  # 移除无法识别的字符标记和零宽字符
    
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


def extract_text_from_pdf(file_data: bytes) -> str:
    """
    从PDF文件提取文本 - Workers版本
    注意：Workers环境可能不支持pymupdf，这里提供一个基础实现
    实际使用时可能需要通过外部API或服务来处理PDF
    """
    # 在Workers环境中，PDF解析可能需要：
    # 1. 使用外部API服务（如Cloudflare的PDF解析服务）
    # 2. 使用纯Python的PDF库（功能有限）
    # 3. 通过AI API处理图片PDF
    
    # 这里提供一个占位实现，实际应该调用外部服务或AI API
    try:
        # 尝试使用pymupdf（如果可用）
        import fitz
        pdf_doc = fitz.open(stream=file_data, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            page_text = page.get_text()
            if page_text:
                if len(pdf_doc) > 1:
                    text += f"--- 第{page_num + 1}页 ---\n{page_text}\n\n"
                else:
                    text += page_text + "\n"
        pdf_doc.close()
        return clean_text(text.strip())
    except ImportError:
        # pymupdf不可用，返回空字符串，提示使用AI API
        print("警告: PDF解析库不可用，请使用AI API处理PDF文件")
        return ""


def extract_text_from_word(file_data: bytes) -> str:
    """
    从Word文档提取文本 - 纯Python实现
    使用zipfile和xml解析.docx文件
    """
    try:
        # .docx文件本质上是ZIP压缩包
        zip_file = zipfile.ZipFile(io.BytesIO(file_data))
        
        # 读取主文档内容（word/document.xml）
        try:
            document_xml = zip_file.read('word/document.xml')
        except KeyError:
            raise Exception("无法读取Word文档内容，文件可能已损坏")
        
        # 解析XML
        root = ET.fromstring(document_xml)
        
        # 定义命名空间
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        # 提取所有段落文本
        text_parts = []
        for para in root.findall('.//w:p', namespaces):
            para_text = []
            for text_elem in para.findall('.//w:t', namespaces):
                if text_elem.text:
                    para_text.append(text_elem.text)
            if para_text:
                text_parts.append(''.join(para_text))
        
        # 提取表格文本
        for table in root.findall('.//w:tbl', namespaces):
            for row in table.findall('.//w:tr', namespaces):
                row_text = []
                for cell in row.findall('.//w:tc', namespaces):
                    cell_text = []
                    for text_elem in cell.findall('.//w:t', namespaces):
                        if text_elem.text:
                            cell_text.append(text_elem.text)
                    if cell_text:
                        row_text.append(' '.join(cell_text))
                if row_text:
                    text_parts.append(' | '.join(row_text))
        
        # 提取页眉页脚
        try:
            # 页眉
            header_xml = zip_file.read('word/header1.xml')
            header_root = ET.fromstring(header_xml)
            for para in header_root.findall('.//w:p', namespaces):
                para_text = []
                for text_elem in para.findall('.//w:t', namespaces):
                    if text_elem.text:
                        para_text.append(text_elem.text)
                if para_text:
                    text_parts.insert(0, ''.join(para_text))
        except KeyError:
            pass
        
        try:
            # 页脚
            footer_xml = zip_file.read('word/footer1.xml')
            footer_root = ET.fromstring(footer_xml)
            for para in footer_root.findall('.//w:p', namespaces):
                para_text = []
                for text_elem in para.findall('.//w:t', namespaces):
                    if text_elem.text:
                        para_text.append(text_elem.text)
                if para_text:
                    text_parts.append(''.join(para_text))
        except KeyError:
            pass
        
        zip_file.close()
        
        # 合并文本
        text = '\n'.join(text_parts)
        
        if not text.strip():
            raise Exception("无法从Word文档中提取文本，文件可能已损坏或格式不正确")
        
        return clean_text(text.strip())
    
    except zipfile.BadZipFile:
        raise Exception("文件格式错误，.docx 文件应该是有效的 ZIP 格式")
    except Exception as e:
        error_msg = str(e)
        if "cannot open" in error_msg.lower() or "permission" in error_msg.lower():
            raise Exception(f"无法打开文件: {error_msg}")
        else:
            raise Exception(f"Word文档解析失败: {error_msg}")


def extract_text(file_data: bytes, filename: str) -> str:
    """
    根据文件类型自动选择解析方法
    
    Args:
        file_data: 文件数据（字节）
        filename: 文件名（用于判断类型）
    """
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if file_ext == 'pdf':
        return extract_text_from_pdf(file_data)
    elif file_ext in ['doc', 'docx']:
        return extract_text_from_word(file_data)
    else:
        raise Exception(f"不支持的文件格式: {file_ext}")

