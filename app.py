"""
智能简历数据库系统 - 主应用
"""
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from config import Config
from models import get_db_session, Resume, Position
from utils.file_parser import extract_text
from utils.info_extractor import InfoExtractor
from utils.api_integration import APIIntegration
from utils.ai_extractor import AIExtractor
from utils.duplicate_checker import check_duplicate
import threading

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config.from_object(Config)

# 初始化OCR引擎（如果启用）
if app.config.get('OCR_ENABLED', True):
    from utils.file_parser import init_ocr_engine
    init_ocr_engine(
        ocr_enabled=app.config.get('OCR_ENABLED', True),
        engine=app.config.get('OCR_ENGINE', 'paddleocr'),
        use_gpu=app.config.get('OCR_USE_GPU', False)
    )

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
        raw_text = extract_text(file_path)
        if not raw_text:
            raise Exception("无法从文件中提取文本，文件可能已损坏或格式不支持")
        
        # 检查是否启用AI（从配置或请求参数）
        ai_enabled = app.config.get('AI_ENABLED', True)
        ai_api_key = app.config.get('AI_API_KEY', '')
        ai_api_base = app.config.get('AI_API_BASE', '')
        ai_model = app.config.get('AI_MODEL', 'gpt-3.5-turbo')
        
        # 如果配置中没有API密钥，尝试从环境变量获取
        if not ai_api_key:
            ai_api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY') or os.environ.get('DEEPSEEK_API_KEY') or ''
        
        # 如果链接了AI API，优先使用AI优化文本提取
        text = raw_text
        ai_extractor = None
        if ai_enabled and ai_api_key:
            try:
                ai_extractor = AIExtractor(
                    api_key=ai_api_key,
                    api_base=ai_api_base if ai_api_base else None,
                    model=ai_model
                )
                # 使用AI优化文本提取
                optimized_text = ai_extractor.optimize_text_extraction(raw_text)
                if optimized_text:
                    text = optimized_text
                    print(f"AI文本优化成功（模型: {ai_model}），文本长度: {len(text)} 字符")
                else:
                    print(f"AI文本优化失败（模型: {ai_model}），使用原始文本")
            except Exception as e:
                print(f"AI文本优化失败（模型: {ai_model}），使用原始文本: {e}")
        
        # 保存原始文本和优化后的文本
        resume.raw_text = text
        
        # 规则提取
        extractor = InfoExtractor()
        
        # AI辅助信息提取（如果启用）
        ai_result = None
        if ai_enabled and ai_api_key and ai_extractor:
            try:
                ai_result = ai_extractor.extract_with_ai(text)
                if ai_result:
                    print(f"AI辅助信息提取成功（模型: {ai_model}），提取到 {len([k for k, v in ai_result.items() if v])} 个字段")
            except Exception as e:
                print(f"AI辅助信息提取失败（模型: {ai_model}），继续使用规则提取: {e}")
        
        # 融合规则提取和AI提取的结果
        info = extractor.extract_all(text, ai_result=ai_result)
        
        # 更新基本信息
        resume.name = info.get('name')
        resume.gender = info.get('gender')
        resume.birth_year = info.get('birth_year')
        # 如果从简历中提取到了年龄，保存到age_from_resume
        extracted_age = info.get('age')
        if extracted_age:
            resume.age_from_resume = extracted_age
            resume.age = extracted_age
        else:
            # 如果没有提取到年龄，但有出生年份，计算年龄
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
        
        # 处理学校信息（仅保留原文提取）
        school_original = info.get('school')
        if school_original:
            resume.school = school_original
            resume.school_original = school_original
        
        # 处理专业信息（仅保留原文提取）
        major_original = info.get('major')
        if major_original:
            resume.major = major_original
            resume.major_original = major_original
        
        # 计算并保存最早工作年份
        if work_experiences:
            work_years = [exp.get('start_year') for exp in work_experiences if exp.get('start_year')]
            if work_years:
                resume.earliest_work_year = min(work_years)
        
        # 查重检测
        existing_resumes = db.query(Resume).filter(
            Resume.parse_status == 'success',
            Resume.id != resume.id
        ).all()
        duplicate_id, similarity = check_duplicate(resume, existing_resumes)
        
        if similarity >= 80.0:
            resume.duplicate_status = '重复简历'
            resume.duplicate_similarity = similarity
            resume.duplicate_resume_id = duplicate_id
        else:
            resume.duplicate_status = None
            resume.duplicate_similarity = similarity if similarity > 0 else None
            resume.duplicate_resume_id = None
        
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
        
        # 获取AI配置（如果前端提供了）
        ai_config = request.form.get('ai_config')
        if ai_config:
            try:
                ai_config_data = json.loads(ai_config)
                # 更新临时配置（仅用于本次处理）
                if ai_config_data.get('ai_api_key'):
                    app.config['AI_API_KEY'] = ai_config_data['ai_api_key']
                if ai_config_data.get('ai_api_base'):
                    app.config['AI_API_BASE'] = ai_config_data['ai_api_base']
                if ai_config_data.get('ai_model'):
                    app.config['AI_MODEL'] = ai_config_data['ai_model']
                if 'ai_enabled' in ai_config_data:
                    app.config['AI_ENABLED'] = ai_config_data['ai_enabled']
            except:
                pass  # 如果解析失败，使用默认配置
        
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
    
    # 允许显示所有状态的简历（pending/processing/success/failed）
    # 用户可以通过状态筛选来查看特定状态的简历
    status_filter = request.args.get('status', '')
    if status_filter:
        query = query.filter(Resume.parse_status == status_filter)
    # 如果没有指定状态筛选，默认显示所有状态的简历
    
    total = query.count()
    resumes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # 注意：查重检测在简历解析时完成，这里不需要重复检测
    # 如果需要对旧简历进行查重，可以单独运行查重脚本
    
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
        # 如果简历中提取到了年龄，优先使用简历中的年龄
        if resume.age_from_resume:
            resume.age = resume.age_from_resume
        elif resume.birth_year:
            # 如果没有从简历提取到年龄，根据出生年份计算
            resume.age = datetime.now().year - resume.birth_year
    if 'earliest_work_year' in data:
        resume.earliest_work_year = data['earliest_work_year']
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
        # 工作经历更新时，如果用户没有手动设置earliest_work_year，自动从工作经历中计算
        if 'earliest_work_year' not in data and resume.work_experience:
            work_years = [exp.get('start_year') for exp in resume.work_experience if exp.get('start_year')]
            if work_years:
                resume.earliest_work_year = min(work_years)
    if 'highest_education' in data:
        resume.highest_education = data['highest_education']
    if 'phone' in data:
        resume.phone = data['phone']
    if 'email' in data:
        resume.email = data['email']
    if 'applied_position' in data:
        resume.applied_position = data['applied_position']
    if 'error_message' in data:
        resume.error_message = data['error_message']
    
    # 如果用户手动设置了earliest_work_year，使用用户设置的值
    if 'earliest_work_year' in data:
        resume.earliest_work_year = data['earliest_work_year']
    
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

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """获取AI配置（不返回密钥）"""
    return jsonify({
        'success': True,
        'data': {
            'ai_enabled': app.config.get('AI_ENABLED', True),
            'ai_model': app.config.get('AI_MODEL', 'gpt-3.5-turbo'),
            'ai_api_base': app.config.get('AI_API_BASE', ''),
            'ai_models': app.config.get('AI_MODELS', [])
        }
    })

