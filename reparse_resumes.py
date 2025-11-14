"""
重新解析所有简历
使用改进后的信息提取逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from models import get_db_session, Resume
from utils.file_parser import extract_text
from utils.info_extractor import InfoExtractor
from utils.api_integration import APIIntegration

def reparse_all_resumes():
    """重新解析所有简历"""
    db = get_db_session()
    extractor = InfoExtractor()
    
    try:
        # 获取所有简历
        resumes = db.query(Resume).all()
        total = len(resumes)
        
        if total == 0:
            print("没有找到简历记录")
            return
        
        print(f"找到 {total} 份简历，开始重新解析...")
        print("=" * 60)
        
        success_count = 0
        failed_count = 0
        
        for idx, resume in enumerate(resumes, 1):
            print(f"\n[{idx}/{total}] 处理: {resume.file_name}")
            
            try:
                # 检查文件是否存在
                if not os.path.exists(resume.file_path):
                    print(f"  ❌ 文件不存在: {resume.file_path}")
                    resume.parse_status = 'failed'
                    resume.error_message = '文件不存在'
                    failed_count += 1
                    continue
                
                # 提取文本
                text = extract_text(resume.file_path)
                if not text:
                    print(f"  ❌ 无法提取文本")
                    resume.parse_status = 'failed'
                    resume.error_message = '无法从文件中提取文本'
                    failed_count += 1
                    continue
                
                # 提取信息
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
                
                # 处理工作经历和公司验证
                work_experiences = info.get('work_experience', [])
                for exp in work_experiences:
                    company_name = exp.get('company')
                    if company_name:
                        standardized, status, confidence, code, alternatives = \
                            APIIntegration.verify_company(company_name)
                        if standardized:
                            exp['company_standardized'] = standardized
                            exp['company_code'] = code
                            exp['company_match_status'] = status
                            exp['company_confidence'] = confidence
                            exp['company_alternatives'] = alternatives
                
                resume.work_experience = work_experiences
                
                # 处理学校验证
                school_original = info.get('school')
                if school_original:
                    resume.school_original = school_original
                    standardized, status, confidence, code, alternatives = \
                        APIIntegration.verify_school(school_original)
                    resume.school = standardized or school_original
                    resume.school_code = code
                    resume.school_match_status = status
                    resume.school_confidence = confidence
                
                # 处理专业验证
                major_original = info.get('major')
                if major_original:
                    resume.major_original = major_original
                    standardized, status, confidence, code, alternatives = \
                        APIIntegration.verify_major(major_original, resume.school_code)
                    resume.major = standardized or major_original
                    resume.major_code = code
                    resume.major_match_status = status
                    resume.major_confidence = confidence
                
                # 计算最早工作年份
                if work_experiences:
                    work_years = [exp.get('start_year') for exp in work_experiences if exp.get('start_year')]
                    if work_years:
                        resume.earliest_work_year = min(work_years)
                
                resume.parse_status = 'success'
                resume.parse_time = datetime.now()
                
                # 显示提取结果
                print(f"  ✅ 解析成功")
                print(f"     姓名: {resume.name or '(未提取)'}")
                print(f"     性别: {resume.gender or '(未提取)'}")
                print(f"     年龄: {resume.age or '(未提取)'}")
                print(f"     手机: {resume.phone or '(未提取)'}")
                print(f"     邮箱: {resume.email or '(未提取)'}")
                print(f"     学历: {resume.highest_education or '(未提取)'}")
                print(f"     学校: {resume.school or '(未提取)'}")
                print(f"     专业: {resume.major or '(未提取)'}")
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ 解析失败: {e}")
                resume.parse_status = 'failed'
                resume.error_message = str(e)
                failed_count += 1
                import traceback
                traceback.print_exc()
            
            # 每10条提交一次
            if idx % 10 == 0:
                db.commit()
                print(f"\n已处理 {idx}/{total} 条记录...")
        
        # 最终提交
        db.commit()
        
        print("\n" + "=" * 60)
        print("重新解析完成！")
        print(f"成功: {success_count} 条")
        print(f"失败: {failed_count} 条")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    reparse_all_resumes()




