"""
密码哈希工具 - 纯Python实现
替代werkzeug.security，兼容Workers环境
"""
import hashlib
import secrets
import base64


def generate_password_hash(password: str, method: str = 'pbkdf2:sha256') -> str:
    """
    生成密码哈希
    
    Args:
        password: 原始密码
        method: 哈希方法（默认pbkdf2:sha256，兼容werkzeug）
        
    Returns:
        密码哈希字符串（格式：pbkdf2:sha256:iterations$salt$hash）
    """
    if method == 'pbkdf2:sha256':
        # 使用PBKDF2-SHA256，兼容werkzeug格式
        iterations = 260000  # 默认迭代次数（werkzeug默认值）
        salt = secrets.token_hex(16)  # 32字符的随机salt
        
        # 使用PBKDF2生成哈希
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
        hash_hex = hash_bytes.hex()
        
        # 返回werkzeug兼容格式：pbkdf2:sha256:iterations$salt$hash
        return f'pbkdf2:sha256:{iterations}${salt}${hash_hex}'
    else:
        raise ValueError(f"不支持的哈希方法: {method}")


def check_password_hash(password_hash: str, password: str) -> bool:
    """
    验证密码
    
    Args:
        password_hash: 存储的密码哈希
        password: 待验证的密码
        
    Returns:
        是否匹配
    """
    if not password_hash or not password:
        return False
    
    try:
        # 解析哈希格式：pbkdf2:sha256:iterations$salt$hash
        if password_hash.startswith('pbkdf2:sha256:'):
            parts = password_hash.replace('pbkdf2:sha256:', '').split('$')
            if len(parts) == 3:
                iterations = int(parts[0])
                salt = parts[1]
                stored_hash = parts[2]
                
                # 使用相同的参数重新计算哈希
                hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
                computed_hash = hash_bytes.hex()
                
                # 使用secrets.compare_digest防止时序攻击
                return secrets.compare_digest(computed_hash, stored_hash)
        
        # 兼容旧格式（如果存在）
        # 这里可以添加其他格式的支持
        return False
    except Exception:
        return False

