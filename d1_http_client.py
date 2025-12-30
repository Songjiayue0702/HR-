"""
Cloudflare D1 HTTP API 客户端
用于在非 Workers 环境中通过 HTTP API 访问 D1 数据库
"""
import os
import json
import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class D1HTTPClient:
    """Cloudflare D1 HTTP API 客户端"""
    
    def __init__(self, account_id: str, api_token: str, database_id: str):
        """
        初始化 D1 HTTP 客户端
        
        Args:
            account_id: Cloudflare 账户 ID
            api_token: Cloudflare API Token（需要有 D1 权限）
            database_id: D1 数据库 ID
        """
        self.account_id = account_id
        self.api_token = api_token
        self.database_id = database_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def execute(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """
        执行 SQL 语句
        
        Args:
            sql: SQL 语句
            params: 参数列表（可选）
            
        Returns:
            执行结果字典，包含 success, result 等字段
        """
        url = f"{self.base_url}/query"
        
        payload = {
            'sql': sql
        }
        
        if params:
            payload['params'] = params
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Cloudflare API 返回格式：{"success": true, "result": {...}, "errors": []}
            if not result.get('success', False):
                errors = result.get('errors', [])
                if errors:
                    error_msg = errors[0].get('message', 'Unknown error')
                    error_code = errors[0].get('code', 0)
                    raise Exception(f"D1 API 错误 [{error_code}]: {error_msg}")
                else:
                    raise Exception("D1 API 返回失败，但无错误信息")
            
            return result.get('result', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"D1 HTTP 请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"D1 API 错误详情: {error_detail}")
                except:
                    logger.error(f"D1 API 响应: {e.response.text}")
            raise Exception(f"D1 连接失败: {str(e)}")
        except Exception as e:
            logger.error(f"D1 执行 SQL 失败: {e}, SQL: {sql}")
            raise
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = self.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"D1 连接测试失败: {e}")
            return False

