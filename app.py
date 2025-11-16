"""
智能简历数据库系统 - 主应用
"""
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from config import Config
from models import get_db_session, Resume, Position, Interview
from utils.file_parser import extract_text
from utils.info_extractor import InfoExtractor
from utils.api_integration import APIIntegration
from utils.ai_extractor import AIExtractor
from utils.duplicate_checker import check_duplicate
from utils.export import export_resumes_to_excel, export_interviews_to_excel
from utils.export_pdf import export_resume_analysis_to_pdf, export_interview_round_analysis_to_pdf
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
        
        # 检测文件类型
        file_ext = os.path.splitext(file_path)[1].lower()
        is_word_file = file_ext in ['.doc', '.docx']
        
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
        
        # 保存原始文本（优先保存优化后的文本，如果没有优化则保存原始文本）
        # 注意：raw_text字段存储的是用于信息提取的文本（可能是优化后的）
        # 如果需要保存真正的原始文本，可以添加新字段
        resume.raw_text = text
        
        # 如果使用了AI优化，原始文本和优化后的文本都保存
        # 但为了信息提取准确性，使用优化后的文本进行提取
        
        # 规则提取
        extractor = InfoExtractor()
        
        # AI辅助信息提取（如果启用）
        ai_result = None
        if ai_enabled and ai_api_key and ai_extractor:
            try:
                ai_result = ai_extractor.extract_with_ai(text, is_word_file=is_word_file)
                if ai_result:
                    print(f"AI辅助信息提取成功（模型: {ai_model}，Word格式: {is_word_file}），提取到 {len([k for k, v in ai_result.items() if v])} 个字段")
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
    """文件上传接口（支持多文件上传）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    # 获取所有上传的文件
    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
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
    
    uploaded_count = 0
    failed_files = []
    resume_ids = []
    
    # 处理每个文件
    for file in files:
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            failed_files.append(file.filename)
            continue
        
        try:
            original_name = file.filename
            name_part, ext = os.path.splitext(original_name)
            ext = ext.lower()
            safe_name = secure_filename(name_part)
            if not safe_name:
                safe_name = 'resume'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # 添加微秒确保唯一性
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
            
            uploaded_count += 1
            resume_ids.append(resume_id)
        except Exception as e:
            print(f"文件 {file.filename} 上传失败: {e}")
            failed_files.append(file.filename)
    
    # 返回结果
    if uploaded_count > 0:
        message = f'成功上传 {uploaded_count} 个文件，正在解析...'
        if failed_files:
            message += f'，{len(failed_files)} 个文件上传失败'
        return jsonify({
            'success': True,
            'message': message,
            'uploaded_count': uploaded_count,
            'failed_count': len(failed_files),
            'failed_files': failed_files,
            'resume_ids': resume_ids
        })
    else:
        return jsonify({
            'success': False,
            'message': f'所有文件上传失败：{", ".join(failed_files) if failed_files else "不支持的文件格式"}'
        }), 400

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
    data = request.json
    resume_ids = data.get('resume_ids', [])
    
    db = get_db_session()
    resumes = db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
    db.close()
    
    if not resumes:
        return jsonify({'success': False, 'message': '没有可导出的简历'}), 400
    
    file_path = export_resumes_to_excel(resumes)
    return send_file(file_path, as_attachment=True, download_name=f'简历批量导出_{datetime.now().strftime("%Y%m%d")}.xlsx')


@app.route('/api/resumes/<int:resume_id>/analysis-pdf', methods=['POST'])
def export_resume_analysis_pdf(resume_id):
    """导出简历分析详情为PDF（基本信息、教育信息、工作经历、简历匹配度分析）"""
    session = get_db_session()
    try:
        resume = session.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return jsonify({'success': False, 'message': '简历不存在'}), 404

        applied_position = (resume.applied_position or '').strip()
        analysis = None

        # 如果有应聘岗位且AI可用，则在导出前实时执行一次匹配分析，保证PDF中的匹配度内容是最新的
        try:
            if applied_position:
                # 获取岗位信息
                position = session.query(Position).filter(Position.position_name == applied_position).first()
                if position:
                    ai_enabled = app.config.get('AI_ENABLED', True)
                    ai_api_key = app.config.get('AI_API_KEY', '')
                    ai_model = app.config.get('AI_MODEL', 'gpt-3.5-turbo')
                    ai_api_base = app.config.get('AI_API_BASE', '')

                    if ai_enabled and ai_api_key:
                        ai_extractor = AIExtractor(
                            api_key=ai_api_key,
                            api_base=ai_api_base if ai_api_base else None,
                            model=ai_model
                        )

                        resume_info = f"""
