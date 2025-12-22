"""重新解析邱曙光和李宜隆的简历"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from models import get_db_session, Resume
from utils.file_parser import extract_text
from utils.info_extractor import InfoExtractor
# 外部API验证和OCR已移除，统一使用AI API智能识别

def reparse_resume(resume):
    """重新解析单个简历"""
    db = get_db_session()
    extractor = InfoExtractor()
    
    try:
        print(f"\n{'='*60}")
        print(f"重新解析简历: {resume.file_name} (ID: {resume.id})")
        print(f"{'='*60}")
        
        # 检查文件
        if not os.path.exists(resume.file_path):
            print(f"文件不存在: {resume.file_path}")
            return
        
        # 提取文本
        print("正在提取文本...")
        text = extract_text(resume.file_path)
        if not text:
            print("无法提取文本")
            resume.parse_status = 'failed'
            resume.error_message = '无法从文件中提取文本'
            db.commit()
            return
        
        print(f"文本提取成功，长度: {len(text)} 字符")
        print(f"中文字符数: {len([c for c in text if '\u4e00' <= c <= '\u9fff'])}")
        print(f"文本预览（前300字符）:")
        print("-" * 60)
        # 安全打印，避免编码错误
        import sys
        if sys.stdout.encoding and 'utf' in sys.stdout.encoding.lower():
            print(text[:300])
        else:
            try:
                print(text[:300].encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                print(repr(text[:300]))
        print("-" * 60)
        
        # 提取信息
        print("\n正在提取信息...")
        info = extractor.extract_all(text)
        
        # 更新基本信息
        resume.name = info.get('name')
        resume.gender = info.get('gender')
        resume.birth_year = info.get('birth_year')
        
        extracted_age = info.get('age')
        if extracted_age:
            resume.age_from_resume = extracted_age
            resume.age = extracted_age
        else:
            if resume.birth_year:
                resume.age = datetime.now().year - resume.birth_year
        
        resume.phone = info.get('phone')
        resume.email = info.get('email')
        resume.highest_education = info.get('highest_education')
        resume.raw_text = text
        resume.error_message = None
        
        # 处理工作经历（统一使用AI API智能识别，无需外部验证）
        work_experiences = info.get('work_experience', [])
        resume.work_experience = work_experiences
        
        # 处理学校信息（统一使用AI API智能识别，无需外部验证）
        school_original = info.get('school')
        if school_original:
            resume.school = school_original
            resume.school_original = school_original
        
        # 处理专业信息（统一使用AI API智能识别，无需外部验证）
        major_original = info.get('major')
        if major_original:
            resume.major = major_original
            resume.major_original = major_original
        
        # 计算最早工作年份
        if work_experiences:
            work_years = [exp.get('start_year') for exp in work_experiences if exp.get('start_year')]
            if work_years:
                resume.earliest_work_year = min(work_years)
        
        resume.parse_status = 'success'
        resume.parse_time = datetime.now()
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("解析完成！")
        print("=" * 60)
        print(f"姓名: {resume.name or '(未提取)'}")
        print(f"性别: {resume.gender or '(未提取)'}")
        print(f"年龄: {resume.age or '(未提取)'}")
        print(f"手机: {resume.phone or '(未提取)'}")
        print(f"邮箱: {resume.email or '(未提取)'}")
        print(f"学历: {resume.highest_education or '(未提取)'}")
        print(f"学校: {resume.school or '(未提取)'}")
        print(f"专业: {resume.major or '(未提取)'}")
        print(f"工作经历: {len(work_experiences)} 条")
        if work_experiences:
            for i, exp in enumerate(work_experiences[:3], 1):
                print(f"  工作{i}: {exp.get('company')} - {exp.get('position')} ({exp.get('start_year')}-{exp.get('end_year')})")
        
    except Exception as e:
        print(f"解析失败: {e}")
        import traceback
        traceback.print_exc()
        resume.parse_status = 'failed'
        resume.error_message = str(e)
        db.commit()
    finally:
        db.close()

def main():
    db = get_db_session()
    try:
        # 查找两个简历
        resumes = db.query(Resume).filter(Resume.name.in_(['邱曙光', '李宜隆'])).all()
        
        if not resumes:
            print("未找到指定的简历")
            return
        
        for resume in resumes:
            reparse_resume(resume)
            
    finally:
        db.close()

if __name__ == '__main__':
    main()

