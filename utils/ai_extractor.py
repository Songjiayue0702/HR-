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
    
    def extract_with_ai(self, text: str, is_word_file: bool = False) -> Optional[Dict[str, Any]]:
        """
        使用AI提取简历信息
        
        Args:
            text: 简历文本内容
            is_word_file: 是否为Word格式文件
            
        Returns:
            提取的信息字典，如果失败返回None
        """
        if not self.enabled:
            return None
            
        try:
            # 智能处理长文本，避免简单截断导致JSON格式内容不全
            max_length = 40000  # 进一步增加长度限制，支持页数较多的简历（GPT-4等模型支持更长的输入）
            
            if len(text) > max_length:
                # 检查是否是JSON格式的文本
                text_stripped = text.strip()
                if text_stripped.startswith('{') or '"工作经历"' in text or '"教育经历"' in text or '"教育背景"' in text:
                    # 对于JSON格式，尝试智能提取关键部分
                    text = self._smart_truncate_json(text, max_length)
                else:
                    # 对于非JSON格式，采用智能截取，保留关键信息区域
                    text = self._smart_truncate_text(text, max_length)
            
            prompt = self._build_prompt(text, is_word_file=is_word_file)
            response = self._call_ai_api(prompt)
            
            if response:
                return self._parse_ai_response(response)
            return None
        except Exception as e:
            print(f"AI提取失败: {e}")
            return None
    
    def _smart_truncate_json(self, text: str, max_length: int) -> str:
        """
        智能截取JSON格式的文本，优先保留完整的结构化字段
        
        Args:
            text: 原始文本
            max_length: 最大长度
            
        Returns:
            截取后的文本
        """
        # 如果文本不是特别长，直接返回
        if len(text) <= max_length:
            return text
        
        # 尝试解析JSON，如果成功，只保留关键字段
        try:
            import json
            # 尝试解析JSON
            data = json.loads(text)
            
            # 构建包含关键字段的新JSON对象
            result_data = {}
            
            # 保留的关键字段（按优先级）
            key_fields = ['工作经历', '教育经历', '教育背景', '个人信息', '基本信息', '姓名', '性别', '手机', '邮箱']
            
            for key in key_fields:
                if key in data:
                    result_data[key] = data[key]
            
            # 额外处理：如果工作经历数组太长，保留所有条目的核心字段（时间、公司、岗位）
            if '工作经历' in result_data and isinstance(result_data['工作经历'], list):
                work_experiences = result_data['工作经历']
                if len(work_experiences) > 0:
                    # 精简每条工作经历，只保留核心字段
                    simplified_experiences = []
                    for exp in work_experiences:
                        if isinstance(exp, dict):
                            simplified_exp = {}
                            # 保留核心字段：时间、公司、职位/岗位
                            for field in ['时间', '公司', '职位', '岗位', 'position', 'company', 'period']:
                                if field in exp:
                                    simplified_exp[field] = exp[field]
                            if simplified_exp:
                                simplified_experiences.append(simplified_exp)
                        else:
                            simplified_experiences.append(exp)
                    result_data['工作经历'] = simplified_experiences
            
            # 如果没有找到关键字段，尝试查找类似的字段名
            if not result_data:
                for key in data.keys():
                    if any(kf in key for kf in ['工作', '教育', '个人', '基本', '姓名', '手机', '邮箱']):
                        result_data[key] = data[key]
            
            # 如果构建的新JSON仍然太长，则截取每个字段的内容
            result_json = json.dumps(result_data, ensure_ascii=False, indent=2)
            if len(result_json) <= max_length:
                return result_json
            else:
                # 如果还是太长，先尝试使用紧凑格式（无缩进）以节省空间
                compact_json = json.dumps(result_data, ensure_ascii=False, separators=(',', ':'))
                if len(compact_json) <= max_length:
                    return compact_json
                # 如果紧凑格式还是太长，进一步精简字段内容
                return self._truncate_json_fields(result_data, max_length)
                
        except (json.JSONDecodeError, Exception):
            # 如果解析失败，使用字符串方式提取关键字段
            pass
        
        # 字符串方式提取关键字段
        key_fields = ['"工作经历"', '"教育经历"', '"教育背景"', '"个人信息"', '"基本信息"']
        
        result_parts = []
        remaining_length = max_length
        
        # 提取文本开头部分（通常包含关键信息）
        start_text = text[:min(500, len(text))]
        if start_text and start_text.strip().startswith('{'):
            result_parts.append(start_text.rstrip().rstrip(',') + ',')
            remaining_length -= len(start_text)
        
        # 查找并提取关键字段的完整内容
        for field in key_fields:
            if remaining_length <= 200:
                break
                
            start_idx = text.find(field)
            if start_idx == -1:
                continue
            
            # 找到字段的开始位置（包含引号和冒号）
            field_start = text.rfind('"', 0, start_idx - 1)  # 找到前一个引号
            if field_start == -1:
                field_start = start_idx
            
            # 尝试找到字段的结束位置（匹配JSON结构）
            bracket_count = 0
            in_string = False
            escape_next = False
            field_end = field_start
            
            # 向前查找，找到该字段的开始（冒号之后）
            colon_pos = text.find(':', field_start)
            if colon_pos != -1:
                bracket_start = colon_pos + 1
                # 跳过空白字符
                while bracket_start < len(text) and text[bracket_start] in ' \n\t\r':
                    bracket_start += 1
                
                if bracket_start < len(text):
                    first_char = text[bracket_start]
                    if first_char == '{':
                        bracket_count = 1
                    elif first_char == '[':
                        bracket_count = 1
                    
                    for i in range(bracket_start + 1, min(bracket_start + remaining_length, len(text))):
                        char = text[i]
                        
                        if escape_next:
                            escape_next = False
                            continue
                            
                        if char == '\\':
                            escape_next = True
                            continue
                            
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                            
                        if not in_string:
                            if char == '{' or char == '[':
                                bracket_count += 1
                            elif char == '}' or char == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    field_end = i + 1
                                    break
                    
                    if field_end > bracket_start:
                        field_content = text[field_start:field_end]
                        if len(field_content) <= remaining_length:
                            result_parts.append(field_content)
                            remaining_length -= len(field_content)
        
        # 添加结束括号
        if result_parts:
            result = '\n'.join(result_parts)
            # 确保有结束括号
            if not result.rstrip().endswith('}'):
                result = result.rstrip().rstrip(',') + '\n}'
            
            if len(result) <= max_length:
                return result
        
        # 如果提取失败，返回截取后的文本（至少保留开头和结尾）
        return text[:max_length // 2] + '...' + text[-max_length // 2:]
    
    def _truncate_json_fields(self, data: dict, max_length: int) -> str:
        """
        截取JSON字段内容，使其不超过最大长度
        优先完整保留工作经历和教育经历的核心字段
        
        Args:
            data: JSON数据
            max_length: 最大长度
            
        Returns:
            截取后的JSON字符串
        """
        import json
        
        # 对每个字段的内容进行截取
        truncated_data = {}
        remaining = max_length - 200  # 预留一些空间给JSON格式符号
        
        # 优先处理关键字段
        priority_keys = ['工作经历', '教育经历', '教育背景', '个人信息', '基本信息']
        
        for key in priority_keys:
            if key in data and remaining > 200:
                value = data[key]
                
                if isinstance(value, list):
                    # 对于工作经历数组，保留所有条目的核心字段
                    if key == '工作经历':
                        truncated_list = []
                        for item in value:
                            if isinstance(item, dict):
                                # 只保留核心字段：时间、公司、职位/岗位
                                core_item = {}
                                for field in ['时间', '公司', '职位', '岗位', 'position', 'company', 'period', 'start_year', 'end_year']:
                                    if field in item:
                                        core_item[field] = item[field]
                                if core_item:
                                    truncated_list.append(core_item)
                            else:
                                truncated_list.append(item)
                        
                        # 序列化测试长度（使用紧凑格式以节省空间）
                        test_data = truncated_data.copy()
                        test_data[key] = truncated_list
                        test_json = json.dumps(test_data, ensure_ascii=False, separators=(',', ':'))
                        
                        if len(test_json) <= max_length:
                            truncated_data[key] = truncated_list
                            remaining = max_length - len(test_json)
                        else:
                            # 如果还是太长，尝试保留更多条目，逐步减少
                            # 优先保留所有条目的核心字段，而不是截断条目数量
                            # 但如果超过限制太多，最多保留前20条
                            max_items = min(20, len(truncated_list))
                            truncated_data[key] = truncated_list[:max_items]
                            # 重新计算剩余空间
                            test_data2 = truncated_data.copy()
                            test_data2[key] = truncated_list[:max_items]
                            test_json2 = json.dumps(test_data2, ensure_ascii=False, separators=(',', ':'))
                            remaining = max_length - len(test_json2)
                    else:
                        # 其他列表，保留前10个元素
                        truncated_data[key] = value[:min(10, len(value))]
                        remaining -= 1000
                elif isinstance(value, dict):
                    # 对于字典，保留所有字段（这些通常是基本信息）
                    test_data = truncated_data.copy()
                    test_data[key] = value
                    test_json = json.dumps(test_data, ensure_ascii=False, indent=2)
                    if len(test_json) <= max_length:
                        truncated_data[key] = value
                        remaining = max_length - len(test_json)
                    else:
                        # 如果太长，只保留关键字段
                        truncated_dict = {}
                        for k, v in value.items():
                            truncated_dict[k] = v
                            test_json2 = json.dumps(truncated_dict, ensure_ascii=False, indent=2)
                            if len(test_json2) < remaining:
                                truncated_dict[k] = v
                            else:
                                break
                        truncated_data[key] = truncated_dict
                        remaining -= 500
                else:
                    # 简单值，直接添加
                    truncated_data[key] = value
                    remaining -= 100
        
        # 处理其他字段
        for key, value in data.items():
            if key in priority_keys:
                continue
                
            if remaining <= 100:
                break
                
            if isinstance(value, (str, int, float, bool, type(None))):
                truncated_data[key] = value
                remaining -= 100
            elif isinstance(value, list) and remaining > 300:
                # 保留前5个元素
                truncated_data[key] = value[:min(5, len(value))]
                remaining -= 500
            elif isinstance(value, dict) and remaining > 300:
                # 保留前5个字段
                truncated_dict = {}
                for k, v in list(value.items())[:5]:
                    truncated_dict[k] = v
                truncated_data[key] = truncated_dict
                remaining -= 500
        
        result = json.dumps(truncated_data, ensure_ascii=False, indent=2)
        if len(result) > max_length:
            # 如果还是太长，使用紧凑格式
            result = json.dumps(truncated_data, ensure_ascii=False, separators=(',', ':'))
        
        return result[:max_length] if len(result) > max_length else result
    
    def _smart_truncate_text(self, text: str, max_length: int) -> str:
        """
        智能截取普通文本，优先保留关键信息区域
        
        Args:
            text: 原始文本
            max_length: 最大长度
            
        Returns:
            截取后的文本
        """
        if len(text) <= max_length:
            return text
        
        # 查找关键区域（工作经历、教育经历等）
        key_sections = ['工作经历', '工作经验', '教育经历', '教育背景', '个人信息', '基本信息']
        
        # 提取关键区域
        important_parts = []
        for section in key_sections:
            idx = text.find(section)
            if idx != -1:
                # 提取该区域及后续一定长度的内容
                section_text = text[idx:min(idx + 3000, len(text))]
                important_parts.append(section_text)
        
        # 如果找到了关键区域，优先保留这些区域
        if important_parts:
            result = text[:500]  # 保留开头
            remaining = max_length - 500
            for part in important_parts[:3]:  # 最多保留3个关键区域
                if len(part) <= remaining:
                    result += '\n...\n' + part
                    remaining -= len(part) + 5
                elif remaining > 200:
                    result += '\n...\n' + part[:remaining]
                    remaining = 0
                if remaining <= 200:
                    break
            return result[:max_length]
        
        # 如果没有找到关键区域，使用简单截取
        return text[:max_length] + "..."
    
    def _build_prompt(self, text: str, is_word_file: bool = False) -> str:
        """构建AI提示词（改进版，提高准确性）"""
        word_instructions = f'''

**Word格式文件特殊处理说明（重要）：**
如果原始文本来自Word文档，请注意以下特点：
1. **表格格式**：Word文档中的信息可能以表格形式呈现，表格中的信息可能是：
   - 键值对格式：第一列是标签（如"姓名"、"性别"、"出生年月"、"手机"、"邮箱"），第二列是值（如"张三"、"男"、"1990"、"13800138000"、"zhang@example.com"）
   - 列表格式：每行是一条记录（如工作经历列表，每行包含：时间、公司、岗位）
2. **段落格式**：信息可能分布在多个段落中，需要跨段落查找相关信息
3. **分栏布局**：某些信息可能采用分栏布局，左右两侧的信息需要分别识别
4. **提取策略（针对Word格式特别重要）**：
   - **个人信息提取**：
     * 优先从表格的键值对中提取（如表格中"姓名"对应"张三"）
     * 如果表格第一列包含"姓名"、"性别"、"出生"、"手机"、"邮箱"等关键词，第二列就是对应的值
     * 注意：表格中的值可能跨多个单元格，需要完整提取
   - **学历信息提取**：
     * 优先从表格中提取，表格可能包含"学校"、"专业"、"学历"等列
     * 如果表格第一列包含"学校"、"专业"、"学历"等关键词，对应列就是值
     * 注意识别表格中的行和列的关系，不要混淆
   - **工作经历提取**：
     * 如果工作经历在表格中，每行通常是一条工作经历
     * 表格列可能包含"时间"、"公司"、"岗位"等，需要识别列标题
     * 如果表格没有列标题，按照常见格式识别：时间、公司、岗位
   - **关键原则**：
     * 表格中的信息通常更准确，优先从表格中提取
     * 注意识别表格的行列关系，第一列通常是标签，后续列是值
     * 如果表格是列表格式（没有标签列），需要根据内容特征识别（如时间格式、公司后缀等）
''' if is_word_file else ''
        
        return f"""你是一个专业的简历信息提取助手。请仔细分析以下**原始文本**，准确提取结构化信息，并以JSON格式返回。

**核心原则（非常重要）：**
1. **原始文本准确性高**：以下提供的文本是从简历文件中直接提取的原始文本，其内容准确性较高，请严格按照原始文本中的实际内容进行提取
2. **分步骤提取**：请按照以下顺序进行提取：
   - 第一步：从原始文本中提取"个人信息"（姓名、性别、出生年份、手机号、邮箱）
   - 第二步：从原始文本中提取"学历信息"（最高学历、毕业学校、专业）
   - 第三步：从原始文本中提取"工作经历"（公司、岗位、时间）
3. **严格遵循原始文本**：不要自行推断、补充或修改任何信息，只提取原始文本中明确存在的内容
4. **如果信息不完整**：如果原始文本中某条信息不完整（如缺少时间或公司），该条信息可以返回null，但不要自行推断补充
{word_instructions}

**个人信息提取规则（第一步，优先从结构化字段，然后使用关键词定位法）：**

**提取优先级（严格按照以下顺序）：**
1. **第一优先级**：从结构化字段中提取（如果存在）
2. **第二优先级**：从关键词定位提取（如果结构化字段不存在或信息不完整）

**关键词列表（用于定位信息位置）：**
- 姓名关键词：姓名、名字、Name、name、中文名、真实姓名、姓 名
- 性别关键词：性别、Gender、gender、男、女
- 出生年份关键词：出生年月、出生日期、出生、生日、Birth、birth、Birthday、birthday、出生年份、出生年、出生年月日
- 手机号关键词：手机、手机号、手机号码、电话、联系电话、联系方式、联系手机、Tel、tel、Phone、phone、Mobile、mobile、移动电话、联系电话
- 邮箱关键词：邮箱、Email、email、E-mail、e-mail、电子邮箱、邮件地址、Mail、mail、电子信箱

**提取方法（优先从结构化字段，然后使用关键词定位法）：**
1. **姓名提取**：
   - **步骤0（第一优先级）**：如果原始文本中包含结构化字段，优先从以下字段中提取：
     * `"个人信息": {{ "姓名": "xxx" }}` 或 `"personal_info": {{ "name": "xxx" }}`
     * `"基本信息": {{ "姓名": "xxx" }}`
     * 这些字段中的姓名准确性最高，直接提取即可
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索姓名关键词（"姓名"、"名字"等）
   - 步骤2：找到关键词后，提取关键词后面的内容（通常在冒号、空格或换行后）
   - 步骤3：验证提取的内容：
     * 姓名通常为2-6个中文字符（常见为2-4个字符）
     * 不包含"姓名："等标签文字
     * 不是城市名、公司名、职位名、地址信息、证书名称等（如"大学英语四级"不是姓名）
     * 不要提取地址中的地名（如"现住址"后面的内容不是姓名）
     * 如果姓名前有单字（如"风高峰"、"凤高峰"），只提取姓名部分（如"高峰"），不要包含前缀
     * 如果提取的内容是证书名称、资格名称等，不是姓名
   - 步骤4：如果找不到姓名关键词，检查文本开头（前100个字符），看是否有明显的姓名格式
   - 步骤5：如果仍无法确定，返回null
   - 示例：原始文本`"个人信息": {{ "姓名": "邱曙光" }}` → 提取"邱曙光"
   - 示例：原始文本`"personal_info": {{ "name": "龙笑" }}` → 提取"龙笑"
   - 示例：原始文本"姓名：张三" → 提取"张三"
   - 示例：原始文本"姓名：风高峰" → 提取"高峰"（不要提取"风"字）
   - 错误示例：不要提取"大学英语四级"（这是证书名称，不是姓名）
   - 错误示例：不要提取"现住址：李楠"中的"现住址"（这是地址标签，姓名是"李楠"）

2. **性别提取**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取，直接使用字段中的"性别"或"gender"值
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索性别关键词（"性别"、"Gender"等）
   - 步骤2：找到关键词后，提取关键词后面的内容（通常在冒号、空格后）
   - 步骤3：验证提取的内容是否为"男"或"女"
   - 步骤4：如果找不到性别关键词，检查姓名所在行或相邻行是否有"男"或"女"
   - 步骤5：如果无法确定，返回null
   - 示例：原始文本"性别：男" → 提取"男"
   - 示例：原始文本"性别 女" → 提取"女"

3. **出生年份提取**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取，直接使用字段中的"出生年月"、"出生日期"、"birth"等值
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索出生年份关键词（"出生年月"、"出生日期"、"出生"、"生日"等）
   - 步骤2：找到关键词后，在关键词附近（前后50个字符）查找4位数字年份（通常是19xx或20xx）
   - 步骤3：验证提取的年份：
     * 年份范围通常在1950-2010之间（出生年份）
     * 不要提取工作年份、毕业年份等
     * 如果关键词后是完整日期（如"1990年5月"），只提取年份部分
   - 步骤4：如果找不到出生年份关键词，检查文本前200个字符中是否有明显的出生年份格式
   - 步骤5：如果无法确定，返回null
   - 示例：原始文本"出生年月：1990年5月" → 提取1990
   - 示例：原始文本"出生日期 1985" → 提取1985
   - 错误示例：不要提取"2019年参加工作"中的2019（这是工作年份）

4. **手机号提取**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取，直接使用字段中的"手机"、"电话"、"phone"等值
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索手机号关键词（"手机"、"电话"、"联系方式"等）
   - 步骤2：找到关键词后，在关键词附近查找11位连续数字
   - 步骤3：验证提取的数字：
     * 必须是11位数字
     * 通常以1开头（如138、139、150等）
     * 可能包含空格或连字符，需要去除后验证
   - 步骤4：如果找不到手机号关键词，在整个文本中搜索11位数字模式
   - 步骤5：如果无法确定，返回null
   - 示例：原始文本"手机：13800138000" → 提取"13800138000"
   - 示例：原始文本"联系电话 150-1234-5678" → 提取"15012345678"（去除连字符）

5. **邮箱提取**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取，直接使用字段中的"邮箱"、"Email"、"email"等值
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索邮箱关键词（"邮箱"、"Email"、"E-mail"等）
   - 步骤2：找到关键词后，在关键词附近查找包含"@"符号的字符串
   - 步骤3：验证提取的邮箱：
     * 必须包含"@"符号
     * "@"前后都有内容
     * 通常包含"."符号（域名）
   - 步骤4：如果找不到邮箱关键词，在整个文本中搜索包含"@"的字符串
   - 步骤5：如果无法确定，返回null
   - 示例：原始文本"邮箱：zhang@example.com" → 提取"zhang@example.com"
   - 示例：原始文本"Email zhang.san@company.com" → 提取"zhang.san@company.com"

**学历信息提取规则（第二步，优先从结构化字段，然后使用关键词定位法）：**

**提取优先级（严格按照以下顺序）：**
1. **第一优先级**：从结构化字段中提取（如果存在）
2. **第二优先级**：从关键词定位提取（如果结构化字段不存在或信息不完整）

**关键词列表（用于定位信息位置）：**
- 教育相关关键词：教育经历、教育背景、教育、学历、毕业院校、毕业学校、学校、院校、就读、毕业于、毕业、Education、education、Educational Background、教育信息
- 学历等级关键词：博士、硕士、研究生、本科、学士、大专、专科、高中、中专、职高、初中、PhD、phd、Master、master、Bachelor、bachelor、College、college、本科学历、专科学历、硕士学历
- 专业相关关键词：专业、主修专业、所学专业、专业方向、Major、major、Specialty、specialty、专业名称

**提取方法（优先从结构化字段，然后使用关键词定位法）：**
1. **定位教育信息区域**：
   - **步骤0（第一优先级）**：如果原始文本中包含结构化字段，优先从以下字段中提取：
     * `"教育背景": [ ... ]` 或 `"education_background": [ ... ]`
     * `"教育经历": [ ... ]`
     * 这些字段中的信息准确性最高，优先提取
     * **重要提示**：如果原始文本本身是完整的JSON格式（以`{{`开头和`}}`结尾，或包含完整的JSON对象结构），请先识别这是一个JSON对象，然后从JSON对象的`"教育背景"`、`"教育经历"`或`"education_background"`字段中直接提取
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索教育相关关键词（"教育经历"、"教育背景"、"学历"等）
   - 步骤2：找到关键词后，将该关键词所在段落及其前后各2行作为教育信息区域
   - 步骤3：如果找不到明确的教育关键词，搜索学历等级关键词（"本科"、"硕士"等），找到后将其所在段落作为教育信息区域

2. **提取最高学历**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"学历": "xxx"`、`"degree": "xxx"`、`"教育程度": "xxx"`、`"education": "xxx"`），直接使用这些值（**重要：当键名是"学历"、"degree"、"教育程度"、"education"时，必须提取其值作为highest_education字段**）
     * 如果对象中没有明确的键值对，但对象是数组或字符串格式，按照"学校，专业，学历"或"学历，学校，专业"等顺序识别
   - **步骤1（第二优先级）**：如果结构化字段中没有，在教育信息区域中搜索所有学历等级关键词
   - 步骤2：按照学历等级排序（博士 > 硕士 > 本科 > 专科 > 高中 > 初中），选择等级最高的
   - 步骤3：如果找到多个学历等级，只提取等级最高的那一个
   - 步骤4：验证提取的学历：
     * 如果原始文本中有"本科学历"，应提取为"本科"或"本科学历"（根据原始文本）
     * 不要将"高中"误认为是学校名称的一部分
   - 步骤5：如果找不到学历等级关键词，返回null
   - 示例：原始文本`"教育背景": {{ "学历": "本科学历" }}` → 提取"本科学历"
   - 示例：原始文本中有"专科"和"本科"，只提取"本科"
   - 示例：原始文本"本科学历" → 提取"本科学历"（保留原始格式）

3. **提取学校名称**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"学校": "xxx"`、`"school": "xxx"`、`"毕业院校": "xxx"`、`"院校": "xxx"`），直接使用这些值（**重要：当键名是"学校"、"school"、"毕业院校"、"院校"时，必须提取其值作为school字段**）
     * 如果对象中没有明确的键值对，但对象是数组或字符串格式，按照"学校，专业，学历"或"学历，学校，专业"等顺序识别：
       - 查找包含学校关键词的字符串（如"大学"、"学院"、"学校"等）
       - 如果找到学校关键词，提取包含该关键词的完整学校名称
   - **步骤1（第二优先级）**：如果结构化字段中没有，在教育信息区域中搜索学校关键词（"学校"、"学院"、"大学"等）
   - 步骤2：找到学校关键词后，提取包含该关键词的完整学校名称
   - 步骤3：验证提取的学校名称：
     * 通常包含"大学"、"学院"、"学校"等后缀
     * 去除"教育经历"、"教育背景"、"毕业院校"等前缀文字
     * 不要包含专业名称、学历等级等信息
     * 不要包含"高中"等学历等级词汇（如"XX大学高中"、"黑龙江明水县一中高中"是错误的，应只提取"XX大学"或"黑龙江明水县一中"）
     * 如果学校名称后紧跟着专业或系（如"陕西师范大学 历史系"），只提取学校名称部分（"陕西师范大学"）
     * 如果有多段教育经历，只提取最高学历对应的学校
   - 步骤4：如果找不到学校名称，返回null
   - 示例：原始文本`"教育背景": {{ "学校": "商洛学院" }}` → 提取"商洛学院"
   - 示例：原始文本`"education_background": [ {{ "school": "陕西师范大学", "major": "历史系" }} ]` → 提取"陕西师范大学"（不要包含"历史系"）
   - 示例：原始文本"教育经历：商洛学院， 生物制药工程专业，本科" → 提取"商洛学院"
   - 示例：原始文本"黑龙江明水县一中高中" → 提取"黑龙江明水县一中"（去除"高中"）
   - 错误示例：不要提取"教育经历：商洛学院"中的"教育经历：商洛学院"（应只提取"商洛学院"）
   - 错误示例：不要提取"XX大学高中"（应只提取"XX大学"，去除"高中"）

4. **提取专业名称**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"专业": "xxx"`、`"major": "xxx"`、`"专业名称": "xxx"`、`"所学专业": "xxx"`），直接使用这些值（**重要：当键名是"专业"、"major"、"专业名称"、"所学专业"时，必须提取其值作为major字段**）
     * 如果对象中没有明确的键值对，但对象是数组或字符串格式，按照"学校，专业，学历"或"学历，学校，专业"等顺序识别：
       - 在学校和学历之间查找专业信息
       - 专业通常是2-20个字符，不包含学历等级关键词
   - **步骤1（第二优先级）**：如果结构化字段中没有，在教育信息区域中，优先在学校名称前后50个字符范围内搜索专业信息
   - 步骤2：搜索专业相关关键词（"专业"、"主修专业"、"系"等）
   - 步骤3：找到专业关键词后，提取关键词后面的内容，或提取紧邻学校名称的专业字段
   - 步骤4：验证提取的专业名称：
     * 通常不包含"专业"、"方向"等后缀（如果包含，可以保留，如"生物制药工程专业"）
     * 不要包含学历等级、学校名称等信息
     * 不要将工作描述误认为专业名称
     * 不要包含"政治面貌"、"党员"、"团员"等非专业信息（如"矿井建设政治面貌"是错误的，应只提取"矿井建设"）
     * 如果专业名称中包含"系"（如"历史系"），可以保留"系"字
     * 专业名称通常为2-20个中文字符
     * 如果有多段教育经历，只提取最高学历对应的专业
   - 步骤5：如果找不到专业信息，返回null
   - 示例：原始文本`"教育背景": {{ "专业": "生物制药工程专业" }}` → 提取"生物制药工程专业"（保留"专业"后缀）
   - 示例：原始文本`"education_background": [ {{ "major": "历史系" }} ]` → 提取"历史系"
   - 示例：原始文本"商洛学院， 生物制药工程专业，本科" → 提取"生物制药工程专业"（保留"专业"后缀）
   - 示例：原始文本"专业：人力资源管理" → 提取"人力资源管理"
   - 示例：原始文本"专业：矿井建设 政治面貌：群众" → 提取"矿井建设"（不要包含"政治面貌"）
   - 错误示例：不要提取"专业：管理客户"中的"管理客户"（这是工作描述，不是专业名称）
   - 错误示例：不要提取"专业：XX专业 政治面貌：党员"中的"XX专业 政治面貌"（应只提取"XX专业"）

5. **完整示例**：
   - 示例1：原始文本"教育经历：商洛学院， 生物制药工程专业，本科"
     * 定位：找到"教育经历"关键词
     * 最高学历：找到"本科"
     * 学校名称：找到"商洛学院"
     * 专业名称：找到"生物制药工程专业"，提取为"生物制药工程专业"
     * 结果：school="商洛学院", major="生物制药工程专业", highest_education="本科"
   - 示例2：原始文本"教育背景：2015-2019 北京大学 计算机科学与技术 本科"
     * 定位：找到"教育背景"关键词
     * 最高学历：找到"本科"
     * 学校名称：找到"北京大学"
     * 专业名称：找到"计算机科学与技术"
     * 结果：school="北京大学", major="计算机科学与技术", highest_education="本科"
   - 示例3：原始文本中只有"本科"但没有明确的学校名称
     * 结果：highest_education="本科", school=null, major=null
   - 示例4（完整JSON格式，结构化字段）：如果原始文本是完整的JSON对象，例如：
     ```
     {{
       "教育经历": [
         {{
           "学校": "北京大学",
           "专业": "计算机科学与技术",
           "学历": "本科",
           "时间": "2015-2019"
         }}
       ]
     }}
     ```
     或
     ```
     {{
       "教育背景": {{
         "学校": "商洛学院",
         "专业": "生物制药工程专业",
         "学历": "本科"
       }}
     }}
     ```
     * **处理步骤（必须严格按照此步骤执行）**：
       1. **首先识别**：原始文本是完整的JSON对象
       2. **提取教育信息**：
          - 如果JSON中有`"教育经历"`数组，从数组中提取最高学历对应的教育信息
          - 如果JSON中有`"教育背景"`或`"education_background"`对象，直接从对象中提取
       3. **提取字段**：
          - 从对象中直接提取`"学历": "本科"` → highest_education="本科"（**注意：键名可能是"学历"、"degree"、"教育程度"、"education"等，都要识别**）
          - 从对象中直接提取`"学校": "北京大学"` → school="北京大学"（**注意：键名可能是"学校"、"school"、"毕业院校"、"院校"等，都要识别**）
          - 从对象中直接提取`"专业": "计算机科学与技术"` → major="计算机科学与技术"（**注意：键名可能是"专业"、"major"、"专业名称"、"所学专业"等，都要识别**）
       4. **如果有多段教育经历**：选择学历等级最高的（博士 > 硕士 > 本科 > 专科 > 高中 > 初中）
     * 最终结果：{{"highest_education": "本科", "school": "北京大学", "major": "计算机科学与技术"}}

**工作经历提取规则（第三步，使用关键词定位法，非常重要）：**

**提取优先级（严格按照以下顺序）：**
1. **第一优先级**：从结构化字段中提取（如果存在）
2. **第二优先级**：从关键词定位提取（如果结构化字段不存在或信息不完整）

**提取方法（优先从结构化字段，然后使用关键词定位法）：**
1. **定位工作经历区域（工作经历模块）**：
   - **步骤0（第一优先级）**：如果原始文本中包含结构化字段，优先从以下字段中提取：
     * `"工作经历": [ ... ]` 或 `"work_experience": [ ... ]`
     * 这些字段中的信息准确性最高，优先提取
     * **重要提示**：如果原始文本本身是完整的JSON格式（以`{{`开头和`}}`结尾，或包含完整的JSON对象结构），请先识别这是一个JSON对象，然后从JSON对象的`"工作经历"`或`"work_experience"`字段中直接提取
     * 在JSON对象中，键名`"岗位"`、`"职位"`、`"position"`都表示职位名称（"岗位"等同于"职位"），应该同等处理和提取
   - **步骤1（第二优先级）**：如果结构化字段中没有，从简历文本中定位"工作经历"区域：
     * **搜索关键词**：
       - 中文：工作经历、工作经验、职业经历、任职经历、工作履历、就职经历
       - 英文：Work Experience、work experience、Employment、Career
     * **识别方法**：
       - 找到关键词后，将该关键词所在段落及其后续内容作为"工作经历模块"
       - 如果找不到明确关键词，但文本中有时间格式（如"2019.02-2020.05"）配合公司关键词（如"公司"、"集团"等），也视为工作经历模块
     * **重要规则**：
       - **位置灵活性**：简历顺序可能不同，允许工作经历模块在"原始文本"的任意位置（可能在个人信息之前、之后，或在教育经历之前、之后等），需要在整个文本中搜索，不要局限于某个固定位置
       - **重要注意**：不要将"教育经历"、"项目经历"、"实习经历"误认为工作经历模块（除非明确标注为工作经历）

2. **从工作经历模块中提取每条工作经历**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 直接遍历数组中的每个对象，每个对象就是一条工作经历
     * 对于每个对象，按以下顺序提取：
       a. 如果对象中有明确的键值对（如`"时间": "xxx"`、`"公司": "xxx"`、`"职位": "xxx"`、`"岗位": "xxx"`、`"position": "xxx"`），直接使用这些值（**重要：当键名是"岗位"时，必须提取其值作为position字段，不要跳过。键名"岗位"、"职位"、"position"都表示职位名称，应该同等处理**）
       b. 如果对象中没有明确的键值对，但对象是数组或字符串格式，按照以下顺序识别：
          - 顺序1："时间，公司，职位"（如`["2019.02-2020.05", "陕西康华医药分公司", "储备干部"]`）
          - 顺序2："公司，职位，时间"（如`["陕西康华医药分公司", "储备干部", "2019.02-2020.05"]`）
          - 顺序3："时间 公司 职位"（如`"2019.02-2020.05 陕西康华医药分公司 储备干部"`）
          - 顺序4："公司 职位 时间"（如`"陕西康华医药分公司 储备干部 2019.02-2020.05"`）
       c. 识别规则：
          - 时间：查找时间格式（如"2019.02-2020.05"、"2019-2020"等）
          - 公司：查找包含公司关键词的字符串（如"公司"、"集团"等）
          - 职位：查找公司后面的内容，通常是2-20个字符
   - **步骤1（第二优先级）**：如果结构化字段中没有，从工作经历模块中，按"时间、公司、职位"为一组，提取每条工作经历：
     * **分组原则**：以一组"时间、公司、职位"为一条工作经历
     * **识别起始标志**：
       - 时间格式（如"2019.02-2020.05"、"2019-2020"、"2025年至今"等）
       - 段落分隔（空行或明显的段落边界）
       - 新的公司名称出现
     * **重要规则**：
       - **跨行提取**：允许时间、公司、岗位不是连续行，可以在3行以内（包括当前行、下一行、下两行、下三行）进行跨行提取
       - 例如：如果第1行是时间"2019.02-2020.05"，第2行是空行或描述，第3行是公司"陕西康华医药分公司"，第4行是职位"储备干部"，这仍然是一条完整的工作经历
       - 如果时间、公司、职位之间的间隔超过3行，则视为不同的工作经历条目
     * **提取字段**：
       - **时间**：必需字段
         * 格式：2019.02-2020.05、2019-2020、2018.07—2019.01、2019.02至2020.05、2025年至今等
         * 提取 start_year（开始年份，如2019）和 end_year（结束年份，如2020；如果"至今"则为null）
         * 如果时间在某一行，可以在该行及后续3行内查找对应的公司和职位
       - **公司**：可选字段（可能为null）
         * 识别包含公司关键词的字符串：公司、集团、企业、中心、研究院、事务所、律所、有限公司等
         * 提取完整公司全称
         * 如果找不到公司名称，返回null
         * 特殊情况：备考、学习、培训等可能没有公司名称
         * 如果时间在某一行，可以在该行及后续3行内查找对应的公司
       - **职位**：可选字段（可能为null）
         * 从公司名称后面或时间后面提取
         * 如果找不到职位名称，返回null
         * 特殊情况：备考、学习等可能没有职位名称
         * 如果时间或公司在某一行，可以在该行及后续3行内查找对应的职位
     * **特殊情况处理**：
       - **只有时间，没有公司和职位**：
         * 示例："2017.08-2018.06 描述：备考北京中医药大学中药化学研究生"
         * 提取：{{"start_year": 2017, "end_year": 2018, "company": null, "position": null}}
       - **有时间和公司，没有职位**：
         * 示例："2020.07-2020.09 兼职考研机构助教老师"
         * 提取：{{"start_year": 2020, "end_year": 2020, "company": "考研机构", "position": "助教老师"}}
       - **有多个职位**：
         * 示例："职位：储备干部、质量管理"
         * 提取：{{"position": "储备干部、质量管理"}}（保留顿号分隔）
       - **跨行提取示例**：
         * 示例1（时间在第1行，公司在第3行，职位在第4行）：
           ```
           2019.02-2020.05
           工作描述：负责质量管理
           陕西康华医药分公司
           储备干部、质量管理
           ```
           * 提取：{{"start_year": 2019, "end_year": 2020, "company": "陕西康华医药分公司", "position": "储备干部、质量管理"}}
         * 示例2（时间在第1行，公司在第2行，职位在第3行）：
           ```
           2018.07—2019.01
           陕西华森特保健公司
           保健品广告策划
           ```
           * 提取：{{"start_year": 2018, "end_year": 2019, "company": "陕西华森特保健公司", "position": "保健品广告策划"}}
         * 示例3（时间、公司、职位都在不同行，但都在3行以内）：
           ```
           2019.02-2020.05
           陕西康华医药分公司
           储备干部、质量管理
           ```
           * 提取：{{"start_year": 2019, "end_year": 2020, "company": "陕西康华医药分公司", "position": "储备干部、质量管理"}}
     * **提取顺序**：
       - 按时间倒序（最新的在前）
       - 如果时间相同，按文本出现顺序
   - **重要**：不要将教育经历中的时间（如"2006/9-2009/7"、"2013.9-2016.6"、"2020年9月-2023年6月"）误认为是工作时间
3. **提取时间信息（必需字段）**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"时间": "2019.02-2020.05"`、`"period": "2019-2020"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，职位"或"公司，职位，时间"等顺序识别：
       - 查找时间格式（如"2019.02-2020.05"、"2019-2020"等）
       - 如果找到时间格式，提取该时间
   - **步骤1（第二优先级）**：如果结构化字段中没有，在每条工作经历条目中搜索时间格式：
     * 支持格式：2019.02-2020.05、2019-2020、2018.07—2019.01、2016.9-2019.2、2019.02至2020.05等
     * 支持格式：2019年2月-2020年5月、2019/02-2020/05等
     * 支持格式：2025年至今、2025年-至今、2025至今、2025.03-至今等
   - 步骤2：从时间格式中提取开始年份和结束年份：
     * start_year：提取开始年份（整数，如2019）
     * end_year：提取结束年份（整数，如2020），如果显示"至今"、"现在"、"现在"等，则返回null
     * 注意："2025年至今"应提取为start_year=2025, end_year=null
     * 注意："2025.03-至今"应提取为start_year=2025, end_year=null
   - 步骤3：验证提取的年份：
     * 年份范围通常在1980-当前年份+1之间（考虑未来年份，如2025）
     * 不要提取出生年份、毕业年份等
     * **非常重要**：不要将教育经历中的时间误认为是工作时间：
       - 如果时间格式出现在"教育背景"、"教育经历"、"education_background"等字段中，不是工作时间
       - 如果时间格式后紧跟着学校名称（如"2006/9-2009/7 西安外事学院"、"2013.9-2016.6 实验中学"、"2020年9月-2023年6月 西北大学"），不是工作时间
       - 工作时间通常在教育时间之后（如果教育时间是2015-2019，工作时间应该是2019年之后）
   - 步骤4：如果找不到时间信息，返回null
   - 示例：原始文本`"工作经历": [ {{ "时间": "2019.02-2020.05" }} ]` → start_year=2019, end_year=2020
   - 示例：原始文本"2019.02-2020.05" → start_year=2019, end_year=2020
   - 示例：原始文本"2025年至今" → start_year=2025, end_year=null
   - 示例：原始文本"2025.03-至今" → start_year=2025, end_year=null
   - 错误示例：不要提取"2006/9-2009/7 西安外事学院"中的2006-2009（这是教育时间，不是工作时间）
   - 错误示例：不要提取"2013.9-2016.6 实验中学"中的2013-2016（这是教育时间，不是工作时间）

4. **提取公司名称（可选字段，可能为null）**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"公司": "xxx"`、`"company": "xxx"`、`"单位": "xxx"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，职位"或"公司，职位，时间"等顺序识别：
       - 查找包含公司关键词的字符串（如"公司"、"集团"、"企业"等）
       - 如果找到公司关键词，提取包含该关键词的完整公司名称
   - **步骤1（第二优先级）**：如果结构化字段中没有，在每条工作经历条目中搜索公司关键词（"公司"、"集团"、"企业"、"中心"、"研究院"、"事务所"、"律所"、"律师事务所"、"有限公司"等）
   - **重要**：
     * 识别包含公司关键词的字符串：公司、集团、企业、中心、研究院、事务所、律所、有限公司等
     * 提取完整公司全称
     * 如果找不到公司名称，返回null
     * 特殊情况：备考、学习、培训等可能没有公司名称
   - 步骤2：找到公司关键词后，提取包含该关键词的完整公司名称
   - 步骤3：验证提取的公司名称：
     * 通常包含"公司"、"集团"、"企业"、"中心"、"研究院"、"事务所"、"律师事务所"、"律所"等后缀
     * 提取完整的公司全称，不要截断（如"上海仁联人力资源有限公司"应完整提取，不要只提取"上海仁联"）
     * 不要包含工作描述、工作内容等文字（如"按时保质地满足公司"不是公司名称）
     * 不要将岗位名称误认为公司名称
     * 不要将教育相关的描述误认为公司名称（如"毕业留校担任南昌职业大学"不是公司名称）
     * 如果公司名称在原始文本中被换行分割，需要完整合并提取
   - 步骤4：如果找不到公司名称，检查是否包含公司特征词（如"有限公司"、"股份"等），即使没有明确的"公司"关键词
   - 步骤5：如果仍找不到公司名称，返回null
   - 示例：原始文本`"工作经历": [ {{ "公司": "上海仁联人力资源有限公司" }} ]` → 提取"上海仁联人力资源有限公司"（完整名称）
   - 示例：原始文本`"work_experience": [ {{ "company": "字节跳动瓜瓜龙启蒙" }} ]` → 提取"字节跳动瓜瓜龙启蒙"
   - 示例：原始文本"陕西康华医药分公司" → 提取"陕西康华医药分公司"（完整名称）
   - 示例：原始文本"上海仁联人力资源有限公司" → 提取"上海仁联人力资源有限公司"（完整名称，不要截断）
   - 错误示例：不要提取"按时保质地满足公司"（这是工作描述，不是公司名称）
   - 错误示例：不要提取"上海仁联"（不完整，应为"上海仁联人力资源有限公司"）

5. **提取职位名称（可选字段，可能为null）**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"职位": "xxx"`、`"position": "xxx"`、`"岗位": "xxx"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，职位"或"公司，职位，时间"等顺序识别：
       - 在时间、公司之后查找职位信息
       - 职位通常是2-20个字符，不包含工作描述关键词
   - **步骤1（第二优先级）**：如果结构化字段中没有，在每条工作经历条目中，优先从公司名称后面或时间后面提取职位信息
   - **重要**：
     * 从公司名称后面或时间后面提取
     * 如果找不到职位名称，返回null
     * 特殊情况：备考、学习等可能没有职位名称
     * 如果有多个职位用顿号"、"或逗号"，"分隔，请完整保留（如"储备干部、质量管理"）
   - 步骤2：搜索岗位关键词（"岗位"、"职位"、"担任"、"任职"、"职务"等），找到后提取关键词后面的内容
   - 步骤3：如果没有岗位关键词，提取公司名称后面的内容作为岗位候选
   - 步骤4：验证提取的岗位名称：
     * 岗位名称通常较短（2-20个字符，常见为2-10个字符）
     * 不要将工作描述、工作内容误认为是岗位名称（如"responsibilities : ["不是岗位名称）
     * 不要将描述性文字误认为是岗位名称（如"描述 : 备考北京中医药大学中药化学研究生"不是岗位名称）
     * 如果有多个职位用顿号"、"或逗号"，"分隔，请完整保留（如"储备干部、质量管理"）
     * 如果提取的内容过长（超过30个字符），可能是误将工作描述当作岗位
     * 岗位名称可能包含：市场营销、网络营销、销售、工程师、经理、主管、专员、助理、律师助理、副总、中控/场控/助播等
     * 注意识别岗位名称，即使原始文本中没有明确的"岗位"、"职位"等关键词
   - 步骤5：如果找不到岗位信息，检查公司名称后面的内容，看是否符合岗位名称特征
   - 步骤6：如果仍找不到岗位信息，返回null
   - 示例：原始文本`"工作经历": [ {{ "职位": "市场营销" }} ]` → 提取"市场营销"
   - 示例：原始文本`"工作经历": [ {{ "岗位": "市场营销" }} ]` → 提取"市场营销"
   - 示例：原始文本`"work_experience": [ {{ "position": "网络营销" }} ]` → 提取"网络营销"
   - 示例：原始文本"储备干部、质量管理" → 提取"储备干部、质量管理"（完整保留）
   - 示例：原始文本"软件工程师\n负责系统开发工作" → 提取"软件工程师"（不要提取"负责系统开发工作"）
   - 示例：原始文本"公司名称 市场营销" → 提取"市场营销"（即使没有"岗位"关键词）
   - 错误示例：不要提取"responsibilities : ["（这是工作描述标签，不是岗位名称）
   - 错误示例：不要提取"描述 : 备考北京中医药大学中药化学研究生"（这是描述，不是岗位名称）

6. **提取顺序**：
   - 按时间倒序（最新的在前）
   - 如果时间相同，按文本出现顺序
7. **完整示例**：
   - 示例1（结构化字段，有明确键值对）：原始文本`"工作经历": [ {{ "时间": "2019.02-2020.05", "公司": "陕西康华医药分公司", "职位": "储备干部、质量管理" }} ]`
     * 直接从结构化字段提取：time="2019.02-2020.05", company="陕西康华医药分公司", position="储备干部、质量管理"
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例1a（结构化字段，使用"岗位"键名）：原始文本`"工作经历": [ {{ "时间": "2019.02-2020.05", "公司": "陕西康华医药分公司", "岗位": "储备干部、质量管理" }} ]`
     * 直接从结构化字段提取：time="2019.02-2020.05", company="陕西康华医药分公司", position="储备干部、质量管理"
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例1b（完整JSON格式，使用"岗位"键名，"至今"时间格式）：如果原始文本是完整的JSON对象，例如：
     ```
     {{
       "工作经历": [
         {{
           "公司": "西安博海新思迈企业管理咨询有限公司",
           "时间": "2020.09-至今",
           "岗位": "市场营销"
         }},
         {{
           "公司": "西安毓秀企业文化传播有限公司",
           "时间": "2018.12-2020.07",
           "岗位": "网络营销"
         }}
       ]
     }}
     ```
     * **处理步骤（必须严格按照此步骤执行）**：
       1. **首先识别**：原始文本是完整的JSON对象
       2. **提取工作经历数组**：从JSON对象的`"工作经历"`字段中提取数组
       3. **遍历数组中的每个对象**：每个对象就是一条工作经历
       4. **对于第一条工作经历**：
          - 从对象中直接提取`"公司": "西安博海新思迈企业管理咨询有限公司"` → company="西安博海新思迈企业管理咨询有限公司"
          - 从对象中直接提取`"时间": "2020.09-至今"` → start_year=2020, end_year=null（因为"至今"表示当前还在职）
          - **关键步骤**：从对象中直接提取`"岗位": "市场营销"` → position="市场营销"（**注意：即使键名是"岗位"而不是"职位"，也必须提取其值**）
       5. **对于第二条工作经历**：
          - company="西安毓秀企业文化传播有限公司"
          - start_year=2018, end_year=2020
          - position="网络营销"（**同样：键名是"岗位"，必须提取**）
     * 最终结果：{{"work_experience": [{{"company": "西安博海新思迈企业管理咨询有限公司", "position": "市场营销", "start_year": 2020, "end_year": null}}, {{"company": "西安毓秀企业文化传播有限公司", "position": "网络营销", "start_year": 2018, "end_year": 2020}}]}}
   - 示例2（结构化字段，无明确键值对，按顺序识别）：原始文本`"工作经历": [ ["2019.02-2020.05", "陕西康华医药分公司", "储备干部、质量管理"] ]`
     * 按照"时间，公司，职位"顺序识别：
       - 第1个元素："2019.02-2020.05" → 时间
       - 第2个元素："陕西康华医药分公司" → 公司
       - 第3个元素："储备干部、质量管理" → 职位
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例3（结构化字段，无明确键值对，字符串格式）：原始文本`"工作经历": [ "2019.02-2020.05 陕西康华医药分公司 储备干部、质量管理" ]`
     * 按照"时间 公司 职位"顺序识别：
       - 找到时间格式："2019.02-2020.05" → 时间
       - 找到公司关键词："陕西康华医药分公司" → 公司
       - 公司后面的内容："储备干部、质量管理" → 职位
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例4（无结构化字段，从关键词提取，完整信息）：原始文本"2018.07—2019.01 陕西华森特保健公司 保健品广告策划"
     * 时间：找到"2018.07—2019.01" → start_year=2018, end_year=2019
     * 公司：找到"陕西华森特保健公司" → company="陕西华森特保健公司"
     * 职位：找到"保健品广告策划" → position="保健品广告策划"
     * 结果：{{"company": "陕西华森特保健公司", "position": "保健品广告策划", "start_year": 2018, "end_year": 2019}}
   - 示例5（无结构化字段，只有时间，没有公司和职位）：原始文本"2017.08-2018.06 描述：备考北京中医药大学中药化学研究生"
     * 时间：找到"2017.08-2018.06" → start_year=2017, end_year=2018
     * 公司：未找到公司关键词 → company=null
     * 职位：未找到职位信息 → position=null
     * 结果：{{"company": null, "position": null, "start_year": 2017, "end_year": 2018}}
   - 示例6（无结构化字段，有时间和公司，没有职位）：原始文本"2020.07-2020.09 兼职考研机构助教老师"
     * 时间：找到"2020.07-2020.09" → start_year=2020, end_year=2020
     * 公司：找到"考研机构" → company="考研机构"
     * 职位：找到"助教老师" → position="助教老师"
     * 结果：{{"company": "考研机构", "position": "助教老师", "start_year": 2020, "end_year": 2020}}
   - 示例7（无结构化字段，有多个职位）：原始文本"2019.02-2020.05 陕西康华医药分公司 储备干部、质量管理"
     * 时间：找到"2019.02-2020.05" → start_year=2019, end_year=2020
     * 公司：找到"陕西康华医药分公司" → company="陕西康华医药分公司"
     * 职位：找到"储备干部、质量管理" → position="储备干部、质量管理"（保留顿号分隔）
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例8（跨行提取，时间在第1行，公司在第3行，职位在第4行）：
     * 原始文本：
       ```
       2019.02-2020.05
       工作描述：负责质量管理
       陕西康华医药分公司
       储备干部、质量管理
       ```
     * 时间：在第1行找到"2019.02-2020.05" → start_year=2019, end_year=2020
     * 公司：在第3行（时间所在行的后续3行内）找到"陕西康华医药分公司" → company="陕西康华医药分公司"
     * 职位：在第4行（时间所在行的后续3行内）找到"储备干部、质量管理" → position="储备干部、质量管理"
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例9（工作经历模块在原始文本的任意位置，如个人信息之后）：
     * 原始文本：
       ```
       姓名：张三
       性别：男
       工作经历
       2019.02-2020.05 陕西康华医药分公司 储备干部
       ```
     * 定位：在整个文本中搜索"工作经历"关键词，找到后将其所在段落及其后续内容作为工作经历模块
     * 提取：{{"company": "陕西康华医药分公司", "position": "储备干部", "start_year": 2019, "end_year": 2020}}

**常见错误避免（重要，必须严格遵守）：**
1. **姓名提取错误避免**：
   - 不要将城市名、公司名、地址信息误认为是姓名
   - 不要提取姓名前的单字（如"风高峰"应提取"高峰"，不要提取"风"）
   - 不要将"现住址"等地址标签误认为是姓名的一部分
   - 不要将证书名称、资格名称误认为是姓名

2. **学校名称提取错误避免**：
   - 不要包含"高中"等学历等级词汇（如"XX大学高中"是错误的）
   - 不要包含专业名称或系名（如"陕西师范大学 历史系"应只提取"陕西师范大学"）

3. **专业名称提取错误避免**：
   - 不要包含"政治面貌"、"党员"、"团员"等非专业信息
   - 不要将工作描述误认为是专业名称
   - 如果专业名称中包含"专业"后缀，可以保留（如"生物制药工程专业"）

4. **工作经历提取错误避免**：
   - 不要将工作描述、工作内容误认为是职位名称（如"负责系统开发工作"不是职位）
   - 不要将项目经历、实习经历误认为是正式工作经历（除非明确标注为工作经历）
   - 不要将公司名称和职位名称混淆
   - 不要将时间信息提取错误（如将毕业时间误认为工作时间）
   - 不要遗漏工作经历条目，确保提取所有工作经历
   - 不要重复提取相同的工作经历
   - 注意识别"至今"、"现在"等时间表达，end_year应返回null
   - 注意识别完整的公司全称，不要截断（如"上海仁联人力资源有限公司"应完整提取）

5. **时间提取错误避免**：
   - 不要将工作年份、毕业年份误认为是出生年份
   - 不要将教育经历中的时间误认为是工作时间
   - 注意识别"2025年至今"等未来时间格式

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

**重要：原始文本格式说明：**
- 如果原始文本是完整的JSON格式（以`{{`开头和`}}`结尾，或包含完整的JSON对象结构），请先识别这是一个JSON对象
- 然后从JSON对象的结构化字段中直接提取信息：
  - **工作经历**：从`"工作经历": [ ... ]`或`"work_experience": [ ... ]`中提取`"时间"`、`"公司"`、`"岗位"`、`"职位"`等字段
  - **教育经历**：从`"教育经历": [ ... ]`、`"教育背景": { ... }`或`"education_background": [ ... ]`中提取`"学校"`、`"专业"`、`"学历"`等字段
- 在JSON对象中：
  - 键名`"岗位"`、`"职位"`、`"position"`都表示职位名称（"岗位"等同于"职位"），应该同等处理和提取
  - 键名`"学校"`、`"school"`、`"毕业院校"`、`"院校"`都表示学校名称，应该同等处理和提取
  - 键名`"专业"`、`"major"`、`"专业名称"`、`"所学专业"`都表示专业名称，应该同等处理和提取
  - 键名`"学历"`、`"degree"`、`"教育程度"`、`"education"`都表示学历等级，应该同等处理和提取
- 如果原始文本不是JSON格式，则按照关键词定位法提取

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


