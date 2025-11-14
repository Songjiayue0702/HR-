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
        'claude-3-opus': {
            'api_base': 'https://api.anthropic.com/v1',
            'endpoint': '/messages'
        },
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
            model: 使用的模型名称（支持：gpt-3.5-turbo, gpt-4, deepseek-chat, deepseek-coder等）
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
        
    def optimize_text_extraction(self, text: str) -> Optional[str]:
        """
        使用AI优化文本提取结果
        修复OCR错误、合并被分割的文本、提高文本准确性
        
        Args:
            text: 原始提取的文本内容
            
        Returns:
            优化后的文本，如果失败返回None
        """
        if not self.enabled:
            return None
            
        try:
            # 如果文本太长，分段处理
            max_length = 12000  # 保留一些余量
            if len(text) <= max_length:
                return self._optimize_text_with_ai(text)
            else:
                # 分段处理
                parts = []
                for i in range(0, len(text), max_length):
                    part = text[i:i+max_length]
                    optimized = self._optimize_text_with_ai(part)
                    if optimized:
                        parts.append(optimized)
                    else:
                        parts.append(part)  # 如果优化失败，使用原文本
                return '\n'.join(parts) if parts else text
        except Exception as e:
            print(f"AI文本优化失败: {e}")
            return None
    
    def _optimize_text_with_ai(self, text: str) -> Optional[str]:
        """使用AI优化单段文本"""
        prompt = f"""请优化以下从简历文件中提取的文本，修复OCR识别错误、合并被换行分割的文本、保持正确的阅读顺序（从左到右、从上到下）。

**优化要求：**
1. 修复OCR常见错误（如"2O25" -> "2025"，"@4q.com" -> "@qq.com"）
2. 合并被换行分割的信息：
   - 时间范围：如"2019\n-\n2020" -> "2019-2020"
   - 公司名：如"北京\n公司" -> "北京公司"
   - 岗位：如"销售\n主管" -> "销售主管"
   - 学校名：如"商洛\n学院" -> "商洛学院"
3. 保持文本的原始结构和上下文位置
4. 不要添加或删除内容，只进行修复和优化
5. 保持页面分隔标记（如果有）

原始文本：
{text}

请只返回优化后的文本，不要添加任何说明或注释。"""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                # 清理可能的markdown标记
                optimized = response.strip()
                if optimized.startswith('```'):
                    # 移除markdown代码块标记
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
        """构建AI提示词（改进版，提高准确性）"""
        return f"""你是一个专业的简历信息提取助手。请仔细分析以下**原始文本**，准确提取结构化信息，并以JSON格式返回。

**核心原则（非常重要）：**
1. **原始文本准确性高**：以下提供的文本是从简历文件中直接提取的原始文本，其内容准确性较高，请严格按照原始文本中的实际内容进行提取
2. **分步骤提取**：请按照以下顺序进行提取：
   - 第一步：从原始文本中提取"个人信息"（姓名、性别、出生年份、手机号、邮箱）
   - 第二步：从原始文本中提取"学历信息"（最高学历、毕业学校、专业）
   - 第三步：从原始文本中提取"工作经历"（公司、岗位、时间）
3. **严格遵循原始文本**：不要自行推断、补充或修改任何信息，只提取原始文本中明确存在的内容
4. **如果信息不完整**：如果原始文本中某条信息不完整（如缺少时间或公司），该条信息可以返回null，但不要自行推断补充

**个人信息提取规则（第一步，优先从结构化字段中提取）：**
1. **优先查找位置**：如果原始文本中包含以下结构化字段，请优先从这些字段中提取：
   - "个人信息": {{ 或 "personal_info": {{
   - 这些字段中通常包含：姓名、出生年月、手机号、邮箱等信息
2. **姓名**：
   - 优先从"个人信息"或"personal_info"字段中提取
   - 如果结构化字段中没有，再从原始文本的其他位置查找
   - 仅提取姓名本身，不要包含"姓名："等标签文字
   - 不要提取城市名、公司名、职位名等
   - 姓名通常为2-6个中文字符
   - 如果原始文本中没有明确的姓名信息，返回null
3. **性别**：
   - 优先从"个人信息"或"personal_info"字段中提取
   - 如果结构化字段中没有，再从原始文本的其他位置查找
   - 提取"男"或"女"，如果无法确定则返回null
4. **出生年份**：
   - 优先从"个人信息"或"personal_info"字段中的"出生年月"、"出生日期"等字段提取
   - 如果结构化字段中没有，再从原始文本的其他位置查找（通常在"出生"、"生日"、"出生年月"等关键词附近）
   - 只提取出生年份（整数，如1990），不要提取工作年份、毕业年份等
   - 如果原始文本中没有明确的出生年份信息，返回null
5. **手机号**：
   - 优先从"个人信息"或"personal_info"字段中提取
   - 如果结构化字段中没有，再从原始文本的其他位置查找
   - 提取11位数字的手机号
   - 如果原始文本中没有手机号，返回null
6. **邮箱**：
   - 优先从"个人信息"或"personal_info"字段中提取
   - 如果结构化字段中没有，再从原始文本的其他位置查找
   - 提取邮箱地址
   - 如果原始文本中没有邮箱，返回null

**学历信息提取规则（第二步，优先从结构化字段中提取）：**
- **优先查找位置**：如果原始文本中包含以下结构化字段，请优先从这些字段中提取：
  - "教育背景": [ 或 "education_background": [
  - 这些字段中通常包含：学校、专业、学历等信息
- **如果结构化字段不存在**：请仔细在原始文本中查找以下关键词相关的段落或区域：
  - 关键词："教育"、"教育经历"、"教育背景"、"学历"、"毕业院校"、"学校"、"毕业学校"、"就读"、"毕业于"等
  - 查找方法：
    1. 搜索包含这些关键词的段落或行
    2. 在该段落前后50个字符范围内查找学校、专业、学历信息
    3. 注意识别常见的格式："学校名称 专业名称 学历" 或 "学历 学校名称 专业名称"
    4. 如果有多段教育经历，选择学历最高的那一段
- **只提取最高学历**：如果原始文本中有多段教育经历，只提取学历最高的那一段（学历等级：博士 > 硕士 > 本科 > 专科 > 高中 > 初中）
- **学校名称**：
  - 优先从"教育背景"或"education_background"字段中提取
  - 如果结构化字段中没有，再从原始文本中"教育"、"教育背景"、"学校"等相关字段中提取完整的学校名称
  - 去除"教育经历"、"教育背景"、"毕业院校"等前缀文字
  - 严格按照原始文本中的学校名称提取，不要修改或简化
- **专业名称**：
  - 优先从"教育背景"或"education_background"字段中提取
  - 如果结构化字段中没有，再从原始文本中学校名称前后提取专业信息，优先提取紧邻学校名称的专业字段
  - 如果原始文本中专业信息不明确，返回null，不要自行推断
- **示例1**：原始文本"教育经历：商洛学院， 生物制药工程专业，本科"
  - 应提取为：school="商洛学院", major="生物制药工程", highest_education="本科"
- **示例2**：原始文本"教育背景：2015-2019 北京大学 计算机科学与技术 本科"
  - 应提取为：school="北京大学", major="计算机科学与技术", highest_education="本科"
- **示例3**：如果原始文本中只有"本科"但没有明确的学校名称，则：
  - highest_education="本科", school=null, major=null

**工作经历提取规则（第三步，优先从结构化字段中提取，非常重要）：**
- **优先查找位置**：如果原始文本中包含以下结构化字段，请优先从这些字段中提取：
  - "工作经历": [ 或 "work_experience": [
  - 这些字段中通常包含：公司、岗位、时间等信息
- **如果结构化字段不存在**：请仔细在原始文本中查找以下关键词相关的段落或区域：
  - 关键词："工作经历"、"工作经验"、"职业经历"、"任职经历"、"工作履历"、"工作"、"就职"、"任职"等
  - 查找方法：
    1. 搜索包含这些关键词的段落或行
    2. 在该段落中逐条识别工作经历，常见格式：
       - "时间 公司名称 岗位名称"
       - "公司名称 岗位名称 时间"
       - "时间-时间 公司名称 岗位名称"
    3. 注意时间格式：2019.02-2020.05、2019-2020、2018.07—2019.01、2016.9-2019.2等
    4. 公司名称通常包含"公司"、"集团"、"企业"、"中心"、"研究院"等后缀
    5. 岗位名称通常较短（2-20个字符），不要将工作描述误认为岗位名称
- **提取原则**：原始文本中的工作经历内容准确性较高，请严格按照原始文本中的实际内容进行提取，不要自行推断、补充或修改任何信息
- **提取顺序**：按照原始文本中的时间顺序，从最新到最旧（倒序）提取工作经历
- **必须准确提取以下信息（严格按照原始文本）：**
  - **公司名称**：
    - 提取完整的公司全称，不要截断，不要省略任何部分
    - 不要包含工作描述、工作内容等文字
    - 不要将公司名称与其他信息混淆
    - 如果公司名称在原始文本中被换行分割，请完整合并提取
    - 示例：原始文本"陕西康华医药分公司"应完整提取为"陕西康华医药分公司"，不要提取为"康华医药"或"陕西康华"
  - **岗位/职位**：
    - 提取准确的职位名称，严格按照原始文本中的职位描述
    - 如果有多个职位用顿号"、"或逗号"，"分隔，请完整保留（如"储备干部、质量管理"）
    - 不要将工作内容、工作描述误认为是职位名称
    - 职位名称通常较短（2-20个字符），如果提取的内容过长，可能是误将工作描述当作职位
    - 示例：原始文本"储备干部、质量管理"应提取为"储备干部、质量管理"，不要提取为"储备干部"或"质量管理"
  - **时间**：必须准确提取开始时间和结束时间
    - 支持多种时间格式：2019.02-2020.05、2019-2020、2018.07—2019.01、2016.9-2019.2、2019.02至2020.05等
    - start_year：提取开始年份（整数，如2019），必须准确，不要提取错误
    - end_year：提取结束年份（整数，如2020），如果显示"至今"、"现在"、"现在"等，则返回null
    - 注意区分工作时间和出生年份、毕业年份等
- **提取步骤建议**：
  1. 首先定位"工作经历"、"工作经验"等关键词所在段落
  2. 逐条分析每条工作经历，按照"时间 公司 职位"或"公司 职位 时间"等格式识别
  3. 对于每条工作经历，严格按照原始文本中的顺序和内容提取，不要改变顺序
  4. 如果原始文本中某条信息不完整（如缺少时间或公司），该条信息可以返回null，但不要自行推断补充
- **常见错误避免**：
  - 不要将工作描述、工作内容误认为是职位名称
  - 不要将项目经历、实习经历误认为是正式工作经历（除非明确标注为工作经历）
  - 不要将公司名称和职位名称混淆
  - 不要将时间信息提取错误（如将毕业时间误认为工作时间）
- **示例1**：原始文本"2019.02-2020.05 陕西康华医药分公司 储备干部、质量管理"
  应提取为：
  {{
    "company": "陕西康华医药分公司",
    "position": "储备干部、质量管理",
    "start_year": 2019,
    "end_year": 2020
  }}
- **示例2**：原始文本"2018.07—2019.01 陕西华森特保健公司 保健品广告策划"
  应提取为：
  {{
    "company": "陕西华森特保健公司",
    "position": "保健品广告策划",
    "start_year": 2018,
    "end_year": 2019
  }}
- **示例3**：原始文本"2016.9-2019.2 北京科技有限公司 软件工程师\n负责系统开发工作"
  应提取为：
  {{
    "company": "北京科技有限公司",
    "position": "软件工程师",
    "start_year": 2016,
    "end_year": 2019
  }}
  注意："负责系统开发工作"是工作描述，不是职位名称，不要提取

**需要提取的字段（严格按照原始文本）：**
- name: 姓名（从原始文本中提取，仅姓名，2-6个中文字符，不要包含其他文字）
- gender: 性别（从原始文本中提取，"男"或"女"，如果无法确定则返回null）
- birth_year: 出生年份（从原始文本中提取，整数，如1990，只提取出生年份，不要提取工作年份）
- phone: 手机号（从原始文本中提取，11位数字）
- email: 邮箱地址（从原始文本中提取）
- highest_education: 最高学历（从原始文本中提取，"博士"、"硕士"、"本科"、"专科"、"高中"、"初中"等，只提取最高学历）
- school: 毕业学校名称（从原始文本中提取，完整的学校名称，去除"教育经历"等前缀，只提取最高学历对应的学校）
- major: 专业名称（从原始文本中提取，完整的专业名称，优先从学校前后提取，只提取最高学历对应的专业）
- work_experience: 工作经历数组（从原始文本中提取，按时间倒序，最新的在前），每个元素包含：
  - company: 公司名称（从原始文本中提取，完整的公司全称，必须准确）
  - position: 职位名称（从原始文本中提取，如果有多个职位用顿号分隔，必须准确）
  - start_year: 开始年份（从原始文本中提取，整数，如2019，必须准确）
  - end_year: 结束年份（从原始文本中提取，整数，如2020，如果至今则返回null，必须准确）

**原始文本（以下文本是从简历文件中直接提取的原始文本，准确性较高，请严格按照此文本进行提取）：**
{text}

**当原始文本没有结构化字段时的提取策略：**
1. **个人信息提取**：
   - 姓名：通常在文本开头或"姓名"、"名字"等关键词后，2-6个中文字符
   - 性别：在"性别"关键词后，或与姓名在同一行/段落
   - 出生年份：在"出生"、"生日"、"出生年月"等关键词后，通常是4位数字年份
   - 手机号：11位连续数字，可能在"手机"、"电话"、"联系方式"等关键词后
   - 邮箱：包含"@"符号，可能在"邮箱"、"Email"、"E-mail"等关键词后
2. **学历信息提取**：
   - 查找包含"教育"、"学历"、"学校"等关键词的段落
   - 识别格式："学校名称 专业名称 学历" 或 "学历 学校名称 专业名称"
   - 如果有多段，选择学历等级最高的（博士>硕士>本科>专科>高中>初中）
3. **工作经历提取**：
   - 查找包含"工作"、"经历"等关键词的段落
   - 逐条识别，每条通常包含：时间、公司名称、岗位名称
   - 注意区分工作描述和岗位名称（岗位名称通常较短）
   - 按时间倒序排列（最新的在前）

**最后提醒：**
- 以下提供的文本是**原始文本**，其准确性较高
- 请严格按照原始文本中的实际内容进行提取，不要自行推断、补充或修改
- 如果原始文本中信息不完整，返回null，不要自行补充
- 分步骤提取：先个人信息，再学历信息，最后工作经历
- 仔细分析文本结构，识别关键段落和关键词

请只返回JSON格式，不要包含任何其他文字说明。确保提取的信息准确无误，严格按照原始文本提取。JSON格式示例：
{{
  "name": "高峰",
  "gender": "男",
  "birth_year": 1990,
  "phone": "13800138000",
  "email": "gaofeng@example.com",
  "highest_education": "本科",
  "school": "商洛学院",
  "major": "生物制药工程",
  "work_experience": [
    {{
      "company": "陕西康华医药分公司",
      "position": "储备干部、质量管理",
      "start_year": 2019,
      "end_year": 2020
    }},
    {{
      "company": "陕西华森特保健公司",
      "position": "保健品广告策划",
      "start_year": 2018,
      "end_year": 2019
    }}
  ]
}}
"""
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """调用AI API（支持多种模型）"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # 根据模型类型构建请求数据
            if 'claude' in self.model.lower():
                # Claude模型使用不同的格式
                data = {
                    'model': self.model,
                    'max_tokens': 2000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': f'你是一个专业的简历信息提取助手。请准确提取简历中的关键信息，并以JSON格式返回。\n\n{prompt}'
                        }
                    ]
                }
            else:
                # OpenAI兼容格式（包括DeepSeek、Qwen等）
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
            
            # 构建完整的API URL
            api_url = f'{self.api_base}{self.api_endpoint}'
            
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=60  # 增加超时时间，某些模型可能需要更长时间
            )
            
            if response.status_code == 200:
                result = response.json()
                # 处理不同模型的响应格式
                if 'choices' in result:
                    # OpenAI格式
                    return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                elif 'content' in result:
                    # Claude格式
                    if isinstance(result['content'], list):
                        return result['content'][0].get('text', '')
                    return result.get('content', '')
                else:
                    # 其他格式，尝试通用提取
                    return str(result)
            else:
                error_msg = f"AI API调用失败: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", {error_detail}"
                except:
                    error_msg += f", {response.text[:200]}"
                print(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            print(f"AI API调用超时（模型: {self.model}）")
            return None
        except Exception as e:
            print(f"AI API调用异常（模型: {self.model}）: {e}")
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


