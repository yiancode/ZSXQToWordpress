#!/usr/bin/env python3
"""
基础接口定义
定义项目中各组件的抽象接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseClient(ABC):
    """客户端基类"""
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """验证连接是否有效
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭连接并清理资源"""
        pass


class ContentClient(BaseClient):
    """内容获取客户端接口"""
    
    @abstractmethod
    def get_content(self, content_id: str) -> Dict[str, Any]:
        """获取单个内容
        
        Args:
            content_id: 内容ID
            
        Returns:
            内容数据
        """
        pass
    
    @abstractmethod
    def get_all_content(self, 
                       batch_size: int = 20,
                       start_time: Optional[Any] = None,
                       max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有内容
        
        Args:
            batch_size: 每批次大小
            start_time: 开始时间
            max_items: 最大数量
            
        Returns:
            内容列表
        """
        pass


class PublishClient(BaseClient):
    """内容发布客户端接口"""
    
    @abstractmethod
    def create_post(self, 
                   title: str,
                   content: str,
                   categories: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   status: str = 'publish') -> str:
        """创建文章
        
        Args:
            title: 标题
            content: 内容
            categories: 分类列表
            tags: 标签列表
            status: 发布状态
            
        Returns:
            文章ID
        """
        pass
    
    @abstractmethod
    def post_exists(self, title: str) -> bool:
        """检查文章是否存在
        
        Args:
            title: 文章标题
            
        Returns:
            是否存在
        """
        pass


class StorageClient(BaseClient):
    """存储客户端接口"""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_key: Optional[str] = None) -> Optional[str]:
        """上传文件
        
        Args:
            local_path: 本地文件路径
            remote_key: 远程存储键名
            
        Returns:
            访问URL，失败返回None
        """
        pass
    
    @abstractmethod
    def download_file(self, url: str) -> Optional[str]:
        """下载文件
        
        Args:
            url: 文件URL
            
        Returns:
            本地文件路径，失败返回None
        """
        pass


class ContentProcessor(ABC):
    """内容处理器接口"""
    
    @abstractmethod
    def process_content(self, raw_content: Dict[str, Any]) -> Dict[str, Any]:
        """处理原始内容
        
        Args:
            raw_content: 原始内容数据
            
        Returns:
            处理后的内容数据
        """
        pass


class StateManager(ABC):
    """状态管理器接口"""
    
    @abstractmethod
    def is_synced(self, item_id: str) -> bool:
        """检查是否已同步
        
        Args:
            item_id: 项目ID
            
        Returns:
            是否已同步
        """
        pass
    
    @abstractmethod
    def mark_synced(self, item_id: str, **kwargs) -> None:
        """标记为已同步
        
        Args:
            item_id: 项目ID
            **kwargs: 其他相关信息
        """
        pass
    
    @abstractmethod
    def save(self) -> None:
        """保存状态"""
        pass
    
    @abstractmethod
    def load(self) -> None:
        """加载状态"""
        pass