"""
D1 查询对象，模拟 SQLAlchemy 的 Query 对象
将 ORM 查询转换为 SQL 并通过 D1 HTTP API 执行
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class D1Query:
    """D1 查询对象，模拟 SQLAlchemy 的 Query"""
    
    def __init__(self, entities, d1_client):
        """
        初始化查询对象
        
        Args:
            entities: 查询的实体类（如 User, Resume 等）
            d1_client: D1 HTTP API 客户端
        """
        self.entities = entities
        self.d1_client = d1_client
        self.model = entities[0] if entities else None
        self._filters = []
        self._limit_value = None
        self._offset_value = None
    
    def filter_by(self, **kwargs):
        """添加等值过滤条件"""
        self._filters.extend(kwargs.items())
        return self
    
    def filter(self, *criterion):
        """添加过滤条件（简化实现，仅支持简单条件）"""
        # 这是一个简化实现，实际应该解析 SQLAlchemy 的 criterion
        # 目前仅记录，在 first() 或 all() 时转换为 SQL
        self._filters.extend(criterion)
        return self
    
    def first(self):
        """获取第一条结果"""
        sql, params = self._build_sql(limit=1)
        try:
            result = self.d1_client.execute(sql, params)
            rows = result.get('results', [])
            if rows:
                return self._row_to_model(rows[0])
            return None
        except Exception as e:
            logger.error(f"D1 查询失败: {e}, SQL: {sql}")
            raise
    
    def all(self):
        """获取所有结果"""
        sql, params = self._build_sql()
        try:
            result = self.d1_client.execute(sql, params)
            rows = result.get('results', [])
            return [self._row_to_model(row) for row in rows]
        except Exception as e:
            logger.error(f"D1 查询失败: {e}, SQL: {sql}")
            raise
    
    def limit(self, limit):
        """限制结果数量"""
        self._limit_value = limit
        return self
    
    def offset(self, offset):
        """设置偏移量"""
        self._offset_value = offset
        return self
    
    def count(self):
        """统计数量"""
        sql, params = self._build_count_sql()
        try:
            result = self.d1_client.execute(sql, params)
            rows = result.get('results', [])
            if rows:
                return rows[0].get('count', 0)
            return 0
        except Exception as e:
            logger.error(f"D1 统计失败: {e}, SQL: {sql}")
            raise
    
    def _build_sql(self, limit=None):
        """构建 SQL 查询语句"""
        if not self.model:
            raise Exception("查询对象没有指定模型")
        
        table_name = self.model.__tablename__
        sql = f"SELECT * FROM {table_name}"
        params = []
        
        # 添加 WHERE 条件
        if self._filters:
            conditions = []
            for filter_item in self._filters:
                if isinstance(filter_item, tuple):
                    # filter_by 的条件 (key, value)
                    key, value = filter_item
                    conditions.append(f"{key} = ?")
                    params.append(value)
                else:
                    # filter 的条件（需要更复杂的解析）
                    # 简化处理：直接使用字符串表示
                    logger.warning(f"复杂的过滤条件可能无法正确处理: {filter_item}")
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        # 添加 LIMIT
        if limit:
            sql += f" LIMIT {limit}"
        elif self._limit_value:
            sql += f" LIMIT {self._limit_value}"
        
        # 添加 OFFSET
        if self._offset_value:
            sql += f" OFFSET {self._offset_value}"
        
        return sql, params
    
    def _build_count_sql(self):
        """构建计数 SQL 语句"""
        if not self.model:
            raise Exception("查询对象没有指定模型")
        
        table_name = self.model.__tablename__
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        params = []
        
        # 添加 WHERE 条件
        if self._filters:
            conditions = []
            for filter_item in self._filters:
                if isinstance(filter_item, tuple):
                    key, value = filter_item
                    conditions.append(f"{key} = ?")
                    params.append(value)
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        return sql, params
    
    def _row_to_model(self, row_data: Dict[str, Any]):
        """将数据库行转换为模型实例"""
        if not self.model:
            return row_data
        
        # 创建模型实例
        instance = self.model()
        
        # 设置属性
        for key, value in row_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance

