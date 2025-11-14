"""
信息提取工具
从简历文本中提取关键信息
"""

import re
import unicodedata
from datetime import datetime


class InfoExtractor:
    """信息提取器"""

    def __init__(self):
        self.current_year = datetime.now().year
        self.education_levels = {
            '博士': 7, '博士后': 7,
            '硕士': 6, '研究生': 6, 'MBA': 6, 'MPA': 6,
            '本科': 5, '学士': 5,
            '专科': 4, '大专': 4, '高职': 4,
            '高中': 3,
            '职高': 2, '中专': 2,
            '初中': 1
        }
        alias_map = {
            '博士': '博士', '博士后': '博士', 'phd': '博士', 'doctor': '博士',
            '硕士': '硕士', '研究生': '硕士', 'master': '硕士', 'mba': '硕士', 'mpa': '硕士', 'mpp': '硕士', 'msc': '硕士', 'ms': '硕士',
            '本科': '本科', '学士': '本科', '学士学位': '本科', 'bachelor': '本科', '统招本科': '本科', '普通本科': '本科', '大学本科': '本科', '专升本': '本科', '全日制本科': '本科',
            '专科': '专科', '大专': '专科', '高等专科': '专科', 'college': '专科', 'associate': '专科', 'diploma': '专科', 'junior college': '专科', '职业学院': '专科', '职业技术学院': '专科',
            '高中': '高中', '普高': '高中', '中学': '高中', '附中': '高中', '一中': '高中', '二中': '高中', '三中': '高中', '四中': '高中',
            '中专': '中专', '技校': '中专', '技工': '中专', '职校': '中专', '高职': '中专', 'technical secondary': '中专', 'technical school': '中专'
        }
        self.education_aliases = {alias.lower(): level for alias, level in alias_map.items()}
        self.education_priority = sorted(self.education_levels.items(), key=lambda item: item[1], reverse=True)

        self.company_regex = re.compile(
            r'([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,50}?'
            r'(?:公司|集团|企业|中心|研究院|研究所|事务所|工作室|银行|医院|学院|学校|大学|事务部|事业部|总公司|分公司|控股|科技|工程|建设|咨询|管理|网络|传媒|股份有限公司|有限责任公司|有限公司))'
        )
        self.position_markers = ['岗位', '职位', '职务', '角色', '任职', '担任', '负责', '工作']
        self.position_keywords_regex = re.compile(
            r'(' + '|'.join(re.escape(marker) for marker in self.position_markers) + r'|主管|顾问|经理|老师|教师|工程师|专员|主任|助理)'
        )
        self.school_keywords = ['大学', '学院', '学校', '中专', '高中', '技校', '职校', '一中', '二中', '三中', '四中', '附中']
        self.school_regex = re.compile(
            r'[\u4e00-\u9fa5]{2,20}(?:大学|学院|学校|专科学校|职业技术学院|中学|高中|中专|一中|二中|三中|四中|附中)'
        )
        self.major_regex = re.compile(
            r'(?:专业|方向)[：:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s/]+)'
        )
        self.education_keywords = ['博士', '硕士', '研究生', '本科', '学士', '大专', '专科', '高中', '中专', '职高', '初中']
        self.key_tokens = [
            '姓名', '性别', '年龄',
            '出生年份', '出生年月', '出生日期',
            '手机', '电话', '联系方式', '联系手机', '手机号', '手机号码', '联系电话',
            '邮箱', 'Email', 'email', 'E-mail',
            '最高学历', '学历',
            '毕业院校', '毕业学校', '学校', '院校',
            '专业'
        ]
        self.key_pattern = '|'.join(re.escape(token) for token in self.key_tokens)
        self.section_keywords = [
            '基本信息', '个人信息', '求职意向', '个人优势', '自我评价',
            '项目经历', '工作经历', '工作经验', '职业经历', '任职经历',
            '教育经历', '教育背景', '培训经历', '证书', '技能特长'
        ]
        self.invalid_name_tokens = {
            '个人', '个人优势', '自我评价', '项目经历', '基本信息',
            '求职意向', '工作经历', '教育经历', '简历', '信息',
            '内容', '业绩', '项目', '岗位', '职位', '工程师',
            '经理', '主管', '老师', '教师', '顾问', '销售', '地址', '邮箱',
            '运营', '客服', '专员', '助播', '设计', '分析师'
        }
        self.company_keywords_regex = re.compile(
            r'([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,40}'
            r'(公司|集团|企业|科技|有限公司|股份|银行|医院|学院|学校|中心|事务所|工作室|研究所|传媒|网络|软件|运营部|事业部|团队))'
        )

    def clean_text(self, text: str) -> str:
        """清洗文本，移除特殊字符"""
        if not text or text is None:
            return ''
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('⻄', '西')
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\xa0', ' ').replace('\u3000', ' ')
        text = text.replace('姓⺠名', '姓名')
        text = text.replace('姓民名', '姓名')
        text = text.replace('姓氏名', '姓名')
        
        # 清理OCR常见错误 - 更彻底的清理
        # 移除所有不可见字符和OCR错误标记
        text = re.sub(r'[□¡¿\u200b\u200c\u200d\ufeff]', '', text)  # 移除OCR无法识别的字符标记和零宽字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # 移除控制字符
        
        # 移除其他常见的OCR错误字符，但保留必要的标点
        # 只保留：中文、英文、数字、常见标点、空格、换行
        # 更宽松的清理：保留更多字符，避免过度清理
        text = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9\s\.,;:：，。；、！？()（）【】\[\]《》\-\+*/=@#%&·•~]', ' ', text)
        
        # 修复常见的OCR识别错误
        text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)  # 移除中文字符间的空格
        # 修复邮箱中的常见OCR错误（如"@4q.com"应该是"@qq.com"）
        text = re.sub(r'@4q\.com', '@qq.com', text, flags=re.IGNORECASE)
        text = re.sub(r'@(\d+)q\.com', r'@qq.com', text, flags=re.IGNORECASE)
        
        # 修复时间格式中的OCR错误：年份中的O应该是0（如"2O25" -> "2025"）
        text = re.sub(r'([12])O(\d{3})', r'\g<1>0\2', text)  # 修复年份中的O -> 0
        text = re.sub(r'(\d{4})\.O(\d)', r'\1.0\2', text)  # 修复月份中的O -> 0（如"2025.O3" -> "2025.03"）
        
        # 修复被换行分割的时间、公司名等信息（保持上下文完整性）
        # 修复时间范围被换行分割（如"2019\n-\n2020" -> "2019-2020"）
        text = re.sub(r'(\d{4})\s*\n\s*[-~至到]\s*\n\s*((?:19|20)\d{2}|至今|现在)', r'\1-\2', text)
        # 修复日期被换行分割（如"2019\n/\n01" -> "2019/01"）
        text = re.sub(r'(\d{4})(?:/|\\)\s*\n\s*(\d{1,2})', r'\1/\2', text)
        # 修复公司名被换行分割（如"北京\n公司" -> "北京公司"）
        text = re.sub(r'([\u4e00-\u9fa5]{2,})\s*\n\s*(公司|集团|企业|有限公司)', r'\1\2', text)
        # 修复岗位被换行分割（如"销售\n主管" -> "销售主管"）
        text = re.sub(r'([\u4e00-\u9fa5]{1,3})\s*\n\s*(主管|经理|总监|工程师|教师|管理员|专员|助理|顾问|销售)', r'\1\2', text)
        # 修复学校名被换行分割（如"北京\n大学" -> "北京大学"）
        text = re.sub(r'([\u4e00-\u9fa5]{1,4})\s*\n\s*(大学|学院|学校)', r'\1\2', text)
        # 去除冗余长字符串（常见的加密文件标识）
        text = re.sub(r'\b[a-zA-Z0-9]{18,}\b', ' ', text)
        # 在常见段落标题前补换行，便于分段
        for keyword in self.section_keywords:
            text = re.sub(rf'\s*{keyword}', f'\n{keyword}', text)
        # 规范空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def _match_education(self, value: str | None) -> str | None:
        if not value:
            return None
        lowered = value.lower()
        best_level = None
        best_score = -1
        for keyword, level in self.education_aliases.items():
            if keyword in lowered:
                score = self.education_levels.get(level, 0)
                if score > best_score:
                    best_level = level
                    best_score = score
        return best_level

    def normalize_education_level(self, value: str | None) -> str | None:
        if not value:
            return None
        text = value.strip().lower()
        cleaned = re.sub(r'[（）()\[\]【】<>]', ' ', text)
        cleaned = re.sub(r'[\s/\\|，,。;；]+', ' ', cleaned)
        for token in cleaned.split():
            if token in self.education_aliases:
                return self.education_aliases[token]
        for alias, level in self.education_aliases.items():
            if alias in text:
                return level
        return None

    def _prefer_higher_level(self, current: str | None, candidate: str | None) -> str | None:
        if not candidate:
            return current
        if not current:
            return candidate
        current_score = self.education_levels.get(current, 0)
        candidate_score = self.education_levels.get(candidate, 0)
        if candidate_score > current_score:
            return candidate
        return current

    def _tokenize_education_line(self, line: str) -> list[str]:
        cleaned = line.replace('\u3000', ' ').strip()
        if not cleaned:
            return []
        tokens = re.split(r'[\s,，;；|/]+', cleaned)
        return [token for token in tokens if token]

    def _clean_school_name(self, school_name: str) -> str:
        """
        清理学校名称，去除无效文字前缀和后缀
        """
        if not school_name:
            return ""
        
        school_cleaned = school_name.strip()
        
        # 移除所有可能的前缀
        invalid_prefixes = [
            '教育经历', '教育背景', '学历', '毕业院校', '毕业学校', 
            '学校', '院校', '就读', '毕业于', '毕业', '教育'
        ]
        for prefix in invalid_prefixes:
            # 移除前缀（支持冒号、空格等分隔符）
            school_cleaned = re.sub(rf'^{re.escape(prefix)}[：:：\s]*', '', school_cleaned, flags=re.IGNORECASE)
            if school_cleaned.startswith(prefix):
                school_cleaned = school_cleaned[len(prefix):].strip()
        
        # 移除后缀中的无效词
        invalid_suffixes = ['教育经历', '教育背景', '学历', '毕业', '教育']
        for suffix in invalid_suffixes:
            if school_cleaned.endswith(suffix) and len(school_cleaned) > len(suffix):
                # 如果学校名以无效后缀结尾，移除它
                school_cleaned = school_cleaned[:-len(suffix)].strip()
        
        # 移除开头的数字、年月等
        school_cleaned = re.sub(r'^[0-9年月\s]+', '', school_cleaned).lstrip('月')
        
        # 移除末尾的标点符号（保留必要的）
        school_cleaned = school_cleaned.rstrip('，,。.；;：:')
        
        # 如果清理后太短（少于2个字符）或只包含无效词，返回原值
        if len(school_cleaned) < 2:
            return school_name.strip()
        
        # 如果清理后的结果只包含无效词，返回原值
        if school_cleaned in invalid_prefixes + invalid_suffixes:
            return school_name.strip()
        
        return school_cleaned

    def _clean_major_candidate(self, token: str) -> str | None:
        if not token:
            return None
        token = token.strip(' ：:，,;；/|.').strip()
        if not token:
            return None
        token = re.sub(r'（[^）]*）', '', token)
        token = re.sub(r'\([^)]*\)', '', token)
        token = token.replace('：', ':')
        if ':' in token:
            token = token.split(':', 1)[-1].strip()
        for prefix in ['专业', '主修课程', '方向', '主修', '主要课程']:
            if token.startswith(prefix):
                token = token[len(prefix):].strip()
        if any(char.isdigit() for char in token):
            return None
        # 排除工作描述相关的关键词，但要保留合法的专业名称
        # 合法的专业名称通常以"管理"、"运营"等结尾（如"人力资源管理"、"工商管理"）
        # 工作描述通常包含"管理"+"其他词"的组合（如"管理客户"、"管理项目"）
        invalid_patterns = [
            r'学习', r'起点', r'学校', r'分析.*需求', r'需求.*分析', r'客户', r'家长', r'孩子', 
            r'负责', r'完成', r'工作(?!管理|运营|销售|营销)', r'项目(?!管理|运营|销售|营销)',
            r'管理(客户|项目|团队|公司|企业|部门)(?!专业|方向|系)',
            r'运营(客户|项目|团队|公司|企业|部门)(?!专业|方向|系)',
            r'销售(客户|项目|团队|公司|企业|部门)(?!专业|方向|系)'
        ]
        # 检查是否是工作描述（包含多个工作关键词的组合）
        work_keywords = ['分析', '需求', '客户', '家长', '孩子', '负责', '完成']
        work_keyword_count = sum(1 for kw in work_keywords if kw in token)
        if work_keyword_count >= 2:
            return None
        # 检查是否是工作描述模式（如"管理客户"、"管理项目"等）
        if re.search(r'管理(客户|项目|团队|公司|企业|部门|工作|内容|职责)', token):
            return None
        if re.search(r'运营(客户|项目|团队|公司|企业|部门|工作|内容|职责)', token):
            return None
        if re.search(r'销售(客户|项目|团队|公司|企业|部门|工作|内容|职责)', token):
            return None
        # 排除明显是工作描述的长文本
        if len(token) > 20:
            return None
        for suffix in ['专业', '方向', '系', '学院', '专科', '本科', '硕士', '博士']:
            if token.endswith(suffix) and len(token) > len(suffix):
                token = token[:-len(suffix)].strip()
        if len(token) < 2 or len(token) > 30:
            return None
        return token

    def _scan_tokens_for_degree_major(self, tokens: list[str], allow_degree: bool = True) -> tuple[str | None, str | None]:
        degree = None
        major = None
        degree_detected = False
        for token in tokens:
            if not token:
                continue
            if allow_degree:
                detected = self.detect_highest_level_in_text(token)
                if detected:
                    degree = self._prefer_higher_level(degree, detected)
                    degree_detected = True
                    continue
            candidate = self._clean_major_candidate(token)
            if not candidate:
                continue
            if '专业' in token or '方向' in token or token.endswith('系'):
                if not major:
                    major = candidate
                    continue
            if degree_detected and not major:
                major = candidate
        return degree, major

    def _extract_education_entries(self, lines: list[str]) -> list[dict]:
        entries = []
        length = len(lines)
        for idx, line in enumerate(lines):
            if not line:
                continue
            school_match = self.school_regex.search(line)
            if not school_match:
                continue
            school = re.sub(r'^[0-9年月\s]+', '', school_match.group(0)).lstrip('月')
            if ('毕业' in school or '教育' in school) and len(school) <= 6:
                alternate_match = self.school_regex.search(line.replace(school, ' ', 1))
                if alternate_match:
                    school = alternate_match.group(0)
                else:
                    continue
            remainder = line.replace(school, ' ', 1)
            tokens = self._tokenize_education_line(remainder)
            degree, major = self._scan_tokens_for_degree_major(tokens)

            # 如果同一行未识别到，尝试相邻行
            for offset in [0, 1, -1, 2, -2]:
                if degree and major:
                    break
                neighbor_idx = idx + offset
                if neighbor_idx < 0 or neighbor_idx >= length:
                    continue
                neighbor_line = lines[neighbor_idx]
                if not neighbor_line:
                    continue
                if not degree:
                    degree = self._prefer_higher_level(
                        degree,
                        self.detect_highest_level_in_text(neighbor_line)
                    )
                if not major:
                    neighbor_tokens = self._tokenize_education_line(neighbor_line)
                    _, neighbor_major = self._scan_tokens_for_degree_major(neighbor_tokens, allow_degree=False)
                    if neighbor_major:
                        major = neighbor_major

            entries.append({
                'index': idx,
                'school': school,
                'highest_education': degree,
                'major': major
            })
        return entries

    def detect_highest_level_in_text(self, text: str) -> str | None:
        if not text:
            return None
        lowered = text.lower()
        best_level = None
        best_score = -1
        for alias, level in self.education_aliases.items():
            if alias in lowered:
                score = self.education_levels.get(level, 0)
                if score > best_score:
                    best_level = level
                    best_score = score
        return best_level

    def _split_company_position(self, text: str) -> tuple[str | None, str | None]:
        if not text:
            return None, None
        candidate = re.sub(r'^[0-9]+[.、)]\s*', '', text.strip())
        best_match = None
        best_len = 0
        best_end = None
        for match in self.company_regex.finditer(candidate):
            span_len = match.end() - match.start()
            if span_len > best_len:
                best_match = match
                best_len = span_len
                best_end = match.end()
        if best_match:
            company = candidate[best_match.start():best_match.end()].strip(' ,-|，;；')
            # 移除括号内容（如"（国舜律所）"）
            company = re.sub(r'[（(][^）)]+[）)]', '', company).strip()
            remainder = candidate[best_end:].strip(' ,-|，;；')
            # 如果remainder中包含括号，先移除括号内容
            remainder = re.sub(r'[（(][^）)]+[）)]', '', remainder).strip()
            # 如果remainder以"有限公司"等公司后缀开头，说明匹配范围过大，需要调整
            if remainder and any(remainder.startswith(suffix) for suffix in ['有限公司', '股份有限公司', '有限责任公司']):
                # 重新计算，找到真正的公司结束位置
                company_text = candidate[best_match.start():best_match.end()]
                # 查找最后一个"公司"的位置
                last_company_pos = company_text.rfind('公司')
                if last_company_pos > 0:
                    # 重新设置remainder
                    actual_end = best_match.start() + last_company_pos + 2
                    remainder = candidate[actual_end:].strip(' ,-|，;；')
                    remainder = re.sub(r'[（(][^）)]+[）)]', '', remainder).strip()
            # 如果remainder以"公司"开头，移除它（可能是匹配错误）
            if remainder and remainder.startswith('公司'):
                remainder = remainder[2:].strip()
            prefix = candidate[:best_match.start()].strip(' ,-|，;；')
            if prefix and re.search(r'[\u4e00-\u9fa5]', prefix):
                if prefix.endswith(('集团', '控股', '股份', '投资')) or len(prefix) <= 6:
                    company = prefix + company
        else:
            company = candidate if self._is_valid_company(candidate) else None
            remainder = '' if company else candidate

        position = None
        if remainder:
            for marker in self.position_markers:
                if marker in remainder:
                    parts = remainder.split(marker, 1)
                    if len(parts) == 2:
                        position = parts[1].lstrip('：:，, \t')
                        break
            if not position and len(remainder) <= 20:
                position = remainder

        if position:
            position = re.sub(r'^(岗位|职位|职务|角色|任职|担任|负责)[：:：，,\s]*', '', position).strip()

        # 移除公司名中的括号内容后再验证
        original_position = position  # 保存原始职位
        if company:
            company_cleaned = re.sub(r'[（(][^）)]+[）)]', '', company).strip()
            if company_cleaned != company:
                company = company_cleaned
            if not self._is_valid_company(company):
                # 即使公司名验证失败，也要保留职位信息
                company = None

        if not company and candidate:
            parts = [p for p in re.split(r'\s+', candidate) if p]
            if parts and re.search(r'[\u4e00-\u9fa5]', parts[0]):
                company = parts[0].strip(' ,-|，;；·•')
                if len(parts) > 1:
                    possible_position = parts[1].strip()
                    if possible_position and len(possible_position) <= 20:
                        if (not position) or (company and position and position.startswith(company)):
                            position = possible_position

        # 如果职位包含"有限公司"等公司后缀，说明提取错误，需要清理
        if position:
            # 移除公司后缀（从开头或中间）
            position = re.sub(r'^有限公司\s*', '', position).strip()
            position = re.sub(r'^股份有限公司\s*', '', position).strip()
            position = re.sub(r'^有限责任公司\s*', '', position).strip()
            position = re.sub(r'\s*有限公司.*$', '', position).strip()
            position = re.sub(r'\s*股份有限公司.*$', '', position).strip()
            position = re.sub(r'\s*有限责任公司.*$', '', position).strip()
            # 如果职位以"公司"开头，移除它
            if position.startswith('公司'):
                position = position[2:].strip()
            # 如果职位太短（少于2个字符），可能是提取错误
            if position and len(position) < 2:
                position = None

        return company, (position or None)

    def parse_key_values(self, text: str) -> dict:
        """解析带有键值对格式的字段，如：姓名：张三"""
        pattern = re.compile(
            rf'({self.key_pattern})\s*[:：]\s*([^\n]+?)\s*(?=(?:{self.key_pattern})\s*[:：]|$)'
        )
        pairs = {}
        lines = text.split('\n')
        
        # 遍历所有行，支持跨行提取值（如果当前行值不完整，检查下一行）
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            for match in pattern.finditer(line):
                key = match.group(1)
                value = match.group(2).strip()
                
                # 如果值看起来不完整（太短或以标点结尾），尝试合并下一行
                if value and len(value) < 5 and idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    # 如果下一行不是新的键值对，可能是值的延续
                    if next_line and not re.match(rf'^{self.key_pattern}\s*[:：]', next_line):
                        # 检查下一行是否包含值的内容（不是工作描述等）
                        if not any(kw in next_line for kw in ['工作内容', '职责', '负责', '完成', '参与']):
                            value = value + ' ' + next_line
                
                if key not in pairs and value:
                    pairs[key] = value.strip()
        return pairs

    @staticmethod
    def _extract_year_from_string(value: str | None, current_year: int) -> int | None:
        if not value:
            return None
        match = re.search(r'(19|20)\d{2}', value)
        if match:
            year = int(match.group(0))
            if 1980 <= year <= current_year:
                return year
        return None

    def _fallback_work_experience(self, text: str):
        """在常规规则未命中时，基于时间线解析工作经历"""
        # 先清理OCR错误字符，避免影响匹配
        text = re.sub(r'[□¡¿]', ' ', text)  # 将OCR错误字符替换为空格
        
        # 预处理：合并可能被换行分割的工作经历信息
        # 1. 合并"公司名\n岗位"格式
        text = re.sub(
            r'([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,50}(?:公司|集团|企业|中心|研究院|研究所|事务所|工作室|银行|医院|学院|学校|大学|事务部|事业部|总公司|分公司|控股|科技|工程|建设|咨询|管理|网络|传媒|股份有限公司|有限责任公司|有限公司))\s*\n\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,30}(?:主管|顾问|经理|老师|教师|工程师|专员|主任|助理|总监|总裁|总经理|副总|储备干部|质量管理|广告策划))',
            r'\1 \2',
            text,
            flags=re.MULTILINE
        )
        # 2. 合并"时间\n公司名"格式
        text = re.sub(
            r'((?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{1,2})?(?:月)?\s*[-~至到—~～]+\s*(?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{0,2})?(?:月)?|至今|现在)\s*\n\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,50}(?:公司|集团|企业|中心|研究院|研究所|事务所|工作室|银行|医院|学院|学校|大学|事务部|事业部|总公司|分公司|控股|科技|工程|建设|咨询|管理|网络|传媒|股份有限公司|有限责任公司|有限公司))',
            r'\1 \2',
            text,
            flags=re.MULTILINE
        )
        # 3. 合并"岗位\n时间"格式
        text = re.sub(
            r'([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,30}(?:主管|顾问|经理|老师|教师|工程师|专员|主任|助理|总监|总裁|总经理|副总|储备干部|质量管理|广告策划))\s*\n\s*((?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{1,2})?(?:月)?\s*[-~至到—~～]+\s*(?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{0,2})?(?:月)?|至今|现在)',
            r'\1 \2',
            text,
            flags=re.MULTILINE
        )
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        experiences = []
        last_company = None
        current_exp = None
        # 改进的时间模式：支持更多格式，如"2020年9月--2021年2月"
        # 放宽匹配条件，支持OCR可能导致的格式错误
        # 支持格式：2019.03-2025.04, 2019.03-2025.0, 2019-2025, 2019.02-2020.05, 2018.07—2019.01等
        # 注意：在提取前已经修复了OCR错误（O -> 0），所以这里匹配正常的数字格式
        # 更宽松的时间模式：支持更多分隔符和格式
        # 支持格式：2016.9-2019.2, 2019.02-2020.05, 2018.07—2019.01, 2019等
        time_pattern = re.compile(
            r'((?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{1,2})?(?:月)?)\s*[-~至到—~～]+\s*'
            r'((?:19|20)\d{2}[./-]?\d{0,2}(?:[年./-]?\d{0,2})?(?:月)?|至今|现在|present)'
        )
        # 支持只有开始年份的格式（如"2019 翔海集团房产开发有限公司 销售顾问"）
        # 更宽松的模式：年份后跟空格或标点，然后是公司名或岗位
        single_year_pattern = re.compile(
            r'^((?:19|20)\d{2})[年\s]+(?!至今|现在|present)([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{3,})'
        )
        position_pattern = re.compile(
            r'(?:担任|职位|岗位|职务|角色|方向)[：:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]+)'
        )

        for idx, line in enumerate(lines):
            # 跳过教育经历部分
            if any(keyword in line for keyword in ['教育经历', '教育背景', '求职意向', '项目经历']):
                continue
            if '教育' in line and '公司' not in line and '工作' not in line:
                last_company = None
                continue
            if any(keyword in line for keyword in ['大学', '学院', '学校', '中学', '高中']) and '公司' not in line and '工作' not in line:
                last_company = None
                continue
            # 跳过表头行
            if re.match(r'^(时间|单位|职位|岗位|名称)[\s\u4e00-\u9fa5]*$', line):
                continue
            # 跳过明显是工作描述的行（如"内容:"、"负责工作:"等）
            if re.match(r'^(内容|负责|职责|业绩|获得|担任角色|负责工作|获得业绩)[：:：]?\s*$', line):
                continue
            if line.strip() in ['内容:', '负责工作:', '获得业绩:', '业绩:', '担任角色:', '负责工作:']:
                continue
            # 跳过以数字开头的工作描述行（如"1.公司主要业务..."），但保留以年份开头的行
            if re.match(r'^\d+[、.。]\s*', line) and not re.match(r'^(19|20)\d{2}', line):
                # 检查是否包含工作描述关键词
                if any(kw in line for kw in ['负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队']):
                    continue

            company_match = self.company_keywords_regex.search(line)
            if company_match:
                last_company = company_match.group(1).strip()

            # 如果行包含不完整的时间格式（如"2020.02-202"），尝试合并下一行
            line_for_match = line
            # 检查是否包含不完整的时间格式（以年份开头，或者包含"年份.月份-年份"但结束部分不完整）
            if re.search(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}[-~至到—]\d{4}$', line) or \
               (re.search(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}[-~至到—]\d{4}', line) and not re.search(r'[-~至到—]\d{4}[./-]?\d{1,2}', line)):
                # 时间可能跨行了，尝试合并下一行
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and (re.match(r'^\d{1,2}', next_line) or re.match(r'^\d{1,2}[./-]', next_line)):
                        line_for_match = line + next_line
            
            # 处理公司名跨行的情况：如果当前行包含时间但不包含公司名，尝试合并前后行
            if re.search(r'(?:19|20)\d{2}', line) and not self.company_keywords_regex.search(line):
                # 尝试合并前一行（可能包含公司名）
                if idx > 0:
                    prev_line = lines[idx - 1].strip()
                    if prev_line and self.company_keywords_regex.search(prev_line):
                        line_for_match = prev_line + ' ' + line_for_match
                # 尝试合并后一行（可能包含公司名或岗位）
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and (self.company_keywords_regex.search(next_line) or 
                                     any(kw in next_line for kw in ['主管', '经理', '总监', '工程师', '教师', '管理员', '专员', '助理', '储备干部', '质量管理', '广告策划'])):
                        line_for_match = line_for_match + ' ' + next_line
            
            matches = list(time_pattern.finditer(line_for_match))
            if matches:
                def clean_candidate(value: str | None):
                    if not value:
                        return None
                    cleaned = re.sub(r'^[0-9]+[.、)]\s*', '', value.strip())
                    cleaned = cleaned.lstrip(':：-—')
                    cleaned = re.split(r'[。；;]', cleaned, 1)[0]
                    cleaned = cleaned.strip()
                    return cleaned or None

                for idx_match, time_match in enumerate(matches):
                    start_part = time_match.group(1)
                    end_part = time_match.group(2)
                    start_year = self._extract_year_from_string(start_part, self.current_year)
                    if end_part in ('至今', '现在'):
                        end_year = None
                    else:
                        end_year = self._extract_year_from_string(end_part, self.current_year)

                    seg_start = time_match.end()
                    seg_end = matches[idx_match + 1].start() if idx_match + 1 < len(matches) else len(line_for_match)
                    after_time = line_for_match[seg_start:seg_end].strip()
                    
                    # 如果after_time为空或很短，尝试从下一行获取（处理换行情况）
                    if not after_time or len(after_time) < 5:
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1].strip()
                            if next_line and not re.match(r'^\d{4}', next_line):
                                after_time = next_line
                                # 如果下一行也有公司名，合并处理
                                if self.company_keywords_regex.search(next_line):
                                    line_for_match = line_for_match + ' ' + next_line
                                    after_time = line_for_match[seg_start:].strip()
                    
                    # 如果after_time以"初"、"末"等时间修饰词结尾，或者包含"进行"但行尾不完整，尝试合并下一行
                    should_merge = False
                    if after_time:
                        # 检查是否以时间修饰词结尾
                        if any(after_time.endswith(modifier) for modifier in ['初', '末', '底', '中', '上旬', '中旬', '下旬']):
                            should_merge = True
                        # 检查是否包含"进行"但行尾不完整（如以"学"、"教"等词结尾，可能是跨行）
                        elif '进行' in after_time and any(after_time.endswith(char) for char in ['学', '教', '辅', '作', '理', '管']):
                            should_merge = True
                    
                    if should_merge and idx + 1 < len(lines):
                        next_line = lines[idx + 1].strip()
                        if next_line and not re.match(r'^\d{4}', next_line) and not any(kw in next_line for kw in ['工作经历', '教育经历', '项目经历']):
                            after_time = after_time + next_line
                    before_start = matches[idx_match - 1].end() if idx_match > 0 else 0
                    before_time = line_for_match[before_start:time_match.start()].strip()
                    
                    company = None
                    role = None
                    
                    # 优先从after_time中提取公司名和岗位（时间后的文本通常包含公司名和岗位）
                    # 处理格式：2019.02-2020.05 陕西康华医药分公司 储备干部、质量管理
                    # 处理格式：2016.9-2019.2 恒源艺术馆·销售主管（支持"·"分隔符）
                    if after_time:
                        # 先尝试从after_time中提取公司名和岗位
                        after_cleaned = after_time.strip()
                        
                        # 支持"·"分隔符（如"恒源艺术馆·销售主管"）
                        if '·' in after_cleaned or '•' in after_cleaned:
                            # 使用"·"或"•"分隔公司名和岗位
                            separator = '·' if '·' in after_cleaned else '•'
                            parts = after_cleaned.split(separator, 1)
                            if len(parts) == 2:
                                comp_candidate_after = parts[0].strip()
                                position_after = parts[1].strip()
                                # 验证公司名
                                if not company:
                                    if self._is_valid_company(comp_candidate_after):
                                        company = comp_candidate_after
                                    else:
                                        comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp_candidate_after).strip()
                                        if self._is_valid_company(comp_cleaned):
                                            company = comp_cleaned
                                        elif any(comp_candidate_after.endswith(suffix) for suffix in ['公司', '集团', '企业', '分公司', '有限公司', '馆', '中心']):
                                            company = comp_candidate_after
                                if not role and position_after and len(position_after) <= 30:
                                    role = position_after
                        
                        # 如果没有"·"分隔符，使用原来的逻辑
                        if not company or not role:
                            # 查找公司名（支持"分公司"等）
                            company_matches_after = list(self.company_keywords_regex.finditer(after_cleaned))
                            if company_matches_after:
                                # 使用第一个匹配（最接近时间的）
                                first_match = company_matches_after[0]
                                comp_candidate_after = after_cleaned[first_match.start():first_match.end()].strip()
                                # 提取公司名后的内容作为岗位（优先从公司名后提取）
                                position_after = after_cleaned[first_match.end():].strip()
                                # 清理岗位：移除多余的标点和空格
                                position_after = re.sub(r'^[，,、\s]+', '', position_after)
                                
                                # 如果公司名后没有岗位信息，尝试从下一行获取（但只取第一行，避免取到工作描述）
                                # 优先从公司名后的文本提取，如果提取不到或太短，才考虑下一行
                                if not position_after or len(position_after) < 2:
                                    if idx + 1 < len(lines):
                                        next_line = lines[idx + 1].strip()
                                        # 检查下一行是否是岗位（不包含工作描述关键词）
                                        invalid_keywords = ['工作内容', '内容一', '内容', '职责', '负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队', '开发', '维护', '跟进', '一手', '房源']
                                        if next_line and not any(kw in next_line for kw in invalid_keywords):
                                            # 检查是否包含岗位关键词或常见岗位名称
                                            position_keywords = ['主管', '经理', '总监', '工程师', '教师', '管理员', '专员', '助理', '顾问', '销售', '储备干部', '质量管理', '广告策划', '销售主管', '销售顾问']
                                            if self.position_keywords_regex.search(next_line) or any(kw in next_line for kw in position_keywords):
                                                # 提取岗位（最多30个字符）
                                                if len(next_line) <= 30:
                                                    position_after = next_line
                                                else:
                                                    # 如果太长，尝试提取包含岗位关键词的部分
                                                    pos_match = self.position_keywords_regex.search(next_line)
                                                    if pos_match:
                                                        start = max(0, pos_match.start() - 3)
                                                        end = min(len(next_line), pos_match.end() + 15)
                                                        position_after = next_line[start:end].strip()
                                                    else:
                                                        # 如果没有匹配到岗位关键词，但包含常见岗位名称，提取包含该名称的部分
                                                        for pos_kw in position_keywords:
                                                            if pos_kw in next_line:
                                                                kw_pos = next_line.find(pos_kw)
                                                                start = max(0, kw_pos - 5)
                                                                end = min(len(next_line), kw_pos + len(pos_kw) + 5)
                                                                position_after = next_line[start:end].strip()
                                                                break
                                
                                # 过滤掉明显是工作描述的内容（如"工作内容"、"内容一"、"间单位"等）
                                invalid_position_keywords = ['工作内容', '内容一', '内容', '间单位', '单位职位', '职责', '负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队', '开发', '维护', '跟进', '一手', '房源', '销售,', '销售，']
                                if any(kw in position_after for kw in invalid_position_keywords):
                                    # 如果包含工作描述关键词，尝试只取前面的部分（通常是岗位名）
                                    # 找到第一个工作描述关键词的位置
                                    first_invalid_pos = len(position_after)
                                    for kw in invalid_position_keywords:
                                        pos = position_after.find(kw)
                                        if pos > 0 and pos < first_invalid_pos:
                                            first_invalid_pos = pos
                                    if first_invalid_pos < len(position_after):
                                        position_after = position_after[:first_invalid_pos].strip()
                                
                                # 支持多个岗位用顿号分隔（如"储备干部、质量管理"）
                                if position_after:
                                    # 如果包含顿号，取第一个岗位或合并
                                    if '、' in position_after:
                                        positions = [p.strip() for p in position_after.split('、') if p.strip()]
                                        if positions:
                                            position_after = positions[0]  # 取第一个岗位
                                    # 移除岗位中的无效词
                                    position_after = re.sub(r'^(岗位|职位|职务|角色|任职|担任|负责)[：:：，,\s]*', '', position_after).strip()
                                    # 过滤掉明显不是岗位的内容
                                    if position_after and len(position_after) <= 30 and not any(kw in position_after for kw in invalid_position_keywords):
                                        if not company:
                                            # 验证公司名
                                            if self._is_valid_company(comp_candidate_after):
                                                company = comp_candidate_after
                                            else:
                                                comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp_candidate_after).strip()
                                                if self._is_valid_company(comp_cleaned):
                                                    company = comp_cleaned
                                                elif any(comp_candidate_after.endswith(suffix) for suffix in ['公司', '集团', '企业', '分公司', '有限公司']):
                                                    company = comp_candidate_after
                                        if not role:
                                            role = position_after
                    
                    # 优先从before_time中提取公司名和岗位（时间前的文本通常包含公司名和岗位）
                    if before_time:
                        before_cleaned = before_time.strip()
                        # 如果before_time很长，可能包含多个公司名，优先提取最后一个（最接近时间的）
                        # 查找所有公司名匹配
                        company_matches = list(self.company_keywords_regex.finditer(before_cleaned))
                        if company_matches:
                            # 使用最后一个匹配（最接近时间的）
                            last_match = company_matches[-1]
                            comp_candidate_full = last_match.group(1).strip()
                            # 从匹配结果中提取真正的公司名（可能包含前面的业绩描述）
                            # 尝试从匹配结果中提取最后一个有效的公司名
                            # 查找"北京"、"上海"等城市名或公司名关键词的位置
                            city_pattern = r'(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|天津|重庆|青岛|大连|苏州|无锡|宁波|厦门|福州|济南|郑州|长沙|合肥|石家庄|太原|哈尔滨|长春|沈阳|昆明|贵阳|南宁|海口|乌鲁木齐|拉萨|银川|西宁|呼和浩特)'
                            city_match = re.search(city_pattern, comp_candidate_full)
                            if city_match:
                                # 从城市名开始提取公司名
                                city_start = city_match.start()
                                comp_candidate = comp_candidate_full[city_start:].strip()
                            else:
                                # 如果没有城市名，尝试从"公司"、"集团"等关键词往前查找
                                # 查找最后一个"公司"、"集团"等关键词
                                company_end_keywords = ['有限公司', '股份有限公司', '有限责任公司', '公司', '集团', '企业']
                                best_pos = -1
                                for keyword in company_end_keywords:
                                    pos = comp_candidate_full.rfind(keyword)
                                    if pos > best_pos:
                                        best_pos = pos
                                if best_pos > 0:
                                    # 从位置往前查找，找到公司名的开始（通常是城市名或公司名关键词）
                                    # 往前查找最多50个字符
                                    search_start = max(0, best_pos - 50)
                                    search_text = comp_candidate_full[search_start:best_pos + len(company_end_keywords[0])]
                                    # 查找城市名或公司名开始位置
                                    city_match = re.search(city_pattern, search_text)
                                    if city_match:
                                        comp_candidate = search_text[city_match.start():].strip()
                                    else:
                                        # 如果没有城市名，从"公司"等关键词往前查找，找到合理的公司名开始
                                        # 通常公司名长度在3-30个字符之间
                                        comp_candidate = comp_candidate_full[max(0, best_pos - 30):best_pos + len(company_end_keywords[0])].strip()
                                else:
                                    comp_candidate = comp_candidate_full
                            
                            # 提取公司名后的内容作为职位候选
                            after_company = before_cleaned[last_match.end():].strip()
                            # 先尝试使用_split_company_position分离公司名和职位
                            _, pos_candidate = self._split_company_position(after_company)
                            if pos_candidate and not role:
                                role = pos_candidate
                            elif after_company and len(after_company) <= 30 and not role:
                                # 如果_split_company_position没有提取到，直接使用after_company作为职位
                                role = after_company
                        else:
                            # 如果没有找到公司关键词，使用_split_company_position
                            comp_candidate, pos_candidate = self._split_company_position(before_cleaned)
                            if pos_candidate and not role:
                                role = pos_candidate
                        
                        if comp_candidate:
                            # 验证公司名，即使验证失败也先保留（后续可能通过清理后验证）
                            if self._is_valid_company(comp_candidate):
                                company = comp_candidate
                            else:
                                # 尝试清理后再验证
                                comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp_candidate).strip()
                                if self._is_valid_company(comp_cleaned):
                                    company = comp_cleaned
                                elif not company:
                                    # 如果清理后仍然无效，但_split_company_position提取到了，先保留（可能是格式问题）
                                    # 检查是否包含公司关键词
                                    if self.company_keywords_regex.search(comp_candidate):
                                        company = comp_candidate
                                    # 如果包含"有限公司"等后缀，即使验证失败也保留（可能是验证规则太严格）
                                    elif any(comp_candidate.endswith(suffix) for suffix in ['有限公司', '股份有限公司', '有限责任公司', '公司', '集团', '企业']):
                                        company = comp_candidate
                        
                        # 如果_split_company_position没有提取到，再尝试其他方法
                        if not company or not role:
                            # 移除公司名，提取岗位
                            before_for_pos = before_cleaned
                            # 如果包含公司关键词，移除公司名部分
                            if self.company_keywords_regex.search(before_for_pos):
                                # 找到公司名结束位置
                                company_match_in_before = self.company_keywords_regex.search(before_for_pos)
                                if company_match_in_before:
                                    company_end_pos = company_match_in_before.end()
                                    before_for_pos = before_for_pos[company_end_pos:].strip()
                                    # 如果还没有公司名，提取公司名
                                    if not company:
                                        comp_from_match = company_match_in_before.group(1).strip()
                                        if self._is_valid_company(comp_from_match):
                                            company = comp_from_match
                                        else:
                                            # 即使验证失败，如果包含公司关键词也保留
                                            company = comp_from_match
                            # 检查是否包含岗位关键词
                            if before_for_pos and (self.position_keywords_regex.search(before_for_pos) or any(kw in before_for_pos for kw in ['副总', '总监', '经理', '总裁', '总经理', 'CEO', '助理', '渠道', '销售', '商务', '律师', '工程师', '专员', '主管', '顾问'])):
                                # 提取岗位（最多30个字符）
                                if len(before_for_pos) <= 30:
                                    if not role:
                                        role = before_for_pos.strip()
                                else:
                                    # 如果太长，尝试提取包含岗位关键词的部分
                                    pos_match = self.position_keywords_regex.search(before_for_pos)
                                    if pos_match:
                                        start = max(0, pos_match.start() - 5)
                                        end = min(len(before_for_pos), pos_match.end() + 15)
                                        if not role:
                                            role = before_for_pos[start:end].strip()
                                    else:
                                        # 如果没有匹配到关键词，取前30个字符
                                        if not role:
                                            role = before_for_pos[:30].strip()

                    # 检查"在XX公司进行XX工作"格式（支持没有"公司"后缀的情况）
                    # 先清理after_time，移除"初"、"末"等时间修饰词
                    cleaned_after = re.sub(r'^(初|末|底|中|上旬|中旬|下旬)[，,。]?\s*', '', after_time)
                    # 如果cleaned_after包含"进行"但没有"工作"，可能是跨行了，尝试合并下一行
                    if '进行' in cleaned_after and '工作' not in cleaned_after:
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1].strip()
                            if next_line and '工作' in next_line and not re.match(r'^\d{4}', next_line):
                                cleaned_after = cleaned_after + next_line
                    
                    # 使用手动匹配方式，找到"在"、"进行"和最后一个"工作"的位置
                    if '进行' in cleaned_after and '工作' in cleaned_after:
                        jinxing_pos = cleaned_after.find('进行')
                        if jinxing_pos > 0:
                            zai_pos = cleaned_after.rfind('在', 0, jinxing_pos)
                            if zai_pos >= 0:
                                company_candidate = cleaned_after[zai_pos+1:jinxing_pos].strip()
                                # 移除公司名中的逗号、句号等标点
                                company_candidate = re.sub(r'^[，,。、]', '', company_candidate).strip()
                                # 找到最后一个"工作"的位置
                                last_work_pos = cleaned_after.rfind('工作')
                                if last_work_pos > jinxing_pos + 2:
                                    role_candidate = cleaned_after[jinxing_pos+2:last_work_pos].strip()
                                    if company_candidate and role_candidate and len(company_candidate) >= 2 and len(role_candidate) >= 2:
                                        company = company_candidate
                                        role = role_candidate
                                        # 移除职位末尾的"工作"等词
                                        role = re.sub(r'\s*(工作|工作内容|工作职责)(?:。|，|,)?$', '', role).strip()
                                        # 如果公司名没有后缀，尝试补全
                                        if not any(company.endswith(suffix) for suffix in ['公司', '集团', '企业', '研究院', '研究所', '中心', '事务所', '工作室']):
                                            if '教育' in company or '学校' in company or '学院' in company:
                                                pass
                                            else:
                                                company = company + '公司'
                    
                    # 如果手动匹配失败，使用正则表达式
                    if not company or not role:
                        in_company_pattern = re.compile(r'在([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,40}(?:公司|集团|企业|研究院|研究所|中心|事务所|工作室|教育|科技|网络|软件))进行(.+?)(?:工作|工作。)')
                        in_match = in_company_pattern.search(cleaned_after)
                        if not in_match:
                            # 尝试匹配没有后缀的情况（如"在斯维教育进行"）
                            in_company_pattern2 = re.compile(r'在([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,20})进行(.+?)(?:工作|工作。)')
                            in_match = in_company_pattern2.search(cleaned_after)
                        if in_match:
                            company = in_match.group(1).strip()
                            role = in_match.group(2).strip()
                            # 移除职位中的"进行"等动词
                            role = re.sub(r'^(进行|从事|负责|担任)\s*', '', role)
                            role = re.sub(r'\s*(工作|工作内容|工作职责)$', '', role)
                            # 如果公司名没有后缀，尝试补全
                            if not any(company.endswith(suffix) for suffix in ['公司', '集团', '企业', '研究院', '研究所', '中心', '事务所', '工作室']):
                                # 检查是否是教育机构
                                if '教育' in company or '学校' in company or '学院' in company:
                                    pass  # 教育机构不需要后缀
                                else:
                                    company = company + '公司'
                    else:
                        for context in [after_time, before_time]:
                            if company and role:
                                break
                            candidate = clean_candidate(context)
                            if not candidate:
                                continue
                            comp, pos = self._split_company_position(candidate)
                            if comp:
                                # 即使公司名验证失败，也要保留职位信息
                                if pos and not role:
                                    role = pos
                                # 检查公司名是否有效
                                if self._is_valid_company(comp):
                                    company = comp
                                else:
                                    # 公司名验证失败，尝试清理后再验证
                                    comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp).strip()
                                    if self._is_valid_company(comp_cleaned):
                                        company = comp_cleaned
                                    # 如果还是没有有效的公司名，但职位存在，继续处理
                                    if not company and pos:
                                        # 尝试从candidate中提取公司名（移除职位部分）
                                        candidate_without_pos = candidate.replace(pos, '').strip()
                                        comp2, _ = self._split_company_position(candidate_without_pos)
                                        if comp2 and self._is_valid_company(comp2):
                                            company = comp2
                                if not role:
                                    # 如果还没有职位，尝试从remainder中提取
                                    remainder = candidate.replace(comp, '').strip(' ,-|，;；')
                                    # 移除括号内容
                                    remainder = re.sub(r'[（(][^）)]+[）)]', '', remainder).strip()
                                    if remainder and not any(k in remainder for k in ['工作经验', '教育', '薪资', '城市', '期望', '优势']):
                                        for marker in self.position_markers:
                                            if marker in remainder:
                                                role = remainder.split(marker, 1)[1].lstrip('：:，, \t')
                                                break
                                        else:
                                            if len(remainder) <= 30:
                                                role = remainder
                            elif candidate and not company:
                                cleaned_candidate = candidate.strip(' ，,;；')
                                if cleaned_candidate and re.search(r'[\u4e00-\u9fa5]', cleaned_candidate):
                                    company = cleaned_candidate
                    
                    # 如果before_time中没有找到公司，但找到了职位，说明公司名可能在上一行
                    if not company and before_time:
                        # 检查before_time是否只包含职位（不包含公司关键词）
                        before_cleaned = before_time.strip()
                        # 移除时间信息
                        before_cleaned = re.sub(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}.*$', '', before_cleaned).strip()
                        
                        if not self.company_keywords_regex.search(before_cleaned):
                            # 检查是否包含职位关键词
                            if self.position_keywords_regex.search(before_cleaned) or any(kw in before_cleaned for kw in ['副总', '总监', '经理', '总裁', '总经理', 'CEO', '助理', '渠道', '销售', '商务']):
                                # 这可能是职位，公司名在上一行
                                role_candidate = before_cleaned
                                # 如果包含"/"或"、"，可能是多个职位，取第一个
                                if '/' in role_candidate:
                                    role_candidate = role_candidate.split('/')[0].strip()
                                elif '、' in role_candidate:
                                    role_candidate = role_candidate.split('、')[0].strip()
                                
                                if role_candidate and len(role_candidate) <= 30:
                                    role = role_candidate
                                    # 尝试从上一行获取公司名
                                    if idx > 0:
                                        prev_line = lines[idx - 1].strip()
                                        if prev_line and not any(kw in prev_line for kw in ['工作内容', '职责', '负责', '完成', '内容:', '岗位名称']):
                                            comp, _ = self._split_company_position(prev_line)
                                            if comp and self._is_valid_company(comp):
                                                company = comp
                                            elif not comp:
                                                # 如果_split_company_position没有提取到，尝试直接使用整行作为公司名
                                                prev_cleaned = re.sub(r'[（(][^）)]+[）)]', '', prev_line).strip()
                                                if self.company_keywords_regex.search(prev_cleaned) or any(kw in prev_cleaned for kw in ['公司', '集团', '企业', '研究院', '研究所', '中心', '事务所', '工作室']):
                                                    company = prev_cleaned
                                            else:
                                                company = comp

                    # 只有在没有通过"在XX进行XX工作"格式匹配到company和role时，才使用其他方式
                    # 但如果已经从before_time中提取到了公司名，优先使用它
                    if not company:
                        if company_match:
                            company = clean_candidate(company_match.group(1))
                        if not company and last_company:
                            company = clean_candidate(last_company)

                    # 如果通过"在XX进行XX工作"格式匹配到了role，优先使用它
                    position = role if role and len(role) <= 40 else None
                    # 清理职位：移除括号内容、移除"进行"等动词
                    if position:
                        position = re.sub(r'[（(][^）)]+[）)]', '', position)
                        position = re.sub(r'^(进行|从事|负责|担任|任)\s*', '', position)
                        position = re.sub(r'\s*(工作|工作内容|工作职责|工作。)$', '', position)
                        position = position.strip(' ，,;；.。')
                        # 过滤无效的岗位名称
                        invalid_positions = ['内容:', '岗位名称', '公司名称', '职位名称', '岗位', '职位', '角色', '人员']
                        if position in invalid_positions or position.endswith(':'):
                            position = None
                        if not position or len(position) < 2:
                            position = None
                    current_exp = {
                        'company': company,
                        'position': position,
                        'start_year': start_year,
                        'end_year': end_year
                    }
                    experiences.append(current_exp)
                    
                    # 检查下一行是否有职位信息（但跳过"内容:"这种无效行）
                    if idx + 1 < len(lines) and not current_exp.get('position'):
                        next_line = lines[idx + 1].strip()
                        # 跳过无效的下一行（如"内容:"、"岗位名称"等）
                        invalid_next_lines = ['内容:', '岗位名称', '公司名称', '职位名称', '岗位', '职位', '负责工作:', '获得业绩:', '担任角色:']
                        if next_line in invalid_next_lines or next_line.endswith(':'):
                            next_line = None
                        # 跳过以数字开头的工作描述行
                        if next_line and re.match(r'^\d+[、.。]\s*', next_line):
                            if any(kw in next_line for kw in ['负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队']):
                                next_line = None
                        # 严格过滤：下一行不能包含工作描述关键词
                        invalid_next_line_keywords = ['工作经验', '教育', '薪资', '城市', '期望', '优势', '工作内容', '内容一', '内容', '职责', '配合', '参与', '完成', '公司', '集团', '负责', '业绩', '获得', '客户', '项目', '团队', '开发', '维护', '跟进', '间单位', '单位职位']
                        if next_line and not any(keyword in next_line for keyword in invalid_next_line_keywords):
                            # 如果下一行看起来像职位描述
                            # 先尝试提取职位关键词部分（最多30个字符）
                            pos_match = position_pattern.search(next_line)
                            if pos_match:
                                position_text = pos_match.group(1).strip()
                                # 移除时间信息（如"2023.04-2025.0"）
                                position_text = re.sub(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}.*$', '', position_text).strip()
                                # 过滤掉明显是工作描述的内容
                                if position_text and len(position_text) <= 30 and not any(kw in position_text for kw in ['工作内容', '内容一', '内容', '间单位', '单位职位', '职责', '负责', '完成']):
                                    current_exp['position'] = position_text
                                    experiences[-1]['position'] = current_exp['position']
                            elif self.position_keywords_regex.search(next_line):
                                # 提取包含职位关键词的部分
                                match = self.position_keywords_regex.search(next_line)
                                if match:
                                    start = max(0, match.start() - 3)
                                    end = min(len(next_line), match.end() + 15)
                                    position_text = next_line[start:end].strip()
                                    # 移除时间信息
                                    position_text = re.sub(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}.*$', '', position_text).strip()
                                    # 移除特殊字符
                                    position_text = re.sub(r'[•\uf0b2\u2022]', '', position_text)
                                    # 如果包含"/"或"、"，可能是多个职位，取第一个
                                    if '/' in position_text:
                                        position_text = position_text.split('/')[0].strip()
                                    elif '、' in position_text:
                                        position_text = position_text.split('、')[0].strip()
                                    if position_text and len(position_text) <= 30:
                                        current_exp['position'] = position_text
                                        experiences[-1]['position'] = current_exp['position']
                            # 或者如果行很短且不包含公司关键词，可能是职位
                            elif len(next_line) <= 30 and not self.company_keywords_regex.search(next_line) and not re.match(r'^\d{4}', next_line):
                                # 移除时间信息
                                clean_line = re.sub(r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}.*$', '', next_line).strip()
                                # 移除特殊字符
                                clean_line = re.sub(r'[•\uf0b2\u2022]', '', clean_line)
                                # 如果包含"/"或"、"，可能是多个职位，取第一个
                                if '/' in clean_line:
                                    clean_line = clean_line.split('/')[0].strip()
                                elif '、' in clean_line:
                                    clean_line = clean_line.split('、')[0].strip()
                                if clean_line and len(clean_line) <= 30 and not any(kw in clean_line for kw in ['公司', '集团', '企业']):
                                    current_exp['position'] = clean_line
                                    experiences[-1]['position'] = current_exp['position']
                    continue

            # 处理只有开始年份的格式（如"2019 翔海集团房产开发有限公司 销售顾问"）
            # 使用更精确的模式，确保年份后面有公司名或岗位
            single_year_match = single_year_pattern.match(line)
            if not single_year_match:
                # 也支持"2019年"格式
                single_year_match = re.match(r'((?:19|20)\d{2})年\s*(.+)', line)
            if single_year_match:
                start_year = int(single_year_match.group(1))
                if 1980 <= start_year <= self.current_year:
                    candidate = single_year_match.group(2).strip()
                    company = None
                    position = None
                    if candidate:
                        # 支持"·"分隔符（如"恒源艺术馆·销售主管"）
                        if '·' in candidate or '•' in candidate:
                            separator = '·' if '·' in candidate else '•'
                            parts = candidate.split(separator, 1)
                            if len(parts) == 2:
                                comp_candidate = parts[0].strip()
                                pos_candidate = parts[1].strip()
                                # 验证公司名
                                if self._is_valid_company(comp_candidate):
                                    company = comp_candidate
                                else:
                                    comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp_candidate).strip()
                                    if self._is_valid_company(comp_cleaned):
                                        company = comp_cleaned
                                    elif any(comp_candidate.endswith(suffix) for suffix in ['公司', '集团', '企业', '分公司', '有限公司', '馆', '中心']):
                                        company = comp_candidate
                                # 过滤掉明显是工作描述的内容
                                if pos_candidate and len(pos_candidate) <= 30:
                                    invalid_position_keywords = ['工作内容', '内容一', '内容', '间单位', '单位职位', '职责', '负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队', '开发', '维护', '跟进', '一手', '房源', '销售,', '销售，']
                                    if not any(kw in pos_candidate for kw in invalid_position_keywords):
                                        position = pos_candidate
                        else:
                            # 使用原来的逻辑，优先从公司名后提取岗位
                            # 先查找公司名
                            company_matches = list(self.company_keywords_regex.finditer(candidate))
                            if company_matches:
                                # 使用第一个匹配的公司名
                                first_match = company_matches[0]
                                comp_candidate = candidate[first_match.start():first_match.end()].strip()
                                # 提取公司名后的内容作为岗位
                                position_candidate = candidate[first_match.end():].strip()
                                # 清理岗位：移除多余的标点和空格
                                position_candidate = re.sub(r'^[，,、\s]+', '', position_candidate)
                                
                                # 验证公司名
                                if self._is_valid_company(comp_candidate):
                                    company = comp_candidate
                                else:
                                    comp_cleaned = re.sub(r'[（(][^）)]+[）)]', '', comp_candidate).strip()
                                    if self._is_valid_company(comp_cleaned):
                                        company = comp_cleaned
                                    elif any(comp_candidate.endswith(suffix) for suffix in ['公司', '集团', '企业', '分公司', '有限公司', '馆', '中心']):
                                        company = comp_candidate
                                
                                # 过滤掉明显是工作描述的内容
                                if position_candidate:
                                    invalid_position_keywords = ['工作内容', '内容一', '内容', '间单位', '单位职位', '职责', '负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队', '开发', '维护', '跟进', '一手', '房源', '销售,', '销售，']
                                    if any(kw in position_candidate for kw in invalid_position_keywords):
                                        # 如果包含工作描述关键词，尝试只取前面的部分
                                        first_invalid_pos = len(position_candidate)
                                        for kw in invalid_position_keywords:
                                            kw_pos = position_candidate.find(kw)
                                            if kw_pos > 0 and kw_pos < first_invalid_pos:
                                                first_invalid_pos = kw_pos
                                        if first_invalid_pos < len(position_candidate):
                                            position_candidate = position_candidate[:first_invalid_pos].strip()
                                    
                                    # 支持多个岗位用顿号分隔
                                    if '、' in position_candidate:
                                        positions = [p.strip() for p in position_candidate.split('、') if p.strip()]
                                        if positions:
                                            position_candidate = positions[0]  # 取第一个岗位
                                    
                                    # 移除岗位中的无效词
                                    position_candidate = re.sub(r'^(岗位|职位|职务|角色|任职|担任|负责)[：:：，,\s]*', '', position_candidate).strip()
                                    
                                    if position_candidate and len(position_candidate) <= 30 and not any(kw in position_candidate for kw in invalid_position_keywords):
                                        position = position_candidate
                            else:
                                # 如果没有找到公司名，使用原来的逻辑
                                comp, pos = self._split_company_position(candidate)
                                if comp:
                                    company = comp
                                    # 过滤掉明显是工作描述的内容
                                    if pos:
                                        invalid_position_keywords = ['工作内容', '内容一', '内容', '间单位', '单位职位', '职责', '负责', '完成', '参与', '配合', '业绩', '客户', '项目', '团队', '开发', '维护', '跟进', '一手', '房源', '销售,', '销售，']
                                        if any(kw in pos for kw in invalid_position_keywords):
                                            # 如果包含工作描述关键词，尝试只取前面的部分
                                            first_invalid_pos = len(pos)
                                            for kw in invalid_position_keywords:
                                                kw_pos = pos.find(kw)
                                                if kw_pos > 0 and kw_pos < first_invalid_pos:
                                                    first_invalid_pos = kw_pos
                                            if first_invalid_pos < len(pos):
                                                pos = pos[:first_invalid_pos].strip()
                                        if pos and not any(kw in pos for kw in invalid_position_keywords):
                                            position = pos
                                        else:
                                            position = None
                                else:
                                    if re.search(r'[\u4e00-\u9fa5]', candidate):
                                        # 如果_split_company_position没有提取到，尝试直接使用整行作为公司名
                                        company = candidate
                    if company or position:
                        experiences.append({
                            'company': company,
                            'position': position,
                            'start_year': start_year,
                            'end_year': None
                        })

        cleaned = []
        seen = set()
        for exp in experiences:
            company = exp.get('company')
            if company:
                company = company.strip()
                exp['company'] = company
            if exp.get('position'):
                exp['position'] = exp['position'].strip()
                if not exp['position']:
                    exp['position'] = None
                else:
                    exp['position'] = re.sub(r'^(岗位|职位|职务|角色)[:：\s]+', '', exp['position'])

            key = (company, exp.get('start_year'), exp.get('end_year'))
            if (exp.get('company') or exp.get('start_year') or exp.get('end_year')) and key not in seen:
                cleaned.append(exp)
                seen.add(key)
        return cleaned

    def _is_valid_company(self, name: str | None) -> bool:
        if not name:
            return False
        name = name.strip().strip('·•.、，,|/;:')
        if len(name) < 3:
            return False
        if not re.search(r'[\u4e00-\u9fa5]', name):
            return False
        if re.match(r'^[0-9A-Za-z\.]+$', name):
            return False
        stopwords = ['负责', '主要', '完成', '客户', '加盟', '团队', '目标', '方案', '区域', '需求', '角色', '内容', '工作', '职责']
        if any(word in name for word in stopwords):
            return False
        # 扩展公司名后缀，支持"馆"、"中心"等（如"恒源艺术馆"）
        suffix_keywords = ['公司', '集团', '企业', '科技', '有限公司', '有限责任公司', '股份有限公司', '网络科技有限公司', '贸易有限公司', '建设有限公司', '工程有限公司', '控股有限公司', '咨询有限公司', '研究院', '研究所', '学校', '大学', '学院', '中心', '事务所', '工作室', '银行', '医院', '运营部', '事业部', '馆', '艺术馆', '博物馆', '展览馆', '文化馆']
        if not any(name.endswith(suffix) for suffix in suffix_keywords):
            return False
        return True

    def _clean_work_experience(self, experiences):
        if not experiences:
            return []
        cleaned = []
        seen = set()
        for exp in experiences:
            company = exp.get('company')
            position = exp.get('position')
            start_year = exp.get('start_year')
            end_year = exp.get('end_year')

            if company:
                company = re.sub(r'[·•]+$', '', company.strip())
                # 移除公司名开头的数字、日期、特殊字符（如"1青岛韦立集团"、"/3-2017/12..."）
                company = re.sub(r'^[\d./\-年月日\s]+', '', company)
                company = re.sub(r'^[0-9]+[.、)]\s*', '', company)
                # 移除公司名中的错误内容（如"年一月在北京丰台区担任核酸点位长"）
                # 如果公司名包含"年"、"月"、"在"、"担任"等关键词，可能是提取错误
                if re.search(r'年[^公司]*[在担任]', company) or re.search(r'^年', company):
                    # 尝试从公司名中提取真正的公司名
                    company_match = self.company_keywords_regex.search(company)
                    if company_match:
                        company = company_match.group(1).strip()
                    else:
                        # 如果无法提取，设为None
                        company = None
                # 移除公司名中的括号内容（如"（国舜律所）"）
                if company:
                    company = re.sub(r'[（(][^）)]+[）)]', '', company)
                    company = company.strip()
                
                # 移除公司名末尾的无效内容（如"公司"后面跟职位关键词）
                # 但要注意不要截断"有限公司"等完整后缀
                if company and ('公司' in company or '集团' in company):
                    # 先检查是否是完整的公司后缀（如"有限公司"、"股份有限公司"）
                    full_suffixes = ['有限公司', '股份有限公司', '有限责任公司', '集团有限公司']
                    has_full_suffix = any(company.endswith(suffix) for suffix in full_suffixes)
                    
                    if not has_full_suffix:
                        # 查找"公司"、"集团"等词的位置（从右往左找最后一个）
                        company_end = max(
                            company.rfind('公司'),
                            company.rfind('集团'),
                            company.rfind('企业'),
                            company.rfind('研究院'),
                            company.rfind('研究所')
                        )
                        if company_end > 0 and company_end < len(company) - 1:
                            # 如果"公司"后面还有内容，检查是否是职位信息混入了
                            after_company = company[company_end:]
                            # 检查是否是"有限公司"的一部分（"限"在"公司"之前）
                            is_limited_company = False
                            if company_end >= 2 and company_end + 2 <= len(company):
                                # 检查"公司"前面是否是"限"，即"有限公司"（4个字符）
                                if company[company_end-2:company_end+2] == '有限公司':
                                    is_limited_company = True
                            # 也检查其他完整后缀
                            if not is_limited_company:
                                for suffix in ['股份有限公司', '有限责任公司', '集团有限公司']:
                                    if company.endswith(suffix):
                                        is_limited_company = True
                                        break
                            # 如果后面包含职位关键词，且不是"有限公司"的一部分，则截断
                            if any(kw in after_company for kw in ['主管', '经理', '总监', '工程师', '教师', '管理员']) and not is_limited_company:
                                company = company[:company_end + 2]  # 保留"公司"等后缀
                exp['company'] = company
            if position:
                position = position.strip()
                # 移除括号内容（如"（几内亚达圣铁路项目）"）
                position = re.sub(r'[（(][^）)]+[）)]', '', position)
                # 移除"进行"等动词前缀
                position = re.sub(r'^(进行|从事|负责|担任|任)\s*', '', position)
                # 移除"工作"等后缀
                position = re.sub(r'\s*(工作|工作内容|工作职责|工作。)$', '', position)
                # 移除多余的标点和空格
                position = position.strip(' ，,;；.。')
                # 过滤无效职位（如"角色"、"人员"等）
                invalid_positions = ['角色', '人员', '工作', '内容', '职责', '负责', '主要', '完成']
                if position in invalid_positions or len(position) < 2:
                    position = None
                # 如果职位包含"公司"、"集团"等公司关键词，可能是提取错误
                if position and any(kw in position for kw in ['公司', '集团', '企业', '有限公司', '股份有限公司']):
                    position = None
                exp['position'] = position or None

            # 过滤无效公司名（包含"活动"、"签约"、"产值"等关键词的可能是描述而非公司名）
            # 但如果公司名以"有限公司"等后缀结尾，即使包含这些关键词也保留（可能是公司名的一部分）
            if company and any(kw in company for kw in ['活动', '签约', '产值', '储备', '完成', '以上', '万', '个', '名', '工作人员', '点位', '核酸', '联动', '负责', '主要', '内容', '业绩', '获得']):
                # 检查是否是完整的公司名（以"有限公司"等后缀结尾）
                has_company_suffix = any(company.endswith(suffix) for suffix in ['有限公司', '股份有限公司', '有限责任公司', '公司', '集团', '企业'])
                if has_company_suffix:
                    # 如果包含"万"等关键词，可能是业绩描述混入了公司名，尝试提取真正的公司名
                    # 查找最后一个"公司"、"集团"等关键词的位置
                    company_end_keywords = ['有限公司', '股份有限公司', '有限责任公司', '公司', '集团', '企业']
                    best_pos = -1
                    best_keyword = None
                    for keyword in company_end_keywords:
                        pos = company.rfind(keyword)
                        if pos > best_pos:
                            best_pos = pos
                            best_keyword = keyword
                    if best_pos > 0:
                        # 从"公司"等关键词往前查找，找到公司名的开始
                        # 查找城市名
                        city_pattern = r'(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|天津|重庆|青岛|大连|苏州|无锡|宁波|厦门|福州|济南|郑州|长沙|合肥|石家庄|太原|哈尔滨|长春|沈阳|昆明|贵阳|南宁|海口|乌鲁木齐|拉萨|银川|西宁|呼和浩特)'
                        search_start = max(0, best_pos - 50)
                        search_text = company[search_start:best_pos + len(best_keyword)]
                        city_match = re.search(city_pattern, search_text)
                        if city_match:
                            city_start = search_start + city_match.start()
                            company = company[city_start:best_pos + len(best_keyword)].strip()
                        else:
                            # 如果没有城市名，从"公司"等关键词往前查找最多30个字符
                            company = company[max(0, best_pos - 30):best_pos + len(best_keyword)].strip()
                else:
                    # 如果没有公司后缀，且包含这些关键词，则过滤
                    company = None
                    exp['company'] = None
            # 过滤占位符公司名
            if company and company in ['公司名称', '主要负责公司', '主要负责', '负责公司']:
                company = None
                exp['company'] = None
            
            # 如果公司名验证失败，但有职位和时间信息，仍然保留（可能是验证规则太严格）
            if not self._is_valid_company(exp.get('company')):
                # 如果公司名包含"有限公司"等后缀，即使验证失败也保留
                if exp.get('company') and any(exp['company'].endswith(suffix) for suffix in ['有限公司', '股份有限公司', '有限责任公司', '公司', '集团', '企业']):
                    # 保留这个工作经历
                    pass
                elif not (start_year or end_year):
                    # 如果没有时间信息，且公司名无效，则跳过
                    continue

            # 如果公司缺少结尾后缀，尝试补全常见"公司"字样
            # 但先检查公司名是否有效，避免给无效公司名补全
            if exp.get('company') and not any(exp['company'].endswith(suffix) for suffix in ['公司', '集团', '企业', '研究院', '研究所', '学院', '学校', '大学', '中心', '事务所', '工作室']):
                # 检查补全后是否会变成有效公司名
                test_company = exp['company'] + '公司'
                if self._is_valid_company(test_company):
                    exp['company'] = test_company
                # 如果补全后仍然无效，不补全

            # 如果岗位为空但公司字符串中包含岗位关键词，自动识别
            # 但要避免将公司名的一部分（如"集团有限公司"）误识别为职位
            if not position and company:
                # 先检查是否是公司名的一部分（包含"公司"、"集团"等）
                if '公司' in company or '集团' in company or '企业' in company:
                    # 如果公司名中包含职位关键词，且职位关键词在"公司"、"集团"等词之后，才提取
                    job_keywords = ['经理', '主管', '总监', '顾问', '工程师', '设计师', '教师', '老师', '专员', '分析师', '总经理', '经理助理', '运营', '销售', '客服', '行政', '助理', '管理员']
                    # 查找"公司"、"集团"等词的位置
                    company_end = max(
                        company.rfind('公司'),
                        company.rfind('集团'),
                        company.rfind('企业'),
                        company.rfind('研究院'),
                        company.rfind('研究所')
                    )
                    if company_end > 0:
                        # 只在公司名之后查找职位关键词
                        after_company = company[company_end:]
                        for keyword in job_keywords:
                            if keyword in after_company:
                                idx = company.rfind(keyword)
                                if idx > company_end:
                                    exp['position'] = company[idx:].strip()
                                    exp['company'] = company[:idx].strip()
                                    break
                else:
                    # 如果没有"公司"等后缀，按原逻辑处理
                    job_keywords = ['经理', '主管', '总监', '顾问', '工程师', '设计师', '教师', '老师', '专员', '分析师', '总经理', '经理助理', '运营', '销售', '客服', '行政', '助理']
                    role_match = re.search(r'(岗位|职位|职务|角色)[:：\s]*([\u4e00-\u9fa5A-Za-z0-9／/\s]{2,30})', company)
                    if role_match:
                        exp['position'] = role_match.group(2).strip()
                        exp['company'] = company[:role_match.start()].strip()
                    else:
                        for keyword in job_keywords:
                            if keyword in company:
                                idx = company.index(keyword)
                                exp['position'] = company[idx:].strip()
                                exp['company'] = company[:idx].strip()
                                break

            # 改进去重逻辑：基于公司名和开始年份去重，忽略结束年份和职位的差异
            # 先规范化公司名（移除前后空格、统一格式）
            normalized_company = None
            if company:
                normalized_company = company.strip()
                # 移除常见的重复前缀（如"1青岛韦立集团" -> "青岛韦立集团"）
                normalized_company = re.sub(r'^[\d./\-年月日\s]+', '', normalized_company)
                normalized_company = re.sub(r'^[0-9]+[.、)]\s*', '', normalized_company)
            
            # 去重键：公司名（规范化后）+ 开始年份
            dedup_key = (normalized_company, start_year)
            if dedup_key in seen:
                # 如果已存在，检查是否需要合并信息（如补充职位或结束年份）
                existing_exp = next((e for e in cleaned if ((e.get('company') or '').strip() == normalized_company or 
                                               (normalized_company and (e.get('company') or '').strip().endswith(normalized_company))) 
                        and e.get('start_year') == start_year), None)
                if existing_exp:
                    # 如果现有记录没有职位，而新记录有，则更新
                    if not existing_exp.get('position') and position:
                        existing_exp['position'] = position
                    # 如果现有记录没有结束年份，而新记录有，则更新
                    if not existing_exp.get('end_year') and end_year:
                        existing_exp['end_year'] = end_year
                    # 如果现有记录有结束年份，而新记录也有结束年份，保留更完整的（有结束年份的优先）
                    if existing_exp.get('end_year') and end_year:
                        # 如果新记录的结束年份更晚，可能是更准确的信息
                        if end_year > existing_exp.get('end_year'):
                            existing_exp['end_year'] = end_year
                    # 注意：如果现有记录有结束年份，而新记录是None（"至今"），不要覆盖
                continue
            
            seen.add(dedup_key)
            # 更新公司名为规范化后的版本
            if normalized_company:
                exp['company'] = normalized_company
            cleaned.append(exp)
        return cleaned

    def extract_name(self, text: str, kv_pairs: dict) -> str | None:
        """提取姓名"""
        value = kv_pairs.get('姓名')
        if value:
            # 清理OCR错误字符
            cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z·• ]', '', value).strip()
            # 移除OCR常见的错误字符（如"□"、"¡"等）
            cleaned = re.sub(r'[□¡¿]', '', cleaned)
            first_part = re.match(r'([\u4e00-\u9fa5·•]{2,8})', cleaned)
            if first_part:
                candidate = first_part.group(1)
                stop_chars = {'族', '籍', '电', '邮', '住', '性', '学', '手', '号', '龄', '现', '籍'}
                for idx, ch in enumerate(candidate):
                    if ch in stop_chars and idx >= 2:
                        candidate = candidate[:idx]
                        break
                if candidate not in self.invalid_name_tokens:
                    return candidate

        # 常见格式：姓名张三 或 姓名：张三
        name_alias_pattern = r'(?:姓名|中文名|中文姓名|英文姓名|英文)\s*[:：]?\s*([\u4e00-\u9fa5·•]{2,8})'
        match = re.search(name_alias_pattern, text)
        if match:
            candidate = match.group(1)
            # 清理OCR错误
            candidate = re.sub(r'[□¡¿]', '', candidate)
            if candidate and candidate not in self.invalid_name_tokens:
                stop_chars = {'族', '籍', '电', '邮', '住', '性', '学', '手', '号', '龄', '现', '籍'}
                for idx, ch in enumerate(candidate):
                    if ch in stop_chars and idx >= 2:
                        candidate = candidate[:idx]
                        break
                first_part = re.match(r'([\u4e00-\u9fa5·•]{2,8})', candidate)
                if first_part:
                    name_value = first_part.group(1)
                    if name_value not in self.invalid_name_tokens:
                        return name_value

        # 常见格式：张三 男 / 张三 女士
        match = re.search(r'([\u4e00-\u9fa5·•]{2,8})\s*(?:先生|女士|男|女)\b', text)
        if match:
            candidate = match.group(1)
            candidate = re.sub(r'[□¡¿]', '', candidate)  # 清理OCR错误
            if candidate and candidate not in self.invalid_name_tokens:
                return candidate

        # 在联系方式附近查找姓名
        phone_match = re.search(r'(?<!\d)(1[3-9]\d{9})(?!\d)', text)
        email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)

        if email_match:
            after = text[email_match.end(): email_match.end() + 30]
            match = re.search(r'([\u4e00-\u9fa5·•]{2,8})', after)
            if match:
                candidate = re.sub(r'[□¡¿]', '', match.group(1))
                if candidate and candidate not in self.invalid_name_tokens:
                    return candidate
            before = text[max(0, email_match.start() - 50): email_match.start()]
            candidates = re.findall(r'[\u4e00-\u9fa5·•]{2,6}', before)
            for cand in reversed(candidates):
                cand_cleaned = re.sub(r'[□¡¿]', '', cand)
                if cand_cleaned and cand_cleaned not in self.invalid_name_tokens:
                    # 检查上下文，避免提取到"意向岗位"、"商家运营"等
                    cand_pos = before.rfind(cand)
                    context = before[max(0, cand_pos-10):min(len(before), cand_pos+len(cand)+10)]
                    if not any(kw in context for kw in ['岗位', '运营', '意向', '城市', '薪资', '类型', '行业', '状态']):
                        return cand_cleaned

        if phone_match:
            before = text[max(0, phone_match.start() - 50): phone_match.start()]
            candidates = re.findall(r'[\u4e00-\u9fa5·•]{2,6}', before)
            for cand in reversed(candidates):
                cand_cleaned = re.sub(r'[□¡¿]', '', cand)
                if cand_cleaned and cand_cleaned not in self.invalid_name_tokens:
                    # 检查上下文
                    cand_pos = before.rfind(cand)
                    context = before[max(0, cand_pos-10):min(len(before), cand_pos+len(cand)+10)]
                    if not any(kw in context for kw in ['岗位', '运营', '意向', '城市', '薪资', '类型', '行业', '状态']):
                        return cand_cleaned

        contact_positions = []
        if phone_match:
            contact_positions.append(phone_match.start())
        if email_match:
            contact_positions.append(email_match.start())
        if contact_positions:
            idx = min(contact_positions)
            window = text[max(0, idx - 60): idx + 40]
            candidates = re.findall(r'[\u4e00-\u9fa5·•]{2,6}', window)
            for cand in reversed(candidates):
                cand_cleaned = re.sub(r'[□¡¿]', '', cand)
                if cand_cleaned and cand_cleaned not in self.invalid_name_tokens:
                    return cand_cleaned

        # Fallback：取前几行中的中文姓名或"姓名："格式
        lines = text.split('\n')[:30]  # 进一步扩大搜索范围
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 清理OCR错误后再匹配
            line_cleaned = re.sub(r'[□¡¿\s]', '', line)  # 移除OCR错误和空格
            # 更宽松的匹配：允许包含少量非中文字符（可能是OCR错误）
            if len(line_cleaned) >= 2 and len(line_cleaned) <= 10:
                # 提取中文字符部分
                chinese_chars = re.findall(r'[\u4e00-\u9fa5]', line_cleaned)
                if len(chinese_chars) >= 2 and len(chinese_chars) <= 6:
                    candidate = ''.join(chinese_chars)
                    # 检查是否包含常见姓名字符（避免提取到"性别"、"年龄"等）
                    if candidate not in self.invalid_name_tokens:
                        # 检查是否在联系方式附近（更可能是姓名）
                        line_lower = line.lower()
                        if any(kw in line_lower for kw in ['电话', '手机', '邮箱', 'email', '联系']):
                            return candidate
                        # 或者检查是否在简历开头（前1000字符内）
                        if text.find(line) < 1000:
                            return candidate
        
        # 最后尝试：从文本开头提取2-6个连续的中文字符
        text_start = text[:300]  # 扩大检查范围到300字符
        # 先尝试匹配独立成行的姓名（如"李宜隆"单独一行）
        lines = text_start.split('\n')
        for line in lines[:10]:  # 检查前10行
            line_cleaned = re.sub(r'[□¡¿\s]', '', line.strip())
            chinese_only = re.sub(r'[^\u4e00-\u9fa5]', '', line_cleaned)
            if 2 <= len(chinese_only) <= 6:
                if chinese_only not in self.invalid_name_tokens:
                    # 检查上下文，确保不是"性别"、"年龄"、"岗位"等
                    line_lower = line.lower()
                    if not any(kw in line_lower for kw in ['性别', '年龄', '出生', '籍贯', '民族', '岗位', '运营', '意向', '城市', '薪资']):
                        return chinese_only
        
        # 如果独立行没找到，尝试从文本中提取
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text_start)
        if len(chinese_chars) >= 2:
            # 尝试提取连续的2-6个字符作为姓名
            for i in range(len(chinese_chars) - 1):
                for length in range(2, min(7, len(chinese_chars) - i + 1)):
                    candidate = ''.join(chinese_chars[i:i+length])
                    if candidate not in self.invalid_name_tokens:
                        # 检查上下文，确保不是"性别"、"年龄"等
                        candidate_pos = text_start.find(candidate)
                        if candidate_pos >= 0:
                            context_start = max(0, candidate_pos - 10)
                            context_end = min(len(text_start), candidate_pos + len(candidate) + 10)
                            context = text_start[context_start:context_end]
                            if not any(kw in context for kw in ['性别', '年龄', '出生', '籍贯', '民族', '岗位', '运营', '意向']):
                                return candidate
        return None

    def extract_gender(self, text: str, kv_pairs: dict) -> str | None:
        """提取性别"""
        value = kv_pairs.get('性别')
        if value:
            if '女' in value:
                return '女'
            if '男' in value:
                return '男'

        # 匹配"性别：男/女"格式
        match = re.search(r'性别\s*[:：]?\s*(男|女)', text)
        if match:
            return match.group(1)

        # 匹配"姓名 男|女"或"姓名 男 | 年龄"格式（如"邱曙光 男 | 41岁"）
        name_gender_pattern = r'([\u4e00-\u9fa5·•]{2,8})\s*(男|女)(?:\s*[|｜]\s*|\s+|\s*$)'
        match = re.search(name_gender_pattern, text)
        if match:
            return match.group(2)

        # 匹配"男|女 | 年龄"格式
        gender_age_pattern = r'(男|女)\s*[|｜]\s*\d+\s*岁'
        match = re.search(gender_age_pattern, text)
        if match:
            return match.group(1)

        # 在基本信息区域查找（前500字符）
        basic_info = text[:500]
        if '男' in basic_info and '女' not in basic_info:
            # 检查是否在合理的上下文中（避免误匹配）
            if re.search(r'(男|女)(?:\s*[|｜]|\s+岁|\s+性)', basic_info):
                return '男'
        elif '女' in basic_info and '男' not in basic_info:
            if re.search(r'(男|女)(?:\s*[|｜]|\s+岁|\s+性)', basic_info):
                return '女'
        
        return None

    def extract_birth_year(self, text: str, kv_pairs: dict) -> int | None:
        """提取出生年份"""
        for key in ['出生年份', '出生年月', '出生日期']:
            value = kv_pairs.get(key)
            if value:
                match = re.search(r'(19|20)\d{2}', value)
                if match:
                    year = int(match.group(0))
                    if 1950 <= year <= self.current_year:
                        return year

        # 优先在基本信息区域查找（前1500字符），避免从工作经历中误提取
        basic_info = text[:1500]
        lines = text.split('\n')
        
        # 优先查找"出生年月"后或下一行的年份（更精确的上下文判断）
        for idx, line in enumerate(lines[:25]):  # 检查前25行，扩大搜索范围
            line_cleaned = line.strip()
            # 查找"出生年月"、"出生日期"、"出生年份"关键词
            birth_keywords = ['出生年月', '出生日期', '出生年份', '出生', '生日']
            if any(kw in line_cleaned for kw in birth_keywords):
                # 在当前行查找年份（优先查找紧跟在关键词后的年份）
                # 查找"出生年月：1984"或"出生年月 1984"格式
                match = re.search(r'(?:出生[年月日]*|生日)\s*[：:：]?\s*(\d{4})', line_cleaned)
                if not match:
                    # 如果没有紧跟在关键词后，查找行内任意位置的年份
                    match = re.search(r'(19|20)\d{2}', line_cleaned)
                if match:
                    year = int(match.group(1))
                    if 1950 <= year <= self.current_year:
                        # 验证上下文：确保年份在"出生"相关关键词附近
                        match_pos = line_cleaned.find(match.group(0))
                        context_start = max(0, match_pos - 20)
                        context_end = min(len(line_cleaned), match_pos + 20)
                        context = line_cleaned[context_start:context_end]
                        if any(kw in context for kw in birth_keywords):
                            return year
                
                # 如果当前行没有年份，检查下一行（但确保下一行在基本信息区域内）
                if idx + 1 < len(lines) and idx + 1 < 25:
                    next_line = lines[idx + 1].strip()
                    # 检查下一行是否包含年份
                    match = re.search(r'(19|20)\d{2}', next_line)
                    if match:
                        year = int(match.group(0))
                        if 1950 <= year <= self.current_year:
                            # 验证下一行不是工作相关的，且可能是出生年份
                            work_keywords = ['工作', '经历', '经验', '任职', '就职', '入职', '公司', '集团', '企业', '岗位', '职位']
                            if not any(kw in next_line for kw in work_keywords):
                                # 检查下一行是否包含出生相关关键词（可能格式是"1984年"）
                                if '年' in next_line or len(next_line) <= 10:
                                    return year
        
        patterns = [
            r'出生[年月日]*[：:]\s*(\d{4})',
            r'生日[：:]\s*(\d{4})',
            r'出生[年月日]*[：:]\s*(\d{4})[年\-/]',  # 支持"出生日期：1985-01-01"格式
            r'(\d{4})年\d{1,2}月\d{0,2}日?',  # 如"1984年1月"、"1984年1月1日"
            r'(\d{4})年',  # 如"1984年"（单独年份）
            r'出生[年月日]*[：:]\s*(\d{4})[年月]',  # 如"出生年月：1984年"
            r'(\d{4})[年\-/]\d{1,2}[月\-/]\d{0,2}',  # 如"1984-01-01"、"1984/01/01"
            r'(\d{4})[年\-/]\d{1,2}月',  # 如"1984-1月"、"1984/1月"
            r'(\d{4})[年\-/]\d{1,2}',  # 如"1984-1"、"1984/1"
        ]
        
        # 先在基本信息区域查找
        for pattern in patterns:
            match = re.search(pattern, basic_info)
            if match:
                year = int(match.group(1))
                if 1950 <= year <= self.current_year:
                    # 验证：确保不是在"工作"、"经历"等关键词附近
                    match_start = match.start()
                    context_start = max(0, match_start - 50)
                    context_end = min(len(basic_info), match_start + 50)
                    context = basic_info[context_start:context_end]
                    # 排除工作相关的上下文，但允许在"出生"、"生日"附近
                    if '出生' in context or '生日' in context:
                        # 如果在"出生"或"生日"附近，即使有"工作"关键词也接受（可能是"工作地点"等）
                        return year
                    elif not any(kw in context for kw in ['工作', '经历', '经验', '任职', '就职', '入职', '公司', '集团', '企业']):
                        return year
        
        # 如果基本信息区域没找到，再在全文中查找，但要排除工作经历中的日期
        # 排除工作经历中的日期格式（如"2025.03-至今"、"2023.04-2025.0"、"2016.9-2019.2"）
        work_date_pattern = r'\d{4}[./-]\d{1,2}[./-]?\d{0,2}\s*[-~至到]+\s*\d{4}'
        text_without_work_dates = re.sub(work_date_pattern, '', text)
        # 也排除单独的工作年份（如"2019 翔海集团"）
        work_year_pattern = r'(?:19|20)\d{2}\s+[\u4e00-\u9fa5]{2,}(?:公司|集团|企业)'
        text_without_work_dates = re.sub(work_year_pattern, '', text_without_work_dates)
        
        for pattern in patterns:
            match = re.search(pattern, text_without_work_dates)
            if match:
                year = int(match.group(1))
                # 排除明显是工作年份的（2000年以后的，且不在"出生"关键词附近）
                if 1950 <= year < 2000:
                    # 对于1980-1999年的，需要验证上下文
                    match_start = match.start()
                    context_start = max(0, match_start - 50)
                    context_end = min(len(text_without_work_dates), match_start + 50)
                    context = text_without_work_dates[context_start:context_end]
                    if '出生' in context or '生日' in context:
                        return year
                elif 2000 <= year <= self.current_year:
                    # 检查是否在"出生"关键词附近（前后50字符内）
                    match_start = match.start()
                    context_start = max(0, match_start - 50)
                    context_end = min(len(text_without_work_dates), match_start + 50)
                    context = text_without_work_dates[context_start:context_end]
                    if '出生' in context or '生日' in context:
                        # 再次验证不在工作相关上下文中
                        if not any(kw in context for kw in ['工作', '经历', '经验', '任职', '就职', '入职']):
                            return year

        # 不再根据"X岁"推算出生年份，因为用户要求：如简历中没有具体出生日期，则"出生年份"为空
        # 只有明确提取到出生日期时才返回年份，否则返回None

        return None

    def extract_age(self, text: str, kv_pairs: dict, birth_year: int | None) -> int | None:
        """提取年龄"""
        age_value = kv_pairs.get('年龄')
        if age_value:
            match = re.search(r'(\d{1,2})', age_value)
            if match:
                age = int(match.group(1))
                if 16 <= age <= 70:
                    return age

        match = re.search(r'年龄\s*[:：]?\s*(\d{1,2})', text)
        if match:
            age = int(match.group(1))
            if 16 <= age <= 70:
                return age

        match = re.search(r'(\d{1,2})\s*岁', text)
        if match:
            age = int(match.group(1))
            if 16 <= age <= 70:
                return age

        if birth_year:
            calc_age = self.current_year - birth_year
            if 16 <= calc_age <= 70:
                return calc_age

        return None

    def extract_phone(self, text: str, kv_pairs: dict) -> str | None:
        """提取手机号"""
        for key in ['手机', '电话', '联系方式', '联系手机', '手机号', '手机号码', '联系电话']:
            value = kv_pairs.get(key)
            if not value:
                continue
            digits = re.sub(r'\D', '', value)
            match = re.search(r'1[3-9]\d{9}', digits)
            if match:
                return match.group(0)

        # 在文本中查找手机号，支持OCR可能的分隔符错误
        # 支持格式：138-4946-2558, 138 4946 2558, 13849462558等
        phone_patterns = [
            r'(?<!\d)(1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)',  # 带分隔符
            r'(?<!\d)(1[3-9]\d{9})(?!\d)',  # 无分隔符
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = re.sub(r'[\s\-]', '', match.group(1))  # 移除分隔符
                if len(phone) == 11:
                    return phone
        return None

    def extract_email(self, text: str, kv_pairs: dict) -> str | None:
        """提取邮箱"""
        for key in ['邮箱', 'Email', 'email', 'E-mail']:
            value = kv_pairs.get(key)
            if value:
                match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', value)
                if match:
                    return match.group(0)

        match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        if match:
            return match.group(0)
        return None

    def extract_work_experience(self, text: str):
        """提取工作经历"""
        work_experiences = []
        # 更宽松的工作经历段落匹配模式
        work_section_patterns = [
            r'(工作经历|工作经验|职业经历|任职经历|工作履历)[：:：]?\s*(.*?)(?=(教育经历|教育背景|项目经历|自我评价|技能|证书|$))',
            r'(工作经历|工作经验|职业经历|任职经历|工作履历)[：:：]?\s*(.*?)(?=(教育|项目|自我|技能|证书|$))',
        ]
        
        work_text = None
        for pattern in work_section_patterns:
            work_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if work_match:
                work_text = work_match.group(2)
                break

        if work_text:
            # 对于工作经历段落，直接使用_fallback_work_experience来提取
            # 因为它有更完善的逻辑来处理各种格式
            work_experiences = self._fallback_work_experience(work_text)

        # 如果从工作经历段落中没有提取到，尝试从全文提取
        # 即使从工作经历段落中提取到了，也尝试从全文提取，确保不遗漏
        full_text_experiences = self._fallback_work_experience(text)
        
        # 合并两部分的提取结果，去重
        if work_experiences:
            # 合并结果，避免重复
            seen_keys = set()
            for exp in work_experiences:
                key = (exp.get('company'), exp.get('start_year'), exp.get('end_year'))
                if key not in seen_keys:
                    seen_keys.add(key)
            # 添加全文提取中不重复的工作经历
            for exp in full_text_experiences:
                key = (exp.get('company'), exp.get('start_year'), exp.get('end_year'))
                if key not in seen_keys:
                    work_experiences.append(exp)
                    seen_keys.add(key)
        else:
            work_experiences = full_text_experiences

        cleaned = self._clean_work_experience(work_experiences)

        def exp_sort_key(exp):
            start_year = exp.get('start_year')
            end_year = exp.get('end_year')
            if start_year is None and end_year is None:
                return (-1, -1)
            primary = start_year if start_year is not None else end_year
            secondary = end_year if end_year is not None else start_year or -1
            return (primary, secondary)

        # 拆分包含职位的公司字符串
        for exp in cleaned:
            company = exp.get('company')
            if not company:
                continue
            if ' ' in company:
                parts = [part for part in company.split() if part]
                if parts:
                    exp['company'] = parts[0]
                    if not exp.get('position') and len(parts) > 1:
                        exp['position'] = ' '.join(parts[1:])

        cleaned.sort(key=exp_sort_key, reverse=True)
        return cleaned

    def extract_earliest_work_year(self, text: str, work_experiences) -> int | None:
        """从工作经历或文本中推断最早工作年份"""
        years = []
        for exp in work_experiences:
            if exp.get('start_year'):
                years.append(exp['start_year'])

        if years:
            return min(years)

        fallback_years = []
        keywords = ['工作', '经历', '任职', '项目', '公司', '职业', '岗位', '职位', '职务', '实习', '就业']
        skip_words = ['出生', '生日', '年龄']
        for line in text.split('\n'):
            if not any(keyword in line for keyword in keywords):
                continue
            if any(keyword in line for keyword in skip_words):
                continue
            for year_str in re.findall(r'(?:19|20)\d{2}', line):
                year = int(year_str)
                if 1980 <= year <= self.current_year:
                    fallback_years.append(year)

        if fallback_years:
            return min(fallback_years)

        # 兜底：直接从全文提取所有合理年份
        all_years = [int(year_str) for year_str in re.findall(r'(?:19|20)\d{2}', text)
                     if 1980 <= int(year_str) <= self.current_year]
        return min(all_years) if all_years else None

    def extract_education(self, text: str, kv_pairs: dict) -> dict:
        """提取教育信息"""
        education_info = {
            'highest_education': None,
            'school': None,
            'major': None
        }

        # 优先从提取后的文本中抓取学历相关信息（改进：优先从文本提取）
        # 先尝试从文本中提取，再考虑键值对
        detected = self.detect_highest_level_in_text(text)
        if detected:
            education_info['highest_education'] = detected

        # 直接解析键值对（作为补充）
        edu_value = kv_pairs.get('最高学历') or kv_pairs.get('学历')
        if edu_value:
            normalized = self.normalize_education_level(edu_value)
            if normalized:
                education_info['highest_education'] = self._prefer_higher_level(
                    education_info['highest_education'], normalized
                )

        # 增强学校名称提取逻辑，去除无效文字
        school_value = (
            kv_pairs.get('毕业院校') or
            kv_pairs.get('毕业学校') or
            kv_pairs.get('学校') or
            kv_pairs.get('院校')
        )
        if school_value:
            # 清理学校名称中的无效前缀和后缀
            school_value = self._clean_school_name(school_value.strip())
            if school_value:
                education_info['school'] = school_value

        major_value = kv_pairs.get('专业')
        if major_value:
            # 验证专业值是否合理（排除工作描述）
            major_value = major_value.strip()
            if major_value and len(major_value) <= 20:
                if not any(kw in major_value for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目', '管理', '运营', '销售']):
                    cleaned_major = self._clean_major_candidate(major_value)
                    if cleaned_major:
                        education_info['major'] = cleaned_major

        # 匹配教育经历段落
        edu_section_pattern = r'(教育经历|教育背景|学历)[：:：]?\s*(.*?)(?=(工作经历|工作经验|项目经历|自我评价|$))'
        edu_match = re.search(edu_section_pattern, text, re.DOTALL | re.IGNORECASE)

        if edu_match:
            edu_text = edu_match.group(2)

            detected = self.detect_highest_level_in_text(edu_text)
            if detected:
                education_info['highest_education'] = self._prefer_higher_level(
                    education_info['highest_education'], detected
                )

            # 优先按时间排序提取最高学历（时间最晚）对应的学校和专业
            edu_lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
            education_entries = []
            
            for line in edu_lines:
                # 提取时间信息
                time_match = re.search(r'(\d{4})[-~至到](\d{4}|至今)', line)
                if time_match:
                    start_year = int(time_match.group(1))
                    end_year_str = time_match.group(2)
                    end_year = int(end_year_str) if end_year_str != '至今' else self.current_year
                else:
                    # 如果没有时间，跳过
                    continue
                
                # 移除时间信息
                line_no_time = re.sub(r'\d{4}[-~至到]\d{4}', '', line)
                line_no_time = re.sub(r'\d{4}[-~至到]至今', '', line_no_time)
                line_no_time = line_no_time.strip()
                
                # 匹配格式：学校 + 学历 + 专业
                school_major_pattern = r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))\s*(本科|专科|硕士|博士|研究生)?\s*([\u4e00-\u9fa5]{2,20})$'
                match = re.search(school_major_pattern, line_no_time)
                if match:
                    school_part = match.group(1)
                    degree_part = match.group(2)
                    major_candidate = match.group(3)
                    
                    # 验证专业候选
                    invalid_majors = ['本科', '专科', '硕士', '博士', '研究生', '学士', '学习', '起点', '网络', '教育']
                    if major_candidate and major_candidate != school_part and len(major_candidate) <= 20:
                        if major_candidate not in invalid_majors:
                            # 检查是否是工作描述（包含多个工作关键词）
                            work_keywords = ['分析', '需求', '客户', '家长', '孩子', '负责', '完成']
                            work_keyword_count = sum(1 for kw in work_keywords if kw in major_candidate)
                            # 允许包含"管理"、"运营"、"销售"的专业（如"人力资源管理"、"工商管理"）
                            if work_keyword_count < 2 and not re.search(r'(管理|运营|销售)(客户|项目|团队|公司|企业|部门|工作|内容|职责)', major_candidate):
                                cleaned_major = self._clean_major_candidate(major_candidate)
                                if cleaned_major:
                                    education_entries.append({
                                        'school': school_part,
                                        'major': cleaned_major,
                                        'degree': degree_part,
                                        'end_year': end_year
                                    })
                                    continue
                
                # 尝试匹配"学校 专业"格式（没有学历）
                simple_pattern = r'([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))\s+([\u4e00-\u9fa5]{2,20})$'
                match = re.search(simple_pattern, line_no_time)
                if match:
                    school_part = match.group(1)
                    major_candidate = match.group(2)
                    invalid_majors = ['本科', '专科', '硕士', '博士', '研究生', '学士', '学习', '起点', '网络', '教育']
                    if major_candidate and major_candidate != school_part and len(major_candidate) <= 20:
                        if major_candidate not in invalid_majors:
                            # 检查是否是工作描述（包含多个工作关键词）
                            work_keywords = ['分析', '需求', '客户', '家长', '孩子', '负责', '完成']
                            work_keyword_count = sum(1 for kw in work_keywords if kw in major_candidate)
                            # 允许包含"管理"、"运营"、"销售"的专业（如"人力资源管理"、"工商管理"）
                            if work_keyword_count < 2 and not re.search(r'(管理|运营|销售)(客户|项目|团队|公司|企业|部门|工作|内容|职责)', major_candidate):
                                cleaned_major = self._clean_major_candidate(major_candidate)
                                if cleaned_major:
                                    education_entries.append({
                                        'school': school_part,
                                        'major': cleaned_major,
                                        'degree': None,
                                        'end_year': end_year
                                    })
            
            # 按结束年份排序，优先提取最新的（时间最晚的）教育经历
            if education_entries:
                education_entries.sort(key=lambda x: x['end_year'], reverse=True)
                best_entry = education_entries[0]
                # 优先使用按时间排序后的结果（覆盖之前可能提取的错误结果）
                education_info['school'] = best_entry['school']
                education_info['major'] = best_entry['major']
                if best_entry['degree']:
                    normalized = self.normalize_education_level(best_entry['degree'])
                    if normalized:
                        education_info['highest_education'] = self._prefer_higher_level(
                            education_info['highest_education'], normalized
                        )
            
            # 如果上面的结构化提取失败，使用原来的逻辑作为备选
            if not education_info['school']:
                school_match = self.school_regex.search(edu_text)
                if school_match:
                    school_text = school_match.group(0)
                    # 清理前缀（如"教育经历"）
                    school_text = re.sub(r'^(教育经历|教育背景|学历)[：:：]?\s*', '', school_text)
                    if school_text:
                        education_info['school'] = school_text.strip()
            
            # 清理学校名中的前缀（如果之前提取时包含了前缀）
            if education_info['school']:
                education_info['school'] = self._clean_school_name(education_info['school'])

            # 专业优先提取学校前后信息
            if not education_info['major'] and education_info['school']:
                # 优先从学校名称前后提取专业
                school_pos = edu_text.find(education_info['school'])
                if school_pos >= 0:
                    # 在学校名称前后150字符内查找专业
                    context_start = max(0, school_pos - 150)
                    context_end = min(len(edu_text), school_pos + len(education_info['school']) + 150)
                    context = edu_text[context_start:context_end]
                    
                    # 优先匹配学校前后的专业信息
                    major_patterns = [
                        # 学校 专业 格式
                        rf'{re.escape(education_info["school"])}\s+([\u4e00-\u9fa5]{{2,20}})\s*(?:专业|方向)',
                        # 专业：xxx 格式（在学校附近）
                        r'专业[：:]\s*([\u4e00-\u9fa5]{2,20})',
                        # xxx 专业 格式（在学校附近）
                        r'([\u4e00-\u9fa5]{2,20})\s*专业',
                        # 主修：xxx 格式
                        r'主修[：:]\s*([\u4e00-\u9fa5]{2,20})',
                    ]
                    for pattern in major_patterns:
                        match = re.search(pattern, context)
                        if match:
                            candidate = match.group(1).strip(' ：:，,;；/|')
                            candidate = re.sub(r'[□¡¿]', '', candidate)
                            if candidate and len(candidate) >= 2 and len(candidate) <= 20:
                                # 验证候选专业
                                if not any(kw in candidate for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目', '本科', '专科', '硕士', '博士']):
                                    cleaned_candidate = self._clean_major_candidate(candidate)
                                    if cleaned_candidate:
                                        education_info['major'] = cleaned_candidate
                                        break
            
            # 如果还没找到，使用原来的逻辑作为备选
            if not education_info['major']:
                major_match = self.major_regex.search(edu_text)
                if major_match:
                    candidate = major_match.group(1).strip()
                    if candidate and len(candidate) <= 20:
                        if not any(kw in candidate for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目', '管理', '运营', '销售']):
                            cleaned_candidate = self._clean_major_candidate(candidate)
                            if cleaned_candidate:
                                education_info['major'] = cleaned_candidate

        if not education_info['school']:
            school_match = self.school_regex.search(text)
            if school_match:
                education_info['school'] = school_match.group(0)

        if not education_info['major']:
            # 扩大搜索范围，不仅限于包含"专业"的行
            # 但优先在教育经历段落中查找，避免误提取工作描述
            for line in text.split('\n'):
                # 先尝试匹配包含"专业"关键词的行
                # 但排除工作经历、项目经历等段落
                if any(kw in line for kw in ['工作经历', '工作经验', '项目经历', '工作内容', '职责', '负责']):
                    continue
                if '专业' in line or '方向' in line:
                    match = self.major_regex.search(line)
                    if match:
                        candidate = match.group(1).strip(' ：:，,;；/|')
                        # 清理OCR错误
                        candidate = re.sub(r'[□¡¿]', '', candidate)
                        # 验证候选专业是否合理（排除工作描述）
                        if candidate and len(candidate) >= 2 and len(candidate) <= 20:
                            # 排除明显是工作描述的内容
                            if not any(kw in candidate for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目']):
                                cleaned_candidate = self._clean_major_candidate(candidate)
                                if cleaned_candidate:
                                    education_info['major'] = cleaned_candidate
                                    break
                # 如果还没找到，尝试在教育经历段落中查找
                # 专业优先提取学校前后信息
                if education_info.get('school') and not education_info.get('major'):
                    # 在学校名称附近查找专业（扩大搜索范围到150字符）
                    school_pos = text.find(education_info['school'])
                    if school_pos >= 0:
                        # 在学校名称前后150字符内查找
                        context_start = max(0, school_pos - 150)
                        context_end = min(len(text), school_pos + len(education_info['school']) + 150)
                        context = text[context_start:context_end]
                        
                        # 优先匹配学校前后的专业信息
                        major_patterns = [
                            # 学校 专业 格式（最优先）
                            rf'{re.escape(education_info["school"])}\s+([\u4e00-\u9fa5]{{2,20}})\s*(?:专业|方向)',
                            # 专业：xxx 格式（在学校附近）
                            r'专业[：:]\s*([\u4e00-\u9fa5]{2,20})',
                            # xxx 专业 格式（在学校附近）
                            r'([\u4e00-\u9fa5]{2,20})\s*专业',
                            # 主修：xxx 格式
                            r'主修[：:]\s*([\u4e00-\u9fa5]{2,20})',
                        ]
                        for pattern in major_patterns:
                            match = re.search(pattern, context)
                            if match:
                                candidate = match.group(1).strip(' ：:，,;；/|')
                                candidate = re.sub(r'[□¡¿]', '', candidate)
                                if candidate and len(candidate) >= 2 and len(candidate) <= 20:
                                    # 验证候选专业（排除学历和工作描述）
                                    if not any(kw in candidate for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目', '本科', '专科', '硕士', '博士', '研究生']):
                                        cleaned_candidate = self._clean_major_candidate(candidate)
                                        if cleaned_candidate:
                                            education_info['major'] = cleaned_candidate
                                            break
                        if education_info.get('major'):
                            break

        if not education_info['school']:
            school_match = self.school_regex.search(text)
            if school_match:
                education_info['school'] = school_match.group(0)

        # 在“教育经历”附近的上下文补充信息
        lines = [line.strip() for line in text.split('\n')]
        for idx, line in enumerate(lines):
            if not line:
                continue
            if any(keyword in line for keyword in ['教育经历', '教育背景', '学历']):
                start = max(0, idx - 1)
                end = min(len(lines), idx + 6)
                for ctx_idx in range(start, end):
                    self._update_education_from_line(education_info, lines[ctx_idx])
                if education_info['highest_education'] and education_info['school'] and education_info['major']:
                    break

        # 若仍缺字段，再围绕学校或学历关键词进行邻近解析
        for idx, line in enumerate(lines):
            if not line:
                continue
            if self.school_regex.search(line) or any(keyword in line for keyword in self.education_keywords):
                start = max(0, idx - 2)
                end = min(len(lines), idx + 5)
                for ctx_idx in range(start, end):
                    self._update_education_from_line(education_info, lines[ctx_idx])
                if education_info['highest_education'] and education_info['school'] and education_info['major']:
                    break

        if education_info['school']:
            # 最终清理学校名前缀（在所有提取逻辑之后）
            education_info['school'] = self._clean_school_name(education_info['school'])
            
            detected = self.detect_highest_level_in_text(education_info['school'])
            if detected:
                education_info['highest_education'] = self._prefer_higher_level(
                    education_info['highest_education'], detected
                )

        # 分析包含学校的行，提取结构化信息
        entries = self._extract_education_entries(lines)
        if entries:
            # 按学历优先级排序，取最高学历对应的记录
            def entry_score(entry):
                return self.education_levels.get(entry.get('highest_education'), 0)

            entries.sort(key=entry_score, reverse=True)
            best_entry = entries[0]
            best_level = best_entry.get('highest_education')
            current_score = self.education_levels.get(education_info['highest_education'], 0)
            best_score = self.education_levels.get(best_level, 0)

            if best_score >= current_score:
                if best_entry.get('school'):
                    # 清理学校名前缀
                    education_info['school'] = self._clean_school_name(best_entry['school'])
                if best_level:
                    education_info['highest_education'] = self._prefer_higher_level(
                        education_info['highest_education'], best_level
                    )
                if best_entry.get('major'):
                    education_info['major'] = best_entry['major']
            else:
                # 即使学历不是更高，也可以补充缺失字段
                if not education_info['school'] and best_entry.get('school'):
                    # 清理学校名前缀
                    education_info['school'] = self._clean_school_name(best_entry['school'])
                if not education_info['major'] and best_entry.get('major'):
                    education_info['major'] = best_entry['major']

        level_match = re.search(r'(博士|硕士|研究生|本科|学士|大专|专科|高中|中专|职高)', text)
        if level_match:
            education_info['highest_education'] = self._prefer_higher_level(
                education_info['highest_education'], level_match.group(1)
            )

        detected = self.detect_highest_level_in_text(text)
        if detected:
            education_info['highest_education'] = self._prefer_higher_level(
                education_info['highest_education'], detected
            )

        if not education_info['highest_education']:
            priority_fallback = [
                ('博士', '博士'),
                ('硕士', '硕士'),
                ('研究生', '硕士'),
                ('本科', '本科'),
                ('学士', '本科'),
                ('大专', '专科'),
                ('专科', '专科'),
                ('college', '专科'),
                ('associate', '专科'),
                ('高中', '高中'),
                ('中学', '高中'),
                ('中专', '中专'),
                ('技校', '中专'),
                ('职校', '中专'),
            ]
            lowered = text.lower()
            for keyword, level in priority_fallback:
                if keyword.lower() in lowered:
                    education_info['highest_education'] = self._prefer_higher_level(
                        education_info['highest_education'], level
                    )
                    break

        if education_info['highest_education'] in {'高中', '初中'}:
            education_info['major'] = None

        return education_info

    def _update_education_from_line(self, education_info: dict, line: str) -> None:
        if not line:
            return
        stripped = line.strip()
        if not stripped:
            return
        # 跳过加密或噪声行
        if re.search(r'[A-Za-z0-9]{18,}', stripped):
            return

        school_match = self.school_regex.search(stripped)
        if school_match:
            candidate_school = re.sub(r'^[0-9年月\s]+', '', school_match.group(0)).lstrip('月')
            if ('毕业' in candidate_school or '教育' in candidate_school) and len(candidate_school) <= 6:
                candidate_school = None
            if (':' in stripped or '：' in stripped) and not candidate_school:
                remainder = stripped.split('：', 1)[-1] if '：' in stripped else stripped.split(':', 1)[-1]
                remainder_match = self.school_regex.search(remainder)
                if remainder_match:
                    candidate_school = re.sub(r'^[0-9年月\s]+', '', remainder_match.group(0)).lstrip('月')
            if candidate_school and not education_info.get('school'):
                education_info['school'] = candidate_school

        major_match = self.major_regex.search(stripped)
        if major_match:
            candidate = major_match.group(1).strip(' ：:，,;；/|')
            if candidate:
                # 验证候选专业是否合理（排除工作描述）
                if candidate and len(candidate) <= 20:
                    if not any(kw in candidate for kw in ['分析', '需求', '客户', '家长', '孩子', '负责', '完成', '工作', '项目', '管理', '运营', '销售']):
                        cleaned_candidate = self._clean_major_candidate(candidate)
                        if cleaned_candidate:
                            if not education_info.get('major') or education_info['major'].startswith('专业'):
                                education_info['major'] = cleaned_candidate
        else:
            if not education_info.get('major'):
                # 尝试识别形如“计算机科学与技术”等独立专业名，常见于学校后面
                if stripped.endswith('专业') and len(stripped) <= 20:
                    education_info['major'] = stripped[:-2].strip()

        level = self.detect_highest_level_in_text(stripped)
        if level:
            education_info['highest_education'] = self._prefer_higher_level(
                education_info.get('highest_education'), level
            )

        # 针对“时间 + 学校 + 专业 + 学历”结构化行的补充解析
        time_cleaned = re.sub(
            r'(?:19|20)\d{2}(?:[./年-]\d{1,2}(?:月)?)?\s*[-~至到]+\s*(?:19|20)\d{2}(?:[./年-]\d{1,2}(?:月)?|至今|现在)',
            ' ',
            stripped
        )
        time_cleaned = re.sub(r'(?:19|20)\d{2}(?:[./年-]\d{1,2}(?:月)?)?', ' ', time_cleaned)
        tokens = [tok for tok in re.split(r'[ \t\|,，;；/]+', time_cleaned) if tok]
        if tokens:
            for idx, token in enumerate(tokens):
                school_value = None
                token_variants = [token]
                if '学历' in token and ('大专' in token or '专科' in token or '本科' in token or '硕士' in token or '研究生' in token):
                    continue
                if any(level in token for level in ['本科', '大专', '专科']) and not any(keyword in token for keyword in ['大学', '学院', '学校', '中学']):
                    if idx + 1 < len(tokens):
                        combined = token + ' ' + tokens[idx + 1]
                        token_variants.append(combined)
                if '：' in token:
                    token_variants.append(token.split('：', 1)[-1].strip())
                if ':' in token:
                    token_variants.append(token.split(':', 1)[-1].strip())
                augmented_variants = []
                for variant in token_variants:
                    variant_no_time = re.sub(r'(?:19|20)\d{2}\s*年?\s*\d{0,2}月?', '', variant)
                    augmented_variants.extend([variant, variant_no_time])
                token_variants = [v.strip() for v in augmented_variants if v.strip()]
                for variant in token_variants:
                    if not variant:
                        continue
                    school_candidate = self.school_regex.search(variant)
                    if not school_candidate:
                        continue
                    candidate_school = re.sub(r'^[0-9年月\s]+', '', school_candidate.group(0)).lstrip('月')
                    if ('毕业' in candidate_school or '教育' in candidate_school) and len(candidate_school) <= 6:
                        continue
                    school_value = candidate_school
                    break
                if not school_value:
                    continue
                if (not education_info.get('school') or education_info.get('school') in {'毕业学校', '毕业院校', '毕业院校'}):
                    education_info['school'] = school_value

                degree_token = self.detect_highest_level_in_text(token)
                if degree_token:
                    education_info['highest_education'] = self._prefer_higher_level(
                        education_info.get('highest_education'), degree_token
                    )

                neighbors = tokens[max(0, idx - 1): idx] + tokens[idx + 1: idx + 5]
                for neighbor in neighbors:
                    if not education_info.get('highest_education'):
                        degree_candidate = self.detect_highest_level_in_text(neighbor)
                        if degree_candidate:
                            education_info['highest_education'] = self._prefer_higher_level(
                                education_info.get('highest_education'), degree_candidate
                            )
                    if not education_info.get('major'):
                        major_candidate = self._clean_major_candidate(neighbor)
                        if major_candidate:
                            education_info['major'] = major_candidate
                    else:
                        if education_info.get('major') and education_info['major'].startswith('专业'):
                            major_candidate = self._clean_major_candidate(neighbor)
                            if major_candidate:
                                education_info['major'] = major_candidate
                    if (education_info.get('highest_education')
                            and education_info.get('major')):
                        break
                if education_info.get('school') and education_info.get('major') and education_info.get('highest_education'):
                    break

    def extract_all(self, text: str, use_ai: bool = False, ai_result: dict = None) -> dict:
        """
        提取所有信息
        
        Args:
            text: 简历文本
            use_ai: 是否使用AI辅助（已废弃，保留兼容性）
            ai_result: AI提取的结果，如果提供则进行融合
        
        Returns:
            提取的信息字典
        """
        cleaned_text = self.clean_text(text)
        kv_pairs = self.parse_key_values(cleaned_text)

        name = self.extract_name(cleaned_text, kv_pairs)
        gender = self.extract_gender(cleaned_text, kv_pairs)
        birth_year = self.extract_birth_year(cleaned_text, kv_pairs)
        age = self.extract_age(cleaned_text, kv_pairs, birth_year)
        phone = self.extract_phone(cleaned_text, kv_pairs)
        email = self.extract_email(cleaned_text, kv_pairs)

        work_experiences = self.extract_work_experience(cleaned_text)
        earliest_work_year = self.extract_earliest_work_year(cleaned_text, work_experiences)

        education = self.extract_education(cleaned_text, kv_pairs)

        rule_result = {
            'name': name,
            'gender': gender,
            'birth_year': birth_year,
            'age': age,
            'phone': phone,
            'email': email,
            'earliest_work_year': earliest_work_year,
            'work_experience': work_experiences,
            'highest_education': education['highest_education'],
            'school': education['school'],
            'major': education['major'],
            'raw_text': cleaned_text
        }
        
        # 如果提供了AI结果，进行融合
        if ai_result:
            from utils.ai_extractor import merge_extraction_results
            return merge_extraction_results(rule_result, ai_result)
        
        return rule_result
