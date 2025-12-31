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
            entities: 查询的实体类（如 User, Resume 等）或列（如 Resume.applied_position）
            d1_client: D1 HTTP API 客户端
        """
        self.entities = entities
        self.d1_client = d1_client
        
        # 检测是否是查询特定列（如 query(Model.column)）
        # SQLAlchemy 的 Column 对象有 table 属性
        if entities and len(entities) > 0:
            first_entity = entities[0]
            # 检查是否是 Column 对象
            if hasattr(first_entity, 'table') and hasattr(first_entity, 'key'):
                # 这是查询特定列的情况
                self.model = first_entity.table  # 获取表对象
                self._selected_columns = [first_entity.key]  # 存储列名
            else:
                # 这是查询整个模型的情况
                self.model = first_entity
                self._selected_columns = None
        else:
            self.model = None
            self._selected_columns = None
        
        self._filters = []
        self._limit_value = None
        self._offset_value = None
        self._distinct = False
    
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
            # 处理不同的返回格式
            # D1 API 可能直接返回列表，也可能返回包含 results 字段的字典
            if isinstance(result, list):
                rows = result
            elif isinstance(result, dict):
                rows = result.get('results', [])
            else:
                rows = []
            
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
            # 处理不同的返回格式
            if isinstance(result, list):
                rows = result
            elif isinstance(result, dict):
                rows = result.get('results', [])
            else:
                rows = []
            
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
            # 处理不同的返回格式
            # D1 API 的 result 字段直接是结果列表
            if isinstance(result, list):
                rows = result
            elif isinstance(result, dict):
                rows = result.get('results', [])
            else:
                rows = []
            
            if rows:
                # COUNT(*) 查询返回的第一行第一列就是计数
                if isinstance(rows[0], dict):
                    # 如果是字典，查找 count 字段或第一个值
                    if 'count' in rows[0]:
                        return int(rows[0]['count'])
                    elif len(rows[0]) > 0:
                        # 取第一个值
                        return int(list(rows[0].values())[0])
                elif isinstance(rows[0], (list, tuple)) and len(rows[0]) > 0:
                    # 如果是列表/元组，取第一个元素
                    return int(rows[0][0])
            return 0
        except Exception as e:
            logger.error(f"D1 统计失败: {e}, SQL: {sql}")
            raise
    
    def distinct(self):
        """去重（简化实现，D1 支持 DISTINCT）"""
        # 这是一个占位方法，实际去重应该在 SQL 中使用 DISTINCT
        # 这里只是返回 self 以支持链式调用
        self._distinct = True
        return self
    
    def _build_sql(self, limit=None):
        """构建 SQL 查询语句"""
        if not self.model:
            raise Exception("查询对象没有指定模型")
        
        table_name = self.model.__tablename__
        
        # 确定要查询的列
        if self._selected_columns:
            # 查询特定列
            columns = ", ".join(self._selected_columns)
            if self._distinct:
                sql = f"SELECT DISTINCT {columns} FROM {table_name}"
            else:
                sql = f"SELECT {columns} FROM {table_name}"
        else:
            # 查询所有列
            if self._distinct:
                sql = f"SELECT DISTINCT * FROM {table_name}"
            else:
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
    
    def _row_to_model(self, row_data):
        """将数据库行转换为模型实例或元组"""
        # 如果查询的是特定列，返回元组（模拟 SQLAlchemy 的行为）
        if self._selected_columns:
            # 返回元组，第一个元素是列的值
            if isinstance(row_data, dict):
                # 如果是字典，取第一个列的值
                col_name = self._selected_columns[0]
                return (row_data.get(col_name),)
            elif isinstance(row_data, (list, tuple)):
                # 如果是列表/元组，直接返回
                return tuple(row_data) if not isinstance(row_data, tuple) else row_data
            else:
                return (row_data,)
        
        # 查询整个模型，返回模型实例
        if not self.model:
            return row_data
        
        # 创建模型实例
        instance = self.model()
        
        # 设置属性
        if isinstance(row_data, dict):
            for key, value in row_data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
        elif isinstance(row_data, (list, tuple)):
            # 如果是列表/元组，尝试按列顺序设置
            # 这是一个简化处理，实际应该根据表结构映射
            logger.warning("D1 查询返回列表格式，可能无法正确映射到模型")
            return row_data
        
        return instance

