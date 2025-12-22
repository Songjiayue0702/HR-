"""
配置文件
"""
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')

# 确保目录存在
for folder in [UPLOAD_FOLDER, EXPORT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Flask配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = UPLOAD_FOLDER
    DATABASE_PATH = DATABASE_PATH
    EXPORT_FOLDER = EXPORT_FOLDER
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # 外部API验证已移除，统一使用AI API智能识别
    
    # AI辅助解析配置
    AI_ENABLED = os.environ.get('AI_ENABLED', 'true').lower() == 'true'
    AI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY') or os.environ.get('DEEPSEEK_API_KEY') or ''
    AI_API_BASE = os.environ.get('OPENAI_API_BASE') or os.environ.get('AI_API_BASE') or ''  # 如果为空，将根据模型自动选择
    AI_MODEL = os.environ.get('AI_MODEL') or 'gpt-3.5-turbo'  # 可选: gpt-3.5-turbo, gpt-4, gpt-4-turbo, deepseek-chat, deepseek-coder, qwen-turbo, qwen-plus等
    
    # 支持的AI模型列表（用于前端选择）
    AI_MODELS = [
        {'value': 'gpt-3.5-turbo', 'label': 'GPT-3.5 Turbo (OpenAI)', 'provider': 'OpenAI'},
        {'value': 'gpt-4', 'label': 'GPT-4 (OpenAI)', 'provider': 'OpenAI'},
        {'value': 'gpt-4-turbo', 'label': 'GPT-4 Turbo (OpenAI)', 'provider': 'OpenAI'},
        {'value': 'deepseek-chat', 'label': 'DeepSeek Chat', 'provider': 'DeepSeek'},
        {'value': 'deepseek-coder', 'label': 'DeepSeek Coder', 'provider': 'DeepSeek'},
        {'value': 'qwen-turbo', 'label': 'Qwen Turbo (阿里云)', 'provider': 'Alibaba'},
        {'value': 'qwen-plus', 'label': 'Qwen Plus (阿里云)', 'provider': 'Alibaba'},
    ]
    
    # OCR功能已移除，所有文档通过AI API处理
    
    # 教育层级选项（用于面试登记表学历下拉）
    EDUCATION_LEVELS = ['博士', '硕士', '本科', '大专', '高中', '职高', '初中', '其他']

