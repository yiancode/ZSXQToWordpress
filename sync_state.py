#!/usr/bin/env python3
"""
同步状态管理模块
负责记录和管理同步历史，避免重复发布
"""
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging


class SyncStateError(Exception):
    """同步状态相关错误"""
    pass


class SyncState:
    """同步状态管理器"""
    
    def __init__(self, state_file: str = "sync_state.json"):
        """初始化状态管理器
        
        Args:
            state_file: 状态文件路径
        """
        self.state_file = state_file
        self.logger = logging.getLogger(__name__)
        self._state: Dict[str, Any] = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """加载状态文件
        
        Returns:
            状态数据
        """
        if not os.path.exists(self.state_file):
            # 如果文件不存在，创建默认状态
            return {
                'synced_topics': {},  # topic_id -> sync_info
                'last_sync_time': None,
                'sync_history': []  # 最近的同步记录
            }
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # 确保必要的字段存在
                if 'synced_topics' not in state:
                    state['synced_topics'] = {}
                if 'last_sync_time' not in state:
                    state['last_sync_time'] = None
                if 'sync_history' not in state:
                    state['sync_history'] = []
                return state
        except json.JSONDecodeError as e:
            self.logger.error(f"状态文件格式错误: {e}")
            # 备份损坏的文件
            backup_file = f"{self.state_file}.backup"
            shutil.copy(self.state_file, backup_file)
            self.logger.warning(f"已备份损坏的状态文件到: {backup_file}")
            raise SyncStateError(
                f"状态文件损坏，已备份到 {backup_file}。"
                "请选择：1) 删除状态文件重新开始 2) 手动修复状态文件 3) 退出"
            )
        except Exception as e:
            raise SyncStateError(f"读取状态文件失败: {e}")
            
    def save(self) -> None:
        """保存状态到文件"""
        try:
            # 先写入临时文件
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
                
            # 原子替换文件
            os.replace(temp_file, self.state_file)
            self.logger.debug("状态文件保存成功")
        except Exception as e:
            raise SyncStateError(f"保存状态文件失败: {e}")
            
    def is_synced(self, topic_id: str) -> bool:
        """检查主题是否已同步
        
        Args:
            topic_id: 主题ID
            
        Returns:
            是否已同步
        """
        return topic_id in self._state['synced_topics']
        
    def mark_synced(self, topic_id: str, wordpress_id: str, 
                   title: str, create_time: str) -> None:
        """标记主题为已同步
        
        Args:
            topic_id: 知识星球主题ID
            wordpress_id: WordPress文章ID
            title: 文章标题
            create_time: 创建时间
        """
        self._state['synced_topics'][topic_id] = {
            'wordpress_id': wordpress_id,
            'title': title,
            'create_time': create_time,
            'sync_time': datetime.now().isoformat()
        }
        
    def get_last_sync_time(self) -> Optional[datetime]:
        """获取最后同步时间
        
        Returns:
            最后同步时间，如果没有则返回None
        """
        last_time = self._state.get('last_sync_time')
        if last_time:
            # 导入日期解析函数
            from content_processor import parse_datetime_safe
            return parse_datetime_safe(last_time)
        return None
        
    def update_last_sync_time(self, sync_time: Optional[datetime] = None) -> None:
        """更新最后同步时间
        
        Args:
            sync_time: 同步时间，默认为当前时间
        """
        if sync_time is None:
            sync_time = datetime.now()
        self._state['last_sync_time'] = sync_time.isoformat()
        
    def add_sync_record(self, record: Dict[str, Any]) -> None:
        """添加同步记录
        
        Args:
            record: 同步记录，包含成功数、失败数等信息
        """
        # 添加时间戳
        record['timestamp'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self._state['sync_history'].append(record)
        
        # 只保留最近10次记录
        if len(self._state['sync_history']) > 10:
            self._state['sync_history'] = self._state['sync_history'][-10:]
            
    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计信息
        
        Returns:
            统计信息
        """
        total_synced = len(self._state['synced_topics'])
        last_sync = self.get_last_sync_time()
        
        # 计算最近一次同步的统计
        recent_stats = None
        if self._state['sync_history']:
            recent_stats = self._state['sync_history'][-1]
            
        return {
            'total_synced': total_synced,
            'last_sync_time': last_sync.isoformat() if last_sync else None,
            'recent_sync': recent_stats
        }
        
    def get_synced_topics_list(self) -> List[Dict[str, Any]]:
        """获取已同步的主题列表
        
        Returns:
            已同步主题信息列表
        """
        topics = []
        for topic_id, info in self._state['synced_topics'].items():
            topic_info = info.copy()
            topic_info['topic_id'] = topic_id
            topics.append(topic_info)
            
        # 按同步时间倒序排序
        topics.sort(key=lambda x: x.get('sync_time', ''), reverse=True)
        return topics
        
    def clear_all(self) -> None:
        """清空所有同步记录（慎用）"""
        self._state = {
            'synced_topics': {},
            'last_sync_time': None,
            'sync_history': []
        }
        self.logger.warning("已清空所有同步记录")