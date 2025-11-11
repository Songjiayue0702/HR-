"""
信息提取工具
从简历文本中提取关键信息
"""

import re
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
            '经理', '主管', '老师', '教师', '顾问', '销售',
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
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\xa0', ' ').replace('\u3000', ' ')
        # 去除冗余长字符串（常见的加密文件标识）
        text = re.sub(r'\b[a-zA-Z0-9]{18,}\b', ' ', text)
        # 在常见段落标题前补换行，便于分段
        for keyword in self.section_keywords:
            text = re.sub(rf'\s*{keyword}', f'\n{keyword}', text)
        # 规范空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

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

            company_match = self.company_keywords_regex.search(line)
            if company_match:
                last_company = company_match.group(1).strip()

            time_match = time_pattern.search(line)
            if time_match:
                start_part = time_match.group(1)
                end_part = time_match.group(2)
                start_year = self._extract_year_from_string(start_part, self.current_year)
                if end_part in ('至今', '现在'):
                    end_year = None
                else:
                    end_year = self._extract_year_from_string(end_part, self.current_year)

                after_time = line[time_match.end():].strip()
                before_time = line[:time_match.start()].strip()
                company = None
                role = None

                def clean_candidate(value: str | None):
                    if not value:
                        return None
                    cleaned = re.sub(r'^[0-9]+[.、)]\s*', '', value.strip())
                    return cleaned or None

                if after_time:
                    candidate = clean_candidate(after_time)
                    if candidate:
                        company = candidate
                        if not role:
                            role_keywords = re.compile(r'(经理|主管|总监|顾问|工程师|设计师|教师|老师|专员|分析师|运营|销售|客服|助理|顾问|职务|岗位|职位|角色)')
                            role_match = role_keywords.search(after_time)
                            if role_match:
                                role = after_time[role_match.start():].strip()
                                company = after_time[:role_match.start()].strip()
                if not company and company_match:
                    company = clean_candidate(company_match.group(1))
                    trailing = line[company_match.end():time_match.start()].strip()
                    trailing = clean_candidate(trailing)
                    if trailing and not any(k in trailing for k in ['工作经验', '教育', '薪资', '城市', '期望', '优势']):
                        role = trailing
                if not company and last_company:
                    company = clean_candidate(last_company)
                if not company and before_time:
                    candidate = clean_candidate(before_time)
                    if candidate:
                        parts = candidate.split()
                        if len(parts) >= 2:
                            company = parts[0]
                            role = ' '.join(parts[1:])
                        else:
                            company = candidate

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
                            current_exp['position'] = ' '.join(line.split())

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
                company = company.strip()
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
            if 2 <= len(cleaned.replace(' ', '')) <= 12:
                return cleaned

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
            match = re.search(r'姓名\s*[:：]\s*([\u4e00-\u9fa5·•]{2,8})', line)
            if match:
                return match.group(1)
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
            return '女'
        if '男' in text:
            return '男'
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
            end_year = exp.get('end_year')
            start_year = exp.get('start_year')
            # 最近结束或正在进行的排前
            if end_year is None and start_year is None:
                return (-1, -1)
            if end_year is None:
                return (self.current_year, start_year or 0)
            return (end_year, start_year or 0)

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
        return cleaned[:2]

    def extract_earliest_work_year(self, text: str, work_experiences) -> int | None:
        """从工作经历或文本中推断最早工作年份"""
        years = []
        for exp in work_experiences:
            if exp.get('start_year'):
                years.append(exp['start_year'])

        if years:
            return min(years)

        fallback_years = []
        for line in text.split('\n'):
            if not any(keyword in line for keyword in ['工作', '经历', '任职', '项目', '公司']):
                continue
            if any(keyword in line for keyword in ['出生', '生日', '年龄']):
                continue
            for year_str in re.findall(r'(?:19|20)\d{2}', line):
                year = int(year_str)
                if 1980 <= year <= self.current_year:
                    fallback_years.append(year)

        return min(fallback_years) if fallback_years else None

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
            highest_level = 0
            for level, score in self.education_levels.items():
                if level in edu_value and score > highest_level:
                    highest_level = score
                    education_info['highest_education'] = level
            if not education_info['highest_education']:
                education_info['highest_education'] = edu_value.strip()

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

        # Fallback：从教育经历段落提取
        if not all([education_info['highest_education'], education_info['school'], education_info['major']]):
            edu_section_pattern = r'(教育经历|教育背景|学历)[：:：]?\s*(.*?)(?=(工作经历|工作经验|项目经历|自我评价|$))'
            edu_match = re.search(edu_section_pattern, text, re.DOTALL | re.IGNORECASE)

            if edu_match:
                edu_text = edu_match.group(2)

                if not education_info['highest_education']:
                    highest_level = 0
                    for level, value in self.education_levels.items():
                        if level in edu_text and value > highest_level:
                            highest_level = value
                            education_info['highest_education'] = level

                if not education_info['school']:
                    school_pattern = r'(?:[\u4e00-\u9fa5]{2,20}(?:大学|学院|学校|专科学校|职业技术学院))'
                    school_match = re.search(school_pattern, edu_text)
                    if school_match:
                        education_info['school'] = school_match.group(0)

                if not education_info['major']:
                    major_pattern = r'(?:专业|方向)[：:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,30})'
                    major_match = re.search(major_pattern, edu_text)
                    if major_match:
                        education_info['major'] = major_match.group(1).strip()
                    else:
                        line_pattern = re.compile(r'([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,40})(?:专业|方向)')
                        for line in edu_text.split('\n'):
                            line = line.strip()
                            if not line:
                                continue
                            candidate = None
                            if '专业' in line or '方向' in line:
                                candidate = re.sub(r'.*(?:专业|方向)[：:：]?\s*', '', line)
                            else:
                                match_line = line_pattern.search(line)
                                if match_line:
                                    candidate = match_line.group(1)
                            if candidate:
                                candidate = candidate.strip()
                                if 2 <= len(candidate) <= 30:
                                    education_info['major'] = candidate
                                    break

                if education_info['school'] and not education_info['major']:
                    tokens_pattern = re.compile(r'[\s]+')
                    level_terms = set(self.education_levels.keys()) | {'本科', '硕士', '博士', '研究生', '大专', '专科'}
                    for line in edu_text.split('\n'):
                        if education_info['school'] not in line:
                            continue
                        tokens = [tok for tok in tokens_pattern.split(line) if tok]
                        filtered = []
                        for tok in tokens:
                            if tok == education_info['school']:
                                continue
                            if re.match(r'(?:19|20)\d{2}(?:[.\-/]\d{1,2})?', tok):
                                continue
                            if any(ch in tok for ch in '年月日-至') and re.search(r'\d', tok):
                                continue
                            if tok in level_terms:
                                continue
                            filtered.append(tok)
                        if filtered:
                            candidate = filtered[0].strip()
                            if candidate and candidate not in level_terms:
                                education_info['major'] = candidate
                                break

        if not education_info['school']:
            school_pattern = r'([\u4e00-\u9fa5]{2,20})(?:大学|学院|学校|中学|中专|高中)'
            school_match = re.search(school_pattern, text)
            if school_match:
                education_info['school'] = school_match.group(0)

        if not education_info['highest_education'] and education_info['school']:
            for level in ['博士', '硕士', '本科', '学士', '大专', '专科', '高中', '中专', '职高']:
                if level in education_info['school'] or level in text:
                    education_info['highest_education'] = level
                    break

        if not education_info['highest_education']:
            level_match = re.search(r'(博士|硕士|研究生|本科|学士|大专|专科|高中|中专|职高)', text)
            if level_match:
                education_info['highest_education'] = level_match.group(1)

        if not education_info['major']:
            major_global_pattern = r'(?:专业|方向)[：:：]?\s*([\u4e00-\u9fa5A-Za-z0-9（）()&·\s]{2,30})'
            match_global = re.search(major_global_pattern, text)
            if match_global:
                candidate = match_global.group(1).strip()
                if candidate:
                    education_info['major'] = candidate

        return education_info

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
        work_experience_years = (
            self.current_year - earliest_work_year if earliest_work_year else None
        )

        education = self.extract_education(cleaned_text, kv_pairs)

        return {
            'name': name,
            'gender': gender,
            'birth_year': birth_year,
            'age': age,
            'phone': phone,
            'email': email,
            'earliest_work_year': earliest_work_year,
            'work_experience_years': work_experience_years,
            'work_experience': work_experiences,
            'highest_education': education['highest_education'],
            'school': education['school'],
            'major': education['major'],
            'raw_text': cleaned_text
        }
