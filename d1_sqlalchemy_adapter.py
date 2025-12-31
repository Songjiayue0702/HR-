"""
D1 HTTP API 的 SQLAlchemy 兼容适配器
由于 D1 通过 HTTP API 访问，无法直接使用 SQLAlchemy，这里提供一个兼容层
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
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
        self._pending_objects = []  # 待添加的对象
        self._pending_deletes = []  # 待删除的对象
    
    def query(self, *entities, **kwargs):
        """创建查询对象（ORM 查询）"""
        from d1_query import D1Query
        return D1Query(entities, self.d1_client)
    
    def add(self, instance):
        """添加实例到会话（立即执行 INSERT）"""
        if instance is None:
            return
        
        # 获取表名
        table_name = instance.__tablename__
        
        # 获取列和值
        columns = []
        values = []
        params = []
        
        # 遍历模型的所有列
        for column in instance.__table__.columns:
            col_name = column.name
            value = getattr(instance, col_name, None)
            
            # 跳过自增主键（值为 None 的主键）
            if column.primary_key and value is None:
                continue
            
            # 处理 None 值
            if value is None:
                # 如果列允许 NULL，添加 NULL 值；否则跳过（让数据库使用默认值）
                if column.nullable:
                    columns.append(col_name)
                    values.append('?')
                    params.append(None)
                continue
            
            # 处理特殊类型
            if isinstance(value, datetime):
                # datetime 对象转换为 ISO 格式字符串
                value = value.isoformat()
            elif isinstance(value, (dict, list)):
                # JSON 类型转换为字符串
                import json
                value = json.dumps(value, ensure_ascii=False)
            
            columns.append(col_name)
            values.append('?')
            params.append(value)
        
        if not columns:
            raise Exception(f"无法插入 {table_name}：没有可插入的列")
        
        # 构建 INSERT SQL
        columns_str = ', '.join(columns)
        values_str = ', '.join(values)
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
        
        try:
            # 执行 INSERT
            result = self.d1_client.execute(sql, params)
            
            # 获取 last_row_id
            last_row_id = None
            
            # D1 HTTP API 返回格式可能是列表或字典
            if isinstance(result, list):
                # 列表格式：[{"meta": {"last_row_id": 123, "changes": 1}}]
                if len(result) > 0 and isinstance(result[0], dict):
                    meta = result[0].get('meta', {})
                    if isinstance(meta, dict):
                        last_row_id = meta.get('last_row_id')
            elif isinstance(result, dict):
                # 字典格式：{"meta": {"last_row_id": 123, "changes": 1}} 或 {"last_row_id": 123}
                if 'meta' in result and isinstance(result['meta'], dict):
                    last_row_id = result['meta'].get('last_row_id')
                elif 'last_row_id' in result:
                    last_row_id = result['last_row_id']
            
            # 如果仍然没有获取到 last_row_id，尝试查询
            if last_row_id is None:
                try:
                    id_result = self.d1_client.execute("SELECT last_insert_rowid() as id", [])
                    if isinstance(id_result, list) and len(id_result) > 0:
                        first_row = id_result[0]
                        if isinstance(first_row, dict):
                            last_row_id = first_row.get('id')
                        else:
                            last_row_id = first_row
                    elif isinstance(id_result, dict):
                        last_row_id = id_result.get('id')
                except Exception as id_err:
                    logger.warning(f"无法获取 last_insert_rowid: {id_err}")
            
            # 更新实例的主键
            if last_row_id is not None:
                for column in instance.__table__.columns:
                    if column.primary_key:
                        setattr(instance, column.name, last_row_id)
                        break
        except Exception as e:
            logger.error(f"D1 INSERT 失败: {e}, SQL: {sql}, Params: {params}")
            raise
    
    def delete(self, instance):
        """删除实例（立即执行 DELETE）"""
        if instance is None:
            return
        
        # 获取表名
        table_name = instance.__table__.name
        
        # 获取主键
        primary_keys = []
        params = []
        for column in instance.__table__.primary_key.columns:
            col_name = column.name
            value = getattr(instance, col_name, None)
            if value is not None:
                primary_keys.append(f"{col_name} = ?")
                params.append(value)
        
        if not primary_keys:
            raise Exception(f"无法删除 {table_name} 实例：缺少主键值")
        
        # 构建 DELETE SQL
        where_clause = ' AND '.join(primary_keys)
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        try:
            self.d1_client.execute(sql, params)
        except Exception as e:
            logger.error(f"D1 DELETE 失败: {e}, SQL: {sql}, Params: {params}")
            raise
    
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
        """提交事务（D1 HTTP API 中每个请求自动提交，这里处理待处理的对象）"""
        # D1 HTTP API 每个请求自动提交，所以这里主要是清理状态
        self._pending_objects = []
        self._pending_deletes = []
    
    def rollback(self):
        """回滚事务（D1 HTTP API 不支持，这里是占位）"""
        self._pending_objects = []
        self._pending_deletes = []
    
    def close(self):
        """关闭会话"""
        self._pending_objects = []
        self._pending_deletes = []


class D1ResultProxy:
    """D1 结果代理类，模拟 SQLAlchemy 的 Result 对象"""
    
    def __init__(self, d1_result):
        self.d1_result = d1_result
        # D1 API 的 result 字段直接是结果列表，不是包含 results 的字典
        if isinstance(d1_result, list):
            self._rows = d1_result
        elif isinstance(d1_result, dict):
            self._rows = d1_result.get('results', [])
        else:
            self._rows = []
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

