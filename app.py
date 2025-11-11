"""
智能简历数据库系统 - 主应用
"""
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from config import Config
from models import get_db_session, Resume
from utils.file_parser import extract_text
from utils.info_extractor import InfoExtractor
from utils.api_integration import APIIntegration
import threading

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config.from_object(Config)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_resume_async(resume_id, file_path):
    """异步处理简历解析"""
    db = get_db_session()
    try:
        resume = db.query(Resume).filter_by(id=resume_id).first()
        if not resume:
            return
        
        resume.parse_status = 'processing'
        db.commit()
        
        # 提取文本
        text = extract_text(file_path)
        
        # 提取信息
        extractor = InfoExtractor()
        info = extractor.extract_all(text)
        
        # 更新基本信息
        resume.name = info.get('name')
        resume.gender = info.get('gender')
        resume.birth_year = info.get('birth_year')
        resume.age = info.get('age')
        resume.phone = info.get('phone')
        resume.email = info.get('email')
        resume.earliest_work_year = info.get('earliest_work_year')
        resume.work_experience_years = info.get('work_experience_years')
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
        
        resume.parse_status = 'success'
        resume.parse_time = datetime.now()
        db.commit()
        
    except Exception as e:
        resume.parse_status = 'failed'
        resume.error_message = str(e)
        db.commit()
        print(f"处理简历失败: {e}")
    finally:
        db.close()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
    if file and allowed_file(file.filename):
        original_name = file.filename
        name_part, ext = os.path.splitext(original_name)
        ext = ext.lower()
        safe_name = secure_filename(name_part)
        if not safe_name:
            safe_name = 'resume'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = f"{timestamp}{safe_name}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 创建数据库记录
        db = get_db_session()
        resume = Resume(
            file_name=file.filename,
            file_path=file_path,
            parse_status='pending'
        )
        db.add(resume)
        db.commit()
        resume_id = resume.id
        db.close()
        
        # 异步处理
        thread = threading.Thread(target=process_resume_async, args=(resume_id, file_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '上传成功，正在解析...',
            'resume_id': resume_id
        })
    
    return jsonify({'success': False, 'message': '不支持的文件格式'}), 400

@app.route('/api/resumes', methods=['GET'])
def get_resumes():
    """获取简历列表"""
    db = get_db_session()
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 筛选
    query = db.query(Resume)
    
    # 搜索
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (Resume.name.like(f'%{search}%')) |
            (Resume.school.like(f'%{search}%')) |
            (Resume.major.like(f'%{search}%'))
        )
    
    # 筛选
    gender = request.args.get('gender', '')
    if gender:
        query = query.filter(Resume.gender == gender)
    
    education = request.args.get('education', '')
    if education:
        query = query.filter(Resume.highest_education == education)
    
    # 排序
    sort_by = request.args.get('sort_by', 'upload_time')
    sort_order = request.args.get('sort_order', 'desc')
    if hasattr(Resume, sort_by):
        if sort_order == 'desc':
            query = query.order_by(getattr(Resume, sort_by).desc())
        else:
            query = query.order_by(getattr(Resume, sort_by).asc())
    
    # 只返回解析成功的
    query = query.filter(Resume.parse_status == 'success')
    
    total = query.count()
    resumes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    db.close()
    
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in resumes],
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/resumes/<int:resume_id>', methods=['GET'])
def get_resume_detail(resume_id):
    """获取简历详情"""
    db = get_db_session()
    resume = db.query(Resume).filter_by(id=resume_id).first()
    db.close()
    
    if not resume:
        return jsonify({'success': False, 'message': '简历不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': resume.to_dict()
    })

@app.route('/api/resumes/<int:resume_id>', methods=['PUT'])
def update_resume(resume_id):
    """更新简历信息"""
    db = get_db_session()
    resume = db.query(Resume).filter_by(id=resume_id).first()
    
    if not resume:
        db.close()
        return jsonify({'success': False, 'message': '简历不存在'}), 404
    
    data = request.json
    
    # 更新字段
    if 'name' in data:
        resume.name = data['name']
    if 'gender' in data:
        resume.gender = data['gender']
    if 'birth_year' in data:
        resume.birth_year = data['birth_year']
        if resume.birth_year:
            resume.age = datetime.now().year - resume.birth_year
    if 'highest_education' in data:
        resume.highest_education = data['highest_education']
    if 'phone' in data:
        resume.phone = data['phone']
    if 'email' in data:
        resume.email = data['email']
    if 'applied_position' in data:
        resume.applied_position = data['applied_position']
    if 'school' in data:
        resume.school = data['school']
    if 'school_original' in data:
        resume.school_original = data['school_original']
    if 'major' in data:
        resume.major = data['major']
    if 'major_original' in data:
        resume.major_original = data['major_original']
    if 'work_experience' in data:
        resume.work_experience = data['work_experience']
    if 'earliest_work_year' in data:
        resume.earliest_work_year = data['earliest_work_year']
    if 'work_experience_years' in data:
        resume.work_experience_years = data['work_experience_years']
    if 'parse_status' in data:
        resume.parse_status = data['parse_status']
    if 'error_message' in data:
        resume.error_message = data['error_message']
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': '更新成功'})


def _remove_file_if_exists(path: str) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@app.route('/api/resumes/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    """删除单个简历"""
    db = get_db_session()
    resume = db.query(Resume).filter_by(id=resume_id).first()
    if not resume:
        db.close()
        return jsonify({'success': False, 'message': '简历不存在'}), 404

    file_path = resume.file_path
    db.delete(resume)
    db.commit()
    db.close()

    _remove_file_if_exists(file_path)

    return jsonify({'success': True, 'message': '删除成功'})


@app.route('/api/resumes/batch_delete', methods=['POST'])
def delete_resumes_batch():
    """批量删除简历"""
    data = request.json or {}
    resume_ids = data.get('resume_ids', [])
    if not resume_ids:
        return jsonify({'success': False, 'message': '请选择要删除的简历'}), 400

    db = get_db_session()
    resumes = db.query(Resume).filter(Resume.id.in_(resume_ids)).all()

    if not resumes:
        db.close()
        return jsonify({'success': False, 'message': '没有找到匹配的简历'}), 404

    file_paths = [resume.file_path for resume in resumes]
    for resume in resumes:
        db.delete(resume)
    db.commit()
    db.close()

    for path in file_paths:
        _remove_file_if_exists(path)

    return jsonify({'success': True, 'message': '批量删除成功', 'deleted': len(file_paths)})

@app.route('/api/export/<int:resume_id>', methods=['GET'])
def export_single(resume_id):
    """导出单个简历"""
    from utils.export import export_resume_to_excel
    
    db = get_db_session()
    resume = db.query(Resume).filter_by(id=resume_id).first()
    db.close()
    
    if not resume:
        return jsonify({'success': False, 'message': '简历不存在'}), 404
    
    file_path = export_resume_to_excel(resume)
    return send_file(file_path, as_attachment=True, download_name=f'简历_{resume.name or resume.id}.xlsx')

@app.route('/api/export/batch', methods=['POST'])
def export_batch():
    """批量导出"""
    from utils.export import export_resumes_to_excel
    
    data = request.json
    resume_ids = data.get('resume_ids', [])
    
    db = get_db_session()
    resumes = db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
    db.close()
    
    if not resumes:
        return jsonify({'success': False, 'message': '没有可导出的简历'}), 400
    
    file_path = export_resumes_to_excel(resumes)
    return send_file(file_path, as_attachment=True, download_name=f'简历批量导出_{datetime.now().strftime("%Y%m%d")}.xlsx')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

