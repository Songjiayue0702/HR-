"""
数据模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config
import json
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class Resume(Base):
    """简历数据模型"""
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_time = Column(DateTime, default=datetime.now)
    
    # 基本信息
    name = Column(String(100))
    gender = Column(String(10))
    birth_year = Column(Integer)
    earliest_work_year = Column(Integer)  # 最早工作年份
    age = Column(Integer)
    age_from_resume = Column(Integer)  # 从简历中提取的原始年龄
    phone = Column(String(50))
    email = Column(String(100))
    
    # 教育信息
    highest_education = Column(String(50))
    school = Column(String(200))
    school_original = Column(String(200))  # 原始学校名称
    school_code = Column(String(100))  # 学校代码
    school_match_status = Column(String(50))  # 匹配状态：完全匹配/多项选择/匹配失败/未校验
    school_confidence = Column(Float)  # 置信度
    
    major = Column(String(200))
    major_original = Column(String(200))  # 原始专业名称
    major_code = Column(String(100))  # 专业代码
    major_match_status = Column(String(50))
    major_confidence = Column(Float)

    applied_position = Column(String(200))
    
    # 匹配度分析结果（最后一次分析的岗位匹配度）
    match_score = Column(Integer)  # 匹配度分数（0-100）
    match_level = Column(String(50))  # 匹配等级（高度匹配/中等匹配/低度匹配）
    match_position = Column(String(200))  # 匹配度分析对应的岗位名称
    
    # 工作经历（JSON格式存储）
    work_experience = Column(JSON)
    
    # 解析状态
    parse_status = Column(String(50), default='pending')  # pending/success/failed
    parse_time = Column(DateTime)
    error_message = Column(Text)
    
    # 查重信息
    duplicate_status = Column(String(50))  # 重复状态：None/重复简历
    duplicate_similarity = Column(Float)  # 重合度（0-100）
    duplicate_resume_id = Column(Integer)  # 匹配到的重复简历ID
    
    # 原始文本内容
    raw_text = Column(Text)
    
    # 操作记录字段
    created_by = Column(String(100))  # 创建者（上传者）
    updated_by = Column(String(100))  # 最后更新者
    created_at = Column(DateTime, default=datetime.now)  # 创建时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'name': self.name,
            'gender': self.gender,
            'birth_year': self.birth_year,
            'earliest_work_year': self.earliest_work_year,
            'age': self.age,
            'age_from_resume': self.age_from_resume,
            'phone': self.phone,
            'email': self.email,
            'highest_education': self.highest_education,
            'school': self.school,
            'school_original': self.school_original,
            'major': self.major,
            'major_original': self.major_original,
            'applied_position': self.applied_position,
            'match_score': self.match_score,
            'match_level': self.match_level,
            'match_position': self.match_position,
            'work_experience': self.work_experience,
            'parse_status': self.parse_status,
            'parse_time': self.parse_time.isoformat() if self.parse_time else None,
            'error_message': self.error_message,
            'duplicate_status': self.duplicate_status,
            'duplicate_similarity': self.duplicate_similarity,
            'duplicate_resume_id': self.duplicate_resume_id,
            'raw_text': self.raw_text,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 数据库初始化
engine = create_engine(f'sqlite:///{Config.DATABASE_PATH}', echo=False)

def init_database():
    """初始化数据库，创建所有表"""
    try:
        Base.metadata.create_all(engine)
        print("✓ 数据库表已创建")
    except Exception as e:
        print(f"✗ 创建数据库表失败: {e}")
        raise

def migrate_database():
    """迁移数据库，添加新字段（仅在表存在时）"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(resumes)"))
            columns = {row[1] for row in result}
            if 'phone' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN phone VARCHAR(50)"))
            if 'email' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN email VARCHAR(100)"))
            if 'applied_position' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN applied_position VARCHAR(200)"))
            if 'earliest_work_year' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN earliest_work_year INTEGER"))
            if 'age_from_resume' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN age_from_resume INTEGER"))
            if 'duplicate_status' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN duplicate_status VARCHAR(50)"))
            if 'duplicate_similarity' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN duplicate_similarity FLOAT"))
            if 'duplicate_resume_id' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN duplicate_resume_id INTEGER"))
            if 'match_score' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN match_score INTEGER"))
            if 'match_level' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN match_level VARCHAR(50)"))
            if 'match_position' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN match_position VARCHAR(200)"))
            if 'created_by' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN created_by VARCHAR(100)"))
            if 'updated_by' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN updated_by VARCHAR(100)"))
            if 'created_at' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN created_at DATETIME"))
            if 'updated_at' not in columns:
                conn.execute(text("ALTER TABLE resumes ADD COLUMN updated_at DATETIME"))
            conn.commit()
            
            # 为 positions 表添加字段（先检查表是否存在）
            try:
                # 检查表是否存在
                conn.execute(text("SELECT 1 FROM positions LIMIT 1"))
                # 表存在，检查并添加字段
                result = conn.execute(text("PRAGMA table_info(positions)"))
                columns = {row[1] for row in result}
                if 'created_by' not in columns:
                    conn.execute(text("ALTER TABLE positions ADD COLUMN created_by VARCHAR(100)"))
                if 'updated_by' not in columns:
                    conn.execute(text("ALTER TABLE positions ADD COLUMN updated_by VARCHAR(100)"))
                if 'created_at' not in columns:
                    conn.execute(text("ALTER TABLE positions ADD COLUMN created_at DATETIME"))
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE positions ADD COLUMN updated_at DATETIME"))
                conn.commit()
            except Exception:
                # 表不存在，稍后会在初始化时创建
                pass
            
            # 为 interviews 表添加字段（先检查表是否存在）
            try:
                # 检查表是否存在
                conn.execute(text("SELECT 1 FROM interviews LIMIT 1"))
                # 表存在，检查并添加字段
                result = conn.execute(text("PRAGMA table_info(interviews)"))
                columns = {row[1] for row in result}
                if 'created_by' not in columns:
                    conn.execute(text("ALTER TABLE interviews ADD COLUMN created_by VARCHAR(100)"))
                if 'updated_by' not in columns:
                    conn.execute(text("ALTER TABLE interviews ADD COLUMN updated_by VARCHAR(100)"))
                if 'created_at' not in columns:
                    conn.execute(text("ALTER TABLE interviews ADD COLUMN created_at DATETIME"))
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE interviews ADD COLUMN updated_at DATETIME"))
                if 'analyzed_by' not in columns:
                    conn.execute(text("ALTER TABLE interviews ADD COLUMN analyzed_by VARCHAR(100)"))
                conn.commit()
            except Exception:
                # 表不存在，稍后会在初始化时创建
                pass
    except Exception as e:
        print(f"警告: 数据库迁移时出错（可能表不存在）: {e}")
        # 不抛出异常，让应用继续启动

