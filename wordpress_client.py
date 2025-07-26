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
    
    def create_content_by_type(self, content_data: Dict[str, Any]) -> str:
        """根据内容类型创建WordPress内容
        
        Args:
            content_data: 内容数据，包含content_type字段
            
        Returns:
            内容ID
        """
        content_type = content_data.get('content_type', 'article')
        post_type = content_data.get('post_type', 'post')
        
        if content_type == 'moment' and post_type == 'moment':
            return self._create_moment(content_data)
        else:
            return self._create_article(content_data)
    
    def _create_article(self, article_data: Dict[str, Any]) -> str:
        """创建WordPress文章（保留原有逻辑）
        
        Args:
            article_data: 文章数据
            
        Returns:
            文章ID
        """
        return self.create_post(
            title=article_data['title'],
            content=article_data['content'],
            categories=article_data.get('categories'),
            tags=article_data.get('tags'),
            status='publish'
        )
    
    def _create_moment(self, moment_data: Dict[str, Any]) -> str:
        """创建WordPress片刻
        
        Args:
            moment_data: 片刻数据
            
        Returns:
            片刻ID
        """
        if not self.client:
            self.connect()
            
        try:
            # 尝试创建自定义文章类型的片刻
            post = WordPressPost()
            post.post_type = 'moment'
            post.title = moment_data['title']
            post.content = moment_data['content']
            post.post_status = 'publish'
            post.comment_status = 'open'
            
            # 处理标签
            tags = moment_data.get('tags', [])
            if tags:
                self.logger.debug(f"=== WordPress片刻标签处理调试 ===")
                self.logger.debug(f"待处理标签: {tags}")
                
                # 确保标签存在
                for tag_name in tags:
                    try:
                        self._get_or_create_tag(tag_name)
                        self.logger.debug(f"片刻标签确认存在: {tag_name}")
                    except Exception as e:
                        self.logger.error(f"处理片刻标签 '{tag_name}' 时出错: {e}")
                
                # 为片刻设置标签
                post.terms_names = {
                    'post_tag': tags
                }
            
            # 添加自定义字段标识这是来自知识星球的片刻
            post.custom_fields = [
                {
                    'key': 'content_source',
                    'value': 'zsxq'
                },
                {
                    'key': 'content_source_type',
                    'value': 'moment'
                },
                {
                    'key': 'zsxq_topic_id',
                    'value': moment_data.get('topic_id', '')
                }
            ]
            
            post_id = self.client.call(posts.NewPost(post))
            self.logger.info(f"成功创建片刻: {moment_data['title']} (ID: {post_id})")
            return str(post_id)
            
        except Exception as e:
            self.logger.error(f"创建片刻失败，尝试作为普通文章创建: {e}")
            # 如果自定义文章类型失败，回退到普通文章
            return self._create_article_as_moment(moment_data)
    
    def _create_article_as_moment(self, moment_data: Dict[str, Any]) -> str:
        """作为普通文章创建片刻（回退方案）
        
        Args:
            moment_data: 片刻数据
            
        Returns:
            文章ID
        """
        # 在标题前加上[片刻]标识
        title = f"[片刻] {moment_data['title']}"
        
        # 在内容中添加片刻标识
        content = f'<div class="moment-content">{moment_data["content"]}</div>'
        
        # 添加片刻相关的标签和分类
        tags = moment_data.get('tags', [])
        tags.append('片刻')  # 确保有片刻标签
        
        categories = moment_data.get('categories', ['片刻'])
        
        return self.create_post(
            title=title,
            content=content,
            categories=categories,
            tags=tags,
            status='publish'
        )
            
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