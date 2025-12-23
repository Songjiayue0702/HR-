"""
Cloudflare R2存储适配器
将本地文件系统操作转换为R2对象存储操作
"""
import io
from typing import Optional, BinaryIO
from datetime import datetime


class R2Storage:
    """R2存储适配器，提供类似本地文件系统的接口"""
    
    def __init__(self, bucket):
        """
        初始化存储适配器
        
        Args:
            bucket: R2存储桶实例（从env.UPLOADS_BUCKET或env.EXPORTS_BUCKET获取）
        """
        self.bucket = bucket
    
    async def upload_file(self, file_data: bytes, key: str, 
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
            # R2的put方法可能因Python运行时版本而异
            # 这里使用标准的R2 API
            await self.bucket.put(
                key, 
                file_data,
                http_metadata={
                    'content-type': content_type or 'application/octet-stream'
                }
            )
            return True
        except Exception as e:
            print(f"R2上传失败: {e}, Key: {key}")
            return False
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """
        从R2下载文件
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            文件数据（字节），如果不存在则返回None
        """
        try:
            obj = await self.bucket.get(key)
            if obj is None:
                return None
            # R2对象的arrayBuffer()方法返回ArrayBuffer，需要转换为bytes
            array_buffer = await obj.arrayBuffer()
            return bytes(array_buffer)
        except Exception as e:
            print(f"R2下载失败: {e}, Key: {key}")
            return None
    
    async def delete_file(self, key: str) -> bool:
        """
        从R2删除文件
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            是否成功
        """
        try:
            await self.bucket.delete(key)
            return True
        except Exception as e:
            print(f"R2删除失败: {e}")
            return False
    
    async def file_exists(self, key: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            key: 对象键（文件路径）
            
        Returns:
            是否存在
        """
        try:
            obj = await self.bucket.head(key)
            return obj is not None
        except:
            return False
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        获取文件的临时访问URL
        
        Args:
            key: 对象键（文件路径）
            expires_in: 过期时间（秒），默认1小时
            
        Returns:
            临时URL，如果失败则返回None
        """
        try:
            # R2可以通过公共URL或签名URL访问
            # 这里返回一个可以通过Worker访问的URL
            # 实际实现可能需要根据R2配置调整
            return f"/api/files/{key}"
        except Exception as e:
            print(f"获取文件URL失败: {e}")
            return None
    
    async def list_files(self, prefix: str = "", limit: int = 1000) -> list:
        """
        列出文件
        
        Args:
            prefix: 前缀过滤
            limit: 最大数量
            
        Returns:
            文件键列表
        """
        try:
            objects = await self.bucket.list({
                'prefix': prefix,
                'limit': limit
            })
            return [obj.key for obj in objects.objects]
        except Exception as e:
            print(f"列出文件失败: {e}")
            return []
    
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


class FileStorageAdapter:
    """文件存储适配器，统一处理上传和导出存储桶"""
    
    def __init__(self, uploads_bucket, exports_bucket):
        """
        初始化文件存储适配器
        
        Args:
            uploads_bucket: 上传存储桶（env.UPLOADS_BUCKET）
            exports_bucket: 导出存储桶（env.EXPORTS_BUCKET）
        """
        self.uploads = R2Storage(uploads_bucket)
        self.exports = R2Storage(exports_bucket)
    
    async def save_upload(self, file_data: bytes, filename: str, 
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
        await self.uploads.upload_file(file_data, key, content_type)
        return key
    
    async def get_upload(self, key: str) -> Optional[bytes]:
        """
        获取上传的文件
        
        Args:
            key: 文件键
            
        Returns:
            文件数据
        """
        return await self.uploads.download_file(key)
    
    async def delete_upload(self, key: str) -> bool:
        """
        删除上传的文件
        
        Args:
            key: 文件键
            
        Returns:
            是否成功
        """
        return await self.uploads.delete_file(key)
    
    async def save_export(self, file_data: bytes, filename: str,
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
        await self.exports.upload_file(file_data, key, content_type)
        return key
    
    async def get_export(self, key: str) -> Optional[bytes]:
        """
        获取导出的文件
        
        Args:
            key: 文件键
            
        Returns:
            文件数据
        """
        return await self.exports.download_file(key)
    
    async def delete_export(self, key: str) -> bool:
        """
        删除导出的文件
        
        Args:
            key: 文件键
            
        Returns:
            是否成功
        """
        return await self.exports.delete_file(key)

