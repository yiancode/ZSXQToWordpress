#!/usr/bin/env python3
"""
内容处理器的单元测试
"""
import unittest
from datetime import datetime
from content_processor import ContentProcessor


class TestContentProcessor(unittest.TestCase):
    """内容处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = ContentProcessor()
        
    def test_generate_title_from_title_field(self):
        """测试从标题字段生成标题"""
        topic = {
            'content': {
                'title': '这是标题',
                'text': '这是内容'
            }
        }
        
        title = self.processor._generate_title(topic)
        self.assertEqual(title, '这是标题')
        
    def test_generate_title_from_first_line(self):
        """测试从第一行生成标题"""
        topic = {
            'content': {
                'text': '这可能是标题\n\n这是正文内容，包含更多的文字。'
            }
        }
        
        title = self.processor._generate_title(topic)
        self.assertEqual(title, '这可能是标题')
        
    def test_generate_title_truncate(self):
        """测试截断长内容作为标题"""
        topic = {
            'content': {
                'text': '这是一段非常长的内容，超过了30个字符，需要被截断作为标题使用。'
            }
        }
        
        title = self.processor._generate_title(topic)
        self.assertEqual(title, '这是一段非常长的内容，超过了30个字符，需要被截断作为标题使...')
        
    def test_generate_title_from_date(self):
        """测试使用日期生成标题"""
        topic = {
            'content': {'text': ''},
            'create_time': '2024-01-15T10:30:00Z'
        }
        
        title = self.processor._generate_title(topic)
        self.assertEqual(title, '2024年01月15日分享')
        
    def test_process_content_basic(self):
        """测试基本内容处理"""
        text = "第一段内容\n\n第二段内容"
        result = self.processor._process_content(text)
        
        self.assertIn('<p>第一段内容</p>', result)
        self.assertIn('<p>第二段内容</p>', result)
        
    def test_process_content_mentions(self):
        """测试处理@提及"""
        text = '这是一条<e type="mention" uid="123">@用户名</e>的消息'
        result = self.processor._process_content(text)
        
        self.assertIn('@用户名', result)
        self.assertNotIn('<e type="mention"', result)
        
    def test_process_content_hashtags(self):
        """测试处理话题标签"""
        text = '分享一个<e type="hashtag">#技术话题#</e>'
        result = self.processor._process_content(text)
        
        self.assertIn('#技术话题#', result)
        self.assertNotIn('<e type="hashtag"', result)
        
    def test_process_content_line_breaks(self):
        """测试处理换行"""
        text = "第一行\n第二行\n\n新段落"
        result = self.processor._process_content(text)
        
        self.assertIn('<br>', result)
        self.assertEqual(result.count('<p>'), 2)
        
    def test_extract_images(self):
        """测试提取图片"""
        topic = {
            'content': {
                'images': [
                    {
                        'large': {'url': 'http://example.com/large1.jpg'},
                        'original': {'url': 'http://example.com/orig1.jpg'}
                    },
                    {
                        'original': {'url': 'http://example.com/orig2.jpg'}
                    }
                ]
            }
        }
        
        images = self.processor._extract_images(topic)
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0], 'http://example.com/large1.jpg')
        self.assertEqual(images[1], 'http://example.com/orig2.jpg')
        
    def test_extract_tags(self):
        """测试提取标签"""
        topic = {
            'content': {
                'text': '分享#Python#和#编程#相关内容'
            },
            'digested': True
        }
        
        tags = self.processor._extract_tags(topic)
        self.assertIn('Python', tags)
        self.assertIn('编程', tags)
        self.assertIn('精华', tags)
        
    def test_determine_categories_by_content(self):
        """测试根据内容确定分类"""
        # 技术内容
        topic1 = {
            'content': {'text': '今天学习了Python编程技术'}
        }
        categories1 = self.processor._determine_categories(topic1)
        self.assertIn('技术分享', categories1)
        
        # 生活内容
        topic2 = {
            'content': {'text': '今天的生活感悟'}
        }
        categories2 = self.processor._determine_categories(topic2)
        self.assertIn('生活感悟', categories2)
        
        # 图文内容
        topic3 = {
            'content': {
                'text': '分享一些照片',
                'images': [{'url': 'test.jpg'}]
            }
        }
        categories3 = self.processor._determine_categories(topic3)
        self.assertIn('图文分享', categories3)
        
    def test_process_topic_complete(self):
        """测试完整的主题处理"""
        topic = {
            'topic_id': '123456',
            'content': {
                'text': '测试标题\n\n这是<e type="mention">@某人</e>分享的#技术#内容',
                'images': [
                    {'large': {'url': 'http://example.com/img.jpg'}}
                ]
            },
            'create_time': '2024-01-15T10:30:00Z',
            'digested': True
        }
        
        article = self.processor.process_topic(topic)
        
        self.assertEqual(article['topic_id'], '123456')
        self.assertEqual(article['title'], '测试标题')
        self.assertIn('@某人', article['content'])
        self.assertEqual(len(article['images']), 1)
        self.assertIn('技术', article['tags'])
        self.assertIn('精华', article['tags'])
        self.assertTrue(article['is_elite'])
        
    def test_format_article_with_images(self):
        """测试格式化带图片的文章"""
        article = {
            'content': '<p>文章内容</p>',
            'images': ['http://old.com/img1.jpg', 'http://old.com/img2.jpg'],
            'create_time': '2024-01-15T10:30:00Z'
        }
        
        processed_images = {
            'http://old.com/img1.jpg': 'http://new.com/img1.jpg',
            'http://old.com/img2.jpg': 'http://new.com/img2.jpg'
        }
        
        formatted = self.processor.format_article_with_images(article, processed_images)
        
        self.assertIn('<img src="http://new.com/img1.jpg"', formatted)
        self.assertIn('<img src="http://new.com/img2.jpg"', formatted)
        self.assertIn('发布于知识星球', formatted)
        self.assertIn('2024-01-15', formatted)


if __name__ == '__main__':
    unittest.main()