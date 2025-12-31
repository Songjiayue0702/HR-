"""
D1 查询对象，模拟 SQLAlchemy 的 Query 对象
将 ORM 查询转换为 SQL 并通过 D1 HTTP API 执行
"""
import logging
from typing import Optional, List, Dict, Any, Tuple

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
        self._order_by = []
    
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
    
    def order_by(self, *criterion):
        """添加排序条件"""
        self._order_by.extend(criterion)
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
            
            if rows and len(rows) > 0:
                first_row = rows[0]
                # COUNT(*) 查询返回的第一行第一列就是计数
                if isinstance(first_row, dict):
                    # 如果是字典，查找 count 字段或第一个值
                    if 'count' in first_row:
                        count_value = first_row['count']
                        # 确保是数值类型
                        if isinstance(count_value, (int, float)):
                            return int(count_value)
                        elif isinstance(count_value, str):
                            return int(count_value)
                        else:
                            logger.warning(f"COUNT 返回了意外的类型: {type(count_value)}, 值: {count_value}")
                            return 0
                    elif len(first_row) > 0:
                        # 取第一个值
                        first_value = list(first_row.values())[0]
                        if isinstance(first_value, (int, float)):
                            return int(first_value)
                        elif isinstance(first_value, str):
                            return int(first_value)
                        else:
                            logger.warning(f"COUNT 返回了意外的类型: {type(first_value)}, 值: {first_value}")
                            return 0
                elif isinstance(first_row, (list, tuple)) and len(first_row) > 0:
                    # 如果是列表/元组，取第一个元素
                    first_value = first_row[0]
                    if isinstance(first_value, (int, float)):
                        return int(first_value)
                    elif isinstance(first_value, str):
                        return int(first_value)
                    else:
                        logger.warning(f"COUNT 返回了意外的类型: {type(first_value)}, 值: {first_value}")
                        return 0
                else:
                    # 如果不是字典也不是列表，尝试直接转换
                    try:
                        if isinstance(first_row, (int, float)):
                            return int(first_row)
                        elif isinstance(first_row, str):
                            return int(first_row)
                    except (ValueError, TypeError):
                        logger.warning(f"无法转换 COUNT 结果: {type(first_row)}, 值: {first_row}")
                        return 0
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
    
    def _parse_expression(self, expr) -> Tuple[Optional[str], List]:
        """
        解析 SQLAlchemy 表达式为 SQL 条件和参数
        
        Returns:
            (sql_condition, params_list) 元组
        """
        if expr is None:
            return None, []
        
        # 优先尝试使用 SQLAlchemy 的编译功能（最可靠的方法）
        try:
            from sqlalchemy.dialects import sqlite
            compiled = expr.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": False})
            sql_str = str(compiled)
            
            # 提取参数
            params_list = []
            if hasattr(compiled, 'params'):
                params_dict = compiled.params
                # 替换命名参数为位置参数
                for param_name, param_value in params_dict.items():
                    # SQLite 使用 ? 作为占位符
                    sql_str = sql_str.replace(f":{param_name}", "?", 1)
                    params_list.append(param_value)
            
            return sql_str, params_list
        except Exception as compile_error:
            # 如果编译失败，尝试手动解析
            logger.debug(f"SQLAlchemy 编译失败，尝试手动解析: {compile_error}")
            pass
        
        # 手动解析：检查是否是 BinaryExpression (==, !=, <, >, <=, >=, LIKE 等)
        if hasattr(expr, 'left') and hasattr(expr, 'right') and hasattr(expr, 'operator'):
            left = expr.left
            right = expr.right
            op = expr.operator
            
            # 获取列名
            column_name = None
            if hasattr(left, 'key') and hasattr(left, 'table'):
                column_name = left.key
            elif hasattr(left, 'name'):
                column_name = left.name
            elif hasattr(left, '__name__'):
                column_name = left.__name__
            
            if not column_name:
                logger.warning(f"无法解析表达式左侧列名: {expr}")
                return None, []
            
            # 处理不同类型的操作符
            try:
                # 尝试获取操作符名称
                op_name = str(op.__name__ if hasattr(op, '__name__') else op)
                
                # 获取右侧的值
                param_value = None
                if isinstance(right, str):
                    param_value = right
                elif hasattr(right, 'value'):
                    param_value = right.value
                elif hasattr(right, '__str__'):
                    param_value = str(right)
                else:
                    param_value = right
                
                # 处理 LIKE 操作
                if 'like' in op_name.lower() or 'ilike' in op_name.lower():
                    return f"{column_name} LIKE ?", [param_value]
                
                # 处理等号 ==
                elif op_name == 'eq' or op == '==':
                    return f"{column_name} = ?", [param_value]
                
                # 处理不等 !=
                elif op_name == 'ne' or op == '!=':
                    return f"{column_name} != ?", [param_value]
                
                # 处理大于 >
                elif op_name == 'gt' or op == '>':
                    return f"{column_name} > ?", [param_value]
                
                # 处理小于 <
                elif op_name == 'lt' or op == '<':
                    return f"{column_name} < ?", [param_value]
                
                # 处理大于等于 >=
                elif op_name == 'ge' or op == '>=':
                    return f"{column_name} >= ?", [param_value]
                
                # 处理小于等于 <=
                elif op_name == 'le' or op == '<=':
                    return f"{column_name} <= ?", [param_value]
                
                # 默认当作等号处理
                else:
                    return f"{column_name} = ?", [param_value]
            except Exception as e:
                logger.warning(f"解析表达式操作符失败: {e}, expr: {expr}")
                return None, []
        
        # 处理 OR/AND 组合 (BooleanClauseList)
        elif hasattr(expr, 'clauses'):
            clauses = expr.clauses
            if len(clauses) == 0:
                return None, []
            
            # 判断是 OR 还是 AND
            is_or = hasattr(expr, 'operator') and ('or' in str(expr.operator).lower() or '|' in str(expr))
            connector = " OR " if is_or else " AND "
            
            sql_parts = []
            all_params = []
            for clause in clauses:
                sql_part, params = self._parse_expression(clause)
                if sql_part:
                    sql_parts.append(f"({sql_part})")
                    all_params.extend(params)
            
            if sql_parts:
                return connector.join(sql_parts), all_params
        
        # 处理 IS NOT NULL (UnaryExpression)
        elif hasattr(expr, 'element') and hasattr(expr, 'operator'):
            try:
                op_name = str(expr.operator.__name__ if hasattr(expr.operator, '__name__') else expr.operator)
                if 'isnot' in op_name.lower() or 'is_not' in op_name.lower():
                    element = expr.element
                    if hasattr(element, 'key'):
                        column_name = element.key
                        return f"{column_name} IS NOT NULL", []
                    elif hasattr(element, 'name'):
                        column_name = element.name
                        return f"{column_name} IS NOT NULL", []
            except:
                pass
        
        # 处理 IN 操作 (CollectionAggregate)
        elif hasattr(expr, 'left') and hasattr(expr, 'right'):
            left = expr.left
            if hasattr(left, 'key'):
                column_name = left.key
            elif hasattr(left, 'name'):
                column_name = left.name
            else:
                return None, []
            
            # 检查右侧是否是列表或 IN 操作
            right = expr.right
            if isinstance(right, (list, tuple)) or (hasattr(right, '__iter__') and not isinstance(right, str)):
                try:
                    values = list(right) if not isinstance(right, (list, tuple)) else right
                    placeholders = ", ".join(["?"] * len(values))
                    return f"{column_name} IN ({placeholders})", values
                except:
                    pass
        
        # 尝试直接编译表达式（如果 SQLAlchemy 支持）
        try:
            # 尝试使用 SQLAlchemy 的编译功能
            from sqlalchemy.dialects import sqlite
            compiled = expr.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": False})
            sql_str = str(compiled)
            # 提取参数占位符
            if hasattr(compiled, 'params'):
                params_dict = compiled.params
                sql_str_with_placeholders = sql_str
                params_list = []
                for key, value in params_dict.items():
                    sql_str_with_placeholders = sql_str_with_placeholders.replace(f":{key}", "?")
                    params_list.append(value)
                return sql_str_with_placeholders, params_list
            return sql_str, []
        except Exception as e:
            logger.warning(f"无法解析表达式，使用编译也失败: {e}, expr: {expr}")
            return None, []
    
    def _parse_order_by(self, expr) -> Optional[str]:
        """解析排序表达式为 SQL ORDER BY 子句"""
        if expr is None:
            return None
        
        try:
            # 处理 desc() 和 asc()
            if hasattr(expr, 'element'):
                # 这是 desc() 或 asc() 包装的表达式
                element = expr.element
                if hasattr(element, 'key'):
                    column_name = element.key
                elif hasattr(element, 'name'):
                    column_name = element.name
                else:
                    return None
                
                # 检查是否是 desc
                if hasattr(expr, 'modifier') or str(expr).upper().endswith('DESC'):
                    return f"{column_name} DESC"
                else:
                    return f"{column_name} ASC"
            else:
                # 直接是列
                if hasattr(expr, 'key'):
                    column_name = expr.key
                    return f"{column_name} ASC"
                elif hasattr(expr, 'name'):
                    column_name = expr.name
                    return f"{column_name} ASC"
        except Exception as e:
            logger.warning(f"解析排序表达式失败: {e}, expr: {expr}")
        
        return None
    
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
                    # 尝试解析 SQLAlchemy 表达式
                    sql_part, sql_params = self._parse_expression(filter_item)
                    if sql_part:
                        conditions.append(f"({sql_part})")
                        params.extend(sql_params)
                    else:
                        logger.warning(f"无法解析过滤条件: {filter_item}")
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        # 添加 ORDER BY
        if self._order_by:
            order_parts = []
            for order_expr in self._order_by:
                order_sql = self._parse_order_by(order_expr)
                if order_sql:
                    order_parts.append(order_sql)
            if order_parts:
                sql += " ORDER BY " + ", ".join(order_parts)
        
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
        
        # 添加 WHERE 条件（使用与 _build_sql 相同的逻辑）
        if self._filters:
            conditions = []
            for filter_item in self._filters:
                if isinstance(filter_item, tuple):
                    key, value = filter_item
                    conditions.append(f"{key} = ?")
                    params.append(value)
                else:
                    # 尝试解析 SQLAlchemy 表达式
                    sql_part, sql_params = self._parse_expression(filter_item)
                    if sql_part:
                        conditions.append(f"({sql_part})")
                        params.extend(sql_params)
                    else:
                        logger.warning(f"无法解析过滤条件: {filter_item}")
            
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

