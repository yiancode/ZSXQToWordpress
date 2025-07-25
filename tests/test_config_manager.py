#!/usr/bin/env python3
"""
配置管理模块的单元测试
"""
import unittest
import json
import os
import tempfile
from config_manager import Config, ConfigError


class TestConfig(unittest.TestCase):
    """配置管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
        
    def create_config_file(self, content: dict):
        """创建测试配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(content, f)
            
    def test_load_valid_config(self):
        """测试加载有效配置"""
        valid_config = {
            "zsxq": {
                "access_token": "test_token",
                "user_agent": "test_agent",
                "group_id": "test_group"
            },
            "wordpress": {
                "url": "https://test.com/xmlrpc.php",
                "username": "test_user",
                "password": "test_pass"
            },
            "qiniu": {
                "access_key": "test_ak",
                "secret_key": "test_sk",
                "bucket": "test_bucket",
                "domain": "test.domain.com"
            },
            "sync": {
                "batch_size": 10,
                "delay_seconds": 1,
                "max_retries": 3
            }
        }
        self.create_config_file(valid_config)
        
        config = Config(self.config_path)
        config.load()
        
        self.assertEqual(config.zsxq['access_token'], 'test_token')
        self.assertEqual(config.wordpress['url'], 'https://test.com/xmlrpc.php')
        self.assertEqual(config.sync['batch_size'], 10)
        self.assertTrue(config.has_qiniu())
        
    def test_missing_config_file(self):
        """测试配置文件不存在的情况"""
        config = Config('non_existent.json')
        with self.assertRaises(ConfigError) as cm:
            config.load()
        self.assertIn('配置文件不存在', str(cm.exception))
        
    def test_invalid_json(self):
        """测试无效的JSON格式"""
        with open(self.config_path, 'w') as f:
            f.write('invalid json content')
            
        config = Config(self.config_path)
        with self.assertRaises(ConfigError) as cm:
            config.load()
        self.assertIn('配置文件格式错误', str(cm.exception))
        
    def test_missing_required_fields(self):
        """测试缺少必要字段"""
        # 缺少access_token
        invalid_config = {
            "zsxq": {
                "user_agent": "test_agent",
                "group_id": "test_group"
            },
            "wordpress": {
                "url": "https://test.com/xmlrpc.php",
                "username": "test_user",
                "password": "test_pass"
            }
        }
        self.create_config_file(invalid_config)
        
        config = Config(self.config_path)
        with self.assertRaises(ConfigError) as cm:
            config.load()
        self.assertIn('access_token', str(cm.exception))
        
    def test_qiniu_optional(self):
        """测试七牛云配置为可选"""
        config_without_qiniu = {
            "zsxq": {
                "access_token": "test_token",
                "user_agent": "test_agent",
                "group_id": "test_group"
            },
            "wordpress": {
                "url": "https://test.com/xmlrpc.php",
                "username": "test_user",
                "password": "test_pass"
            }
        }
        self.create_config_file(config_without_qiniu)
        
        config = Config(self.config_path)
        config.load()
        
        self.assertFalse(config.has_qiniu())
        self.assertEqual(config.qiniu, {})
        
    def test_default_sync_values(self):
        """测试同步配置的默认值"""
        minimal_config = {
            "zsxq": {
                "access_token": "test_token",
                "user_agent": "test_agent",
                "group_id": "test_group"
            },
            "wordpress": {
                "url": "https://test.com/xmlrpc.php",
                "username": "test_user",
                "password": "test_pass"
            }
        }
        self.create_config_file(minimal_config)
        
        config = Config(self.config_path)
        config.load()
        
        self.assertEqual(config.sync['batch_size'], 20)
        self.assertEqual(config.sync['delay_seconds'], 2)
        self.assertEqual(config.sync['max_retries'], 5)
        
    def test_invalid_sync_values(self):
        """测试无效的同步配置值"""
        invalid_config = {
            "zsxq": {
                "access_token": "test_token",
                "user_agent": "test_agent",
                "group_id": "test_group"
            },
            "wordpress": {
                "url": "https://test.com/xmlrpc.php",
                "username": "test_user",
                "password": "test_pass"
            },
            "sync": {
                "batch_size": -1
            }
        }
        self.create_config_file(invalid_config)
        
        config = Config(self.config_path)
        with self.assertRaises(ConfigError) as cm:
            config.load()
        self.assertIn('batch_size必须大于0', str(cm.exception))


if __name__ == '__main__':
    unittest.main()