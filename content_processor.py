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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化处理器
        
        Args:
            config: 配置信息，包含source部分用于生成来源链接
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
    def process_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个主题，转换为WordPress内容格式（支持文章和片刻）
        
        Args:
            topic: 知识星球主题数据
            
        Returns:
            处理后的内容数据
        """
        # 提取基本信息
        topic_id = str(topic.get('topic_id', ''))
        topic_type = topic.get('type', '')
        
        # 确定内容类型（文章 or 主题）
        content_type = self._determine_content_type(topic)
        
        # 根据内容类型选择处理方式
        if content_type == 'article':
            return self._process_article(topic)
        else:
            return self._process_topic(topic)
    
    def _determine_content_type(self, topic: Dict[str, Any]) -> str:
        """确定内容类型（文章 or 短内容）
        
        Args:
            topic: 主题数据
            
        Returns:
            内容类型：'article' 或 'short_content'
        """
        topic_type = topic.get('type', 'talk')
        
        # 检查配置中的映射设置
        config_mapping = self.config.get('content_mapping', {})
        
        if config_mapping.get('enable_type_mapping', True):
            # 使用配置中的映射规则
            article_types = config_mapping.get('article_types', ['article'])
            short_content_types = config_mapping.get('short_content_types', ['talk', 'q&a-question', 'q&a-answer'])
            
            if topic_type in article_types:
                return 'article'
            elif topic_type in short_content_types:
                return 'short_content'
        
        # 默认规则：article类型为文章，其他为短内容
        if topic_type == 'article':
            return 'article'
        else:
            return 'short_content'
    
    def _process_article(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """处理文章内容（保留原有逻辑）
        
        Args:
            topic: 知识星球主题数据
            
        Returns:
            处理后的文章数据
        """
        topic_id = str(topic.get('topic_id', ''))
        topic_type = topic.get('type', '')
        
        # 根据主题类型获取内容
        text_content = ''
        if topic_type == 'talk' and 'talk' in topic:
            text_content = topic['talk'].get('text', '')
        elif topic_type == 'q&a-question' and 'question' in topic:
            text_content = topic['question'].get('text', '')
        elif topic_type == 'q&a-answer' and 'answer' in topic:
            text_content = topic['answer'].get('text', '')
        elif 'content' in topic:
            text_content = topic['content'].get('text', '')
        
        # 处理标题 - 根据配置决定是否同步标题
        sync_title = self.config.get('sync', {}).get('sync_title', True)
        if sync_title:
            title = self._generate_title(topic)
        else:
            title = ""  # 不同步标题时设置为空
        
        # 处理内容 - 传递标题以便去重
        processed_content = self._process_content(text_content, title)
        
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
            'content_type': 'article',  # 标记为文章
            'post_type': 'post',  # WordPress文章类型
            'raw_data': topic  # 保留原始数据
        }
        
        
        return article
    
    def _process_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """处理主题
        
        Args:
            topic: 知识星球主题数据
            
        Returns:
            处理后的主题数据
        """
        topic_id = str(topic.get('topic_id', ''))
        topic_type = topic.get('type', '')
        
        # 根据主题类型获取内容
        text_content = ''
        if topic_type == 'talk' and 'talk' in topic:
            text_content = topic['talk'].get('text', '')
        elif topic_type == 'q&a-question' and 'question' in topic:
            text_content = topic['question'].get('text', '')
        elif topic_type == 'q&a-answer' and 'answer' in topic:
            text_content = topic['answer'].get('text', '')
        elif 'content' in topic:
            text_content = topic['content'].get('text', '')
        
        # 生成主题标题 - 根据配置决定是否同步标题
        sync_title = self.config.get('sync', {}).get('sync_title', True)
        if sync_title:
            title = self._generate_topic_title(topic, text_content)
        else:
            title = ""  # 不同步标题时设置为空
        
        # 处理短内容
        processed_content = self._process_topic_text(text_content)
        
        # 提取图片
        images = self._extract_images(topic)
        
        # 处理标签
        tags = self._extract_tags(topic)
        
        # 获取配置中的主题设置
        topic_settings = self.config.get('content_mapping', {}).get('topic_settings', {})
        short_content_category = topic_settings.get('category', '短内容')
        
        # 构建短内容数据
        short_content = {
            'topic_id': topic_id,
            'title': title,
            'content': processed_content,
            'images': images,
            'tags': tags,
            'categories': [short_content_category],
            'create_time': topic.get('create_time', ''),
            'is_elite': topic.get('digested', False),  # 是否精华
            'content_type': 'short_content',  # 标记为短内容
            'post_type': 'post',  # 使用标准WordPress文章类型
            'raw_data': topic  # 保留原始数据
        }
        
        
        return short_content
    
    def _generate_topic_title(self, topic: Dict[str, Any], text_content: str = "") -> str:
        """生成主题标题
        
        Args:
            topic: 主题数据
            text_content: 文本内容
            
        Returns:
            主题标题
        """
        # 获取配置中的最大标题长度
        topic_settings = self.config.get('content_mapping', {}).get('topic_settings', {})
        max_length = topic_settings.get('max_title_length', 30)
        title_prefix = topic_settings.get('title_prefix', '[主题]')
        
        if not text_content:
            # 如果没有文本内容，尝试从topic中获取
            topic_type = topic.get('type', '')
            if topic_type == 'talk' and 'talk' in topic:
                text_content = topic['talk'].get('text', '')
            elif topic_type == 'q&a-question' and 'question' in topic:
                text_content = topic['question'].get('text', '')
            elif topic_type == 'q&a-answer' and 'answer' in topic:
                text_content = topic['answer'].get('text', '')
            elif 'content' in topic:
                text_content = topic['content'].get('text', '')
        
        # 清理文本，去除HTML标签和特殊字符
        import re
        clean_text = re.sub(r'<[^>]*>', '', text_content)  # 去除HTML标签
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # 规范化空白字符
        
        if clean_text:
            # 使用内容前缀作为标题
            if len(clean_text) <= max_length:
                title = clean_text
            else:
                # 智能截断：在合适的位置截断
                title = clean_text[:max_length].rstrip()
                # 如果截断位置不是句末，添加省略号
                if not title.endswith(('。', '！', '？', '，', '、')):
                    title += '…'
            
            # 添加前缀标识
            title = f"{title_prefix} {title}"
        else:
            # 如果没有内容，使用时间戳作为标题
            create_time = topic.get('create_time', '')
            if create_time:
                dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                title = f"{title_prefix} {dt.strftime('%m-%d %H:%M')}"
            else:
                title = f"{title_prefix} 无标题内容"
        
        return title
    
    def _process_topic_text(self, text: str) -> str:
        """处理主题格式
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的短内容
        """
        if not text:
            return ""
        
        # 基本的内容处理（比文章处理更简化）
        import urllib.parse
        
        # 处理@提及 - 转换为普通文本
        processed = re.sub(r'<e type="mention"[^>]*>(@[^<]+)</e>', r'\1', text)
        
        # 处理话题标签
        processed = re.sub(r'<e type="hashtag"[^>]*>#([^<]+)#</e>', r'#\1#', processed)
        
        # 处理链接（简化版）
        def replace_link(match):
            full_tag = match.group(0)
            href_match = re.search(r'href="([^"]*)"', full_tag)
            title_match = re.search(r'title="([^"]*)"', full_tag)
            
            if href_match:
                url = urllib.parse.unquote(href_match.group(1))
                if title_match:
                    link_text = urllib.parse.unquote(title_match.group(1))
                else:
                    link_text = url
                return f'<a href="{url}" target="_blank">{link_text}</a>'
            else:
                return full_tag
        
        processed = re.sub(r'<e type="web"[^>]*/>', replace_link, processed)
        
        # 短内容保持简洁，只转换必要的换行
        processed = processed.replace('\n\n', '</p><p>')
        processed = processed.replace('\n', '<br>')
        
        # 包装在段落标签中
        if processed and not processed.startswith('<p>'):
            processed = f'<p>{processed}</p>'
        
        return processed
        
    def _generate_title(self, topic: Dict[str, Any]) -> str:
        """生成文章标题 - 改进版，智能避免重复
        
        Args:
            topic: 主题数据
            
        Returns:
            文章标题
        """
        topic_type = topic.get('type', '')
        
        # 根据主题类型获取文本内容
        text = ''
        if topic_type == 'talk' and 'talk' in topic:
            text = topic['talk'].get('text', '')
        elif topic_type == 'q&a-question' and 'question' in topic:
            text = topic['question'].get('text', '')
        elif topic_type == 'q&a-answer' and 'answer' in topic:
            text = topic['answer'].get('text', '')
        elif 'content' in topic:
            content = topic['content']
            text = content.get('text', '')
            # 如果有标题字段，直接使用
            if content.get('title'):
                return content['title']
        
        # 从内容提取标题
        lines = text.strip().split('\n')
        if lines and lines[0]:
            first_line = lines[0].strip()
            
            # 改进的标题判断逻辑
            if len(first_line) <= 80 and not first_line.endswith(('。', '！', '？', '，', '、')):
                # 智能截断：在合适的位置截断，避免简单字符截断
                if len(first_line) > 50:
                    # 寻找合适的断点（标点符号、空格、冒号等）
                    breakpoints = ['：', ':', '，', '、', ' ', '-', '－']
                    best_cut = 30
                    for bp in breakpoints:
                        pos = first_line.find(bp, 20)  # 从第20个字符开始找
                        if 20 <= pos <= 45:  # 在合理范围内
                            best_cut = pos + 1
                            break
                    
                    title = first_line[:best_cut].rstrip('：: ') + '…'
                else:
                    title = first_line
                    
                # 记录原始第一行，用于后续去重
                self._title_source_line = first_line
                return title
                
        # 如果第一行不适合做标题，尝试提取关键信息
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if clean_text:
            # 智能提取：寻找句子的主要部分
            sentences = re.split(r'[。！？]', clean_text)
            if sentences and sentences[0]:
                first_sentence = sentences[0].strip()
                if len(first_sentence) <= 50:
                    title = first_sentence
                    self._title_source_line = None  # 没有对应的原始行
                    return title
            
            # 最后的截断方案
            if len(clean_text) > 30:
                title = clean_text[:30] + '…'
            else:
                title = clean_text
            self._title_source_line = None
        else:
            # 使用时间作为标题
            create_time = topic.get('create_time', '')
            if create_time:
                dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                title = dt.strftime('%Y年%m月%d日分享')
            else:
                title = '无标题'
            self._title_source_line = None
                
        return title
        
    def _process_content(self, text: str, title: str = "") -> str:
        """处理文本内容，转换格式
        
        Args:
            text: 原始文本
            title: 文章标题（用于去重）
            
        Returns:
            处理后的文本
        """
        if not text:
            return ""
        
        # 【增强去重逻辑】智能处理各种重复情况
        text = self._remove_title_duplication(text, title)
        
        import urllib.parse
        
        # 处理@提及 - 转换为普通文本
        processed = re.sub(r'<e type="mention"[^>]*>(@[^<]+)</e>', r'\1', text)
        
        # 处理话题标签
        processed = re.sub(r'<e type="hashtag"[^>]*>#([^<]+)#</e>', r'#\1#', processed)
        
        # 处理链接 - 新的处理方式
        def replace_link(match):
            """替换链接标签为HTML链接"""
            full_tag = match.group(0)
            
            # 提取href和title属性
            href_match = re.search(r'href="([^"]*)"', full_tag)
            title_match = re.search(r'title="([^"]*)"', full_tag)
            
            if href_match:
                # URL解码
                encoded_url = href_match.group(1)
                url = urllib.parse.unquote(encoded_url)
                
                # 获取链接文本
                if title_match:
                    link_text = urllib.parse.unquote(title_match.group(1))
                else:
                    link_text = url
                
                return f'<a href="{url}" target="_blank">{link_text}</a>'
            else:
                # 如果没有href，返回原文本
                return full_tag
        
        # 使用新的链接处理方式
        processed = re.sub(r'<e type="web"[^>]*/>', replace_link, processed)
        
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
    
    def _remove_title_duplication(self, text: str, title: str) -> str:
        """智能去除正文中与标题重复的内容
        
        Args:
            text: 原始正文
            title: 文章标题
            
        Returns:
            去重后的正文
        """
        if not text or not title:
            return text
            
        lines = text.strip().split('\n')
        if not lines or not lines[0]:
            return text
            
        first_line = lines[0].strip()
        
        # 检查各种重复情况
        if self._is_title_duplicate(first_line, title):
            remaining_lines = lines[1:]
            return '\n'.join(remaining_lines).strip()
            
        return text
    
    def _is_title_duplicate(self, first_line: str, title: str) -> bool:
        """检查第一行是否与标题重复
        
        Args:
            first_line: 正文第一行
            title: 文章标题
            
        Returns:
            是否重复
        """
        # 检查是否有记录的原始标题行
        if hasattr(self, '_title_source_line') and self._title_source_line:
            if first_line == self._title_source_line:
                return True
        
        # 检查完全匹配
        if self._exact_match(first_line, title):
            return True
            
        # 检查截断匹配
        if self._truncated_match(first_line, title):
            return True
            
        # 检查模糊匹配
        if self._fuzzy_match(first_line, title):
            return True
            
        return False
    
    def _exact_match(self, first_line: str, title: str) -> bool:
        """检查完全匹配"""
        return first_line.startswith(title.rstrip('…..'))
    
    def _truncated_match(self, first_line: str, title: str) -> bool:
        """检查截断匹配"""
        clean_title = title.rstrip('…..')
        return (first_line.startswith(clean_title) and 
                len(clean_title) >= 10)
    
    def _fuzzy_match(self, first_line: str, title: str) -> bool:
        """检查模糊匹配（忽略标点符号）"""
        import re
        clean_title = title.rstrip('…..')
        # 移除标点符号进行比较
        title_clean = re.sub(r'[^\w\s]', '', clean_title)
        first_line_clean = re.sub(r'[^\w\s]', '', first_line)
        
        return (title_clean and 
                first_line_clean.startswith(title_clean) and 
                len(title_clean) >= 8)
        
    def _extract_images(self, topic: Dict[str, Any]) -> List[str]:
        """提取主题中的图片URL - 增强版，递归搜索所有可能的图片字段
        
        Args:
            topic: 主题数据
            
        Returns:
            图片URL列表
        """
        images = []
        
        # 根据主题类型提取图片
        topic_type = topic.get('type', '')
        
        def extract_image_urls(data, path="root"):
            """递归提取图片URL"""
            urls = []
            if isinstance(data, dict):
                # 查找images字段
                if 'images' in data:
                    images_data = data['images']
                    if isinstance(images_data, list):
                        for i, img in enumerate(images_data):
                            if isinstance(img, dict):
                                # 优先级：large > original > thumbnail > url
                                for size in ['large', 'original', 'thumbnail']:
                                    if size in img and isinstance(img[size], dict) and 'url' in img[size]:
                                        url = img[size]['url']
                                        urls.append(url)
                                        break
                                else:
                                    # 直接包含url字段
                                    if 'url' in img:
                                        url = img['url']
                                        urls.append(url)
                            elif isinstance(img, str) and img.startswith('http'):
                                # 直接是URL字符串
                                urls.append(img)
                
                # 递归搜索其他字段
                for key, value in data.items():
                    if key != 'images' and isinstance(value, (dict, list)):
                        urls.extend(extract_image_urls(value, f"{path}.{key}"))
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    urls.extend(extract_image_urls(item, f"{path}[{i}]"))
            
            return urls
        
        # 使用递归方法提取所有图片
        images = extract_image_urls(topic)
        return images
        
    def _extract_tags(self, topic: Dict[str, Any]) -> List[str]:
        """提取标签
        
        Args:
            topic: 主题数据
            
        Returns:
            标签列表
        """
        tags = []
        
        # 根据主题类型获取文本内容
        topic_type = topic.get('type', '')
        text_content = ''
        
        if topic_type == 'talk' and 'talk' in topic:
            text_content = topic['talk'].get('text', '')
        elif topic_type == 'q&a-question' and 'question' in topic:
            text_content = topic['question'].get('text', '')
        elif topic_type == 'q&a-answer' and 'answer' in topic:
            text_content = topic['answer'].get('text', '')
        elif 'content' in topic:
            text_content = topic['content'].get('text', '')
        
        if not text_content:
            return tags
        
        # 方法1: 提取HTML格式的hashtag标签
        # 格式: <e type="hashtag" hid="xxx" title="%23标签名%23" />
        html_tags = re.findall(r'<e type="hashtag"[^>]*title="([^"]*)"[^>]*/?>', text_content)
        for tag in html_tags:
            # 解码URL编码 (%23 = #)
            import urllib.parse
            decoded_tag = urllib.parse.unquote(tag)
            # 移除首尾的#号
            clean_tag = decoded_tag.strip('#')
            if clean_tag:
                tags.append(clean_tag)
        
        # 方法2: 提取普通的#标签#格式
        hashtags = re.findall(r'#([^#\s]+)#', text_content)
        for tag in hashtags:
            tags.append(tag)
        
        # 如果是精华内容，添加精华标签
        if topic.get('digested', False):
            tags.append('精华')
            
        # 去重
        unique_tags = list(set(tags))
        
        return unique_tags
        
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
            
            # 从配置中获取知识星球信息
            source_config = self.config.get('source', {})
            source_name = source_config.get('name', '知识星球')
            source_url = source_config.get('url', '')
            
            if source_url:
                content += f'\n\n<p style="color: #666; font-size: 14px;">—— 发布于 <a href="{source_url}" target="_blank">{source_name}</a> {time_str}</p>'
            else:
                content += f'\n\n<p style="color: #666; font-size: 14px;">—— 发布于 {source_name} {time_str}</p>'
            
        return content