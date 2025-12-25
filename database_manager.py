"""
数据库管理器
支持 Cloudflare D1 和 SQLite 双数据库架构
"""
import os
import logging
from typing import Optional, Any, Dict, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器，自动选择 D1 或 SQLite"""
    
    def __init__(self):
        self.db_type = None
        self.engine = None
        self.Session = None
        self.d1_db = None
        self.d1_adapter = None
        self._initialized = False
        
    def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return
        
        try:
            # 检查是否在 Cloudflare Workers 环境
            if self._is_cloudflare_env():
                logger.info("检测到 Cloudflare 环境，尝试使用 D1 数据库")
                self._init_d1()
            else:
                logger.info("使用 SQLite 数据库")
                self._init_sqlite()
            
            self._initialized = True
            logger.info(f"数据库初始化完成，类型: {self.db_type}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            # 降级到 SQLite
            if self.db_type != 'sqlite':
                logger.warning("降级到 SQLite 数据库")
                self._init_sqlite()
                self._initialized = True
    
    def _is_cloudflare_env(self) -> bool:
        """检查是否在 Cloudflare 环境"""
        # 检查环境变量
        cf_vars = [
            'CF_ACCOUNT_ID',
            'CF_API_TOKEN',
            'CF_D1_DATABASE_ID',
            'DB'  # Cloudflare Workers 中的 D1 数据库对象
        ]
        return any(os.environ.get(var) for var in cf_vars) or hasattr(os, 'getenv') and os.getenv('DB')
    
    def _init_d1(self):
        """初始化 Cloudflare D1 数据库"""
        try:
            # 尝试从环境获取 D1 数据库对象
            # 在 Cloudflare Workers 中，DB 对象通过 env 传递
            # 这里我们检查是否有相关的环境变量或全局对象
            
            # 检查是否有 D1 相关的环境变量
            d1_db_id = os.environ.get('CF_D1_DATABASE_ID')
            account_id = os.environ.get('CF_ACCOUNT_ID')
            api_token = os.environ.get('CF_API_TOKEN')
            
            if d1_db_id and account_id and api_token:
                # 使用 Cloudflare API 连接 D1
                logger.info("使用 Cloudflare API 连接 D1 数据库")
                # 注意：实际实现需要根据 Cloudflare API 文档
                # 这里只是示例
                self.db_type = 'd1'
                # 在实际 Cloudflare Workers 环境中，DB 对象会通过 env 传递
                # self.d1_db = env.DB
                # from d1_adapter import D1Adapter
                # self.d1_adapter = D1Adapter(self.d1_db)
            else:
                # 检查是否有全局 DB 对象（在 Workers 环境中）
                # 这通常不会在本地环境存在，所以会降级到 SQLite
                raise Exception("D1 数据库配置不完整")
                
        except Exception as e:
            logger.warning(f"D1 初始化失败: {e}，将使用 SQLite")
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
    
    def get_session(self) -> Optional[Session]:
        """获取数据库会话（SQLite）"""
        if not self._initialized:
            self.initialize()
        
        if self.db_type == 'sqlite' and self.Session:
            return self.Session()
        return None
    
    def execute(self, sql: str, params: tuple = ()) -> Any:
        """执行 SQL 语句（统一接口）"""
        if not self._initialized:
            self.initialize()
        
        if self.db_type == 'd1' and self.d1_adapter:
            # D1 数据库（异步，需要特殊处理）
            # 在实际 Workers 环境中，这应该是异步的
            # 这里返回一个占位符
            logger.warning("D1 执行需要异步环境，当前使用 SQLite")
            return self._execute_sqlite(sql, params)
        else:
            # SQLite 数据库
            return self._execute_sqlite(sql, params)
    
    def _execute_sqlite(self, sql: str, params: tuple = ()) -> Any:
        """执行 SQLite SQL 语句"""
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
                result['success'] = True
                result['message'] = 'D1 数据库已配置（需要 Workers 环境测试）'
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
            status['d1_db_id'] = os.environ.get('CF_D1_DATABASE_ID')
        
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


def get_db_session() -> Optional[Session]:
    """获取数据库会话（兼容现有代码）"""
    manager = get_database_manager()
    return manager.get_session()

