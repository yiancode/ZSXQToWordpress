#!/usr/bin/env python3
"""
WordPress客户端的单元测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from wordpress_client import WordPressClient, WordPressError
from wordpress_xmlrpc import WordPressPost, WordPressTerm
from wordpress_xmlrpc.exceptions import InvalidCredentialsError, ServerConnectionError


class TestWordPressClient(unittest.TestCase):
    """WordPress客户端测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.client = WordPressClient(
            url="https://test.com/xmlrpc.php",
            username="test_user",
            password="test_pass"
        )
        
    @patch('wordpress_client.Client')
    def test_connect_success(self, mock_client_class):
        """测试连接成功"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.call.return_value = []
        
        self.client.connect()
        
        mock_client_class.assert_called_once_with(
            "https://test.com/xmlrpc.php",
            "test_user",
            "test_pass"
        )
        self.assertIsNotNone(self.client.client)
        
    @patch('wordpress_client.Client')
    def test_connect_invalid_credentials(self, mock_client_class):
        """测试认证失败"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.call.side_effect = InvalidCredentialsError()
        
        with self.assertRaises(WordPressError) as cm:
            self.client.connect()
        self.assertIn('认证失败', str(cm.exception))
        
    @patch('wordpress_client.Client')
    def test_connect_xmlrpc_disabled(self, mock_client_class):
        """测试XML-RPC被禁用"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.call.side_effect = ServerConnectionError("XML-RPC services are disabled")
        
        with self.assertRaises(WordPressError) as cm:
            self.client.connect()
        self.assertIn('XML-RPC', str(cm.exception))
        
    @patch('wordpress_client.Client')
    def test_validate_connection(self, mock_client_class):
        """测试验证连接"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.call.return_value = []
        
        result = self.client.validate_connection()
        self.assertTrue(result)
        
    @patch('wordpress_client.Client')
    def test_create_post_simple(self, mock_client_class):
        """测试创建简单文章"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.call.side_effect = [
            [],  # connect test
            "123"  # new post ID
        ]
        
        post_id = self.client.create_post(
            title="测试文章",
            content="测试内容"
        )
        
        self.assertEqual(post_id, "123")
        # 验证调用了NewPost
        calls = mock_client.call.call_args_list
        self.assertEqual(len(calls), 2)
        
    @patch('wordpress_client.Client')
    def test_create_post_with_categories_and_tags(self, mock_client_class):
        """测试创建带分类和标签的文章"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # 模拟分类和标签
        mock_category = Mock()
        mock_category.id = "1"
        mock_category.name = "技术"
        
        mock_tag = Mock()
        mock_tag.id = "2"
        mock_tag.name = "Python"
        
        mock_client.call.side_effect = [
            [],  # connect test
            [mock_category],  # get categories
            [mock_tag],  # get tags
            "123"  # new post ID
        ]
        
        post_id = self.client.create_post(
            title="测试文章",
            content="测试内容",
            categories=["技术"],
            tags=["Python"]
        )
        
        self.assertEqual(post_id, "123")
        
    @patch('wordpress_client.Client')
    def test_create_post_create_new_category(self, mock_client_class):
        """测试创建新分类"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.call.side_effect = [
            [],  # connect test
            [],  # get categories (empty)
            10,  # new category ID
            "123"  # new post ID
        ]
        
        post_id = self.client.create_post(
            title="测试文章",
            content="测试内容",
            categories=["新分类"]
        )
        
        self.assertEqual(post_id, "123")
        # 验证分类被缓存
        self.assertEqual(self.client._category_cache["新分类"], 10)
        
    @patch('wordpress_client.Client')
    def test_post_exists_true(self, mock_client_class):
        """测试文章存在的情况"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_post = Mock()
        mock_post.title = "已存在的文章"
        
        mock_client.call.side_effect = [
            [],  # connect test
            [mock_post]  # existing posts
        ]
        
        exists = self.client.post_exists("已存在的文章")
        self.assertTrue(exists)
        
    @patch('wordpress_client.Client')
    def test_post_exists_false(self, mock_client_class):
        """测试文章不存在的情况"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_post = Mock()
        mock_post.title = "其他文章"
        
        mock_client.call.side_effect = [
            [],  # connect test
            [mock_post]  # existing posts
        ]
        
        exists = self.client.post_exists("新文章")
        self.assertFalse(exists)
        
    @patch('wordpress_client.Client')
    def test_create_post_error_handling(self, mock_client_class):
        """测试创建文章时的错误处理"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.call.side_effect = [
            [],  # connect test
            Exception("网络错误")  # error on NewPost
        ]
        
        with self.assertRaises(WordPressError) as cm:
            self.client.create_post("测试", "内容")
        self.assertIn('创建文章失败', str(cm.exception))


if __name__ == '__main__':
    unittest.main()