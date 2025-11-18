import sys
sys.path.insert(0, '.')
from models import get_db_session, Resume
from utils.file_parser import extract_text, init_ocr_engine
from utils.info_extractor import InfoExtractor
from config import Config
import re

init_ocr_engine(Config.OCR_ENABLED, Config.OCR_ENGINE, Config.OCR_USE_GPU)
db = get_db_session()

r = db.query(Resume).filter_by(name='邱曙光').first()
if r:
    text = extract_text(r.file_path)
    extractor = InfoExtractor()
    cleaned = extractor.clean_text(text)
    
    # 查找工作经历段落
    work_section_pattern = r'(工作经历|工作经验|职业经历|任职经历)[：:：]?\s*(.*?)(?=(教育经历|教育背景|项目经历|自我评价|$))'
    work_match = re.search(work_section_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if work_match:
        work_text = work_match.group(2)
        lines = [line.strip() for line in work_text.split('\n') if line.strip()]
        print('工作经历段落行数:', len(lines))
        print('前20行:')
        for i, line in enumerate(lines[:20], 1):
            print(f'{i}. {line}')
        
        # 查找所有时间模式
        time_pattern = re.compile(
            r'((?:19|20)\d{2}(?:[年./-]?\d{1,2})?(?:月)?)\s*[-~至到—]+\s*'
            r'((?:19|20)\d{2}(?:[年./-]?\d{0,2})?(?:月)?|至今|现在)'
        )
        print('\n找到的时间段:')
        for i, line in enumerate(lines, 1):
            matches = list(time_pattern.finditer(line))
            if matches:
                for m in matches:
                    print(f'行{i}: {m.group(1)}-{m.group(2)}')
    
    # 提取工作经历
    info = extractor.extract_all(text)
    print(f'\n提取到的工作经历: {len(info.get("work_experience", []))}条')
    for i, exp in enumerate(info.get('work_experience', []), 1):
        print(f'{i}. 公司: {exp.get("company")}, 岗位: {exp.get("position")}, 时间: {exp.get("start_year")}-{exp.get("end_year")}')

db.close()








