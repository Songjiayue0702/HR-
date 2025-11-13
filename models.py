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
            'school_code': self.school_code,
            'school_match_status': self.school_match_status,
            'school_confidence': self.school_confidence,
            'major': self.major,
            'major_original': self.major_original,
            'major_code': self.major_code,
            'major_match_status': self.major_match_status,
            'major_confidence': self.major_confidence,
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

def get_db_session():
    """获取数据库会话"""
    return Session()