@app.route('/api/ai/config', methods=['POST'])
def save_ai_config():
    """保存AI配置"""
    try:
        data = request.json
        ai_enabled = data.get('ai_enabled', True)
        ai_model = data.get('ai_model', 'gpt-3.5-turbo')
        ai_api_key = data.get('ai_api_key', '')
        ai_api_base = data.get('ai_api_base', '')
        
        # 更新配置（注意：这里只是临时更新，重启后会恢复）
        # 实际生产环境应该保存到配置文件或数据库
        app.config['AI_ENABLED'] = ai_enabled
        app.config['AI_MODEL'] = ai_model
        if ai_api_key:
            app.config['AI_API_KEY'] = ai_api_key
        if ai_api_base:
            app.config['AI_API_BASE'] = ai_api_base
        
        return jsonify({
            'success': True,
            'message': 'AI配置已保存（当前会话有效）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存配置失败: {str(e)}'
        }), 400

@app.route('/api/ai/test', methods=['POST'])
def test_ai_connection():
    """测试AI连接"""
    try:
        data = request.json
        api_key = data.get('api_key', '')
        api_base = data.get('api_base', '')
        model = data.get('model', 'gpt-3.5-turbo')
        
        if not api_key:
            return jsonify({
                'success': False,
                'message': '请提供API密钥'
            }), 400
        
        # 创建临时AI提取器进行测试
        ai_extractor = AIExtractor(
            api_key=api_key,
            api_base=api_base if api_base else None,
            model=model
        )
        
        # 使用简单的测试文本
        test_text = "姓名：张三\n性别：男\n手机：13800138000"
        result = ai_extractor.extract_with_ai(test_text)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'AI连接测试成功',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'AI连接测试失败，请检查API密钥和网络连接'
            }), 400
            
    except Exception as e:
            return jsonify({
                'success': False,
                'message': f'测试失败: {str(e)}'
            }), 400

