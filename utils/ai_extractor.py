"""
AI辅助简历信息提取模块
使用大语言模型提升解析准确性
"""

import json
import os
from typing import Dict, Optional, Any
import requests


class AIExtractor:
    """AI辅助信息提取器"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        初始化AI提取器
        
        Args:
            api_key: OpenAI API密钥，如果为None则从环境变量获取
            api_base: API基础URL，如果为None则使用OpenAI默认
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY')
        self.api_base = api_base or os.environ.get('OPENAI_API_BASE') or 'https://api.openai.com/v1'
        self.model = model
        self.enabled = bool(self.api_key)
        
    def extract_with_ai(self, text: str) -> Optional[Dict[str, Any]]:
        """
        使用AI提取简历信息
        
        Args:
            text: 简历文本内容
            
        Returns:
            提取的信息字典，如果失败返回None
        """
        if not self.enabled:
            return None
            
        try:
            # 截断文本以避免超出token限制
            max_length = 8000  # 保留一些余量
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            prompt = self._build_prompt(text)
            response = self._call_ai_api(prompt)
            
            if response:
                return self._parse_ai_response(response)
            return None
        except Exception as e:
            print(f"AI提取失败: {e}")
            return None
    
    def _build_prompt(self, text: str) -> str:
        """构建AI提示词"""
        return f"""请从以下简历文本中提取结构化信息，并以JSON格式返回。如果某个字段无法确定，请返回null。

需要提取的字段：
- name: 姓名（仅姓名，不要包含其他文字）
- gender: 性别（"男"或"女"，如果无法确定则返回null）
- birth_year: 出生年份（整数，如1990）
- phone: 手机号（11位数字）
- email: 邮箱地址
- highest_education: 最高学历（"博士"、"硕士"、"本科"、"专科"、"高中"、"初中"等）
- school: 毕业学校名称（完整的学校名称）
- major: 专业名称（完整的专业名称）
- work_experience: 工作经历数组，每个元素包含：
  - company: 公司名称
  - position: 职位名称
  - start_year: 开始年份（整数）
  - end_year: 结束年份（整数，如果至今则返回null）

简历文本：
{text}

请只返回JSON格式，不要包含任何其他文字说明。JSON格式示例：
{{
  "name": "张三",
  "gender": "男",
  "birth_year": 1990,
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "highest_education": "本科",
  "school": "北京大学",
  "major": "计算机科学与技术",
  "work_experience": [
    {{
      "company": "某某科技有限公司",
      "position": "软件工程师",
      "start_year": 2015,
      "end_year": 2020
    }}
  ]
}}
"""
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """调用AI API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            data = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个专业的简历信息提取助手。请准确提取简历中的关键信息，并以JSON格式返回。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,  # 降低随机性，提高准确性
                'max_tokens': 2000
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                print(f"AI API调用失败: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"AI API调用异常: {e}")
            return None
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析AI返回的JSON响应"""
        try:
            # 尝试提取JSON部分（可能包含markdown代码块）
            text = response_text.strip()
            
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # 解析JSON
            data = json.loads(text)
            
            # 验证和规范化数据
            return self._normalize_ai_result(data)
            
        except json.JSONDecodeError as e:
            print(f"AI响应JSON解析失败: {e}, 响应内容: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"解析AI响应异常: {e}")
            return None
    
    def _normalize_ai_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化AI返回的结果"""
        result = {}
        
        # 姓名
        if 'name' in data and data['name']:
            name = str(data['name']).strip()
            # 移除可能的标签文字
            name = name.replace('姓名：', '').replace('姓名:', '').strip()
            if name and len(name) <= 20:
                result['name'] = name
        
        # 性别
        if 'gender' in data:
            gender = str(data['gender']).strip()
            if gender in ['男', '女']:
                result['gender'] = gender
            else:
                result['gender'] = None
        
        # 出生年份
        if 'birth_year' in data and data['birth_year']:
            try:
                year = int(data['birth_year'])
                if 1950 <= year <= 2024:
                    result['birth_year'] = year
            except (ValueError, TypeError):
                pass
        
        # 手机号
        if 'phone' in data and data['phone']:
            phone = str(data['phone']).strip()
            # 只保留数字
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) == 11:
                result['phone'] = phone
        
        # 邮箱
        if 'email' in data and data['email']:
            email = str(data['email']).strip()
            if '@' in email and len(email) <= 100:
                result['email'] = email
        
        # 学历
        if 'highest_education' in data and data['highest_education']:
            edu = str(data['highest_education']).strip()
            # 标准化学历名称
            edu_map = {
                '博士': '博士', '博士后': '博士',
                '硕士': '硕士', '研究生': '硕士', 'MBA': '硕士', 'MPA': '硕士',
                '本科': '本科', '学士': '本科',
                '专科': '专科', '大专': '专科', '高职': '专科',
                '高中': '高中',
                '中专': '中专', '职高': '中专',
                '初中': '初中'
            }
            for key, value in edu_map.items():
                if key in edu:
                    result['highest_education'] = value
                    break
            else:
                result['highest_education'] = edu if edu else None
        
        # 学校
        if 'school' in data and data['school']:
            school = str(data['school']).strip()
            if school and len(school) <= 200:
                result['school'] = school
        
        # 专业
        if 'major' in data and data['major']:
            major = str(data['major']).strip()
            if major and len(major) <= 200:
                result['major'] = major
        
        # 工作经历
        if 'work_experience' in data and isinstance(data['work_experience'], list):
            work_exps = []
            for exp in data['work_experience']:
                if not isinstance(exp, dict):
                    continue
                normalized_exp = {}
                
                if 'company' in exp and exp['company']:
                    normalized_exp['company'] = str(exp['company']).strip()
                
                if 'position' in exp and exp['position']:
                    normalized_exp['position'] = str(exp['position']).strip()
                
                if 'start_year' in exp and exp['start_year']:
                    try:
                        year = int(exp['start_year'])
                        if 1980 <= year <= 2024:
                            normalized_exp['start_year'] = year
                    except (ValueError, TypeError):
                        pass
                
                if 'end_year' in exp and exp['end_year']:
                    try:
                        year = int(exp['end_year'])
                        if 1980 <= year <= 2024:
                            normalized_exp['end_year'] = year
                    except (ValueError, TypeError):
                        pass
                elif 'end_year' in exp and exp['end_year'] is None:
                    normalized_exp['end_year'] = None
                
                if normalized_exp:
                    work_exps.append(normalized_exp)
            
            if work_exps:
                result['work_experience'] = work_exps
        
        return result


