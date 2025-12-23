"""
Cloudflare D1数据库适配器
将SQLAlchemy风格的ORM操作转换为D1数据库操作
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash


class D1Adapter:
    """D1数据库适配器，提供类似SQLAlchemy的接口"""
    
    def __init__(self, db):
        """
        初始化适配器
        
        Args:
            db: Cloudflare D1数据库实例（从env.DB获取）
        """
        self.db = db
    
    async def execute(self, sql: str, params: tuple = ()) -> Dict[str, Any]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            执行结果
        """
        # 将参数转换为列表（D1需要列表格式）
        param_list = list(params) if params else []
        
        # 执行SQL
        # 注意：D1的API可能因Python运行时版本而异
        try:
            stmt = self.db.prepare(sql)
            if param_list:
                result = await stmt.bind(*param_list).first()
            else:
                result = await stmt.first()
            return result
        except Exception as e:
            print(f"D1执行SQL失败: {e}, SQL: {sql}, Params: {param_list}")
            raise
    
    async def execute_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行SQL语句并返回所有结果
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            结果列表
        """
        param_list = list(params) if params else []
        try:
            stmt = self.db.prepare(sql)
            if param_list:
                result = await stmt.bind(*param_list).all()
            else:
                result = await stmt.all()
            return result
        except Exception as e:
            print(f"D1执行SQL失败: {e}, SQL: {sql}, Params: {param_list}")
            raise
    
    async def execute_many(self, sql: str, params_list: List[tuple]) -> None:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表
        """
        for params in params_list:
            param_list = list(params) if params else []
            await self.db.prepare(sql).bind(*param_list).run()
    
    # ========== Resume相关操作 ==========
    
    async def create_resume(self, resume_data: Dict[str, Any]) -> int:
        """创建简历记录"""
        sql = """
            INSERT INTO resumes (
                file_name, file_path, upload_time, parse_status,
                created_by, updated_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        params = (
            resume_data.get('file_name'),
            resume_data.get('file_path'),
            now,
            resume_data.get('parse_status', 'pending'),
            resume_data.get('created_by', 'system'),
            resume_data.get('updated_by', 'system'),
            now,
            now
        )
        result = await self.db.prepare(sql).bind(*params).run()
        return result.meta.last_row_id
    
    async def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """获取简历"""
        sql = "SELECT * FROM resumes WHERE id = ?"
        result = await self.db.prepare(sql).bind(resume_id).first()
        if result:
            return self._normalize_resume(result)
        return None
    
    async def update_resume(self, resume_id: int, updates: Dict[str, Any]) -> bool:
        """更新简历"""
        # 构建UPDATE语句
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key == 'work_experience' and isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif value is None:
                set_clauses.append(f"{key} = NULL")
                continue
            
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        sql = f"UPDATE resumes SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(resume_id)
        
        await self.db.prepare(sql).bind(*params).run()
        return True
    
    async def list_resumes(self, filters: Dict[str, Any] = None, 
                          limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出简历"""
        sql = "SELECT * FROM resumes WHERE 1=1"
        params = []
        
        if filters:
            if 'parse_status' in filters:
                sql += " AND parse_status = ?"
                params.append(filters['parse_status'])
            if 'name' in filters and filters['name']:
                sql += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
            if 'applied_position' in filters and filters['applied_position']:
                sql += " AND applied_position LIKE ?"
                params.append(f"%{filters['applied_position']}%")
        
        sql += " ORDER BY upload_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = await self.db.prepare(sql).bind(*params).all()
        return [self._normalize_resume(r) for r in results]
    
    async def delete_resume(self, resume_id: int) -> bool:
        """删除简历"""
        sql = "DELETE FROM resumes WHERE id = ?"
        await self.db.prepare(sql).bind(resume_id).run()
        return True
    
    def _normalize_resume(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """规范化简历数据"""
        result = dict(row)
        
        # 解析JSON字段
        if result.get('work_experience'):
            try:
                result['work_experience'] = json.loads(result['work_experience']) if isinstance(result['work_experience'], str) else result['work_experience']
            except:
                result['work_experience'] = None
        
        return result
    
    # ========== User相关操作 ==========
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        sql = "SELECT * FROM users WHERE username = ?"
        result = await self.db.prepare(sql).bind(username).first()
        return dict(result) if result else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        sql = "SELECT * FROM users WHERE id = ?"
        result = await self.db.prepare(sql).bind(user_id).first()
        return dict(result) if result else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """创建用户"""
        sql = """
            INSERT INTO users (
                username, password_hash, role, real_name, department, 
                group_name, is_active, create_time, update_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        params = (
            user_data['username'],
            user_data['password_hash'],
            user_data.get('role', 'employee'),
            user_data.get('real_name'),
            user_data.get('department'),
            user_data.get('group_name'),
            user_data.get('is_active', 1),
            now,
            now
        )
        result = await self.db.prepare(sql).bind(*params).run()
        return result.meta.last_row_id
    
    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """更新用户"""
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("update_time = ?")
        params.append(datetime.now().isoformat())
        
        sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(user_id)
        
        await self.db.prepare(sql).bind(*params).run()
        return True
    
    async def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        sql = "SELECT * FROM users ORDER BY create_time DESC"
        results = await self.db.prepare(sql).all()
        return [dict(r) for r in results]
    
    # ========== Position相关操作 ==========
    
    async def create_position(self, position_data: Dict[str, Any]) -> int:
        """创建岗位"""
        sql = """
            INSERT INTO positions (
                position_name, work_content, job_requirements, core_requirements,
                create_time, update_time, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        params = (
            position_data['position_name'],
            position_data.get('work_content'),
            position_data.get('job_requirements'),
            position_data.get('core_requirements'),
            now,
            now,
            position_data.get('created_by', 'system'),
            position_data.get('updated_by', 'system')
        )
        result = await self.db.prepare(sql).bind(*params).run()
        return result.meta.last_row_id
    
    async def get_position(self, position_id: int) -> Optional[Dict[str, Any]]:
        """获取岗位"""
        sql = "SELECT * FROM positions WHERE id = ?"
        result = await self.db.prepare(sql).bind(position_id).first()
        return dict(result) if result else None
    
    async def list_positions(self) -> List[Dict[str, Any]]:
        """列出所有岗位"""
        sql = "SELECT * FROM positions ORDER BY create_time DESC"
        results = await self.db.prepare(sql).all()
        return [dict(r) for r in results]
    
    async def update_position(self, position_id: int, updates: Dict[str, Any]) -> bool:
        """更新岗位"""
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("update_time = ?")
        params.append(datetime.now().isoformat())
        
        sql = f"UPDATE positions SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(position_id)
        
        await self.db.prepare(sql).bind(*params).run()
        return True
    
    async def delete_position(self, position_id: int) -> bool:
        """删除岗位"""
        sql = "DELETE FROM positions WHERE id = ?"
        await self.db.prepare(sql).bind(position_id).run()
        return True
    
    # ========== Interview相关操作 ==========
    
    async def create_interview(self, interview_data: Dict[str, Any]) -> int:
        """创建面试记录"""
        sql = """
            INSERT INTO interviews (
                resume_id, name, applied_position, identity_code,
                match_score, match_level, status,
                create_time, update_time, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        params = (
            interview_data['resume_id'],
            interview_data.get('name'),
            interview_data.get('applied_position'),
            interview_data.get('identity_code'),
            interview_data.get('match_score'),
            interview_data.get('match_level'),
            interview_data.get('status', '待面试'),
            now,
            now,
            interview_data.get('created_by', 'system'),
            interview_data.get('updated_by', 'system')
        )
        result = await self.db.prepare(sql).bind(*params).run()
        return result.meta.last_row_id
    
    async def get_interview(self, interview_id: int) -> Optional[Dict[str, Any]]:
        """获取面试记录"""
        sql = "SELECT * FROM interviews WHERE id = ?"
        result = await self.db.prepare(sql).bind(interview_id).first()
        if result:
            return self._normalize_interview(result)
        return None
    
    async def update_interview(self, interview_id: int, updates: Dict[str, Any]) -> bool:
        """更新面试记录"""
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            # 处理JSON字段
            if key in ['registration_form_recent_work_experience', 'registration_form_consideration_factors']:
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif value is None:
                set_clauses.append(f"{key} = NULL")
                continue
            
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("update_time = ?")
        params.append(datetime.now().isoformat())
        
        sql = f"UPDATE interviews SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(interview_id)
        
        await self.db.prepare(sql).bind(*params).run()
        return True
    
    async def list_interviews(self, filters: Dict[str, Any] = None,
                             limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出面试记录"""
        sql = "SELECT * FROM interviews WHERE 1=1"
        params = []
        
        if filters:
            if 'resume_id' in filters:
                sql += " AND resume_id = ?"
                params.append(filters['resume_id'])
            if 'status' in filters:
                sql += " AND status = ?"
                params.append(filters['status'])
        
        sql += " ORDER BY create_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = await self.db.prepare(sql).bind(*params).all()
        return [self._normalize_interview(r) for r in results]
    
    async def delete_interview(self, interview_id: int) -> bool:
        """删除面试记录"""
        sql = "DELETE FROM interviews WHERE id = ?"
        await self.db.prepare(sql).bind(interview_id).run()
        return True
    
    def _normalize_interview(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """规范化面试数据"""
        result = dict(row)
        
        # 解析JSON字段
        json_fields = ['registration_form_recent_work_experience', 'registration_form_consideration_factors']
        for field in json_fields:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field]) if isinstance(result[field], str) else result[field]
                except:
                    result[field] = [] if 'experience' in field else []
        
        return result
    
    # ========== 工具方法 ==========
    
    async def init_tables(self):
        """初始化数据库表（如果不存在）"""
        # 这里可以执行CREATE TABLE IF NOT EXISTS语句
        # 由于D1数据库可能已经通过迁移脚本创建，这里主要是确保表存在
        pass
    
    def check_password(self, password_hash: str, password: str) -> bool:
        """验证密码"""
        return check_password_hash(password_hash, password)
    
    def hash_password(self, password: str) -> str:
        """生成密码哈希"""
        return generate_password_hash(password)

