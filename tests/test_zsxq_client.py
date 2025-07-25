#!/usr/bin/env python3
"""
知识星球API客户端的单元测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
from zsxq_client import ZsxqClient, ZsxqAPIError


class TestZsxqClient(unittest.TestCase):
    """知识星球客户端测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.client = ZsxqClient(
            access_token="test_token",
            user_agent="test_agent",
            group_id="test_group",
            max_retries=3,
            delay_seconds=0  # 测试时禁用延迟
        )
        
    @patch('zsxq_client.requests.Session')
    def test_client_initialization(self, mock_session):
        """测试客户端初始化"""
        client = ZsxqClient(
            access_token="test_token",
            user_agent="test_agent",
            group_id="test_group"
        )
        
        self.assertEqual(client.access_token, "test_token")
        self.assertEqual(client.user_agent, "test_agent")
        self.assertEqual(client.group_id, "test_group")
        
    @patch.object(ZsxqClient, '_make_request')
    def test_validate_connection_success(self, mock_request):
        """测试连接验证成功"""
        mock_request.return_value = {'succeeded': True}
        
        result = self.client.validate_connection()
        self.assertTrue(result)
        mock_request.assert_called_once()
        
    @patch.object(ZsxqClient, '_make_request')
    def test_validate_connection_failure(self, mock_request):
        """测试连接验证失败"""
        mock_request.side_effect = ZsxqAPIError("连接失败")
        
        result = self.client.validate_connection()
        self.assertFalse(result)
        
    def test_make_request_success(self):
        """测试请求成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'succeeded': True, 'data': 'test'}
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client._make_request('GET', 'http://test.com')
            self.assertEqual(result, {'succeeded': True, 'data': 'test'})
            
    def test_make_request_401_error(self):
        """测试401认证错误"""
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            with self.assertRaises(ZsxqAPIError) as cm:
                self.client._make_request('GET', 'http://test.com')
            self.assertIn('认证失败', str(cm.exception))
            
    def test_make_request_with_retry(self):
        """测试请求重试机制"""
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = requests.HTTPError()
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'succeeded': True}
        
        with patch.object(self.client.session, 'request', 
                         side_effect=[mock_response_fail, mock_response_success]):
            with patch('time.sleep'):  # 跳过延迟
                result = self.client._make_request('GET', 'http://test.com')
                self.assertEqual(result, {'succeeded': True})
                
    @patch.object(ZsxqClient, '_make_request')
    def test_get_topics(self, mock_request):
        """测试获取主题列表"""
        mock_topics = [
            {'topic_id': '1', 'content': 'test1'},
            {'topic_id': '2', 'content': 'test2'}
        ]
        mock_request.return_value = {
            'succeeded': True,
            'resp_data': {'topics': mock_topics}
        }
        
        topics = self.client.get_topics(count=2)
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]['topic_id'], '1')
        
    @patch.object(ZsxqClient, 'get_topics')
    def test_get_all_topics_pagination(self, mock_get_topics):
        """测试分页获取所有主题"""
        # 模拟三页数据
        page1 = [{'topic_id': f'{i}', 'create_time': f'2024-01-0{i}T00:00:00Z'} 
                for i in range(1, 3)]
        page2 = [{'topic_id': f'{i}', 'create_time': f'2024-01-0{i}T00:00:00Z'} 
                for i in range(3, 5)]
        page3 = []  # 最后一页为空
        
        mock_get_topics.side_effect = [page1, page2, page3]
        
        topics = self.client.get_all_topics(batch_size=2)
        self.assertEqual(len(topics), 4)
        self.assertEqual(mock_get_topics.call_count, 3)
        
    @patch.object(ZsxqClient, 'get_topics')
    def test_get_all_topics_with_start_time(self, mock_get_topics):
        """测试带开始时间的增量获取"""
        start_time = datetime(2024, 1, 3, 0, 0, 0)
        
        topics = [
            {'topic_id': '1', 'create_time': '2024-01-05T00:00:00Z'},
            {'topic_id': '2', 'create_time': '2024-01-04T00:00:00Z'},
            {'topic_id': '3', 'create_time': '2024-01-02T00:00:00Z'},  # 早于start_time
        ]
        
        mock_get_topics.return_value = topics
        
        result = self.client.get_all_topics(batch_size=10, start_time=start_time)
        # 应该只返回前两个主题
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['topic_id'], '1')
        self.assertEqual(result[1]['topic_id'], '2')
        
    @patch.object(ZsxqClient, '_make_request')
    def test_get_topic_detail(self, mock_request):
        """测试获取主题详情"""
        mock_detail = {
            'topic_id': '123',
            'content': '详细内容',
            'images': ['image1.jpg', 'image2.jpg']
        }
        mock_request.return_value = {
            'succeeded': True,
            'resp_data': {'topic': mock_detail}
        }
        
        detail = self.client.get_topic_detail('123')
        self.assertEqual(detail['topic_id'], '123')
        self.assertEqual(len(detail['images']), 2)
        
    def test_api_error_message(self):
        """测试API错误信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'succeeded': False,
            'msg': '参数错误'
        }
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            with self.assertRaises(ZsxqAPIError) as cm:
                self.client._make_request('GET', 'http://test.com')
            self.assertIn('参数错误', str(cm.exception))


if __name__ == '__main__':
    unittest.main()