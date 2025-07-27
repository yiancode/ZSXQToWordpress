#!/usr/bin/env python3
"""
WordPress XML-RPC客户端
负责与WordPress进行交互，发布文章
"""
import logging
import ssl
import urllib3
from typing import List, Dict, Any, Optional
import warnings

# Python 3.9+ 兼容性修复
import collections.abc
import collections
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable

from wordpress_xmlrpc import Client, WordPressPost, WordPressTerm
from wordpress_xmlrpc.methods import posts, taxonomies
from wordpress_xmlrpc.exceptions import InvalidCredentialsError, ServerConnectionError
from interfaces import PublishClient


class WordPressError(Exception):
    """WordPress相关错误"""
    pass


class WordPressClient(PublishClient):
    """WordPress XML-RPC客户端"""
    
    def __init__(self, url: str, username: str, password: str, verify_ssl: bool = True):
        """初始化客户端
        
        Args:
            url: WordPress XML-RPC端点URL
            username: 用户名
            password: 密码
            verify_ssl: 是否验证SSL证书（默认True）
        """
        self.url = url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._category_cache = {}  # 分类缓存
        self._tag_cache = {}  # 标签缓存
        
        # SSL配置警告
        if not verify_ssl:
            self.logger.warning("SSL证书验证已禁用，存在安全风险！请仅在开发环境使用。")
            # 仅在需要时禁用SSL警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def connect(self) -> None:
        """连接到WordPress"""
        try:
            # 根据SSL配置创建客户端
            if not self.verify_ssl:
                # 创建不验证SSL的上下文
                import xmlrpc.client
                context = ssl._create_unverified_context()
                transport = xmlrpc.client.SafeTransport(context=context)
                self.client = Client(self.url, self.username, self.password, transport=transport)
            else:
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
    
    def close(self) -> None:
        """关闭连接并清理资源"""
        # WordPress XML-RPC客户端不需要显式关闭
        self.logger.info("WordPress客户端连接已关闭")
    
    def create_content_by_type(self, content_data: Dict[str, Any]) -> str:
        """根据内容类型创建WordPress内容
        
        Args:
            content_data: 内容数据，包含content_type字段
            
        Returns:
            内容ID
        """
        content_type = content_data.get('content_type', 'article')
        
        if content_type == 'topic':
            return self._create_topic(content_data)
        else:
            return self._create_article(content_data)
    
    def _create_article(self, article_data: Dict[str, Any]) -> str:
        """创建WordPress文章（保留原有逻辑）
        
        Args:
            article_data: 文章数据
            
        Returns:
            文章ID
        """
        # 处理空标题情况
        title = article_data['title']
        if not title or title.strip() == "":
            # 生成默认标题
            from datetime import datetime
            create_time = article_data.get('create_time', '')
            if create_time:
                try:
                    dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    title = dt.strftime('文章 %Y-%m-%d %H:%M')
                except:
                    title = "无标题文章"
            else:
                title = "无标题文章"
        
        # 获取post类型
        post_type = article_data.get('post_type', 'post')
        
        return self.create_post(
            title=title,
            content=article_data['content'],
            categories=article_data.get('categories'),
            tags=article_data.get('tags'),
            post_type=post_type,
            status='publish'
        )
    
    def _create_topic(self, content_data: Dict[str, Any]) -> str:
        """创建WordPress片刻内容
        
        Args:
            content_data: 片刻数据
            
        Returns:
            文章ID
        """
        # 获取标题 - 如果配置了不同步标题，则保持空标题
        title = content_data['title']
        sync_title_disabled = content_data.get('_sync_title_disabled', False)
        
        if not title or title.strip() == "":
            if not sync_title_disabled:
                # 只有在没有明确禁用标题同步时才生成默认标题
                from datetime import datetime
                create_time = content_data.get('create_time', '')
                if create_time:
                    try:
                        dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                        title = dt.strftime('片刻 %m-%d %H:%M')
                    except:
                        title = "无标题片刻"
                else:
                    title = "无标题片刻"
            else:
                # 标题同步被禁用，使用空字符串或最小标题
                title = " "  # WordPress需要非空标题，使用单个空格
        
        # 在内容中添加片刻标识
        content = f'<div class="moment-content">{content_data["content"]}</div>'
        
        # 获取标签和分类
        tags = content_data.get('tags', [])
        categories = content_data.get('categories', ['片刻'])
        
        # 获取post类型
        post_type = content_data.get('post_type', 'post')
        
        return self.create_post(
            title=title,
            content=content,
            categories=categories,
            tags=tags,
            post_type=post_type,
            status='publish'
        )
    
    # 移除原有的_create_article_as_moment方法，因为_create_topic已经是通用实现
            
    def create_post(self, title: str, content: str,
                   categories: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   post_type: str = 'post',
                   status: str = 'publish') -> str:
        """创建文章
        
        Args:
            title: 文章标题
            content: 文章内容
            categories: 分类列表
            tags: 标签列表
            post_type: 文章类型 (post/moment等)
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
        post.post_type = post_type
        post.comment_status = 'open'
        
        # 处理分类 - 使用更简单的方式避免序列化问题
        if categories:
            try:
                # 确保分类存在
                for cat_name in categories:
                    self._get_or_create_category(cat_name)
                
                # 使用简单的字符串列表而不是WordPressTerm对象
                if not hasattr(post, 'terms_names'):
                    post.terms_names = {}
                post.terms_names['category'] = categories
                self.logger.info(f"设置分类: {categories}")
            except Exception as e:
                self.logger.error(f"设置分类时出错: {e}")
                # 继续发布文章，即使分类设置失败
        
        # 处理标签 - 使用更简单的方式避免序列化问题
        if tags:
            # 确保标签存在，但不在创建文章时设置
            for tag_name in tags:
                try:
                    self._get_or_create_tag(tag_name)
                except Exception as e:
                    self.logger.error(f"处理标签 '{tag_name}' 时出错: {e}")
            
            # 使用简单的字符串列表而不是WordPressTerm对象
            post.terms_names = {
                'post_tag': tags
            }
        
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