#!/usr/bin/env python3
"""
七牛云上传器的单元测试
"""
import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from qiniu_uploader import QiniuUploader, QiniuError


class TestQiniuUploader(unittest.TestCase):
    """七牛云上传器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.uploader = QiniuUploader(
            access_key="test_ak",
            secret_key="test_sk",
            bucket="test_bucket",
            domain="test.domain.com"
        )
        
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.uploader.access_key, "test_ak")
        self.assertEqual(self.uploader.secret_key, "test_sk")
        self.assertEqual(self.uploader.bucket, "test_bucket")
        self.assertEqual(self.uploader.domain, "test.domain.com")
        
        # 测试去除末尾斜杠
        uploader2 = QiniuUploader("ak", "sk", "bucket", "domain.com/")
        self.assertEqual(uploader2.domain, "domain.com")
        
    @patch('qiniu_uploader.Auth')
    def test_validate_config_success(self, mock_auth_class):
        """测试配置验证成功"""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.upload_token.return_value = "test_token"
        
        uploader = QiniuUploader("ak", "sk", "bucket", "domain")
        result = uploader.validate_config()
        
        self.assertTrue(result)
        mock_auth.upload_token.assert_called_once_with("bucket")
        
    @patch('qiniu_uploader.Auth')
    def test_validate_config_failure(self, mock_auth_class):
        """测试配置验证失败"""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.upload_token.side_effect = Exception("Invalid credentials")
        
        uploader = QiniuUploader("ak", "sk", "bucket", "domain")
        result = uploader.validate_config()
        
        self.assertFalse(result)
        
    @patch('qiniu_uploader.requests.get')
    def test_download_image_success(self, mock_get):
        """测试下载图片成功"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.iter_content.return_value = [b'fake_image_data']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 下载图片
        temp_path = self.uploader.download_image("http://example.com/image.jpg")
        
        self.assertIsNotNone(temp_path)
        self.assertTrue(temp_path.endswith('.jpg'))
        
        # 清理临时文件
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
            
    @patch('qiniu_uploader.requests.get')
    def test_download_image_failure(self, mock_get):
        """测试下载图片失败"""
        mock_get.side_effect = Exception("Network error")
        
        temp_path = self.uploader.download_image("http://example.com/image.jpg")
        self.assertIsNone(temp_path)
        
    @patch('qiniu_uploader.requests.get')
    def test_download_image_content_types(self, mock_get):
        """测试不同内容类型的图片下载"""
        test_cases = [
            ('image/png', '.png'),
            ('image/gif', '.gif'),
            ('image/webp', '.webp'),
            ('application/octet-stream', '.jpg'),  # 默认
        ]
        
        for content_type, expected_ext in test_cases:
            with self.subTest(content_type=content_type):
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {'content-type': content_type}
                mock_response.iter_content.return_value = [b'data']
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                temp_path = self.uploader.download_image("http://example.com/image")
                
                self.assertIsNotNone(temp_path)
                self.assertTrue(temp_path.endswith(expected_ext))
                
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
    @patch('qiniu_uploader.put_file')
    @patch('qiniu_uploader.etag')
    @patch('qiniu_uploader.Auth')
    def test_upload_image_success(self, mock_auth_class, mock_etag, mock_put_file):
        """测试上传图片成功"""
        # 设置mock
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.upload_token.return_value = "test_token"
        
        mock_etag.return_value = "test_etag"
        mock_put_file.return_value = (
            {'key': 'test_etag.jpg'},
            {'status_code': 200}
        )
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'test_image_data')
            temp_path = f.name
            
        try:
            uploader = QiniuUploader("ak", "sk", "bucket", "http://domain.com")
            url = uploader.upload_image(temp_path)
            
            self.assertEqual(url, "http://domain.com/test_etag.jpg")
            mock_put_file.assert_called_once()
        finally:
            os.unlink(temp_path)
            
    @patch('qiniu_uploader.put_file')
    @patch('qiniu_uploader.Auth')
    def test_upload_image_with_custom_key(self, mock_auth_class, mock_put_file):
        """测试使用自定义key上传图片"""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.upload_token.return_value = "test_token"
        
        mock_put_file.return_value = (
            {'key': 'custom_name.jpg'},
            {'status_code': 200}
        )
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            
        try:
            uploader = QiniuUploader("ak", "sk", "bucket", "domain.com")
            url = uploader.upload_image(temp_path, key="custom_name.jpg")
            
            self.assertEqual(url, "http://domain.com/custom_name.jpg")
        finally:
            os.unlink(temp_path)
            
    @patch('qiniu_uploader.put_file')
    @patch('qiniu_uploader.Auth')
    def test_upload_image_failure(self, mock_auth_class, mock_put_file):
        """测试上传图片失败"""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.upload_token.return_value = "test_token"
        
        mock_put_file.return_value = (None, {'error': 'Upload failed'})
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            
        try:
            uploader = QiniuUploader("ak", "sk", "bucket", "domain.com")
            url = uploader.upload_image(temp_path)
            self.assertIsNone(url)
        finally:
            os.unlink(temp_path)
            
    def test_process_images_in_content(self):
        """测试处理内容中的图片"""
        content = "文章内容 ![图片1](http://old.com/img1.jpg) 和 ![图片2](http://old.com/img2.jpg)"
        images = ["http://old.com/img1.jpg", "http://old.com/img2.jpg"]
        
        # Mock process_image方法
        with patch.object(self.uploader, 'process_image') as mock_process:
            mock_process.side_effect = [
                "http://new.com/img1.jpg",
                "http://new.com/img2.jpg"
            ]
            
            new_content = self.uploader.process_images_in_content(content, images)
            
            self.assertIn("http://new.com/img1.jpg", new_content)
            self.assertIn("http://new.com/img2.jpg", new_content)
            self.assertNotIn("http://old.com", new_content)
            
    def test_process_images_in_content_with_failure(self):
        """测试处理内容中的图片（部分失败）"""
        content = "文章内容 ![图片](http://old.com/img.jpg)"
        images = ["http://old.com/img.jpg"]
        
        with patch.object(self.uploader, 'process_image') as mock_process:
            # 返回原URL表示处理失败
            mock_process.return_value = "http://old.com/img.jpg"
            
            new_content = self.uploader.process_images_in_content(content, images)
            
            # 内容应该保持不变
            self.assertEqual(content, new_content)


if __name__ == '__main__':
    unittest.main()