Session = sessionmaker(bind=engine)

class Position(Base):
    """岗位目录数据模型"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_name = Column(String(200), nullable=False)  # 岗位名称
    work_content = Column(Text)  # 工作内容
    job_requirements = Column(Text)  # 任职资格
    core_requirements = Column(Text)  # 核心需求
    create_time = Column(DateTime, default=datetime.now)  # 创建时间
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间
    
    # 操作记录字段
    created_by = Column(String(100))  # 创建者
    updated_by = Column(String(100))  # 最后更新者
    created_at = Column(DateTime, default=datetime.now)  # 创建时间（与create_time保持一致）
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间（与update_time保持一致）
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'position_name': self.position_name,
            'work_content': self.work_content,
            'job_requirements': self.job_requirements,
            'core_requirements': self.core_requirements,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Interview(Base):
    """面试流程数据模型"""
    __tablename__ = 'interviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, nullable=False)  # 关联的简历ID
    name = Column(String(100))  # 候选人姓名（冗余，便于直接显示）
    applied_position = Column(String(200))  # 应聘岗位（冗余）
    identity_code = Column(String(200))  # 身份验证码（冗余，用于绑定和查找）

    # 简历匹配度
    match_score = Column(Integer)  # 匹配度分数
    match_level = Column(String(50))  # 匹配等级（高度匹配/中等匹配/低度匹配等）

    # 面试流程状态（根据各轮结果自动推导）
    status = Column(String(50), default='待面试')

    # 一面
    round1_interviewer = Column(String(100))
    round1_time = Column(String(50))  # 直接存字符串，前端控制格式
    round1_result = Column(String(50))  # 通过/未通过/待定 等

    # 二面
    round2_interviewer = Column(String(100))
    round2_time = Column(String(50))
    round2_result = Column(String(50))

    # 三面
    round3_enabled = Column(Integer, default=0)  # 0: 无三面, 1: 有三面
    round3_interviewer = Column(String(100))
    round3_time = Column(String(50))
    round3_result = Column(String(50))

    # 分轮次面试评价与文档（录音逐字稿等）
    round1_comment = Column(Text)
    round2_comment = Column(Text)
    round3_comment = Column(Text)

    round1_doc_path = Column(String(500))  # 一面文档（录音逐字稿等）
    round2_doc_path = Column(String(500))  # 二面文档
    round3_doc_path = Column(String(500))  # 三面文档
    
    # 面试评价填写链接token（用于生成邀请链接）
    round1_comment_token = Column(String(100))  # 一面评价填写token
    round2_comment_token = Column(String(100))  # 二面评价填写token
    round3_comment_token = Column(String(100))  # 三面评价填写token

    # AI 分析结果（按轮次）
    round1_ai_result = Column(Text)
    round2_ai_result = Column(Text)
    round3_ai_result = Column(Text)

    # Offer 与入职信息
    offer_issued = Column(Integer, default=0)  # 是否发放offer：0 否，1 是
    offer_date = Column(String(50))            # offer 发放日期
    offer_department = Column(String(200))     # 拟入职架构
    offer_onboard_plan_date = Column(String(50))  # 拟入职日期

    onboard = Column(Integer, default=0)       # 是否入职：0 否，1 是
    onboard_date = Column(String(50))          # 实际入职日期
    onboard_department = Column(String(200))   # 入职架构
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 操作记录字段
    created_by = Column(String(100))  # 创建者（邀约发起者）
    updated_by = Column(String(100))  # 最后更新者
    created_at = Column(DateTime, default=datetime.now)  # 创建时间（与create_time保持一致）
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间（与update_time保持一致）
    
    # 简历分析记录字段（用于记录谁进行了分析）
    analyzed_by = Column(String(100))  # 分析者（进行简历分析的用户）

    # 面试登记表字段
    registration_form_fill_date = Column(String(50))  # 填写日期（只读，自动生成）
    registration_form_contact = Column(String(50))  # 联系方式（可修改）
    registration_form_email = Column(String(100))  # 邮箱（可修改）
    registration_form_birth_date = Column(String(50))  # 出生日期（可修改）
    registration_form_ethnicity = Column(String(50))  # 民族
    registration_form_marital_status = Column(String(50))  # 婚姻状况（未婚、已婚、离异）
    registration_form_has_children = Column(String(10))  # 有无子女（有、无）
    registration_form_origin = Column(String(200))  # 籍贯
    registration_form_id_card = Column(String(50))  # 身份证号（选填）
    registration_form_first_work_date = Column(String(50))  # 首次工作时间
    registration_form_recent_work_experience = Column(JSON)  # 近两份工作经历（JSON格式）
    registration_form_education = Column(Text)  # 最高学历院校及专业及起始时间
    registration_form_hobbies = Column(Text)  # 个人爱好及特长
    registration_form_current_salary = Column(String(50))  # 原月薪
    registration_form_expected_salary = Column(String(50))  # 期望月薪
    registration_form_available_date = Column(String(50))  # 最快到岗时间
    registration_form_address_province = Column(String(50))  # 现住址-省
    registration_form_address_city = Column(String(50))  # 现住址-市
    registration_form_address_district = Column(String(50))  # 现住址-区
    registration_form_address_detail = Column(String(500))  # 现住址-详细地址
    registration_form_can_travel = Column(String(10))  # 能否出差（是、否）
    registration_form_consideration_factors = Column(Text)  # 考虑新公司的主要因素（排序后的JSON字符串）
    registration_form_token = Column(String(100))  # 面试登记表填写token（用于生成邀请链接）
    registration_form_education_start_date = Column(String(50))
    registration_form_education_end_date = Column(String(50))
    registration_form_institution = Column(String(200))
    registration_form_major = Column(String(200))
    registration_form_degree = Column(String(100))
    registration_form_full_time = Column(String(20))

    def _parse_json_field(self, value, default):
        if not value:
            return default
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return default

    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'name': self.name,
            'applied_position': self.applied_position,
            'identity_code': self.identity_code,
            'match_score': self.match_score,
            'match_level': self.match_level,
            'status': self.status,
            'round1_interviewer': self.round1_interviewer,
            'round1_time': self.round1_time,
            'round1_result': self.round1_result,
            'round2_interviewer': self.round2_interviewer,
            'round2_time': self.round2_time,
            'round2_result': self.round2_result,
            'round3_enabled': self.round3_enabled,
            'round3_interviewer': self.round3_interviewer,
            'round3_time': self.round3_time,
            'round3_result': self.round3_result,
            'round1_comment': self.round1_comment,
            'round2_comment': self.round2_comment,
            'round3_comment': self.round3_comment,
            'round1_doc_path': self.round1_doc_path,
            'round2_doc_path': self.round2_doc_path,
            'round3_doc_path': self.round3_doc_path,
            'round1_comment_token': self.round1_comment_token,
            'round2_comment_token': self.round2_comment_token,
            'round3_comment_token': self.round3_comment_token,
            'round1_ai_result': self.round1_ai_result,
            'round2_ai_result': self.round2_ai_result,
            'round3_ai_result': self.round3_ai_result,
            'offer_issued': self.offer_issued,
            'offer_date': self.offer_date,
            'offer_department': self.offer_department,
            'offer_onboard_plan_date': self.offer_onboard_plan_date,
            'onboard': self.onboard,
            'onboard_date': self.onboard_date,
            'onboard_department': self.onboard_department,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analyzed_by': self.analyzed_by,
            # 面试登记表字段
            'registration_form_fill_date': self.registration_form_fill_date,
            'registration_form_contact': self.registration_form_contact,
            'registration_form_email': self.registration_form_email,
            'registration_form_birth_date': self.registration_form_birth_date,
            'registration_form_ethnicity': self.registration_form_ethnicity,
            'registration_form_marital_status': self.registration_form_marital_status,
            'registration_form_has_children': self.registration_form_has_children,
            'registration_form_origin': self.registration_form_origin,
            'registration_form_id_card': self.registration_form_id_card,
            'registration_form_first_work_date': self.registration_form_first_work_date,
            'registration_form_recent_work_experience': self._parse_json_field(self.registration_form_recent_work_experience, []),
            'registration_form_education': self.registration_form_education,
            'registration_form_hobbies': self.registration_form_hobbies,
            'registration_form_current_salary': self.registration_form_current_salary,
            'registration_form_expected_salary': self.registration_form_expected_salary,
            'registration_form_available_date': self.registration_form_available_date,
            'registration_form_address_province': self.registration_form_address_province,
            'registration_form_address_city': self.registration_form_address_city,
            'registration_form_address_district': self.registration_form_address_district,
            'registration_form_address_detail': self.registration_form_address_detail,
            'registration_form_can_travel': self.registration_form_can_travel,
            'registration_form_consideration_factors': self._parse_json_field(self.registration_form_consideration_factors, []),
            'registration_form_education_start_date': self.registration_form_education_start_date,
            'registration_form_education_end_date': self.registration_form_education_end_date,
            'registration_form_institution': self.registration_form_institution,
            'registration_form_major': self.registration_form_major,
            'registration_form_degree': self.registration_form_degree,
            'registration_form_full_time': self.registration_form_full_time,
            'registration_form_token': self.registration_form_token,
        }

class GlobalAIConfig(Base):
    """全局AI配置数据模型（管理员设置）"""
    __tablename__ = 'global_ai_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 配置项（单例模式，只保留一条记录）
    ai_enabled = Column(Integer, default=1)  # 是否启用AI：1 启用，0 禁用
    ai_api_key = Column(Text)  # API密钥（加密存储）
    ai_api_base = Column(String(500))  # API基础URL
    ai_model = Column(String(100), default='gpt-3.5-turbo')  # AI模型
    
    # 操作记录
    created_by = Column(String(100))  # 创建者（管理员用户名）
    updated_by = Column(String(100))  # 最后更新者
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self, include_key=False):
        """
        转换为字典
        
        Args:
            include_key: 是否包含API密钥（解密后）
        """
        result = {
            'id': self.id,
            'ai_enabled': bool(self.ai_enabled),
            'ai_api_base': self.ai_api_base,
            'ai_model': self.ai_model,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_key:
            # 解密API密钥
            from utils.encryption import decrypt_value
            result['ai_api_key'] = decrypt_value(self.ai_api_key) if self.ai_api_key else ''
        else:
            # 不返回密钥，只返回是否已设置
            result['ai_api_key_set'] = bool(self.ai_api_key)
        
        return result

class User(Base):
    """用户数据模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)  # 用户名
    password_hash = Column(String(255), nullable=False)  # 密码哈希
    role = Column(String(50), nullable=False, default='employee')  # 角色：admin（管理员）、manager（主管）、employee（员工）
    real_name = Column(String(100))  # 真实姓名
    department = Column(String(200))  # 部门
    group_name = Column(String(200))  # 小组名称（用于数据统计）
    is_active = Column(Integer, default=1)  # 是否激活：1 激活，0 禁用
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'real_name': self.real_name,
            'department': self.department,
            'group_name': self.group_name,
            'is_active': self.is_active,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
    
    def has_permission(self, permission):
        """检查权限"""
        if self.role == 'admin':
            return True  # 管理员拥有所有权限
        elif self.role == 'manager':
            # 主管权限
            return permission in ['view_department', 'view_group', 'view_personal']
        else:  # employee
            # 员工权限
            return permission == 'view_personal'

