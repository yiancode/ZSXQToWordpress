#!/usr/bin/env python3
"""
知识星球API客户端
负责与知识星球API进行交互，获取内容数据
"""
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging


class ZsxqAPIError(Exception):
    """知识星球API错误"""
    pass


class ZsxqClient:
    """知识星球API客户端"""
    
    BASE_URL = "https://api.zsxq.com/v2"
    
    def __init__(self, access_token: str, user_agent: str, group_id: str,
                 max_retries: int = 5, delay_seconds: int = 2):
        """初始化客户端
        
        Args:
            access_token: 访问令牌
            user_agent: 用户代理
            group_id: 群组ID
            max_retries: 最大重试次数
            delay_seconds: 请求延迟（秒）
        """
        self.access_token = access_token
        self.user_agent = user_agent
        self.group_id = group_id
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': f'zsxq_access_token={access_token}',
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8'
        })
        
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发起请求（带重试机制）
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 请求参数
            
        Returns:
            响应数据
        """
        last_error = None
        retry_delay = 1
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"发起请求: {method} {url}, 尝试 {attempt + 1}/{self.max_retries}")
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    data = response.json()
                    # 知识星球API可能不总是返回succeeded字段，需要检查code字段
                    if data.get('succeeded', True) and data.get('code', 0) != 401:
                        return data
                    else:
                        error_msg = data.get('msg') or data.get('error') or '未知错误'
                        if data.get('code') == 401:
                            raise ZsxqAPIError("认证失败，请检查access_token是否有效")
                        raise ZsxqAPIError(f"API返回错误: {error_msg}")
                        
                elif response.status_code == 401:
                    raise ZsxqAPIError("认证失败，请检查access_token是否有效")
                    
                elif response.status_code == 429:
                    self.logger.warning("触发频率限制，等待后重试")
                    time.sleep(retry_delay * 2)
                    retry_delay *= 2
                    continue
                    
                else:
                    response.raise_for_status()
                    
            except requests.RequestException as e:
                last_error = e
                self.logger.warning(f"请求失败: {e}, 等待 {retry_delay}秒后重试")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # 指数退避，最多60秒
                
        raise ZsxqAPIError(f"请求失败，已重试{self.max_retries}次: {last_error}")
        
    def validate_connection(self) -> bool:
        """验证连接是否有效
        
        Returns:
            是否连接成功
        """
        try:
            # 尝试获取主题列表来验证连接
            url = f"{self.BASE_URL}/groups/{self.group_id}/topics"
            params = {'count': 1}
            self._make_request('GET', url, params=params)
            return True
        except Exception as e:
            self.logger.error(f"验证连接失败: {e}")
            return False
            
    def get_topics(self, count: int = 20, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取主题列表
        
        Args:
            count: 获取数量
            end_time: 结束时间（用于分页）
            
        Returns:
            主题列表
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/topics"
        params = {
            'count': min(count, 50)  # API限制最多50条，移除scope参数
        }
        
        if end_time:
            params['end_time'] = end_time
            
        response = self._make_request('GET', url, params=params)
        topics = response.get('resp_data', {}).get('topics', [])
        
        # 添加请求延迟，避免频率限制
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return topics
        
    def get_all_topics(self, batch_size: int = 20, 
                      start_time: Optional[datetime] = None,
                      max_topics: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有主题（支持分页）
        
        Args:
            batch_size: 每批获取数量
            start_time: 开始时间（用于增量同步）
            max_topics: 最大获取数量（用于测试）
            
        Returns:
            所有主题列表
        """
        all_topics = []
        end_time = None
        total_fetched = 0
        
        while True:
            # 检查是否达到最大数量限制
            if max_topics and len(all_topics) >= max_topics:
                self.logger.info(f"已达到最大获取数量 {max_topics}，停止获取")
                break
                
            # 计算本次批次大小
            current_batch_size = batch_size
            if max_topics:
                remaining = max_topics - len(all_topics)
                current_batch_size = min(batch_size, remaining)
                
            self.logger.info(f"获取第 {total_fetched + 1} - {total_fetched + current_batch_size} 条内容")
            topics = self.get_topics(count=current_batch_size, end_time=end_time)
            
            if not topics:
                break
                
            # 过滤开始时间之前的内容
            if start_time:
                filtered_topics = []
                for topic in topics:
                    create_time_str = topic.get('create_time', '')
                    if create_time_str:
                        create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        if create_time <= start_time:
                            # 遇到更早的内容，停止获取
                            self.logger.info(f"遇到早于 {start_time} 的内容，停止获取")
                            all_topics.extend(filtered_topics)
                            return all_topics
                    filtered_topics.append(topic)
                topics = filtered_topics
                
            all_topics.extend(topics)
            total_fetched += len(topics)
            
            # 获取最后一条的时间作为下一页的结束时间
            if len(topics) < batch_size:
                # 没有更多内容了
                break
                
            last_topic = topics[-1]
            end_time = last_topic.get('create_time')
            if not end_time:
                break
                
            self.logger.info(f"已获取 {total_fetched} 条内容，继续获取...")
            
        self.logger.info(f"总共获取了 {len(all_topics)} 条内容")
        return all_topics
        
    def get_topic_detail(self, topic_id: str) -> Dict[str, Any]:
        """获取主题详情
        
        Args:
            topic_id: 主题ID
            
        Returns:
            主题详情
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/topics/{topic_id}"
        response = self._make_request('GET', url)
        
        # 添加请求延迟
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return response.get('resp_data', {}).get('topic', {})