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
        if not text:
            return ''
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('⻄', '西')
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\xa0', ' ').replace('\u3000', ' ')
        text = text.replace('姓⺠名', '姓名')
        text = text.replace('姓民名', '姓名')
        text = text.replace('姓氏名', '姓名')
        text = re.sub(r'(\d{4})\s*\n\s*[-~至到]\s*\n\s*((?:19|20)\d{2}|至今|现在)', r'\1-\2', text)
        text = re.sub(r'(\d{4})(?:/|\\)\n(\d{1,2})', r'\1/\2', text)
        text = re.sub(r'([\u4e00-\u9fa5]{2,})\n(公司|集团|企业)', r'\1\2', text)
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
        if any(keyword in token for keyword in ['学习', '起点', '学校']):
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
            remainder = candidate[best_end:].strip(' ,-|，;；')
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

        if company and not self._is_valid_company(company):
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

        return company, (position or None)

    def parse_key_values(self, text: str) -> dict:
        """解析带有键值对格式的字段，如：姓名：张三"""
        pattern = re.compile(
            rf'({self.key_pattern})\s*[:：]\s*([^\n]+?)\s*(?=(?:{self.key_pattern})\s*[:：]|$)'
        )
        pairs = {}
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            for match in pattern.finditer(line):
                key = match.group(1)
                value = match.group(2).strip()
                if key not in pairs and value:
                    pairs[key] = value
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
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        experiences = []
        last_company = None
        current_exp = None
        time_pattern = re.compile(
            r'((?:19|20)\d{2}(?:[./-]\d{1,2})?)\s*[-~至到]+\s*'
            r'((?:19|20)\d{2}(?:[./-]\d{1,2})?|至今|现在)'
        )
        position_pattern = re.compile(
            r'(?:担任|职位|岗位|职务|角色|方向)[：:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]+)'
        )

        for line in lines:
            if any(keyword in line for keyword in ['教育经历', '教育背景', '求职意向', '项目经历']):
                continue
            if '教育' in line and '公司' not in line:
                last_company = None
                continue
            if any(keyword in line for keyword in ['大学', '学院', '学校', '中学', '高中']) and '公司' not in line:
                last_company = None
                continue
            if re.match(r'^(时间|单位|职位|岗位|名称)[\s\u4e00-\u9fa5]*$', line):
                continue

            company_match = self.company_keywords_regex.search(line)
            if company_match:
                last_company = company_match.group(1).strip()

            matches = list(time_pattern.finditer(line))
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
                    seg_end = matches[idx_match + 1].start() if idx_match + 1 < len(matches) else len(line)
                    after_time = line[seg_start:seg_end].strip()
                    before_start = matches[idx_match - 1].end() if idx_match > 0 else 0
                    before_time = line[before_start:time_match.start()].strip()

                    company = None
                    role = None

                    for context in [after_time, before_time]:
                        if company:
                            break
                        candidate = clean_candidate(context)
                        if not candidate:
                            continue
                        comp, pos = self._split_company_position(candidate)
                        if comp:
                            company = comp
                            if pos:
                                role = pos
                            else:
                                remainder = candidate.replace(comp, '').strip(' ,-|，;；')
                                if remainder and not any(k in remainder for k in ['工作经验', '教育', '薪资', '城市', '期望', '优势']):
                                    for marker in self.position_markers:
                                        if marker in remainder:
                                            role = remainder.split(marker, 1)[1].lstrip('：:，, \t')
                                            break
                                    else:
                                        if len(remainder) <= 20:
                                            role = remainder
                        elif candidate and not company:
                            cleaned_candidate = candidate.strip(' ，,;；')
                            if cleaned_candidate and re.search(r'[\u4e00-\u9fa5]', cleaned_candidate):
                                company = cleaned_candidate

                    if not company and company_match:
                        company = clean_candidate(company_match.group(1))
                    if not company and last_company:
                        company = clean_candidate(last_company)

                    position = role if role and len(role) <= 40 else None
                    current_exp = {
                        'company': company,
                        'position': position,
                        'start_year': start_year,
                        'end_year': end_year
                    }
                    experiences.append(current_exp)
                continue

            if current_exp:
                pos_match = position_pattern.search(line)
                if pos_match:
                    current_exp['position'] = pos_match.group(1).strip()
                elif not current_exp.get('position'):
                    if not any(keyword in line for keyword in ['工作经验', '教育', '薪资', '城市', '期望', '优势']):
                        if 2 <= len(line) <= 30:
                            possible_position = ' '.join(line.split())
                            if self.position_keywords_regex.search(possible_position):
                                current_exp['position'] = possible_position
                            else:
                                current_exp['position'] = None
                        else:
                            current_exp['position'] = None
                continue

            single_year_match = re.match(r'((?:19|20)\d{2})[年.\s-]*\s*(.+)', line)
            if single_year_match:
                start_year = int(single_year_match.group(1))
                if 1980 <= start_year <= self.current_year:
                    candidate = single_year_match.group(2).strip()
                    company = None
                    position = None
                    if candidate:
                        comp, pos = self._split_company_position(candidate)
                        if comp:
                            company = comp
                            position = pos
                        else:
                            if re.search(r'[\u4e00-\u9fa5]', candidate):
                                company = candidate
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
        suffix_keywords = ['公司', '集团', '企业', '科技', '有限公司', '有限责任公司', '股份有限公司', '网络科技有限公司', '贸易有限公司', '建设有限公司', '工程有限公司', '控股有限公司', '咨询有限公司', '研究院', '研究所', '学校', '大学', '学院', '中心', '事务所', '工作室', '银行', '医院', '运营部', '事业部']
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
                exp['company'] = company
            if position:
                position = position.strip()
                exp['position'] = position or None

            if not self._is_valid_company(exp.get('company')) and not (start_year or end_year):
                continue

            # 如果公司缺少结尾后缀，尝试补全常见“公司”字样
            if exp.get('company') and not any(exp['company'].endswith(suffix) for suffix in ['公司', '集团', '企业', '研究院', '研究所', '学院', '学校', '大学', '中心', '事务所', '工作室']):
                exp['company'] = exp['company'] + '公司'

            # 如果岗位为空但公司字符串中包含岗位关键词，自动识别
            if not position and company:
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

            key = (exp.get('company'), start_year, end_year, exp.get('position'))
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(exp)
        return cleaned

    def extract_name(self, text: str, kv_pairs: dict) -> str | None:
        """提取姓名"""
        value = kv_pairs.get('姓名')
        if value:
            cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z·• ]', '', value).strip()
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
            if candidate not in self.invalid_name_tokens:
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
        if match and match.group(1) not in self.invalid_name_tokens:
            return match.group(1)

        # 在联系方式附近查找姓名
        phone_match = re.search(r'(?<!\d)(1[3-9]\d{9})(?!\d)', text)
        email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)

        if email_match:
            after = text[email_match.end(): email_match.end() + 20]
            match = re.search(r'([\u4e00-\u9fa5·•]{2,8})', after)
            if match and match.group(1) not in self.invalid_name_tokens:
                return match.group(1)
            before = text[max(0, email_match.start() - 20): email_match.start()]
            candidates = re.findall(r'[\u4e00-\u9fa5·•]{2,6}', before)
            for cand in reversed(candidates):
                if cand not in self.invalid_name_tokens:
                    return cand

        if phone_match:
            before = text[max(0, phone_match.start() - 30): phone_match.start()]
            candidates = re.findall(r'[\u4e00-\u9fa5·•]{2,6}', before)
            for cand in reversed(candidates):
                if cand not in self.invalid_name_tokens:
                    return cand

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
                if cand not in self.invalid_name_tokens:
                    return cand

        # Fallback：取前几行中的中文姓名或“姓名：”格式
        lines = text.split('\n')[:15]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(r'^[\u4e00-\u9fa5·•]{2,6}$', line)
            if match and line not in self.invalid_name_tokens:
                return match.group(0)
        return None

    def extract_gender(self, text: str, kv_pairs: dict) -> str | None:
        """提取性别"""
        value = kv_pairs.get('性别')
        if value:
            if '女' in value:
                return '女'
            if '男' in value:
                return '男'

        match = re.search(r'性别\s*[:：]?\s*(男|女)', text)
        if match:
            return match.group(1)

        if '女' in text:
            return None
        if '男' in text:
            return None
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

        patterns = [
            r'出生[年月日]*[：:]\s*(\d{4})',
            r'生日[：:]\s*(\d{4})',
            r'(\d{4})年\d{1,2}月\d{0,2}日?',
            r'(\d{4})\.\d{1,2}\.\d{1,2}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year = int(match.group(1))
                if 1950 <= year <= self.current_year:
                    return year

        # 根据“X岁”推算出生年份
        age_match = re.search(r'(\d{1,2})\s*岁', text)
        if age_match:
            age = int(age_match.group(1))
            if 16 <= age <= 70:
                return self.current_year - age

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

        match = re.search(r'(?<!\d)(1[3-9]\d{9})(?!\d)', text)
        if match:
            return match.group(1)
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
        work_section_pattern = r'(工作经历|工作经验|职业经历|任职经历)[：:：]?\s*(.*?)(?=(教育经历|教育背景|项目经历|自我评价|$))'
        work_match = re.search(work_section_pattern, text, re.DOTALL | re.IGNORECASE)

        if work_match:
            work_text = work_match.group(2)
            company_pattern = r'([\u4e00-\u9fa5a-zA-Z0-9（）()&·\.]{2,30})(?:公司|集团|企业|科技|有限|股份|工作室)'
            position_pattern = r'(?:担任|职位|岗位|职务)[：:：]?\s*([\u4e00-\u9fa5a-zA-Z0-9（）()&·\.]+)'
            time_pattern = r'((?:19|20)\d{2})[年./-]?(?:\d{1,2})?[月.]?\s*[-~至到]+\s*((?:19|20)\d{2})?[年./-]?(?:\d{1,2})?[月.]?|((?:19|20)\d{2})[年./-]?(?:\d{1,2})?[月.]?\s*(至今|现在)'

            lines = work_text.split('\n')
            current_exp = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                company_match = re.search(company_pattern, line)
                if company_match:
                    if current_exp:
                        work_experiences.append(current_exp)
                    current_exp = {
                        'company': company_match.group(1),
                        'position': None,
                        'start_year': None,
                        'end_year': None
                    }

                position_match = re.search(position_pattern, line)
                if position_match and current_exp:
                    current_exp['position'] = position_match.group(1)

                time_match = re.search(time_pattern, line)
                if time_match and current_exp:
                    start_year = time_match.group(1) or time_match.group(3)
                    end_year = time_match.group(2)
                    if start_year:
                        start_year = int(start_year)
                        if 1980 <= start_year <= self.current_year:
                            current_exp['start_year'] = start_year
                    if end_year and end_year.isdigit():
                        end_year = int(end_year)
                        if 1980 <= end_year <= self.current_year:
                            current_exp['end_year'] = end_year

            if current_exp:
                work_experiences.append(current_exp)

        if not work_experiences:
            work_experiences = self._fallback_work_experience(text)

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

        # 直接解析键值对
        edu_value = kv_pairs.get('最高学历') or kv_pairs.get('学历')
        if edu_value:
            normalized = self.normalize_education_level(edu_value)
            if normalized:
                education_info['highest_education'] = self._prefer_higher_level(
                    education_info['highest_education'], normalized
                )

        school_value = (
            kv_pairs.get('毕业院校') or
            kv_pairs.get('毕业学校') or
            kv_pairs.get('学校') or
            kv_pairs.get('院校')
        )
        if school_value:
            education_info['school'] = school_value.strip()

        major_value = kv_pairs.get('专业')
        if major_value:
            education_info['major'] = major_value.strip()

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

            if not education_info['school']:
                school_match = self.school_regex.search(edu_text)
                if school_match:
                    education_info['school'] = school_match.group(0)

            if not education_info['major']:
                major_match = self.major_regex.search(edu_text)
                if major_match:
                    education_info['major'] = major_match.group(1).strip()

        if not education_info['school']:
            school_match = self.school_regex.search(text)
            if school_match:
                education_info['school'] = school_match.group(0)

        if not education_info['major']:
            for line in text.split('\n'):
                if '专业' not in line and '方向' not in line:
                    continue
                match = self.major_regex.search(line)
                if match:
                    candidate = match.group(1).strip(' ：:，,;；/|')
                    if candidate:
                        education_info['major'] = candidate
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
                    education_info['school'] = best_entry['school']
                if best_level:
                    education_info['highest_education'] = self._prefer_higher_level(
                        education_info['highest_education'], best_level
                    )
                if best_entry.get('major'):
                    education_info['major'] = best_entry['major']
            else:
                # 即使学历不是更高，也可以补充缺失字段
                if not education_info['school'] and best_entry.get('school'):
                    education_info['school'] = best_entry['school']
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
                if not education_info.get('major') or education_info['major'].startswith('专业'):
                    education_info['major'] = candidate
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

    def extract_all(self, text: str) -> dict:
        """提取所有信息"""
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

        return {
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