姓名：{resume.name or '未知'}
性别：{resume.gender or '未知'}
年龄：{resume.age or '未知'}
学历：{resume.highest_education or '未知'}
毕业学校：{resume.school or '未知'}
专业：{resume.major or '未知'}
工龄：{resume.earliest_work_year and (datetime.now().year - resume.earliest_work_year) or '未知'}年
工作经历：{json.dumps(resume.work_experience or [], ensure_ascii=False, indent=2)}
"""

                        position_info = f"""
岗位名称：{position.position_name}
工作内容：{position.work_content or '未填写'}
任职资格：{position.job_requirements or '未填写'}
核心需求：{position.core_requirements or '未填写'}
"""

                        prompt = f"""请分析以下简历与岗位的匹配度，并给出详细的分析报告。

【简历信息】
{resume_info}

【岗位要求】
{position_info}

请从以下维度进行分析：
1. 教育背景匹配度（学历、学校、专业）
2. 工作经验匹配度（工作年限、工作内容、岗位相关性）
3. 技能匹配度（根据工作经历推断的技能）
4. 综合匹配度评分（0-100分）

请以JSON格式返回分析结果，格式如下：
{{
    "match_score": 85,
    "match_level": "高度匹配",
    "detailed_analysis": "详细的分析说明...",
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["建议1", "建议2"]
}}

其中：
- match_score: 匹配度分数（0-100）
- match_level: 匹配等级（高度匹配/中等匹配/低度匹配）
- detailed_analysis: 详细分析说明（200-500字）
- strengths: 优势匹配点列表
- weaknesses: 不足匹配点列表
- suggestions: 改进建议列表

