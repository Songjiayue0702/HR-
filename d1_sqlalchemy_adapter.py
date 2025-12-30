"""
D1 HTTP API 的 SQLAlchemy 兼容适配器
由于 D1 通过 HTTP API 访问，无法直接使用 SQLAlchemy，这里提供一个兼容层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from d1_http_client import D1HTTPClient
from d1_query import D1Query

logger = logging.getLogger(__name__)


class D1Session:
    """
    D1 的 SQLAlchemy Session 兼容类
    将 SQLAlchemy 操作转换为 D1 HTTP API 调用
    """
    
    def __init__(self, d1_client: D1HTTPClient, bind=None, **kwargs):
        self.d1_client = d1_client
        self._d1_results = []
        self.bind = bind
        self._query_cache = {}
    
    def query(self, *entities, **kwargs):
        """创建查询对象（ORM 查询）"""
        from d1_query import D1Query
        return D1Query(entities, self.d1_client)
    
    def execute(self, statement, *args, **kwargs):
        """执行语句"""
        # 处理 SQLAlchemy 的 text 对象
        if hasattr(statement, 'text'):
            sql = statement.text
        elif isinstance(statement, str):
            sql = statement
        else:
            # 对于 ORM 查询，尝试转换为 SQL
            # 这是一个简化实现，可能无法处理所有情况
            try:
                sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
            except:
                sql = str(statement)
        
        # 处理参数
        params = None
        if args and len(args) > 0:
            if isinstance(args[0], (list, tuple)):
                params = list(args[0])
            else:
                params = [args[0]]
        elif 'parameters' in kwargs:
            params = list(kwargs['parameters']) if isinstance(kwargs['parameters'], (list, tuple)) else [kwargs['parameters']]
        
        # 执行 SQL
        try:
            result = self.d1_client.execute(sql, params)
            # 将结果包装为类似 SQLAlchemy 的结果对象
            return D1ResultProxy(result)
        except Exception as e:
            logger.error(f"D1 执行失败: {e}, SQL: {sql}")
            raise
    
    def commit(self):
        """提交事务（D1 HTTP API 中每个请求自动提交）"""
        pass
    
    def rollback(self):
        """回滚事务（D1 HTTP API 不支持，这里是占位）"""
        pass
    
    def close(self):
        """关闭会话"""
        pass


class D1ResultProxy:
    """D1 结果代理类，模拟 SQLAlchemy 的 Result 对象"""
    
    def __init__(self, d1_result: Dict[str, Any]):
        self.d1_result = d1_result
        self._rows = d1_result.get('results', [])
        self._index = 0
    
    def fetchall(self):
        """获取所有结果"""
        return [D1Row(row) for row in self._rows]
    
    def fetchone(self):
        """获取一行结果"""
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return D1Row(row)
        return None
    
    def first(self):
        """获取第一行结果"""
        if self._rows:
            return D1Row(self._rows[0])
        return None
    
    def all(self):
        """获取所有结果"""
        return self.fetchall()
    
    def scalar(self):
        """获取标量值"""
        first = self.first()
        if first:
            # 返回第一个列的值
            return first[0] if hasattr(first, '__getitem__') else first
        return None


class D1Row:
    """D1 行对象，模拟 SQLAlchemy 的 Row 对象"""
    
    def __init__(self, row_data: Dict[str, Any]):
        self._data = row_data
    
    def __getitem__(self, key):
        """通过索引或键访问"""
        if isinstance(key, int):
            # 通过索引访问（按列的顺序）
            values = list(self._data.values())
            return values[key] if key < len(values) else None
        else:
            # 通过键访问
            return self._data.get(key)
    
    def __getattr__(self, name):
        """通过属性访问"""
        return self._data.get(name)
    
    def keys(self):
        """获取所有键"""
        return self._data.keys()
    
    def values(self):
        """获取所有值"""
        return self._data.values()
    
    def items(self):
        """获取所有键值对"""
        return self._data.items()
    
    def __iter__(self):
        """迭代值"""
        return iter(self._data.values())
    
    def __repr__(self):
        return f"<D1Row {self._data}>"


class D1Engine:
    """D1 Engine 兼容类"""
    
    def __init__(self, d1_client: D1HTTPClient):
        self.d1_client = d1_client
    
    def connect(self, **kwargs):
        """创建连接（返回一个兼容对象）"""
        return D1Connection(self.d1_client)
    
    def execute(self, statement, *args, **kwargs):
        """执行语句"""
        session = D1Session(self.d1_client)
        return session.execute(statement, *args, **kwargs)


class D1Connection:
    """D1 连接对象"""
    
    def __init__(self, d1_client: D1HTTPClient):
        self.d1_client = d1_client
    
    def execute(self, statement, *args, **kwargs):
        """执行语句"""
        session = D1Session(self.d1_client)
        return session.execute(statement, *args, **kwargs)
    
    def commit(self):
        """提交（D1 HTTP API 自动提交）"""
        pass
    
    def close(self):
        """关闭连接"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

