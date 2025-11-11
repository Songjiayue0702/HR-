"""
外部API集成
企查查、学校名录、专业名录API
"""
import requests
from config import Config

class APIIntegration:
    """API集成类"""
    
    @staticmethod
    def verify_company(company_name):
        """
        通过企查查API验证公司名称
        返回: (标准化名称, 状态, 置信度, 公司代码, 备选列表)
        """
        if not Config.QICHACHA_API_KEY or not company_name:
            return None, '未校验', 0.0, None, []
        
        try:
            # 这里需要根据实际API文档调整
            # 示例请求
            params = {
                'key': Config.QICHACHA_API_KEY,
                'keyword': company_name
            }
            
            response = requests.get(Config.QICHACHA_API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # 根据实际API响应格式解析
                # 示例结构
                if data.get('Status') == '200' and data.get('Result'):
                    result = data['Result']
                    if isinstance(result, list) and len(result) > 0:
                        if len(result) == 1:
                            # 完全匹配
                            company = result[0]
                            return (
                                company.get('Name'),
                                '完全匹配',
                                0.95,
                                company.get('CreditCode'),
                                []
                            )
                        else:
                            # 多项选择
                            companies = [item.get('Name') for item in result[:5]]
                            return (
                                result[0].get('Name'),
                                '多项选择',
                                0.8,
                                result[0].get('CreditCode'),
                                companies
                            )
                    else:
                        return None, '匹配失败', 0.0, None, []
                else:
                    return None, '匹配失败', 0.0, None, []
            else:
                return None, '未校验', 0.0, None, []
        
        except Exception as e:
            print(f"企查查API调用失败: {e}")
            return None, '未校验', 0.0, None, []
    
    @staticmethod
    def verify_school(school_name):
        """
        通过学校名录API验证学校名称
        返回: (标准化名称, 状态, 置信度, 学校代码, 备选列表)
        """
        if not Config.SCHOOL_API_URL or not school_name:
            return None, '未校验', 0.0, None, []
        
        try:
            # 这里需要根据实际API文档调整
            params = {'name': school_name}
            response = requests.get(Config.SCHOOL_API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # 解析响应
                if data.get('success') and data.get('data'):
                    schools = data['data']
                    if len(schools) == 1:
                        school = schools[0]
                        return (
                            school.get('name'),
                            '完全匹配',
                            0.95,
                            school.get('code'),
                            []
                        )
                    elif len(schools) > 1:
                        school_names = [s.get('name') for s in schools[:5]]
                        return (
                            schools[0].get('name'),
                            '多项选择',
                            0.8,
                            schools[0].get('code'),
                            school_names
                        )
                    else:
                        return None, '匹配失败', 0.0, None, []
                else:
                    return None, '匹配失败', 0.0, None, []
            else:
                return None, '未校验', 0.0, None, []
        
        except Exception as e:
            print(f"学校名录API调用失败: {e}")
            return None, '未校验', 0.0, None, []
    
    @staticmethod
    def verify_major(major_name, school_code=None):
        """
        通过专业名录API验证专业名称
        返回: (标准化名称, 状态, 置信度, 专业代码, 备选列表)
        """
        if not Config.MAJOR_API_URL or not major_name:
            return None, '未校验', 0.0, None, []
        
        try:
            params = {'name': major_name}
            if school_code:
                params['school_code'] = school_code
            
            response = requests.get(Config.MAJOR_API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    majors = data['data']
                    if len(majors) == 1:
                        major = majors[0]
                        return (
                            major.get('name'),
                            '完全匹配',
                            0.95,
                            major.get('code'),
                            []
                        )
                    elif len(majors) > 1:
                        major_names = [m.get('name') for m in majors[:5]]
                        return (
                            majors[0].get('name'),
                            '多项选择',
                            0.8,
                            majors[0].get('code'),
                            major_names
                        )
                    else:
                        return None, '匹配失败', 0.0, None, []
                else:
                    return None, '匹配失败', 0.0, None, []
            else:
                return None, '未校验', 0.0, None, []
        
        except Exception as e:
            print(f"专业名录API调用失败: {e}")
            return None, '未校验', 0.0, None, []

