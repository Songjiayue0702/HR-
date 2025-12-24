"""
数据导出工具 - Cloudflare Workers版本
使用CSV格式替代Excel，纯Python实现
"""
import csv
import io
from datetime import datetime
from typing import List, Dict, Any


def prepare_work_experiences(work_experience, max_count=None):
    """获取工作经历并格式化"""
    experiences = work_experience or []
    
    if max_count is not None:
        experiences = experiences[:max_count]
        while len(experiences) < max_count:
            experiences.append({})
    
    prepared = []
    for exp in experiences:
        start_year = exp.get('start_year') if exp else None
        end_year = exp.get('end_year') if exp else None
        if start_year and end_year:
            time_range = f"{start_year}-{end_year}"
        elif start_year and not end_year:
            time_range = f"{start_year}-至今"
        elif not start_year and end_year:
            time_range = f"至{end_year}"
        else:
            time_range = ''
        prepared.append({
            'company': (exp or {}).get('company') or '',
            'position': (exp or {}).get('position') or '',
            'start_year': start_year or '',
            'end_year': end_year or '',
            'time': time_range
        })
    return prepared


def export_resume_to_csv(resume: Dict[str, Any]) -> bytes:
    """
    导出单个简历到CSV格式
    
    Args:
        resume: 简历数据字典
        
    Returns:
        CSV文件的字节数据
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 设置CSV写入器支持中文
    writer.writerow(['简历信息'])
    writer.writerow([])
    
    # 基本信息
    writer.writerow(['基本信息'])
    writer.writerow(['姓名', resume.get('name', '')])
    writer.writerow(['性别', resume.get('gender', '')])
    writer.writerow(['出生年份', resume.get('birth_year', '')])
    writer.writerow(['年龄', resume.get('age', '')])
    writer.writerow(['手机号', resume.get('phone', '')])
    writer.writerow(['邮箱', resume.get('email', '')])
    writer.writerow([])
    
    # 教育信息
    writer.writerow(['教育信息'])
    writer.writerow(['最高学历', resume.get('highest_education', '')])
    writer.writerow(['毕业院校', resume.get('school', '')])
    writer.writerow(['专业', resume.get('major', '')])
    writer.writerow([])
    
    # 工作经历
    writer.writerow(['工作经历'])
    work_experiences = prepare_work_experiences(resume.get('work_experience'))
    writer.writerow(['公司', '职位', '开始年份', '结束年份', '时间段'])
    for exp in work_experiences:
        writer.writerow([
            exp['company'],
            exp['position'],
            exp['start_year'],
            exp['end_year'],
            exp['time']
        ])
    writer.writerow([])
    
    # 其他信息
    writer.writerow(['其他信息'])
    writer.writerow(['应聘岗位', resume.get('applied_position', '')])
    writer.writerow(['匹配度', resume.get('match_score', '')])
    writer.writerow(['匹配等级', resume.get('match_level', '')])
    
    # 转换为字节
    csv_data = output.getvalue()
    output.close()
    
    # 添加BOM以支持Excel正确显示中文
    return ('\ufeff' + csv_data).encode('utf-8-sig')


def export_resumes_to_csv(resumes: List[Dict[str, Any]]) -> bytes:
    """
    批量导出简历到CSV格式
    
    Args:
        resumes: 简历数据列表
        
    Returns:
        CSV文件的字节数据
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 表头
    writer.writerow([
        'ID', '姓名', '性别', '出生年份', '年龄', '手机号', '邮箱',
        '最高学历', '毕业院校', '专业', '应聘岗位',
        '匹配度', '匹配等级', '上传时间', '解析状态'
    ])
    
    # 数据行
    for resume in resumes:
        # 格式化工作经历
        work_exps = resume.get('work_experience', [])
        work_exp_text = '; '.join([
            f"{exp.get('company', '')}-{exp.get('position', '')}({exp.get('start_year', '')}-{exp.get('end_year', '至今')})"
            for exp in work_exps[:3]  # 只显示前3段
        ])
        
        upload_time = resume.get('upload_time', '')
        if isinstance(upload_time, str):
            upload_time_str = upload_time
        else:
            upload_time_str = upload_time.isoformat() if hasattr(upload_time, 'isoformat') else str(upload_time)
        
        writer.writerow([
            resume.get('id', ''),
            resume.get('name', ''),
            resume.get('gender', ''),
            resume.get('birth_year', ''),
            resume.get('age', ''),
            resume.get('phone', ''),
            resume.get('email', ''),
            resume.get('highest_education', ''),
            resume.get('school', ''),
            resume.get('major', ''),
            resume.get('applied_position', ''),
            resume.get('match_score', ''),
            resume.get('match_level', ''),
            upload_time_str,
            resume.get('parse_status', '')
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    # 添加BOM以支持Excel正确显示中文
    return ('\ufeff' + csv_data).encode('utf-8-sig')


def export_interviews_to_csv(interviews: List[Dict[str, Any]]) -> bytes:
    """
    导出面试记录到CSV格式
    
    Args:
        interviews: 面试记录列表
        
    Returns:
        CSV文件的字节数据
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 表头
    writer.writerow([
        'ID', '姓名', '应聘岗位', '身份验证码',
        '匹配度', '匹配等级', '状态',
        '一面面试官', '一面时间', '一面结果',
        '二面面试官', '二面时间', '二面结果',
        '三面面试官', '三面时间', '三面结果',
        '是否发offer', 'offer日期', '是否入职', '入职日期',
        '创建时间', '更新时间'
    ])
    
    # 数据行
    for interview in interviews:
        create_time = interview.get('create_time', '')
        if isinstance(create_time, str):
            create_time_str = create_time
        else:
            create_time_str = create_time.isoformat() if hasattr(create_time, 'isoformat') else str(create_time)
        
        update_time = interview.get('update_time', '')
        if isinstance(update_time, str):
            update_time_str = update_time
        else:
            update_time_str = update_time.isoformat() if hasattr(update_time, 'isoformat') else str(update_time)
        
        writer.writerow([
            interview.get('id', ''),
            interview.get('name', ''),
            interview.get('applied_position', ''),
            interview.get('identity_code', ''),
            interview.get('match_score', ''),
            interview.get('match_level', ''),
            interview.get('status', ''),
            interview.get('round1_interviewer', ''),
            interview.get('round1_time', ''),
            interview.get('round1_result', ''),
            interview.get('round2_interviewer', ''),
            interview.get('round2_time', ''),
            interview.get('round2_result', ''),
            interview.get('round3_interviewer', ''),
            interview.get('round3_time', ''),
            interview.get('round3_result', ''),
            '是' if interview.get('offer_issued') == 1 else '否',
            interview.get('offer_date', ''),
            '是' if interview.get('onboard') == 1 else '否',
            interview.get('onboard_date', ''),
            create_time_str,
            update_time_str
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    # 添加BOM以支持Excel正确显示中文
    return ('\ufeff' + csv_data).encode('utf-8-sig')



