#!/usr/bin/env python3
"""
WordPress XML-RPC客户端
负责与WordPress进行交互，发布文章
"""
import logging
import ssl
import urllib3
from typing import List, Dict, Any, Optional

# Python 3.9+ 兼容性修复
import collections.abc
import collections
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable

from wordpress_xmlrpc import Client, WordPressPost, WordPressTerm
from wordpress_xmlrpc.methods import posts, taxonomies
from wordpress_xmlrpc.exceptions import InvalidCredentialsError, ServerConnectionError

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建一个不验证SSL的上下文
ssl._create_default_https_context = ssl._create_unverified_context


class WordPressError(Exception):
    """WordPress相关错误"""
    pass


class WordPressClient:
    """WordPress XML-RPC客户端"""
    
    def __init__(self, url: str, username: str, password: str):
        """初始化客户端
        
        Args:
            url: WordPress XML-RPC端点URL
            username: 用户名
            password: 密码
        """
        self.url = url
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._category_cache = {}  # 分类缓存
        self._tag_cache = {}  # 标签缓存
        
    def connect(self) -> None:
        """连接到WordPress"""
        try:
            self.client = Client(self.url, self.username, self.password)
            # 测试连接
            self.client.call(posts.GetPosts({'number': 1}))
            self.logger.info("成功连接到WordPress")
        except InvalidCredentialsError:
            raise WordPressError("WordPress认证失败，请检查用户名和密码")
        except ServerConnectionError as e:
            if "XML-RPC" in str(e):
                raise WordPressError("无法连接到WordPress XML-RPC，请确保已启用XML-RPC功能")
            else:
                raise WordPressError(f"无法连接到WordPress: {e}")
        except Exception as e:
            raise WordPressError(f"连接WordPress时发生错误: {e}")
            
    def validate_connection(self) -> bool:
        """验证连接是否有效
        
        Returns:
            是否连接成功
        """
        try:
            if not self.client:
                self.connect()
            self.client.call(posts.GetPosts({'number': 1}))
            return True
        except Exception as e:
            self.logger.error(f"验证连接失败: {e}")
            return False
            
    def create_post(self, title: str, content: str, 
                   categories: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   status: str = 'publish') -> str:
        """创建文章
        
        Args:
            title: 文章标题
            content: 文章内容
            categories: 分类列表
            tags: 标签列表
            status: 发布状态 (publish/draft)
            
        Returns:
            文章ID
        """
        if not self.client:
            self.connect()
            
        post = WordPressPost()
        post.title = title
        post.content = content
        post.post_status = status
        post.comment_status = 'open'
        
        # 处理分类 - 暂时简化，只使用默认分类
        if categories:
            # 暂时注释掉，避免API问题
            pass
            # category_terms = []
            # for cat_name in categories:
            #     cat_id = self._get_or_create_category(cat_name)
            #     if cat_id:
            #         term = WordPressTerm()
            #         term.taxonomy = 'category'
            #         term.term_id = str(cat_id)
            #         category_terms.append(term)
            # if category_terms:
            #     post.terms = category_terms
        
        # 处理标签 - 使用更简单的方式避免序列化问题
        if tags:
            self.logger.debug(f"=== WordPress标签处理调试 ===")
            self.logger.debug(f"待处理标签: {tags}")
            
            # 确保标签存在，但不在创建文章时设置
            for tag_name in tags:
                try:
                    self._get_or_create_tag(tag_name)
                    self.logger.debug(f"标签确认存在: {tag_name}")
                except Exception as e:
                    self.logger.error(f"处理标签 '{tag_name}' 时出错: {e}")
            
            # 使用简单的字符串列表而不是WordPressTerm对象
            post.terms_names = {
                'post_tag': tags
            }
            self.logger.debug(f"使用terms_names设置标签: {tags}")
        
        try:
            post_id = self.client.call(posts.NewPost(post))
            self.logger.info(f"成功创建文章: {title} (ID: {post_id})")
            return str(post_id)
        except Exception as e:
            raise WordPressError(f"创建文章失败: {e}")
            
    def post_exists(self, title: str) -> bool:
        """检查文章是否已存在（通过标题）
        
        Args:
            title: 文章标题
            
        Returns:
            是否存在
        """
        if not self.client:
            self.connect()
            
        try:
            # 搜索相同标题的文章
            existing_posts = self.client.call(posts.GetPosts({
                'post_status': ['publish', 'draft', 'private'],
                'number': 100,  # 获取最近100篇
                'orderby': 'date',
                'order': 'DESC'
            }))
            
            for post in existing_posts:
                if post.title == title:
                    self.logger.info(f"发现重复文章: {title}")
                    return True
                    
            return False
        except Exception as e:
            self.logger.error(f"检查文章是否存在时出错: {e}")
            # 出错时保守处理，假设不存在
            return False
            
    def _get_or_create_category(self, name: str) -> Optional[int]:
        """获取或创建分类
        
        Args:
            name: 分类名称
            
        Returns:
            分类ID
        """
        # 检查缓存
        if name in self._category_cache:
            return self._category_cache[name]
            
        try:
            # 获取所有分类
            categories = self.client.call(taxonomies.GetTerms('category'))
            
            # 查找是否已存在
            for cat in categories:
                if cat.name == name:
                    self._category_cache[name] = int(cat.id)
                    return int(cat.id)
                    
            # 创建新分类
            new_cat = WordPressTerm()
            new_cat.taxonomy = 'category'
            new_cat.name = name
            cat_id = self.client.call(taxonomies.NewTerm(new_cat))
            self._category_cache[name] = cat_id
            self.logger.info(f"创建新分类: {name} (ID: {cat_id})")
            return cat_id
            
        except Exception as e:
            self.logger.error(f"创建分类失败: {name}, 错误: {e}")
            return None
            
    def _get_or_create_tag(self, name: str) -> Optional[int]:
        """获取或创建标签
        
        Args:
            name: 标签名称
            
        Returns:
            标签ID
        """
        # 检查缓存
        if name in self._tag_cache:
            return self._tag_cache[name]
            
        try:
            # 获取所有标签
            tags = self.client.call(taxonomies.GetTerms('post_tag'))
            
            # 查找是否已存在
            for tag in tags:
                if tag.name == name:
                    self._tag_cache[name] = int(tag.id)
                    return int(tag.id)
                    
            # 创建新标签
            new_tag = WordPressTerm()
            new_tag.taxonomy = 'post_tag'
            new_tag.name = name
            tag_id = self.client.call(taxonomies.NewTerm(new_tag))
            self._tag_cache[name] = tag_id
            self.logger.info(f"创建新标签: {name} (ID: {tag_id})")
            return tag_id
            
        except Exception as e:
            self.logger.error(f"创建标签失败: {name}, 错误: {e}")
            return None