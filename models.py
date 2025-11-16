"""
数据模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

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
            'work_experience': self.work_experience,
            'parse_status': self.parse_status,
            'parse_time': self.parse_time.isoformat() if self.parse_time else None,
            'error_message': self.error_message,
            'duplicate_status': self.duplicate_status,
            'duplicate_similarity': self.duplicate_similarity,
            'duplicate_resume_id': self.duplicate_resume_id,
            'raw_text': self.raw_text
        }

# 数据库初始化
engine = create_engine(f'sqlite:///{Config.DATABASE_PATH}', echo=False)
Base.metadata.create_all(engine)

# 简单的列更新，确保新增字段存在
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
    conn.commit()
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
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'position_name': self.position_name,
            'work_content': self.work_content,
            'job_requirements': self.job_requirements,
            'core_requirements': self.core_requirements,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }

class Interview(Base):
    """面试流程数据模型"""
    __tablename__ = 'interviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, nullable=False)  # 关联的简历ID
    name = Column(String(100))  # 候选人姓名（冗余，便于直接显示）
    applied_position = Column(String(200))  # 应聘岗位（冗余）

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

    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'name': self.name,
            'applied_position': self.applied_position,
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
        }

# 确保表存在
Base.metadata.create_all(engine)

# 检查positions/interviews表是否存在，如果不存在则创建；并做简单列补全
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

    for clause in add_cols:
        conn.execute(text(f"ALTER TABLE interviews {clause}"))

    conn.commit()

def get_db_session():
    """获取数据库会话"""
    return Session()

