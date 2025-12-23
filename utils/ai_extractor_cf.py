"""
AI辅助简历信息提取模块 - Cloudflare Workers版本
使用原生fetch API替代requests和openai库
"""
import json
import os
from typing import Dict, Optional, Any


class AIExtractor:
    """AI辅助信息提取器 - Workers版本"""
    
    # 支持的AI模型配置
    MODEL_CONFIGS = {
        # OpenAI模型
        'gpt-3.5-turbo': {
            'api_base': 'https://api.openai.com/v1',
            'endpoint': '/chat/completions'
        },
        'gpt-4': {
            'api_base': 'https://api.openai.com/v1',
            'endpoint': '/chat/completions'
        },
        'gpt-4-turbo': {
            'api_base': 'https://api.openai.com/v1',
            'endpoint': '/chat/completions'
        },
        # DeepSeek模型
        'deepseek-chat': {
            'api_base': 'https://api.deepseek.com/v1',
            'endpoint': '/chat/completions'
        },
        'deepseek-coder': {
            'api_base': 'https://api.deepseek.com/v1',
            'endpoint': '/chat/completions'
        },
        # 其他兼容OpenAI API的模型
        'qwen-turbo': {
            'api_base': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'endpoint': '/chat/completions'
        },
        'qwen-plus': {
            'api_base': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'endpoint': '/chat/completions'
        },
    }
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        初始化AI提取器
        
        Args:
            api_key: AI API密钥，如果为None则从环境变量获取
            api_base: API基础URL，如果为None则根据模型自动选择
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY') or os.environ.get('DEEPSEEK_API_KEY')
        self.model = model
        
        # 根据模型自动选择API基础URL
        if api_base:
            self.api_base = api_base.rstrip('/')
        elif model in self.MODEL_CONFIGS:
            self.api_base = self.MODEL_CONFIGS[model]['api_base']
        else:
            # 默认使用OpenAI格式
            self.api_base = os.environ.get('OPENAI_API_BASE') or 'https://api.openai.com/v1'
        
        # 获取API端点
        if model in self.MODEL_CONFIGS:
            self.api_endpoint = self.MODEL_CONFIGS[model]['endpoint']
        else:
            self.api_endpoint = '/chat/completions'
        
        self.enabled = bool(self.api_key)
    
    async def _call_ai_api(self, prompt: str, system_prompt: Optional[str] = None, fetch_func=None) -> Optional[str]:
        """
        调用AI API - 使用fetch API（Workers原生）
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            fetch_func: fetch函数（Workers环境传入）
            
        Returns:
            AI返回的文本内容
        """
        if not self.enabled:
            return None
        
        url = f"{self.api_base}{self.api_endpoint}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            # 使用fetch API（Workers原生）
            # 如果fetch_func未提供，尝试使用全局fetch
            if fetch_func is None:
                try:
                    # 在Workers Python环境中，fetch可能通过全局变量或import提供
                    import builtins
                    fetch_func = getattr(builtins, 'fetch', None)
                    if fetch_func is None:
                        # 尝试从环境获取
                        import os
                        fetch_func = os.environ.get('__FETCH__')
                except:
                    pass
            
            if fetch_func is None:
                raise Exception("fetch函数不可用，请在Workers环境中调用")
            
            response = await fetch_func(url, {
                "method": "POST",
                "headers": headers,
                "body": json.dumps(payload)
            })
            
            if not response.ok:
                error_text = await response.text()
                print(f"AI API调用失败: {response.status} - {error_text}")
                return None
            
            data = await response.json()
            
            # 提取回复内容
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return content.strip() if content else None
            
            return None
        except Exception as e:
            print(f"AI API调用异常: {e}")
            return None
    
    async def optimize_text_extraction(self, text: str, fetch_func=None) -> Optional[str]:
        """
        使用AI优化文本提取结果
        
        Args:
            text: 原始文本
            fetch_func: fetch函数（Workers环境传入）
        """
        if not self.enabled:
            return None
        
        try:
            max_length = 12000
            if len(text) <= max_length:
                return await self._optimize_text_with_ai(text, fetch_func)
            else:
                parts = []
                for i in range(0, len(text), max_length):
                    part = text[i:i+max_length]
                    optimized = await self._optimize_text_with_ai(part, fetch_func)
                    if optimized:
                        parts.append(optimized)
                    else:
                        parts.append(part)
                return '\n'.join(parts) if parts else text
        except Exception as e:
            print(f"AI文本优化失败: {e}")
            return None
    
    async def _optimize_text_with_ai(self, text: str, fetch_func=None) -> Optional[str]:
        """使用AI优化单段文本"""
        prompt = f"""请优化以下从简历文件中提取的文本，修复OCR识别错误、合并被换行分割的文本、保持正确的阅读顺序。

**优化要求：**
1. 修复OCR常见错误（如"2O25" -> "2025"，"@4q.com" -> "@qq.com"）
2. 合并被换行分割的信息
3. 保持文本的原始结构和上下文位置
4. 不要添加或删除内容，只进行修复和优化

原始文本：
{text}

请只返回优化后的文本，不要添加任何说明或注释。"""
        
        try:
            response = await self._call_ai_api(prompt, fetch_func=fetch_func)
            if response:
                optimized = response.strip()
                if optimized.startswith('```'):
                    lines = optimized.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines[-1].strip() == '```':
                        lines = lines[:-1]
                    optimized = '\n'.join(lines).strip()
                return optimized
            return None
        except Exception as e:
            print(f"AI文本优化调用失败: {e}")
            return None
    
    async def extract_with_ai(self, text: str, is_word_file: bool = False, fetch_func=None) -> Optional[Dict[str, Any]]:
        """
        使用AI提取简历信息
        """
        if not self.enabled:
            return None
        
        try:
            # 构建提取提示
            system_prompt = """你是一个专业的简历信息提取助手。请从简历文本中提取以下信息，并以JSON格式返回：
{
    "name": "姓名",
    "gender": "性别（男/女）",
    "birth_year": 出生年份（整数，如1990），
    "age": 年龄（整数），
    "phone": "手机号",
    "email": "邮箱",
    "highest_education": "最高学历（博士/硕士/本科/大专/高中等）",
    "school": "毕业院校",
    "major": "专业",
    "work_experience": [
        {
            "company": "公司名称",
            "position": "职位",
            "start_year": 开始年份（整数），
            "end_year": 结束年份（整数，如至今则为null）
        }
    ]
}

只返回JSON，不要添加任何说明。"""
            
            user_prompt = f"""请从以下简历文本中提取信息：

{text[:8000]}  # 限制长度避免超出token限制

请返回JSON格式的提取结果。"""
            
            response = await self._call_ai_api(user_prompt, system_prompt, fetch_func)
            if not response:
                return None
            
            # 解析JSON响应
            try:
                # 清理可能的markdown标记
                cleaned = response.strip()
                if cleaned.startswith('```json'):
                    cleaned = cleaned[7:]
                if cleaned.startswith('```'):
                    cleaned = cleaned[3:]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                
                result = json.loads(cleaned)
                return result
            except json.JSONDecodeError as e:
                print(f"AI返回的JSON解析失败: {e}, 响应: {response[:200]}")
                return None
        except Exception as e:
            print(f"AI信息提取失败: {e}")
            return None