请只返回JSON格式，不要包含其他文字说明。"""

                        response_text = ai_extractor._call_ai_api(prompt)

                        # 解析JSON
                        import re
                        try:
                            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                            if json_match:
                                analysis = json.loads(json_match.group())
                            else:
                                analysis = json.loads(response_text)
                        except json.JSONDecodeError:
                            analysis = {
                                'match_score': 50,
                                'match_level': '中等匹配',
                                'detailed_analysis': response_text[:500] if len(response_text) > 500 else response_text,
                                'strengths': [],
                                'weaknesses': [],
                                'suggestions': []
                            }

                        # 对得分做同样的“放宽”与等级划分，保持与页面一致
                        try:
                            raw_score = analysis.get('match_score')
                            if raw_score is None:
                                raw_score = 60
                            raw_score = float(raw_score)
                            new_score = int(max(50, min(100, raw_score * 0.7 + 30)))
                            analysis['match_score'] = new_score

                            if new_score >= 80:
                                level = '高度匹配'
                            elif new_score >= 60:
                                level = '中等匹配'
                            else:
                                level = '低度匹配'
                            analysis['match_level'] = level
                        except Exception:
                            pass
        except Exception as _:
            # 匹配度分析失败时，不影响PDF导出，只是不带匹配信息
            analysis = None

        file_path = export_resume_analysis_to_pdf(resume, analysis)
        download_name = f"简历分析报告_{resume.name or resume_id}.pdf"
        return send_file(file_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({'success': False, 'message': f'导出分析报告失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/interviews', methods=['GET'])
def list_interviews():
    """获取面试流程列表，可按姓名/岗位搜索"""
    session = get_db_session()
    try:
        search = (request.args.get('search') or '').strip()
        # 关联简历表以便生成身份验证码
        query = session.query(Interview, Resume).join(Resume, Interview.resume_id == Resume.id)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Interview.name.like(like)) |
                (Interview.applied_position.like(like))
            )
        rows = query.order_by(Interview.update_time.desc()).all()
        data = []
        for iv, res in rows:
            d = iv.to_dict()
            # 身份验证码：姓名+手机号后四位
            identity_code = ''
            if res.name:
                phone = res.phone or ''
                if phone and len(phone) >= 4:
                    identity_code = res.name + phone[-4:]
                else:
                    identity_code = res.name
            d['identity_code'] = identity_code
            data.append(d)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取面试列表失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/interviews', methods=['POST'])
def create_interview():
    """
    创建一条面试流程记录
    请求体: { "resume_id": 123 }
    自动带入当前简历的姓名和应聘岗位
    """
    try:
        data = request.json or {}
        resume_id = data.get('resume_id')
        match_score = data.get('match_score')
        match_level = data.get('match_level')
        if not resume_id:
            return jsonify({'success': False, 'message': '缺少简历ID'}), 400

        session = get_db_session()
        try:
            resume = session.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                return jsonify({'success': False, 'message': '简历不存在'}), 404

            interview = Interview(
                resume_id=resume.id,
                name=resume.name or '',
                applied_position=resume.applied_position or '',
                match_score=match_score,
                match_level=match_level
            )
            session.add(interview)
            session.commit()

            return jsonify({'success': True, 'data': interview.to_dict()})
        finally:
            session.close()
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建面试记录失败: {str(e)}'}), 500


def _calc_interview_status(interview: Interview) -> str:
    """
    根据各轮结果 + Offer/入职信息 计算面试流程状态
    基本规则：
    1. 优先级：已入职 > 已发offer > 轮次结果
    2. 轮次结果：
       - 默认：待面试
       - 一面 result 未通过：一面面试未通过
       - 一面通过，二面未填：一面面试通过
       - 二面 result 未通过：二面面试未通过
       - 二面通过，round3_enabled=0：面试通过
       - 二面通过，round3_enabled=1 且三面未填：二面面试通过
       - 三面 result 未通过：三面面试未通过
       - 三面 result 通过：面试通过
    3. Offer 与入职：
       - 如果 onboard=1 且实际入职日期、入职架构填写完整：状态为“已入职”
       - 否则，如果 offer_issued=1 且 Offer 发放日期、拟入职架构、拟入职日期填写完整：状态为“已发offer”
    """
    # 先处理入职/offer状态（最高优先级）
    if interview.onboard and interview.onboard_date and interview.onboard_department:
        return '已入职'

    if interview.offer_issued and interview.offer_date and interview.offer_department and interview.offer_onboard_plan_date:
        return '已发offer'

    # 以下为原有轮次状态计算逻辑
    # 一面
    if interview.round1_result:
        if interview.round1_result == '未通过':
            return '一面面试未通过'
        elif interview.round1_result == '通过':
            # 看二面
            if not interview.round2_result:
                return '一面面试通过'
    else:
        return '待面试'

    # 二面
    if interview.round2_result:
        if interview.round2_result == '未通过':
            return '二面面试未通过'
        elif interview.round2_result == '通过':
            if not interview.round3_enabled:
                return '面试通过'
            # 有三面
            if not interview.round3_result:
                return '二面面试通过'
    else:
        return '一面面试通过'

    # 三面
    if interview.round3_result:
        if interview.round3_result == '未通过':
            return '三面面试未通过'
        elif interview.round3_result == '通过':
            return '面试通过'

    return interview.status or '待面试'


@app.route('/api/interviews/<int:interview_id>', methods=['GET'])
def get_interview(interview_id):
    """获取单条面试记录详情"""
    session = get_db_session()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({'success': False, 'message': '面试记录不存在'}), 404
        return jsonify({'success': True, 'data': interview.to_dict()})
    finally:
        session.close()


@app.route('/api/interviews/<int:interview_id>', methods=['PUT'])
def update_interview(interview_id):
    """更新面试流程详情"""
    data = request.json or {}
    session = get_db_session()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({'success': False, 'message': '面试记录不存在'}), 404

        # 更新各轮信息
        interview.round1_interviewer = data.get('round1_interviewer')
        interview.round1_time = data.get('round1_time')
        interview.round1_result = data.get('round1_result')

        interview.round2_interviewer = data.get('round2_interviewer')
        interview.round2_time = data.get('round2_time')
        interview.round2_result = data.get('round2_result')

        interview.round3_enabled = 1 if data.get('round3_enabled') else 0
        interview.round3_interviewer = data.get('round3_interviewer')
        interview.round3_time = data.get('round3_time')
        interview.round3_result = data.get('round3_result')

        # 分轮次面试评价
        interview.round1_comment = data.get('round1_comment')
        interview.round2_comment = data.get('round2_comment')
        interview.round3_comment = data.get('round3_comment')

        # AI 分析结果（只读展示，但需要持久化）
        interview.round1_ai_result = data.get('round1_ai_result')
        interview.round2_ai_result = data.get('round2_ai_result')
        interview.round3_ai_result = data.get('round3_ai_result')

        # 应聘岗位（同时同步到简历）
        applied_position = data.get('applied_position')
        if applied_position is not None:
            interview.applied_position = applied_position or None
            try:
                resume = session.query(Resume).filter(Resume.id == interview.resume_id).first()
                if resume:
                    resume.applied_position = applied_position or None
            except Exception as _:
                pass

        # Offer 与入职信息
        interview.offer_issued = 1 if data.get('offer_issued') else 0
        interview.offer_date = data.get('offer_date')
        interview.offer_department = data.get('offer_department')
        interview.offer_onboard_plan_date = data.get('offer_onboard_plan_date')

        interview.onboard = 1 if data.get('onboard') else 0
        interview.onboard_date = data.get('onboard_date')
        interview.onboard_department = data.get('onboard_department')

        # 自动计算状态
        interview.status = _calc_interview_status(interview)

        session.commit()
        return jsonify({'success': True, 'data': interview.to_dict()})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'更新面试记录失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/interviews/resume-ids', methods=['GET'])
def get_interview_resume_ids():
    """返回所有已邀约面试的 resume_id 列表，用于前端标记“已邀约”"""
    session = get_db_session()
    try:
        ids = session.query(Interview.resume_id).distinct().all()
        id_list = [row[0] for row in ids]
        return jsonify({'success': True, 'data': id_list})
    finally:
        session.close()


@app.route('/api/interviews/<int:interview_id>/upload-doc', methods=['POST'])
def upload_interview_doc(interview_id):
    """上传面试文档（录音逐字稿等），按轮次区分"""
    session = get_db_session()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({'success': False, 'message': '面试记录不存在'}), 404

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未找到上传文件'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        # 轮次：1/2/3
        round_str = request.form.get('round')
        if round_str not in ('1', '2', '3'):
            return jsonify({'success': False, 'message': '缺少或错误的轮次参数'}), 400

        # 保存到上传目录
        upload_folder = os.path.join(app.static_folder, 'interview_docs')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(f"interview_{interview_id}_round{round_str}_{file.filename}")
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # 保存相对路径（供前端访问）
        rel_path = f"interview_docs/{filename}"
        if round_str == '1':
            interview.round1_doc_path = rel_path
        elif round_str == '2':
            interview.round2_doc_path = rel_path
        else:
            interview.round3_doc_path = rel_path
        session.commit()

        return jsonify({'success': True, 'data': interview.to_dict()})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'上传录音失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/interviews/export', methods=['POST'])
def export_interviews():
    """导出面试流程：选中或全部"""
    try:
        data = request.json or {}
        interview_ids = data.get('interview_ids', [])

        session = get_db_session()
        if interview_ids:
            interviews = session.query(Interview).filter(Interview.id.in_(interview_ids)).all()
        else:
            interviews = session.query(Interview).order_by(Interview.update_time.desc()).all()

        # 构造简历映射，用于导出时生成身份验证码
        resume_ids = [iv.resume_id for iv in interviews]
        resumes = session.query(Resume).filter(Resume.id.in_(resume_ids)).all() if resume_ids else []
        resume_map = {r.id: r for r in resumes}
        session.close()

        if not interviews:
            return jsonify({'success': False, 'message': '没有可导出的面试记录'}), 400

        file_path = export_interviews_to_excel(interviews, resume_map)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'面试流程导出_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


@app.route('/api/interviews/<int:interview_id>/analyze-doc', methods=['POST'])
def analyze_interview_doc(interview_id):
    """
    使用AI对面试文档（录音逐字稿等）进行分析
    请求体: { "round": 1|2|3 }
    """
    try:
        data = request.json or {}
        round_str = str(data.get('round') or '')
        if round_str not in ('1', '2', '3'):
            return jsonify({'success': False, 'message': '缺少或错误的轮次参数'}), 400

        session = get_db_session()
        interview = session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            session.close()
            return jsonify({'success': False, 'message': '面试记录不存在'}), 404

        # 选择对应轮次的文档路径
        doc_path = None
        if round_str == '1':
            doc_path = interview.round1_doc_path
        elif round_str == '2':
            doc_path = interview.round2_doc_path
        else:
            doc_path = interview.round3_doc_path

        if not doc_path:
            session.close()
            return jsonify({'success': False, 'message': '当前轮次暂无文档可供分析'}), 400

        file_path = os.path.join(app.static_folder, doc_path)
        if not os.path.exists(file_path):
            session.close()
            return jsonify({'success': False, 'message': '文档文件不存在，请重新上传'}), 400

        # 提取文档文本
        try:
            doc_text = extract_text(file_path)
        except Exception as e:
            session.close()
            return jsonify({'success': False, 'message': f'文档内容提取失败: {str(e)}'}), 500

        if not doc_text:
            session.close()
            return jsonify({'success': False, 'message': '文档内容为空，无法分析'}), 400

        # 检查AI配置
        ai_enabled = app.config.get('AI_ENABLED', True)
        ai_api_key = app.config.get('AI_API_KEY', '')
        ai_model = app.config.get('AI_MODEL', 'gpt-3.5-turbo')
        ai_api_base = app.config.get('AI_API_BASE', '')

        if not ai_enabled or not ai_api_key:
            session.close()
            return jsonify({'success': False, 'message': 'AI功能未启用或未配置API密钥，请在设置中配置AI'}), 400

        # 使用AI进行面试文档分析
        from utils.ai_extractor import AIExtractor
        ai_extractor = AIExtractor(
            api_key=ai_api_key,
            api_base=ai_api_base if ai_api_base else None,
            model=ai_model
        )

        # 读取岗位信息（用于结合岗位要求分析）
        position_info_text = ""
        try:
            resume = session.query(Resume).filter(Resume.id == interview.resume_id).first()
            if resume and resume.applied_position:
                position = session.query(Position).filter(Position.position_name == resume.applied_position).first()
                if position:
                    position_info_text = f"""