def merge_extraction_results(rule_result: Dict[str, Any], ai_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    融合规则提取和AI提取的结果
    
    策略：
    1. 优先使用规则提取的结果（更可靠）
    2. 如果规则提取为空，使用AI提取的结果
    3. 对于某些字段，如果AI结果更合理，则使用AI结果
    
    Args:
        rule_result: 规则提取的结果
        ai_result: AI提取的结果
        
    Returns:
        融合后的结果
    """
    if not ai_result:
        return rule_result
    
    merged = rule_result.copy()
    
    # 姓名：如果规则提取为空或明显不合理，使用AI结果
    if not merged.get('name') or merged.get('name') in ['地址', '邮箱', '手机', '电话']:
        if ai_result.get('name'):
            merged['name'] = ai_result['name']
    
    # 性别：如果规则提取为空，使用AI结果
    if not merged.get('gender') and ai_result.get('gender'):
        merged['gender'] = ai_result['gender']
    
    # 出生年份：如果规则提取为空，使用AI结果
    if not merged.get('birth_year') and ai_result.get('birth_year'):
        merged['birth_year'] = ai_result['birth_year']
        # 重新计算年龄
        from datetime import datetime
        if merged['birth_year']:
            merged['age'] = datetime.now().year - merged['birth_year']
    
    # 手机号：如果规则提取为空，使用AI结果
    if not merged.get('phone') and ai_result.get('phone'):
        merged['phone'] = ai_result['phone']
    
    # 邮箱：如果规则提取为空，使用AI结果
    if not merged.get('email') and ai_result.get('email'):
        merged['email'] = ai_result['email']
    
    # 学历：如果规则提取为空，使用AI结果
    if not merged.get('highest_education') and ai_result.get('highest_education'):
        merged['highest_education'] = ai_result['highest_education']
    
    # 学校：如果规则提取为空，使用AI结果
    if not merged.get('school') and ai_result.get('school'):
        merged['school'] = ai_result['school']
    
    # 专业：如果规则提取为空，使用AI结果
    if not merged.get('major') and ai_result.get('major'):
        merged['major'] = ai_result['major']
    
    # 工作经历：合并两个结果，去重并排序
    rule_exps = merged.get('work_experience', [])
    ai_exps = ai_result.get('work_experience', [])
    
    if ai_exps and (not rule_exps or len(rule_exps) < len(ai_exps)):
        # 如果AI提取的工作经历更多，使用AI的结果
        merged['work_experience'] = ai_exps
        # 重新计算最早工作年份
        if ai_exps:
            years = [exp.get('start_year') for exp in ai_exps if exp.get('start_year')]
            if years:
                merged['earliest_work_year'] = min(years)
    
    return merged


