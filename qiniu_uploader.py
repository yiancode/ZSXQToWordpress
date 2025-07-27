#!/usr/bin/env python3
"""
七牛云图片上传模块
负责处理图片的下载和上传到七牛云
"""
import os
import tempfile
import requests
import logging
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
from qiniu import Auth, put_file, etag
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class QiniuError(Exception):
    """七牛云相关错误"""
    pass


class QiniuUploader:
    """七牛云上传器"""
    
    def __init__(self, access_key: str, secret_key: str, bucket: str, domain: str):
        """初始化上传器
        
        Args:
            access_key: AccessKey
            secret_key: SecretKey
            bucket: 存储空间名称
            domain: 访问域名
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.domain = domain.rstrip('/')  # 去除末尾的斜杠
        self.logger = logging.getLogger(__name__)
        
        # 初始化七牛云认证
        self.auth = Auth(access_key, secret_key)
        
        # 线程锁用于批量处理
        self._upload_lock = threading.Lock()
        
    def validate_config(self) -> bool:
        """验证配置是否有效
        
        Returns:
            是否配置有效
        """
        try:
            # 生成一个测试token
            token = self.auth.upload_token(self.bucket)
            return bool(token)
        except Exception as e:
            self.logger.error(f"七牛云配置验证失败: {e}")
            return False
            
    def download_image(self, image_url: str) -> Optional[str]:
        """下载图片到临时文件
        
        Args:
            image_url: 图片URL
            
        Returns:
            临时文件路径，失败返回None
        """
        try:
            self.logger.info(f"开始下载图片: {image_url}")
            
            # 发送请求下载图片
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 获取文件扩展名
            content_type = response.headers.get('content-type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                # 从URL尝试获取扩展名
                parsed_url = urlparse(image_url)
                path = parsed_url.path
                if '.' in path:
                    ext = os.path.splitext(path)[1]
                else:
                    ext = '.jpg'  # 默认jpg
                    
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_path = temp_file.name
            
            # 写入图片数据
            with temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        
            self.logger.info(f"图片下载成功: {temp_path}")
            return temp_path
            
        except requests.RequestException as e:
            self.logger.error(f"下载图片失败: {image_url}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"处理图片时发生错误: {e}")
            return None
            
    def upload_image(self, local_path: str, key: Optional[str] = None) -> Optional[str]:
        """上传图片到七牛云
        
        Args:
            local_path: 本地图片路径
            key: 七牛云存储的文件名，不指定则自动生成
            
        Returns:
            图片访问URL，失败返回None
        """
        try:
            # 如果没有指定key，使用文件的etag作为文件名
            if not key:
                file_etag = etag(local_path)
                ext = os.path.splitext(local_path)[1]
                key = f"{file_etag}{ext}"
                
            self.logger.info(f"开始上传图片到七牛云: {key}")
            
            # 生成上传token
            token = self.auth.upload_token(self.bucket, key, 3600)
            
            # 上传文件
            ret, info = put_file(token, key, local_path)
            
            if ret and ret.get('key') == key:
                # 构建访问URL - 始终使用HTTPS
                if self.domain.startswith('http://') or self.domain.startswith('https://'):
                    url = f"{self.domain}/{key}"
                    # 如果是http，转换为https
                    if url.startswith('http://'):
                        url = url.replace('http://', 'https://', 1)
                else:
                    url = f"https://{self.domain}/{key}"
                    
                self.logger.info(f"图片上传成功: {url}")
                return url
            else:
                self.logger.error(f"图片上传失败: {info}")
                return None
                
        except Exception as e:
            self.logger.error(f"上传图片到七牛云时发生错误: {e}")
            return None
            
    def process_image(self, image_url: str) -> str:
        """处理图片：下载并上传到七牛云
        
        Args:
            image_url: 原始图片URL
            
        Returns:
            七牛云图片URL，失败返回原始URL
        """
        # 下载图片
        temp_path = self.download_image(image_url)
        if not temp_path:
            self.logger.warning(f"图片下载失败，使用原始链接: {image_url}")
            return image_url
            
        try:
            # 上传到七牛云
            qiniu_url = self.upload_image(temp_path)
            if qiniu_url:
                return qiniu_url
            else:
                self.logger.warning(f"图片上传失败，使用原始链接: {image_url}")
                return image_url
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except Exception as e:
                self.logger.warning(f"清理临时文件失败: {e}")
                
    def process_images_in_content(self, content: str, images: list) -> str:
        """处理内容中的所有图片
        
        Args:
            content: 包含图片的内容
            images: 图片URL列表
            
        Returns:
            替换图片链接后的内容
        """
        if not images:
            return content
            
        processed_content = content
        for image_url in images:
            try:
                # 处理图片
                new_url = self.process_image(image_url)
                if new_url != image_url:
                    # 替换内容中的图片链接
                    processed_content = processed_content.replace(image_url, new_url)
            except Exception as e:
                self.logger.error(f"处理图片时发生错误: {image_url}, 错误: {e}")
                
        return processed_content
    
    def process_images_batch(self, image_urls: List[str], max_workers: int = 3) -> Dict[str, str]:
        """批量处理图片（并发版本）
        
        Args:
            image_urls: 图片URL列表
            max_workers: 最大并发工作线程数
            
        Returns:
            原始URL到新URL的映射字典
        """
        if not image_urls:
            return {}
            
        self.logger.info(f"开始批量处理 {len(image_urls)} 张图片，最大并发数: {max_workers}")
        result_map = {}
        
        def process_single(url: str) -> Tuple[str, str]:
            """处理单张图片"""
            try:
                new_url = self.process_image(url)
                return url, new_url
            except Exception as e:
                self.logger.error(f"批量处理图片失败: {url}, 错误: {e}")
                return url, url  # 失败时返回原始URL
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {executor.submit(process_single, url): url for url in image_urls}
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    original_url, new_url = future.result()
                    result_map[original_url] = new_url
                    self.logger.debug(f"批量处理完成: {original_url} -> {new_url}")
                except Exception as e:
                    url = futures[future]
                    self.logger.error(f"处理图片时发生异常: {url}, 错误: {e}")
                    result_map[url] = url
                    
        self.logger.info(f"批量图片处理完成，成功处理 {len([v for k,v in result_map.items() if k != v])} 张")
        return result_map
    
    def download_images_batch(self, image_urls: List[str], max_workers: int = 3) -> Dict[str, Optional[str]]:
        """批量下载图片
        
        Args:
            image_urls: 图片URL列表
            max_workers: 最大并发工作线程数
            
        Returns:
            URL到本地文件路径的映射
        """
        if not image_urls:
            return {}
            
        result_map = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.download_image, url): url for url in image_urls}
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    local_path = future.result()
                    result_map[url] = local_path
                except Exception as e:
                    self.logger.error(f"批量下载图片失败: {url}, 错误: {e}")
                    result_map[url] = None
                    
        return result_map