# 岗位目录API
@app.route('/api/positions', methods=['GET'])
def get_positions():
    """获取岗位列表"""
    try:
        session = get_db_session()
        positions = session.query(Position).order_by(Position.update_time.desc()).all()
        session.close()
        
        return jsonify({
            'success': True,
            'data': [pos.to_dict() for pos in positions]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取岗位列表失败: {str(e)}'
        }), 500

@app.route('/api/positions', methods=['POST'])
def create_position():
    """创建岗位"""
    try:
        data = request.json
        position_name = data.get('position_name', '').strip()
        
        if not position_name:
            return jsonify({
                'success': False,
                'message': '岗位名称不能为空'
            }), 400
        
        session = get_db_session()
        position = Position(
            position_name=position_name,
            work_content=data.get('work_content', '').strip() or None,
            job_requirements=data.get('job_requirements', '').strip() or None,
            core_requirements=data.get('core_requirements', '').strip() or None
        )
        session.add(position)
        session.commit()
        position_id = position.id
        session.close()
        
        return jsonify({
            'success': True,
            'message': '岗位创建成功',
            'data': position.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建岗位失败: {str(e)}'
        }), 500

@app.route('/api/positions/<int:position_id>', methods=['GET'])
def get_position(position_id):
    """获取单个岗位详情"""
    try:
        session = get_db_session()
        position = session.query(Position).filter(Position.id == position_id).first()
        session.close()
        
        if not position:
            return jsonify({
                'success': False,
                'message': '岗位不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': position.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取岗位详情失败: {str(e)}'
        }), 500

@app.route('/api/positions/<int:position_id>', methods=['PUT'])
def update_position(position_id):
    """更新岗位"""
    try:
        data = request.json
        position_name = data.get('position_name', '').strip()
        
        if not position_name:
            return jsonify({
                'success': False,
                'message': '岗位名称不能为空'
            }), 400
        
        session = get_db_session()
        position = session.query(Position).filter(Position.id == position_id).first()
        
        if not position:
            session.close()
            return jsonify({
                'success': False,
                'message': '岗位不存在'
            }), 404
        
        position.position_name = position_name
        position.work_content = data.get('work_content', '').strip() or None
        position.job_requirements = data.get('job_requirements', '').strip() or None
        position.core_requirements = data.get('core_requirements', '').strip() or None
        position.update_time = datetime.now()
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': '岗位更新成功',
            'data': position.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新岗位失败: {str(e)}'
        }), 500

@app.route('/api/positions/<int:position_id>', methods=['DELETE'])
def delete_position(position_id):
    """删除岗位"""
    try:
        session = get_db_session()
        position = session.query(Position).filter(Position.id == position_id).first()
        
        if not position:
            session.close()
            return jsonify({
                'success': False,
                'message': '岗位不存在'
            }), 404
        
        session.delete(position)
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': '岗位删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除岗位失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

