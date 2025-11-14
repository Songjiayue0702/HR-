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
            # 截断文本以避免超出token限制
            max_length = 8000  # 保留一些余量
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            prompt = self._build_prompt(text, is_word_file=is_word_file)
            response = self._call_ai_api(prompt)
            
            if response:
                return self._parse_ai_response(response)
            return None
        except Exception as e:
            print(f"AI提取失败: {e}")
            return None
    
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
   - **步骤1（第二优先级）**：如果结构化字段中没有，在原始文本中搜索教育相关关键词（"教育经历"、"教育背景"、"学历"等）
   - 步骤2：找到关键词后，将该关键词所在段落及其前后各2行作为教育信息区域
   - 步骤3：如果找不到明确的教育关键词，搜索学历等级关键词（"本科"、"硕士"等），找到后将其所在段落作为教育信息区域

2. **提取最高学历**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"学历": "xxx"`、`"degree": "xxx"`），直接使用这些值
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
     * 如果对象中有明确的键值对（如`"学校": "xxx"`、`"school": "xxx"`），直接使用这些值
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
     * 如果对象中有明确的键值对（如`"专业": "xxx"`、`"major": "xxx"`），直接使用这些值
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

**工作经历提取规则（第三步，使用关键词定位法，非常重要）：**

**提取优先级（严格按照以下顺序）：**
1. **第一优先级**：从结构化字段中提取（如果存在）
2. **第二优先级**：从关键词定位提取（如果结构化字段不存在或信息不完整）

**关键词列表（用于定位信息位置）：**
- 工作经历关键词：工作经历、工作经验、职业经历、任职经历、工作履历、工作、就职、任职、Work Experience、work experience、Employment、employment、Career、career、工作信息
- 公司关键词：公司、集团、企业、中心、研究院、研究所、事务所、工作室、银行、医院、有限公司、股份有限公司、有限责任公司、Company、company、Corporation、corporation、律所、律师事务所
- 岗位关键词：岗位、职位、职务、角色、任职、担任、负责、Position、position、Job、job、Role、role、职位名称
- 时间关键词：时间、期间、Period、period、Duration、duration、工作期间

**提取方法（优先从结构化字段，然后使用关键词定位法）：**
1. **定位工作经历区域**：
   - **步骤0（第一优先级）**：如果原始文本中包含结构化字段，优先从以下字段中提取：
     * `"工作经历": [ ... ]` 或 `"work_experience": [ ... ]`
     * 这些字段中的信息准确性最高，优先提取
   - 步骤1：如果结构化字段中没有，在原始文本中搜索工作经历关键词（"工作经历"、"工作经验"等）
   - 步骤2：找到关键词后，将该关键词所在段落及其后续所有段落作为工作经历区域
   - 步骤3：如果找不到明确的工作经历关键词，搜索公司关键词，找到后将其所在段落作为工作经历区域

2. **识别工作经历条目**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 直接遍历数组中的每个对象，每个对象就是一条工作经历
     * 对于每个对象，按以下顺序提取：
       a. 如果对象中有明确的键值对（如`"时间": "xxx"`、`"公司": "xxx"`、`"职位": "xxx"`），直接使用这些值
       b. 如果对象中没有明确的键值对，但对象是数组或字符串格式，按照以下顺序识别：
          - 顺序1："时间，公司，岗位"（如`["2019.02-2020.05", "陕西康华医药分公司", "储备干部"]`）
          - 顺序2："公司，岗位，时间"（如`["陕西康华医药分公司", "储备干部", "2019.02-2020.05"]`）
          - 顺序3："时间 公司 岗位"（如`"2019.02-2020.05 陕西康华医药分公司 储备干部"`）
          - 顺序4："公司 岗位 时间"（如`"陕西康华医药分公司 储备干部 2019.02-2020.05"`）
       c. 识别规则：
          - 时间：查找时间格式（如"2019.02-2020.05"、"2019-2020"等）
          - 公司：查找包含公司关键词的字符串（如"公司"、"集团"等）
          - 岗位：查找公司后面的内容，通常是2-20个字符
   - **步骤1（第二优先级）**：如果结构化字段中没有，在工作经历区域中，逐行或逐段分析
   - 步骤2：识别每条工作经历的起始标志：
     * 时间格式（如"2019.02-2020.05"、"2019-2020"、"2025年至今"等）
     * 公司名称（包含"公司"、"集团"、"企业"、"中心"、"研究院"、"事务所"、"律所"等后缀）
     * 明确的段落分隔
   - 步骤3：将每条工作经历作为独立条目处理
   - 步骤4：注意不要遗漏工作经历，确保提取所有工作经历条目
   - 步骤5：注意不要重复提取相同的工作经历（如果发现重复，只保留一条）
   - **重要**：不要将教育经历中的时间（如"2006/9-2009/7"、"2013.9-2016.6"、"2020年9月-2023年6月"）误认为是工作时间
3. **提取时间信息**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"时间": "2019.02-2020.05"`、`"period": "2019-2020"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，岗位"或"公司，岗位，时间"等顺序识别：
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

4. **提取公司名称**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"公司": "xxx"`、`"company": "xxx"`、`"单位": "xxx"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，岗位"或"公司，岗位，时间"等顺序识别：
       - 查找包含公司关键词的字符串（如"公司"、"集团"、"企业"等）
       - 如果找到公司关键词，提取包含该关键词的完整公司名称
   - **步骤1（第二优先级）**：如果结构化字段中没有，在每条工作经历条目中搜索公司关键词（"公司"、"集团"、"企业"、"中心"、"研究院"、"事务所"、"律所"、"律师事务所"等）
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

5. **提取岗位名称**：
   - **步骤0（第一优先级）**：如果从结构化字段中提取：
     * 如果对象中有明确的键值对（如`"职位": "xxx"`、`"position": "xxx"`、`"岗位": "xxx"`），直接使用这些值
     * 如果对象中没有明确的键值对，按照"时间，公司，岗位"或"公司，岗位，时间"等顺序识别：
       - 在时间、公司之后查找岗位信息
       - 岗位通常是2-20个字符，不包含工作描述关键词
   - **步骤1（第二优先级）**：如果结构化字段中没有，在每条工作经历条目中，优先从公司名称后面提取岗位信息
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
   - 示例：原始文本`"work_experience": [ {{ "position": "网络营销" }} ]` → 提取"网络营销"
   - 示例：原始文本"储备干部、质量管理" → 提取"储备干部、质量管理"（完整保留）
   - 示例：原始文本"软件工程师\n负责系统开发工作" → 提取"软件工程师"（不要提取"负责系统开发工作"）
   - 示例：原始文本"公司名称 市场营销" → 提取"市场营销"（即使没有"岗位"关键词）
   - 错误示例：不要提取"responsibilities : ["（这是工作描述标签，不是岗位名称）
   - 错误示例：不要提取"描述 : 备考北京中医药大学中药化学研究生"（这是描述，不是岗位名称）

6. **提取顺序**：
   - 按照原始文本中的时间顺序，从最新到最旧（倒序）提取工作经历
   - 如果时间相同，按照在文本中的出现顺序
7. **完整示例**：
   - 示例1（结构化字段，有明确键值对）：原始文本`"工作经历": [ {{ "时间": "2019.02-2020.05", "公司": "陕西康华医药分公司", "职位": "储备干部、质量管理" }} ]`
     * 直接从结构化字段提取：time="2019.02-2020.05", company="陕西康华医药分公司", position="储备干部、质量管理"
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例2（结构化字段，无明确键值对，按顺序识别）：原始文本`"工作经历": [ ["2019.02-2020.05", "陕西康华医药分公司", "储备干部、质量管理"] ]`
     * 按照"时间，公司，岗位"顺序识别：
       - 第1个元素："2019.02-2020.05" → 时间
       - 第2个元素："陕西康华医药分公司" → 公司
       - 第3个元素："储备干部、质量管理" → 岗位
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例3（结构化字段，无明确键值对，字符串格式）：原始文本`"工作经历": [ "2019.02-2020.05 陕西康华医药分公司 储备干部、质量管理" ]`
     * 按照"时间 公司 岗位"顺序识别：
       - 找到时间格式："2019.02-2020.05" → 时间
       - 找到公司关键词："陕西康华医药分公司" → 公司
       - 公司后面的内容："储备干部、质量管理" → 岗位
     * 结果：{{"company": "陕西康华医药分公司", "position": "储备干部、质量管理", "start_year": 2019, "end_year": 2020}}
   - 示例4（无结构化字段，从关键词提取）：原始文本"2018.07—2019.01 陕西华森特保健公司 保健品广告策划"
     * 时间：找到"2018.07—2019.01" → start_year=2018, end_year=2019
     * 公司：找到"陕西华森特保健公司" → company="陕西华森特保健公司"
     * 岗位：找到"保健品广告策划" → position="保健品广告策划"
     * 结果：{{"company": "陕西华森特保健公司", "position": "保健品广告策划", "start_year": 2018, "end_year": 2019}}
   - 示例5（无结构化字段，从关键词提取）：原始文本"2016.9-2019.2 北京科技有限公司 软件工程师\n负责系统开发工作"
     * 时间：找到"2016.9-2019.2" → start_year=2016, end_year=2019
     * 公司：找到"北京科技有限公司" → company="北京科技有限公司"
     * 岗位：找到"软件工程师" → position="软件工程师"（注意：不要提取"负责系统开发工作"）
     * 结果：{{"company": "北京科技有限公司", "position": "软件工程师", "start_year": 2016, "end_year": 2019}}

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