【岗位信息】
岗位名称：{position.position_name}
工作内容：{position.work_content or '未填写'}
任职资格：{position.job_requirements or '未填写'}
核心需求：{position.core_requirements or '未填写'}
"""
        except Exception as _:
            position_info_text = ""

        # 构建分析提示词
        round_name = {'1': '一面', '2': '二面', '3': '三面'}[round_str]
        prompt = f"""请你作为一名资深HR，根据以下【{round_name}面试录音逐字稿】内容，以及岗位要求，对候选人的表现进行专业分析。

{position_info_text}

【分析要求】：
1. 用 3-5 条要点总结候选人的核心优点（专业能力、沟通表达、思维方式、价值观等）。
2. 用 3-5 条要点指出候选人的主要不足或风险点。
3. 给出一个综合评价结论（适合/可考虑/不太适合），并简要说明原因。
4. 结合上面的岗位信息，特别指出候选人与岗位在关键要求上的高度匹配点和明显不匹配点。
5. 给出5个可用于下一轮面试的重点追问问题，问题要结合本轮表现和岗位要求设计。

【面试逐字稿】：
{doc_text}

请用中文输出，采用以下JSON格式返回（不要包含额外解释文字）：
{{
  "summary": "整体概括（3-5句话）",
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "conclusion": "综合结论，例如：总体匹配度较高，建议进入下一轮/可以考虑/不太适合等",
  "next_questions": ["下一轮追问问题1", "下一轮追问问题2"]
}}"""

        try:
            response_text = ai_extractor._call_ai_api(prompt)

            # 解析JSON
            import re
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = {
                    'summary': response_text[:500] if len(response_text) > 500 else response_text,
                    'strengths': [],
                    'weaknesses': [],
                    'conclusion': '',
                    'next_questions': []
                }

            session.close()
            return jsonify({'success': True, 'data': analysis})
        except Exception as e:
            session.close()
            return jsonify({'success': False, 'message': f'AI分析失败: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'分析请求失败: {str(e)}'}), 500


@app.route('/api/interviews/<int:interview_id>/analysis-pdf', methods=['POST'])
def export_interview_round_analysis_pdf(interview_id):
    """导出单轮面试AI分析结果为PDF"""
    try:
        data = request.json or {}
        round_str = str(data.get('round') or '')
        if round_str not in ('1', '2', '3'):
            return jsonify({'success': False, 'message': '缺少或错误的轮次参数'}), 400

        session = get_db_session()
        try:
            interview = session.query(Interview).filter(Interview.id == interview_id).first()
        finally:
            session.close()

        if not interview:
            return jsonify({'success': False, 'message': '面试记录不存在'}), 404

        # 选择对应轮的AI分析文本（优先使用数据库中的内容，如为空则尝试使用前端传来的analysis_text）
        client_text = data.get('analysis_text') or ''
        if round_str == '1':
            analysis_text = interview.round1_ai_result or client_text
            round_name = '一面'
        elif round_str == '2':
            analysis_text = interview.round2_ai_result or client_text
            round_name = '二面'
        else:
            analysis_text = interview.round3_ai_result or client_text
            round_name = '三面'

        if not analysis_text:
            return jsonify({'success': False, 'message': '当前轮次暂无AI分析结果，请先执行AI分析'}), 400

        file_path = export_interview_round_analysis_to_pdf(interview, round_name, analysis_text)
        download_name = f'{round_name}面试反馈报告_{interview.name or interview_id}.pdf'
        return send_file(file_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({'success': False, 'message': f'导出AI分析报告失败: {str(e)}'}), 500

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """获取AI配置（不返回密钥）"""
    ai_enabled = app.config.get('AI_ENABLED', True)
    ai_api_key = app.config.get('AI_API_KEY', '')
    # 检查AI是否真正可用（启用且有API密钥）
    ai_available = ai_enabled and bool(ai_api_key)
    
    return jsonify({
        'success': True,
        'data': {
            'ai_enabled': ai_enabled,
            'ai_available': ai_available,  # 新增：AI是否真正可用
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

@app.route('/api/resumes/<int:resume_id>/match-analysis', methods=['POST'])
def analyze_resume_match(resume_id):
    """分析简历与岗位的匹配度"""
    try:
        data = request.json
        applied_position = data.get('applied_position', '').strip()
        
        if not applied_position:
            return jsonify({
                'success': False,
                'message': '请先选择应聘岗位'
            }), 400
        
        # 获取简历信息
        session = get_db_session()
        resume = session.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            session.close()
            return jsonify({
                'success': False,
                'message': '简历不存在'
            }), 404
        
        # 获取岗位信息
        position = session.query(Position).filter(Position.position_name == applied_position).first()
        if not position:
            session.close()
            return jsonify({
                'success': False,
                'message': '岗位不存在，请先在岗位目录中添加该岗位'
            }), 404
        
        session.close()
        
        # 检查AI配置
        ai_enabled = app.config.get('AI_ENABLED', True)
        ai_api_key = app.config.get('AI_API_KEY', '')
        ai_model = app.config.get('AI_MODEL', 'gpt-3.5-turbo')
        ai_api_base = app.config.get('AI_API_BASE', '')
        
        if not ai_enabled or not ai_api_key:
            return jsonify({
                'success': False,
                'message': 'AI功能未启用或未配置API密钥，请在设置中配置AI'
            }), 400
        
        # 使用AI进行匹配度分析
        from utils.ai_extractor import AIExtractor
        ai_extractor = AIExtractor(
            api_key=ai_api_key,
            api_base=ai_api_base if ai_api_base else None,
            model=ai_model
        )
        
        # 构建分析提示
        resume_info = f"""
