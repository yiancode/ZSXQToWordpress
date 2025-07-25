#!/usr/bin/env python3
"""
内容处理模块
负责将知识星球内容转换为WordPress格式
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class ContentProcessor:
    """内容处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.logger = logging.getLogger(__name__)
        
    def process_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个主题，转换为WordPress文章格式
        
        Args:
            topic: 知识星球主题数据
            
        Returns:
            处理后的文章数据
        """
        # 提取基本信息
        topic_id = str(topic.get('topic_id', ''))
        content = topic.get('content', {})
        
        # 处理标题
        title = self._generate_title(topic)
        
        # 处理内容
        text_content = content.get('text', '')
        processed_content = self._process_content(text_content)
        
        # 提取图片
        images = self._extract_images(topic)
        
        # 处理标签
        tags = self._extract_tags(topic)
        
        # 处理分类
        categories = self._determine_categories(topic)
        
        # 构建文章数据
        article = {
            'topic_id': topic_id,
            'title': title,
            'content': processed_content,
            'images': images,
            'tags': tags,
            'categories': categories,
            'create_time': topic.get('create_time', ''),
            'is_elite': topic.get('digested', False),  # 是否精华
            'raw_data': topic  # 保留原始数据
        }
        
        return article
        
    def _generate_title(self, topic: Dict[str, Any]) -> str:
        """生成文章标题
        
        Args:
            topic: 主题数据
            
        Returns:
            文章标题
        """
        content = topic.get('content', {})
        text = content.get('text', '')
        
        # 如果有标题字段，直接使用
        if content.get('title'):
            return content['title']
            
        # 从内容提取标题
        # 1. 尝试找第一行作为标题
        lines = text.strip().split('\n')
        if lines and lines[0]:
            first_line = lines[0].strip()
            # 如果第一行比较短且不是以标点结尾，可能是标题
            if len(first_line) <= 50 and not first_line.endswith(('。', '！', '？', '，')):
                return first_line
                
        # 2. 截取前30个字符作为标题
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if len(clean_text) > 30:
            title = clean_text[:30] + '...'
        elif clean_text:
            title = clean_text
        else:
            title = ''
            
        # 3. 如果还是空的，使用时间作为标题
        if not title:
            create_time = topic.get('create_time', '')
            if create_time:
                dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                title = dt.strftime('%Y年%m月%d日分享')
            else:
                title = '无标题'
                
        return title
        
    def _process_content(self, text: str) -> str:
        """处理文本内容，转换格式
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return ""
            
        # 处理@提及 - 转换为普通文本
        processed = re.sub(r'<e type="mention"[^>]*>(@[^<]+)</e>', r'\1', text)
        
        # 处理话题标签
        processed = re.sub(r'<e type="hashtag"[^>]*>#([^<]+)#</e>', r'#\1#', processed)
        
        # 处理链接
        processed = re.sub(r'<e type="web"[^>]*>([^<]+)</e>', r'\1', processed)
        
        # 处理换行 - 保持段落结构
        paragraphs = processed.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # 将单个换行转换为<br>
                para = para.replace('\n', '<br>\n')
                formatted_paragraphs.append(f'<p>{para}</p>')
                
        processed = '\n\n'.join(formatted_paragraphs)
        
        return processed
        
    def _extract_images(self, topic: Dict[str, Any]) -> List[str]:
        """提取主题中的图片URL
        
        Args:
            topic: 主题数据
            
        Returns:
            图片URL列表
        """
        images = []
        
        # 从content中提取图片
        content = topic.get('content', {})
        if 'images' in content:
            for img in content['images']:
                if isinstance(img, dict):
                    # 获取大图URL
                    large_url = img.get('large', {}).get('url')
                    if large_url:
                        images.append(large_url)
                    else:
                        # 退而求其次，获取原始URL
                        original_url = img.get('original', {}).get('url')
                        if original_url:
                            images.append(original_url)
                            
        return images
        
    def _extract_tags(self, topic: Dict[str, Any]) -> List[str]:
        """提取标签
        
        Args:
            topic: 主题数据
            
        Returns:
            标签列表
        """
        tags = []
        
        # 从内容中提取话题标签
        content_text = topic.get('content', {}).get('text', '')
        hashtags = re.findall(r'#([^#\s]+)#', content_text)
        tags.extend(hashtags)
        
        # 如果是精华内容，添加精华标签
        if topic.get('digested', False):
            tags.append('精华')
            
        # 去重
        tags = list(set(tags))
        
        return tags
        
    def _determine_categories(self, topic: Dict[str, Any]) -> List[str]:
        """确定文章分类
        
        Args:
            topic: 主题数据
            
        Returns:
            分类列表
        """
        categories = []
        
        # 根据内容类型确定分类
        content = topic.get('content', {})
        
        # 如果有图片，可能是图文分享
        if content.get('images'):
            categories.append('图文分享')
            
        # 根据话题标签推断分类
        content_text = content.get('text', '')
        if re.search(r'技术|编程|代码|开发', content_text, re.IGNORECASE):
            categories.append('技术分享')
        elif re.search(r'生活|日常|感悟', content_text, re.IGNORECASE):
            categories.append('生活感悟')
        elif re.search(r'读书|书籍|阅读', content_text, re.IGNORECASE):
            categories.append('读书笔记')
            
        # 如果没有分类，使用默认分类
        if not categories:
            categories.append('知识星球')
            
        return categories
        
    def format_article_with_images(self, article: Dict[str, Any], 
                                 processed_images: Dict[str, str]) -> str:
        """格式化文章内容，包含处理后的图片
        
        Args:
            article: 文章数据
            processed_images: 原始URL到新URL的映射
            
        Returns:
            格式化后的HTML内容
        """
        content = article['content']
        
        # 如果有图片，将其插入到内容中
        if article['images']:
            image_html = []
            for original_url in article['images']:
                new_url = processed_images.get(original_url, original_url)
                image_html.append(f'<img src="{new_url}" alt="图片" style="max-width: 100%; height: auto;">')
                
            # 将图片添加到内容末尾
            if image_html:
                content += '\n\n' + '\n'.join(image_html)
                
        # 添加来源说明
        create_time = article.get('create_time', '')
        if create_time:
            dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            content += f'\n\n<p style="color: #666; font-size: 14px;">—— 发布于知识星球 {time_str}</p>'
            
        return content