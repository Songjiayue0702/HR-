"""
R2存储适配器（Railway版本 - 使用S3兼容API）
用于在Railway环境中通过S3兼容API连接Cloudflare R2
"""
import os
import boto3
from botocore.client import Config
from typing import Optional
from datetime import datetime
from io import BytesIO


class R2S3Storage:
    """R2存储适配器（使用S3兼容API）"""
    
    def __init__(self, bucket_name: str):
        """
        初始化R2存储适配器
        
        Args:
            bucket_name: R2存储桶名称
        """
        self.bucket_name = bucket_name
        
        # 从环境变量获取R2配置
        account_id = os.environ.get('CF_R2_ACCOUNT_ID')
        access_key_id = os.environ.get('CF_R2_ACCESS_KEY_ID')
        secret_access_key = os.environ.get('CF_R2_SECRET_ACCESS_KEY')
        
        if not all([account_id, access_key_id, secret_access_key]):
            raise ValueError("R2环境变量未完整设置: 需要 CF_R2_ACCOUNT_ID, CF_R2_ACCESS_KEY_ID, CF_R2_SECRET_ACCESS_KEY")
        
        # R2的S3兼容端点
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        
        # 创建S3客户端（R2兼容）
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version='s3v4')
        )
    
    def upload_file(self, file_data: bytes, key: str, 
                   content_type: Optional[str] = None) -> bool:
        """
        上传文件到R2
        
        Args:
            file_data: 文件数据（字节）
            key: 对象键（文件路径）
            content_type: 内容类型（MIME类型）
            
        Returns:
            是否成功
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type or 'application/octet-stream'
            )
            return True
        except Exception as e:
            print(f"R2上传失败: {e}, Key: {key}")
            return False
    
    def download_file(self, key: str) -> Optional[bytes]:
        """
        从R2下载文件
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            文件数据（字节），如果不存在则返回None
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"R2下载失败: {e}, Key: {key}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        删除文件
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            是否成功
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            print(f"R2删除失败: {e}, Key: {key}")
            return False
    
    def file_exists(self, key: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            是否存在
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except self.s3_client.exceptions.ClientError:
            return False
        except Exception as e:
            print(f"R2检查文件存在失败: {e}, Key: {key}")
            return False
    
    def generate_file_key(self, filename: str, folder: str = "uploads") -> str:
        """
        生成文件键（路径）
        
        Args:
            filename: 文件名
            folder: 文件夹（uploads或exports）
            
        Returns:
            文件键
        """
        # 生成时间戳文件名，避免冲突
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        # 移除文件名中的特殊字符，只保留安全字符
        safe_name = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
        return f"{folder}/{timestamp}_{safe_name}"


class R2StorageAdapter:
    """R2存储适配器，统一处理上传和导出存储桶"""
    
    def __init__(self):
        """初始化，从环境变量读取桶名"""
        uploads_bucket = os.environ.get('CF_R2_BUCKET_NAME', 'resume-uploads')
        exports_bucket = os.environ.get('CF_R2_EXPORTS_BUCKET_NAME', 'resume-exports')
        
        self.uploads = R2S3Storage(uploads_bucket)
        self.exports = R2S3Storage(exports_bucket)
    
    def save_upload(self, file_data: bytes, filename: str, 
                   content_type: Optional[str] = None) -> str:
        """
        保存上传的文件
        
        Args:
            file_data: 文件数据
            filename: 原始文件名
            content_type: 内容类型
            
        Returns:
            文件键（用于存储在数据库中）
        """
        key = self.uploads.generate_file_key(filename, "uploads")
        self.uploads.upload_file(file_data, key, content_type)
        return key
    
    def get_upload(self, key: str) -> Optional[bytes]:
        """
        获取上传的文件
        
        Args:
            key: 文件键
            
        Returns:
            文件数据
        """
        return self.uploads.download_file(key)
    
    def delete_upload(self, key: str) -> bool:
        """
        删除上传的文件
        
        Args:
            key: 文件键
            
        Returns:
            是否成功
        """
        return self.uploads.delete_file(key)
    
    def save_export(self, file_data: bytes, filename: str,
                   content_type: Optional[str] = None) -> str:
        """
        保存导出的文件
        
        Args:
            file_data: 文件数据
            filename: 文件名
            content_type: 内容类型
            
        Returns:
            文件键
        """
        key = self.exports.generate_file_key(filename, "exports")
        self.exports.upload_file(file_data, key, content_type)
        return key
    
    def get_export(self, key: str) -> Optional[bytes]:
        """
        获取导出的文件
        
        Args:
            key: 文件键
            
        Returns:
            文件数据
        """
        return self.exports.download_file(key)
    
    def delete_export(self, key: str) -> bool:
        """
        删除导出的文件
        
        Args:
            key: 文件键
            
        Returns:
            是否成功
        """
        return self.exports.delete_file(key)

