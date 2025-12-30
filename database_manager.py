"""
数据库管理器
支持 Cloudflare D1 和 SQLite 双数据库架构
优先级：D1 > SQLite
"""
import os
import logging
from typing import Optional, Any, Dict, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器，自动选择 D1 或 SQLite（按优先级）"""
    
    def __init__(self):
        self.db_type = None
        self.engine = None
        self.Session = None
        self.d1_db = None
        self.d1_client = None  # D1 HTTP API 客户端
        self.d1_adapter = None
        self._initialized = False
        
    def initialize(self):
        """初始化数据库连接（按优先级：D1 > SQLite）"""
        if self._initialized:
            return
        
        # 优先级 1: 尝试使用 D1
        if self._is_cloudflare_env():
            try:
                logger.info("检测到 Cloudflare D1 环境变量，尝试使用 D1 数据库")
                self._init_d1()
                self._initialized = True
                logger.info(f"✓ 数据库初始化完成，类型: {self.db_type}")
                return
            except Exception as e:
                logger.warning(f"D1 初始化失败: {e}，降级到 SQLite")
        
        # 优先级 2: 使用 SQLite（降级方案）
        try:
            logger.info("使用 SQLite 数据库（降级方案）")
            self._init_sqlite()
            self._initialized = True
            logger.info(f"✓ 数据库初始化完成，类型: {self.db_type}")
        except Exception as e:
            logger.error(f"SQLite 初始化失败: {e}")
            raise
    
    def _is_cloudflare_env(self) -> bool:
        """检查是否在 Cloudflare 环境"""
        # 检查环境变量（支持两种命名方式：CF_* 和 D1_*）
        cf_vars = [
            'CF_ACCOUNT_ID', 'D1_ACCOUNT_ID',
            'CF_API_TOKEN', 'D1_API_TOKEN',
            'CF_D1_DATABASE_ID', 'D1_DATABASE_ID',
            'DB'  # Cloudflare Workers 中的 D1 数据库对象
        ]
        return any(os.environ.get(var) for var in cf_vars) or hasattr(os, 'getenv') and os.getenv('DB')
    
    def _init_d1(self):
        """初始化 Cloudflare D1 数据库（通过 HTTP API）"""
        try:
            # 支持两种环境变量命名方式：CF_* 和 D1_*
            d1_db_id = os.environ.get('CF_D1_DATABASE_ID') or os.environ.get('D1_DATABASE_ID')
            account_id = os.environ.get('CF_ACCOUNT_ID') or os.environ.get('D1_ACCOUNT_ID')
            api_token = os.environ.get('CF_API_TOKEN') or os.environ.get('D1_API_TOKEN')
            
            if not all([d1_db_id, account_id, api_token]):
                raise Exception("D1 数据库配置不完整，需要 D1_ACCOUNT_ID, D1_API_TOKEN, D1_DATABASE_ID")
            
            # 使用 HTTP API 客户端连接 D1
            from d1_http_client import D1HTTPClient
            from d1_sqlalchemy_adapter import D1Engine, D1Session
            
            self.d1_client = D1HTTPClient(account_id, api_token, d1_db_id)
            
            # 测试连接
            if not self.d1_client.test_connection():
                raise Exception("D1 连接测试失败")
            
            # 创建兼容 SQLAlchemy 的 Engine 和 Session
            self.engine = D1Engine(self.d1_client)
            
            # 创建 Session 类（使用 D1Session）
            def make_d1_session():
                return D1Session(self.d1_client)
            
            self.Session = make_d1_session
            self.db_type = 'd1'
            logger.info("D1 数据库已通过 HTTP API 初始化并连接成功")
            
        except ImportError as e:
            logger.error(f"无法导入 D1 模块: {e}")
            raise Exception(f"D1 模块导入失败: {e}")
        except Exception as e:
            logger.warning(f"D1 初始化失败: {e}")
            raise
    
    def _init_sqlite(self):
        """初始化 SQLite 数据库"""
        from config import Config
        
        database_path = os.environ.get('DATABASE_PATH', Config.DATABASE_PATH)
        
        # 创建 SQLite 引擎
        self.engine = create_engine(
            f'sqlite:///{database_path}',
            echo=False,
            poolclass=StaticPool,
            connect_args={'check_same_thread': False}
        )
        
        self.Session = sessionmaker(bind=self.engine)
        self.db_type = 'sqlite'
        logger.info(f"SQLite 数据库已初始化: {database_path}")
    
    def get_session(self):
        """获取数据库会话（D1 或 SQLite）"""
        if not self._initialized:
            self.initialize()
        
        if self.Session:
            return self.Session()
        return None
    
    def execute(self, sql: str, params: tuple = ()) -> Any:
        """执行 SQL 语句（统一接口）"""
        if not self._initialized:
            self.initialize()
        
        if self.db_type == 'd1' and self.d1_client:
            # D1 数据库（通过 HTTP API）
            params_list = list(params) if params else None
            result = self.d1_client.execute(sql, params_list)
            # 返回类似 SQLAlchemy 的结果对象
            from d1_sqlalchemy_adapter import D1ResultProxy
            return D1ResultProxy(result)
        else:
            # SQLite 数据库
            return self._execute_sql(sql, params)
    
    def _execute_sql(self, sql: str, params: tuple = ()) -> Any:
        """执行 SQL 语句（SQLite）"""
        if not self.engine:
            raise Exception("数据库未初始化")
        
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(sql), params)
            else:
                result = conn.execute(text(sql))
            conn.commit()
            return result
    
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        result = {
            'success': False,
            'db_type': self.db_type,
            'message': '',
            'error': None
        }
        
        try:
            if not self._initialized:
                self.initialize()
            
            if self.db_type == 'sqlite':
                # 测试 SQLite 连接
                session = self.get_session()
                if session:
                    session.execute(text('SELECT 1'))
                    session.close()
                    result['success'] = True
                    result['message'] = 'SQLite 连接正常'
                else:
                    result['message'] = '无法创建 SQLite 会话'
            elif self.db_type == 'd1':
                # 测试 D1 连接
                if self.d1_client:
                    if self.d1_client.test_connection():
                        result['success'] = True
                        result['message'] = 'D1 数据库连接正常'
                    else:
                        result['message'] = 'D1 数据库连接测试失败'
                else:
                    result['message'] = 'D1 客户端未初始化'
            else:
                result['message'] = '未知的数据库类型'
                
        except Exception as e:
            result['error'] = str(e)
            result['message'] = f'连接测试失败: {e}'
            logger.error(f"数据库连接测试失败: {e}")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """获取数据库状态信息"""
        status = {
            'initialized': self._initialized,
            'db_type': self.db_type or 'unknown',
            'sqlite_path': None,
            'd1_configured': False,
            'tables': []
        }
        
        if self.db_type == 'sqlite' and self.engine:
            from config import Config
            status['sqlite_path'] = os.environ.get('DATABASE_PATH', Config.DATABASE_PATH)
            
            # 获取表列表
            try:
                inspector = inspect(self.engine)
                status['tables'] = inspector.get_table_names()
            except Exception as e:
                logger.error(f"获取表列表失败: {e}")
        
        elif self.db_type == 'd1':
            status['d1_configured'] = True
            status['d1_db_id'] = os.environ.get('CF_D1_DATABASE_ID') or os.environ.get('D1_DATABASE_ID')
            status['d1_account_id'] = os.environ.get('CF_ACCOUNT_ID') or os.environ.get('D1_ACCOUNT_ID')
        
        return status


# 全局数据库管理器实例
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例（单例模式）"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


def get_db_session():
    """获取数据库会话（兼容现有代码）"""
    manager = get_database_manager()
    return manager.get_session()