姓名：{resume.name or '未知'}
性别：{resume.gender or '未知'}
年龄：{resume.age or '未知'}
学历：{resume.highest_education or '未知'}
毕业学校：{resume.school or '未知'}
专业：{resume.major or '未知'}
工龄：{resume.earliest_work_year and (datetime.now().year - resume.earliest_work_year) or '未知'}年
工作经历：{json.dumps(resume.work_experience or [], ensure_ascii=False, indent=2)}
"""
        
        position_info = f"""
岗位名称：{position.position_name}
工作内容：{position.work_content or '未填写'}
任职资格：{position.job_requirements or '未填写'}
核心需求：{position.core_requirements or '未填写'}
"""
        
        prompt = f"""请分析以下简历与岗位的匹配度，并给出详细的分析报告。

【简历信息】
{resume_info}

【岗位要求】
{position_info}

请从以下维度进行分析：
1. 教育背景匹配度（学历、学校、专业）
2. 工作经验匹配度（工作年限、工作内容、岗位相关性）
3. 技能匹配度（根据工作经历推断的技能）
4. 综合匹配度评分（0-100分）

请以JSON格式返回分析结果，格式如下：
{{
    "match_score": 85,
    "match_level": "高度匹配",
    "detailed_analysis": "详细的分析说明...",
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["建议1", "建议2"]
}}