# 确保表存在
Base.metadata.create_all(engine)

# 检查users表是否存在，如果不存在则创建；并确保默认管理员账户存在
with engine.connect() as conn:
    try:
        conn.execute(text("SELECT 1 FROM users LIMIT 1"))
        # 表已存在，检查是否有admin用户
        session = Session()
        admin_user = session.query(User).filter_by(username='admin').first()
        if not admin_user:
            # 如果没有admin用户，创建默认管理员账户
            admin = User(
                username='admin',
                role='admin',
                real_name='系统管理员',
                is_active=1
            )
            admin.set_password('admin123')  # 默认密码，建议首次登录后修改
            session.add(admin)
            session.commit()
        session.close()
    except Exception:
        # 表不存在，创建表并创建默认管理员账户
        User.__table__.create(engine)
        session = Session()
        admin = User(
            username='admin',
            role='admin',
            real_name='系统管理员',
            is_active=1
        )
        admin.set_password('admin123')  # 默认密码，建议首次登录后修改
        session.add(admin)
        session.commit()
        session.close()

# 检查positions/interviews表是否存在，如果不存在则创建；并做简单列补全
# 注意：这段代码已移至 init_database() 和 migrate_database() 函数中，延迟执行
# 以下代码保留作为备用，但不会在导入时执行
"""
with engine.connect() as conn:
    try:
        conn.execute(text("SELECT 1 FROM positions LIMIT 1"))
    except Exception:
        Position.__table__.create(engine)

    # interviews 表
    try:
        conn.execute(text("SELECT 1 FROM interviews LIMIT 1"))
    except Exception:
        Interview.__table__.create(engine)

    # 简单列补全（避免老库缺少新字段）
    result = conn.execute(text("PRAGMA table_info(interviews)"))
    i_columns = {row[1] for row in result}
    add_cols = []
    if 'match_score' not in i_columns:
        add_cols.append("ADD COLUMN match_score INTEGER")
    if 'match_level' not in i_columns:
        add_cols.append("ADD COLUMN match_level VARCHAR(50)")
    if 'round1_interviewer' not in i_columns:
        add_cols.append("ADD COLUMN round1_interviewer VARCHAR(100)")
    if 'round1_time' not in i_columns:
        add_cols.append("ADD COLUMN round1_time VARCHAR(50)")
    if 'round1_result' not in i_columns:
        add_cols.append("ADD COLUMN round1_result VARCHAR(50)")
    if 'round2_interviewer' not in i_columns:
        add_cols.append("ADD COLUMN round2_interviewer VARCHAR(100)")
    if 'round2_time' not in i_columns:
        add_cols.append("ADD COLUMN round2_time VARCHAR(50)")
    if 'round2_result' not in i_columns:
        add_cols.append("ADD COLUMN round2_result VARCHAR(50)")
    if 'round3_enabled' not in i_columns:
        add_cols.append("ADD COLUMN round3_enabled INTEGER DEFAULT 0")
    if 'round3_interviewer' not in i_columns:
        add_cols.append("ADD COLUMN round3_interviewer VARCHAR(100)")
    if 'round3_time' not in i_columns:
        add_cols.append("ADD COLUMN round3_time VARCHAR(50)")
    if 'round3_result' not in i_columns:
        add_cols.append("ADD COLUMN round3_result VARCHAR(50)")
    if 'round1_comment' not in i_columns:
        add_cols.append("ADD COLUMN round1_comment TEXT")
    if 'round2_comment' not in i_columns:
        add_cols.append("ADD COLUMN round2_comment TEXT")
    if 'round3_comment' not in i_columns:
        add_cols.append("ADD COLUMN round3_comment TEXT")
    if 'round1_doc_path' not in i_columns:
        add_cols.append("ADD COLUMN round1_doc_path VARCHAR(500)")
    if 'round2_doc_path' not in i_columns:
        add_cols.append("ADD COLUMN round2_doc_path VARCHAR(500)")
    if 'round3_doc_path' not in i_columns:
        add_cols.append("ADD COLUMN round3_doc_path VARCHAR(500)")
    if 'round1_comment_token' not in i_columns:
        add_cols.append("ADD COLUMN round1_comment_token VARCHAR(100)")
    if 'round2_comment_token' not in i_columns:
        add_cols.append("ADD COLUMN round2_comment_token VARCHAR(100)")
    if 'round3_comment_token' not in i_columns:
        add_cols.append("ADD COLUMN round3_comment_token VARCHAR(100)")
    if 'round1_ai_result' not in i_columns:
        add_cols.append("ADD COLUMN round1_ai_result TEXT")
    if 'round2_ai_result' not in i_columns:
        add_cols.append("ADD COLUMN round2_ai_result TEXT")
    if 'round3_ai_result' not in i_columns:
        add_cols.append("ADD COLUMN round3_ai_result TEXT")
    if 'offer_issued' not in i_columns:
        add_cols.append("ADD COLUMN offer_issued INTEGER DEFAULT 0")
    if 'offer_date' not in i_columns:
        add_cols.append("ADD COLUMN offer_date VARCHAR(50)")
    if 'offer_department' not in i_columns:
        add_cols.append("ADD COLUMN offer_department VARCHAR(200)")
    if 'offer_onboard_plan_date' not in i_columns:
        add_cols.append("ADD COLUMN offer_onboard_plan_date VARCHAR(50)")
    if 'onboard' not in i_columns:
        add_cols.append("ADD COLUMN onboard INTEGER DEFAULT 0")
    if 'onboard_date' not in i_columns:
        add_cols.append("ADD COLUMN onboard_date VARCHAR(50)")
    if 'onboard_department' not in i_columns:
        add_cols.append("ADD COLUMN onboard_department VARCHAR(200)")
    if 'identity_code' not in i_columns:
        add_cols.append("ADD COLUMN identity_code VARCHAR(200)")
    # 面试登记表字段
    if 'registration_form_fill_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_fill_date VARCHAR(50)")
    if 'registration_form_contact' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_contact VARCHAR(50)")
    if 'registration_form_email' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_email VARCHAR(100)")
    if 'registration_form_birth_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_birth_date VARCHAR(50)")
    if 'registration_form_ethnicity' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_ethnicity VARCHAR(50)")
    if 'registration_form_marital_status' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_marital_status VARCHAR(50)")
    if 'registration_form_has_children' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_has_children VARCHAR(10)")
    if 'registration_form_origin' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_origin VARCHAR(200)")
    if 'registration_form_id_card' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_id_card VARCHAR(50)")
    if 'registration_form_first_work_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_first_work_date VARCHAR(50)")
    if 'registration_form_recent_work_experience' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_recent_work_experience TEXT")
    if 'registration_form_education' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_education TEXT")
    if 'registration_form_hobbies' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_hobbies TEXT")
    if 'registration_form_current_salary' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_current_salary VARCHAR(50)")
    if 'registration_form_expected_salary' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_expected_salary VARCHAR(50)")
    if 'registration_form_available_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_available_date VARCHAR(50)")
    if 'registration_form_address_province' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_address_province VARCHAR(50)")
    if 'registration_form_address_city' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_address_city VARCHAR(50)")
    if 'registration_form_address_district' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_address_district VARCHAR(50)")
    if 'registration_form_address_detail' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_address_detail VARCHAR(500)")
    if 'registration_form_can_travel' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_can_travel VARCHAR(10)")
    if 'registration_form_consideration_factors' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_consideration_factors TEXT")
    if 'registration_form_education_start_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_education_start_date VARCHAR(50)")
    if 'registration_form_education_end_date' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_education_end_date VARCHAR(50)")
    if 'registration_form_institution' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_institution VARCHAR(200)")
    if 'registration_form_major' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_major VARCHAR(200)")
    if 'registration_form_degree' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_degree VARCHAR(100)")
    if 'registration_form_full_time' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_full_time VARCHAR(20)")
    if 'registration_form_token' not in i_columns:
        add_cols.append("ADD COLUMN registration_form_token VARCHAR(100)")

    for clause in add_cols:
        conn.execute(text(f"ALTER TABLE interviews {clause}"))

    conn.commit()
"""

# 延迟初始化：不在导入时执行，而是在应用启动时调用
# 先创建表结构
init_database()

# 然后执行迁移（添加新字段）
migrate_database()

def get_db_session():
    """获取数据库会话"""
    return Session()

