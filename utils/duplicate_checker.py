"""
简历查重工具
计算两个简历的相似度，判断是否为重复简历
"""
from typing import Optional, Tuple


def calculate_similarity(resume1, resume2) -> float:
    """
    计算两个简历的相似度（0-100）
    
    Args:
        resume1: 第一个简历对象
        resume2: 第二个简历对象
    
    Returns:
        相似度百分比（0-100）
    """
    if not resume1 or not resume2:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    # 1. 姓名匹配（权重30%）
    if resume1.name and resume2.name:
        weight = 30.0
        total_weight += weight
        if resume1.name.strip() == resume2.name.strip():
            total_score += weight
        elif resume1.name.strip() in resume2.name.strip() or resume2.name.strip() in resume1.name.strip():
            total_score += weight * 0.7  # 部分匹配
    
    # 2. 手机号匹配（权重25%）
    if resume1.phone and resume2.phone:
        weight = 25.0
        total_weight += weight
        phone1 = ''.join(filter(str.isdigit, resume1.phone))
        phone2 = ''.join(filter(str.isdigit, resume2.phone))
        if phone1 and phone2:
            if phone1 == phone2:
                total_score += weight
            elif len(phone1) >= 7 and len(phone2) >= 7:
                # 后7位匹配
                if phone1[-7:] == phone2[-7:]:
                    total_score += weight * 0.8
                elif phone1[-4:] == phone2[-4:]:
                    total_score += weight * 0.5
    
    # 3. 邮箱匹配（权重20%）
    if resume1.email and resume2.email:
        weight = 20.0
        total_weight += weight
        email1 = resume1.email.strip().lower()
        email2 = resume2.email.strip().lower()
        if email1 == email2:
            total_score += weight
        elif '@' in email1 and '@' in email2:
            # 提取邮箱用户名部分
            user1 = email1.split('@')[0]
            user2 = email2.split('@')[0]
            if user1 == user2:
                total_score += weight * 0.8
    
    # 4. 工作经历匹配（权重15%）
    if resume1.work_experience and resume2.work_experience:
        weight = 15.0
        total_weight += weight
        work_score = _compare_work_experience(resume1.work_experience, resume2.work_experience)
        total_score += weight * work_score
    
    # 5. 学校匹配（权重5%）
    if resume1.school and resume2.school:
        weight = 5.0
        total_weight += weight
        school1 = resume1.school.strip()
        school2 = resume2.school.strip()
        if school1 == school2:
            total_score += weight
        elif school1 in school2 or school2 in school1:
            total_score += weight * 0.7
    
    # 6. 专业匹配（权重3%）
    if resume1.major and resume2.major:
        weight = 3.0
        total_weight += weight
        major1 = resume1.major.strip()
        major2 = resume2.major.strip()
        if major1 == major2:
            total_score += weight
        elif major1 in major2 or major2 in major1:
            total_score += weight * 0.7
    
    # 7. 出生年份/年龄匹配（权重2%）
    if resume1.birth_year and resume2.birth_year:
        weight = 2.0
        total_weight += weight
        if resume1.birth_year == resume2.birth_year:
            total_score += weight
    elif resume1.age and resume2.age:
        weight = 2.0
        total_weight += weight
        if abs(resume1.age - resume2.age) <= 1:
            total_score += weight
    
    # 计算最终相似度
    if total_weight == 0:
        return 0.0
    
    similarity = (total_score / total_weight) * 100
    return round(similarity, 2)


def _compare_work_experience(work_exp1, work_exp2) -> float:
    """
    比较两个工作经历列表的相似度
    
    Returns:
        相似度（0-1）
    """
    if not work_exp1 or not work_exp2:
        return 0.0
    
    if len(work_exp1) == 0 or len(work_exp2) == 0:
        return 0.0
    
    # 提取公司名和岗位
    companies1 = [exp.get('company', '').strip() for exp in work_exp1 if exp.get('company')]
    companies2 = [exp.get('company', '').strip() for exp in work_exp2 if exp.get('company')]
    
    positions1 = [exp.get('position', '').strip() for exp in work_exp1 if exp.get('position')]
    positions2 = [exp.get('position', '').strip() for exp in work_exp2 if exp.get('position')]
    
    # 计算公司名匹配度
    company_match = 0.0
    if companies1 and companies2:
        matched = 0
        for c1 in companies1:
            for c2 in companies2:
                if c1 and c2:
                    if c1 == c2:
                        matched += 1
                        break
                    elif c1 in c2 or c2 in c1:
                        matched += 0.5
                        break
        company_match = matched / max(len(companies1), len(companies2))
    
    # 计算岗位匹配度
    position_match = 0.0
    if positions1 and positions2:
        matched = 0
        for p1 in positions1:
            for p2 in positions2:
                if p1 and p2:
                    if p1 == p2:
                        matched += 1
                        break
                    elif p1 in p2 or p2 in p1:
                        matched += 0.5
                        break
        position_match = matched / max(len(positions1), len(positions2))
    
    # 综合匹配度
    return (company_match * 0.6 + position_match * 0.4)


def check_duplicate(new_resume, existing_resumes) -> Tuple[Optional[int], float]:
    """
    检查新简历是否与已有简历重复
    
    Args:
        new_resume: 新上传的简历对象
        existing_resumes: 已有简历列表（排除自己）
    
    Returns:
        (匹配到的重复简历ID, 相似度) 或 (None, 相似度)
    """
    max_similarity = 0.0
    duplicate_id = None
    
    for existing in existing_resumes:
        if existing.id == new_resume.id:
            continue
        
        similarity = calculate_similarity(new_resume, existing)
        if similarity >= 80.0 and similarity > max_similarity:
            max_similarity = similarity
            duplicate_id = existing.id
    
    return (duplicate_id, max_similarity)
