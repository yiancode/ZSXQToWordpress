#!/usr/bin/env python3
"""
同步状态管理的单元测试
"""
import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
from sync_state import SyncState, SyncStateError


class TestSyncState(unittest.TestCase):
    """同步状态管理测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, 'test_state.json')
        
    def tearDown(self):
        """测试后清理"""
        # 删除所有测试文件
        for filename in os.listdir(self.temp_dir):
            filepath = os.path.join(self.temp_dir, filename)
            os.remove(filepath)
        os.rmdir(self.temp_dir)
        
    def test_init_new_state(self):
        """测试初始化新状态"""
        state = SyncState(self.state_file)
        
        self.assertEqual(len(state._state['synced_topics']), 0)
        self.assertIsNone(state._state['last_sync_time'])
        self.assertEqual(len(state._state['sync_history']), 0)
        
    def test_load_existing_state(self):
        """测试加载已存在的状态"""
        # 创建测试状态文件
        test_data = {
            'synced_topics': {'123': {'wordpress_id': '456'}},
            'last_sync_time': '2024-01-15T10:00:00',
            'sync_history': [{'success': 10}]
        }
        with open(self.state_file, 'w') as f:
            json.dump(test_data, f)
            
        state = SyncState(self.state_file)
        
        self.assertEqual(len(state._state['synced_topics']), 1)
        self.assertIn('123', state._state['synced_topics'])
        
    def test_save_state(self):
        """测试保存状态"""
        state = SyncState(self.state_file)
        state.mark_synced('123', '456', '测试标题', '2024-01-15T10:00:00')
        state.save()
        
        # 重新加载验证
        with open(self.state_file, 'r') as f:
            saved_data = json.load(f)
            
        self.assertIn('123', saved_data['synced_topics'])
        self.assertEqual(saved_data['synced_topics']['123']['wordpress_id'], '456')
        
    def test_is_synced(self):
        """测试检查是否已同步"""
        state = SyncState(self.state_file)
        state.mark_synced('123', '456', '测试', '2024-01-15T10:00:00')
        
        self.assertTrue(state.is_synced('123'))
        self.assertFalse(state.is_synced('999'))
        
    def test_mark_synced(self):
        """测试标记为已同步"""
        state = SyncState(self.state_file)
        state.mark_synced('123', '456', '测试标题', '2024-01-15T10:00:00')
        
        info = state._state['synced_topics']['123']
        self.assertEqual(info['wordpress_id'], '456')
        self.assertEqual(info['title'], '测试标题')
        self.assertIn('sync_time', info)
        
    def test_last_sync_time(self):
        """测试最后同步时间"""
        state = SyncState(self.state_file)
        
        # 初始状态应该为None
        self.assertIsNone(state.get_last_sync_time())
        
        # 更新时间
        test_time = datetime(2024, 1, 15, 10, 0, 0)
        state.update_last_sync_time(test_time)
        
        # 验证
        last_time = state.get_last_sync_time()
        self.assertEqual(last_time, test_time)
        
        # 使用默认时间（当前时间）
        state.update_last_sync_time()
        new_time = state.get_last_sync_time()
        self.assertIsNotNone(new_time)
        self.assertGreater(new_time, test_time)
        
    def test_sync_record(self):
        """测试同步记录"""
        state = SyncState(self.state_file)
        
        # 添加记录
        record = {
            'success': 10,
            'failed': 2,
            'skipped': 5
        }
        state.add_sync_record(record)
        
        # 验证
        self.assertEqual(len(state._state['sync_history']), 1)
        saved_record = state._state['sync_history'][0]
        self.assertEqual(saved_record['success'], 10)
        self.assertIn('timestamp', saved_record)
        
    def test_sync_history_limit(self):
        """测试同步历史记录限制"""
        state = SyncState(self.state_file)
        
        # 添加超过10条记录
        for i in range(15):
            state.add_sync_record({'index': i})
            
        # 应该只保留最后10条
        self.assertEqual(len(state._state['sync_history']), 10)
        # 验证是最后10条
        self.assertEqual(state._state['sync_history'][0]['index'], 5)
        self.assertEqual(state._state['sync_history'][-1]['index'], 14)
        
    def test_sync_statistics(self):
        """测试同步统计"""
        state = SyncState(self.state_file)
        
        # 添加一些数据
        state.mark_synced('1', '10', '标题1', '2024-01-15T10:00:00')
        state.mark_synced('2', '20', '标题2', '2024-01-15T11:00:00')
        state.update_last_sync_time(datetime(2024, 1, 15, 12, 0, 0))
        state.add_sync_record({'success': 2, 'failed': 0})
        
        stats = state.get_sync_statistics()
        
        self.assertEqual(stats['total_synced'], 2)
        self.assertIsNotNone(stats['last_sync_time'])
        self.assertEqual(stats['recent_sync']['success'], 2)
        
    def test_synced_topics_list(self):
        """测试获取已同步主题列表"""
        state = SyncState(self.state_file)
        
        # 添加主题，故意打乱时间顺序
        state._state['synced_topics']['1'] = {
            'wordpress_id': '10',
            'title': '标题1',
            'sync_time': '2024-01-15T12:00:00'
        }
        state._state['synced_topics']['2'] = {
            'wordpress_id': '20',
            'title': '标题2',
            'sync_time': '2024-01-15T10:00:00'
        }
        
        topics = state.get_synced_topics_list()
        
        # 应该按时间倒序排序
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]['topic_id'], '1')
        self.assertEqual(topics[1]['topic_id'], '2')
        
    def test_clear_all(self):
        """测试清空所有记录"""
        state = SyncState(self.state_file)
        
        # 添加一些数据
        state.mark_synced('123', '456', '测试', '2024-01-15T10:00:00')
        state.update_last_sync_time()
        state.add_sync_record({'test': True})
        
        # 清空
        state.clear_all()
        
        # 验证
        self.assertEqual(len(state._state['synced_topics']), 0)
        self.assertIsNone(state._state['last_sync_time'])
        self.assertEqual(len(state._state['sync_history']), 0)
        
    def test_corrupted_state_file(self):
        """测试损坏的状态文件"""
        # 创建损坏的文件
        with open(self.state_file, 'w') as f:
            f.write('{"invalid json"')
            
        # 应该抛出错误并备份文件
        with self.assertRaises(SyncStateError) as cm:
            SyncState(self.state_file)
            
        self.assertIn('状态文件损坏', str(cm.exception))
        self.assertTrue(os.path.exists(f"{self.state_file}.backup"))


if __name__ == '__main__':
    unittest.main()