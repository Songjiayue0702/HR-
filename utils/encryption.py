"""
加密工具 - 用于加密存储敏感信息（如API密钥）
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

def get_encryption_key():
    """
    获取加密密钥
    从环境变量 ENCRYPTION_KEY 读取，如果没有则生成一个（仅用于开发）
    """
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    
    if encryption_key:
        # 如果环境变量是32字节的base64编码密钥，直接使用
        try:
            return base64.urlsafe_b64decode(encryption_key.encode())
        except:
            # 如果不是base64格式，使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'cloudflare_workers_ai_config',  # 固定盐值
                iterations=100000,
                backend=default_backend()
            )
            return kdf.derive(encryption_key.encode())
    else:
        # 开发环境：使用默认密钥（警告：生产环境必须设置ENCRYPTION_KEY）
        print("警告: 未设置 ENCRYPTION_KEY 环境变量，使用默认密钥（不安全）")
        default_key = b'dev-encryption-key-32-bytes-long!!'  # 32字节
        return default_key

def encrypt_value(value: str) -> str:
    """
    加密字符串值
    
    Args:
        value: 要加密的字符串
        
    Returns:
        加密后的base64编码字符串
    """
    if not value:
        return ''
    
    try:
        key = get_encryption_key()
        # 确保密钥是32字节
        if len(key) != 32:
            key = key[:32] if len(key) > 32 else key.ljust(32, b'0')
        
        # 使用Fernet对称加密
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted = f.encrypt(value.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"加密失败: {e}")
        # 如果加密失败，返回原值（不推荐，但保证功能可用）
        return value

def decrypt_value(encrypted_value: str) -> str:
    """
    解密字符串值
    
    Args:
        encrypted_value: 加密后的base64编码字符串
        
    Returns:
        解密后的原始字符串
    """
    if not encrypted_value:
        return ''
    
    try:
        key = get_encryption_key()
        # 确保密钥是32字节
        if len(key) != 32:
            key = key[:32] if len(key) > 32 else key.ljust(32, b'0')
        
        # 使用Fernet对称解密
        f = Fernet(base64.urlsafe_b64encode(key))
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_value.encode('utf-8')))
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"解密失败: {e}")
        # 如果解密失败，可能是未加密的值，直接返回
        return encrypted_value