其中：
- match_score: 匹配度分数（0-100）
- match_level: 匹配等级（高度匹配/中等匹配/低度匹配）
- detailed_analysis: 详细分析说明（200-500字）
- strengths: 优势匹配点列表
- weaknesses: 不足匹配点列表
- suggestions: 改进建议列表

请只返回JSON格式，不要包含其他文字说明。"""
        
        try:
            response_text = ai_extractor._call_ai_api(prompt)
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    # 如果找不到JSON，尝试直接解析
                    analysis_result = json.loads(response_text)
            except json.JSONDecodeError:
                # 如果解析失败，返回一个默认结构
                analysis_result = {
                    'match_score': 50,
                    'match_level': '中等匹配',
                    'detailed_analysis': response_text[:500] if len(response_text) > 500 else response_text,
                    'strengths': [],
                    'weaknesses': [],
                    'suggestions': []
                }
            
            # 对匹配得分进行“温和放宽”，避免评分过于严苛
            # 原始得分区间 0-100，转换为约 50-100 的区间，更贴近日常使用场景
            try:
                raw_score = analysis_result.get('match_score')
                if raw_score is None:
                    raw_score = 60
                raw_score = float(raw_score)
                # 简单线性放宽：new = raw * 0.7 + 30，限制在 [50, 100]
                new_score = int(max(50, min(100, raw_score * 0.7 + 30)))
                analysis_result['match_score'] = new_score

                # 根据调整后的得分重新划分匹配等级
                # ≥80：高匹配度；≥60：中匹配度；<60：低匹配度
                if new_score >= 80:
                    level = '高度匹配'
                elif new_score >= 60:
                    level = '中等匹配'
                else:
                    level = '低度匹配'
                analysis_result['match_level'] = level
            except Exception:
                # 若转换失败，则保持原始结果
                pass

            # 同步匹配结果到面试流程（如有对应的面试记录）
            try:
                session_sync = get_db_session()
                interviews = session_sync.query(Interview).filter(Interview.resume_id == resume_id).all()
                if interviews:
                    for it in interviews:
                        it.match_score = analysis_result.get('match_score')
                        it.match_level = analysis_result.get('match_level')
                    session_sync.commit()
                session_sync.close()
            except Exception as sync_err:
                # 不影响主流程，仅打印日志
                print(f"同步匹配结果到面试流程失败: {sync_err}")
            
            return jsonify({
                'success': True,
                'data': analysis_result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'AI分析失败: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

