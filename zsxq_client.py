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
from interfaces import ContentClient


class ZsxqAPIError(Exception):
    """知识星球API错误"""
    pass


class ZsxqClient(ContentClient):
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
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json; charset=utf-8',
            'Origin': 'https://wx.zsxq.com',
            'Referer': 'https://wx.zsxq.com/',
            'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
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
                        error_code = data.get('code', 0)
                        self.logger.error(f"API响应错误，完整响应: {data}")
                        if error_code == 401:
                            raise ZsxqAPIError("认证失败，请检查access_token是否有效")
                        elif error_code == 1059:
                            # 1059错误通常是分页相关的临时错误，允许上层处理重试
                            raise ZsxqAPIError(f"API返回错误(code:{error_code}): {error_msg}")
                        else:
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
    
    def close(self) -> None:
        """关闭连接并清理资源"""
        if hasattr(self, 'session') and self.session:
            self.session.close()
            self.logger.info("知识星球客户端连接已关闭")
    
    def get_content(self, content_id: str) -> Dict[str, Any]:
        """获取单个内容（实现接口方法）
        
        Args:
            content_id: 内容ID
            
        Returns:
            内容数据
        """
        return self.get_topic_detail(content_id)
    
    def get_all_content(self, 
                       batch_size: int = 20,
                       start_time: Optional[Any] = None,
                       max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有内容（实现接口方法）
        
        Args:
            batch_size: 每批次大小
            start_time: 开始时间
            max_items: 最大数量
            
        Returns:
            内容列表
        """
        return self.get_all_topics(
            batch_size=batch_size,
            start_time=start_time,
            max_topics=max_items
        )
            
    def get_topics(self, count: int = 20, end_time: Optional[str] = None, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取主题列表
        
        Args:
            count: 获取数量
            end_time: 结束时间（用于分页）
            scope: 筛选范围 (e.g., "all", "digests")
            
        Returns:
            主题列表
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/topics"
        params = {
            'count': min(count, 50)
        }

        if scope:
            params['scope'] = scope
        
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
                       max_topics: Optional[int] = None,
                       scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有主题（支持分页）
        
        Args:
            batch_size: 每批获取数量
            start_time: 开始时间（用于增量同步）
            max_topics: 最大获取数量（用于测试）
            scope: 筛选范围 (e.g., "all", "digests")
            
        Returns:
            所有主题列表
        """
        all_topics = []
        end_time = None
        total_fetched = 0
        
        log_prefix = f"范围 '{scope}': " if scope else ""
        
        while True:
            # 检查是否达到最大数量限制
            if max_topics and len(all_topics) >= max_topics:
                self.logger.info(f"{log_prefix}已达到最大获取数量 {max_topics}，停止获取")
                break
                
            # 计算本次批次大小，确保不小于20（除非剩余数量不足20）
            remaining = max_topics - len(all_topics) if max_topics else float('inf')
            current_batch_size = max(20, min(batch_size, remaining)) if remaining >= 20 else remaining
            
            if current_batch_size <= 0:
                break
                
            self.logger.info(f"{log_prefix}获取第 {total_fetched + 1} - {total_fetched + current_batch_size} 条内容")
            # 多重重试机制
            topics = None
            for retry_attempt in range(3):  # 最多重试3次
                try:
                    topics = self.get_topics(count=int(current_batch_size), end_time=end_time, scope=scope)
                    break  # 成功获取，跳出重试循环
                except ZsxqAPIError as e:
                    if 'code' in str(e) and '1059' in str(e):
                        retry_delay = (retry_attempt + 1) * 15  # 递增延迟：15s, 30s, 45s
                        self.logger.warning(f"{log_prefix}API分页错误(1059)，第 {retry_attempt + 1}/3 次重试，等待 {retry_delay}秒...")
                        
                        if retry_attempt < 2:  # 不是最后一次重试
                            time.sleep(retry_delay)
                        else:
                            self.logger.error(f"{log_prefix}连续重试失败，停止获取。已获取 {len(all_topics)} 条内容")
                            return all_topics  # 直接返回已获取的内容
                    else:
                        self.logger.error(f"{log_prefix}API请求失败: {e}")
                        raise
                        
            # 检查是否成功获取到数据
            if topics is None:
                self.logger.warning(f"{log_prefix}未能获取到数据，停止获取")
                break
            
            if not topics:
                break
                
            # 过滤开始时间之前的内容
            if start_time:
                filtered_topics = []
                for topic in topics:
                    create_time_str = topic.get('create_time', '')
                    if create_time_str:
                        create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        # 确保start_time也是aware datetime
                        if start_time.tzinfo is None:
                            # 如果start_time是naive，假设它是UTC时间
                            from datetime import timezone
                            start_time = start_time.replace(tzinfo=timezone.utc)
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
    
    def get_columns(self) -> List[Dict[str, Any]]:
        """获取群组中的所有专栏列表
        
        Returns:
            专栏列表
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/columns"
        response = self._make_request('GET', url)
        
        columns = response.get('resp_data', {}).get('columns', [])
        
        # 解码专栏名称中的Unicode字符
        for column in columns:
            if 'name' in column:
                try:
                    # 将 \uXXXX 格式的Unicode字符解码
                    column['name'] = column['name'].encode().decode('unicode_escape')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    # 如果解码失败，保持原始值
                    pass
        
        # 添加请求延迟
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return columns
    
    def get_topics_by_column(self, column_id: str, count: int = 20, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """按专栏获取主题列表
        
        Args:
            column_id: 专栏ID
            count: 获取数量
            end_time: 结束时间（用于分页）
            
        Returns:
            主题列表
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/topics"
        params = {
            'count': min(count, 50),  # API限制最多50条
            'scope': f'by_column_id_{column_id}'
        }
        
        if end_time:
            params['end_time'] = end_time
            
        response = self._make_request('GET', url, params=params)
        topics = response.get('resp_data', {}).get('topics', [])
        
        # 添加请求延迟，避免频率限制
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return topics
    
    def get_all_topics_by_column(self, column_id: str, batch_size: int = 20,
                                start_time: Optional[datetime] = None,
                                max_topics: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指定专栏下的所有主题（支持分页）
        
        Args:
            column_id: 专栏ID
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
                
            # 计算本次批次大小，确保不小于20（除非剩余数量不足20）
            remaining = max_topics - len(all_topics) if max_topics else float('inf')
            current_batch_size = max(20, min(batch_size, remaining)) if remaining >= 20 else remaining
            
            if current_batch_size <= 0:
                break
                
            self.logger.info(f"获取专栏 {column_id} 第 {total_fetched + 1} - {total_fetched + current_batch_size} 条内容")
            try:
                topics = self.get_topics_by_column(column_id, count=current_batch_size, end_time=end_time)
            except ZsxqAPIError as e:
                if 'code' in str(e) and '1059' in str(e):
                    self.logger.warning(f"API分页错误，停止获取。已获取 {len(all_topics)} 条内容")
                    break
                else:
                    raise
            
            if not topics:
                break
                
            # 过滤开始时间之前的内容
            if start_time:
                filtered_topics = []
                for topic in topics:
                    create_time_str = topic.get('create_time', '')
                    if create_time_str:
                        create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        # 确保start_time也是aware datetime
                        if start_time.tzinfo is None:
                            # 如果start_time是naive，假设它是UTC时间
                            from datetime import timezone
                            start_time = start_time.replace(tzinfo=timezone.utc)
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
                
            self.logger.info(f"专栏 {column_id} 已获取 {total_fetched} 条内容，继续获取...")
            
        self.logger.info(f"专栏 {column_id} 总共获取了 {len(all_topics)} 条内容")
        return all_topics
    
    def get_menus(self) -> List[Dict[str, Any]]:
        """获取星球主页菜单（Tab标签）
        
        Returns:
            菜单列表
        """
        url = f"{self.BASE_URL}/groups/{self.group_id}/menus"
        response = self._make_request('GET', url)
        
        menus = response.get('resp_data', {}).get('menus', [])
        
        # 添加请求延迟
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return menus
    
    def get_columns_mapping(self) -> Dict[str, str]:
        """获取专栏名称到ID的映射字典
        
        Returns:
            专栏名称到ID的映射 {专栏名称: 专栏ID}
        """
        try:
            columns = self.get_columns()
            mapping = {}
            
            for column in columns:
                column_id = str(column.get('column_id', ''))
                column_name = column.get('name', '')
                
                if column_id and column_name:
                    mapping[column_name] = column_id
                    self.logger.debug(f"发现专栏: {column_name} -> {column_id}")
            
            self.logger.info(f"成功获取 {len(mapping)} 个专栏映射")
            return mapping
            
        except Exception as e:
            self.logger.error(f"获取专栏映射失败: {e}")
            return {}

    def get_topics_by_hashtag(self, hashtag_id: str, count: int = 20, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """按标签获取主题列表
        
        Args:
            hashtag_id: 标签ID
            count: 获取数量
            end_time: 结束时间（用于分页）
            
        Returns:
            主题列表
        """
        url = f"{self.BASE_URL}/hashtags/{hashtag_id}/topics"
        params = {
            'count': min(count, 50)
        }
        
        if end_time:
            params['end_time'] = end_time
            
        response = self._make_request('GET', url, params=params)
        topics = response.get('resp_data', {}).get('topics', [])
        
        # 添加请求延迟
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
            
        return topics

    def get_all_topics_by_hashtag(self, hashtag_id: str, batch_size: int = 20,
                                 start_time: Optional[datetime] = None,
                                 max_topics: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指定标签下的所有主题（支持分页）
        
        Args:
            hashtag_id: 标签ID
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
                
            # 计算本次批次大小，确保不小于20（除非剩余数量不足20）
            remaining = max_topics - len(all_topics) if max_topics else float('inf')
            current_batch_size = max(20, min(batch_size, remaining)) if remaining >= 20 else remaining
            
            if current_batch_size <= 0:
                break
                
            self.logger.info(f"获取标签 {hashtag_id} 第 {total_fetched + 1} - {total_fetched + current_batch_size} 条内容")
            try:
                topics = self.get_topics_by_hashtag(hashtag_id, count=current_batch_size, end_time=end_time)
            except ZsxqAPIError as e:
                if 'code' in str(e) and '1059' in str(e):
                    self.logger.warning(f"API分页错误，停止获取。已获取 {len(all_topics)} 条内容")
                    break
                else:
                    raise
            
            if not topics:
                break
                
            # 过滤开始时间之前的内容
            if start_time:
                filtered_topics = []
                for topic in topics:
                    create_time_str = topic.get('create_time', '')
                    if create_time_str:
                        create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                        # 确保start_time也是aware datetime
                        if start_time.tzinfo is None:
                            from datetime import timezone
                            start_time = start_time.replace(tzinfo=timezone.utc)
                        if create_time <= start_time:
                            self.logger.info(f"遇到早于 {start_time} 的内容，停止获取")
                            all_topics.extend(filtered_topics)
                            return all_topics
                    filtered_topics.append(topic)
                topics = filtered_topics
                
            all_topics.extend(topics)
            total_fetched += len(topics)
            
            # 获取最后一条的时间作为下一页的结束时间
            if len(topics) < batch_size:
                break
                
            last_topic = topics[-1]
            end_time = last_topic.get('create_time')
            if not end_time:
                break
                
            self.logger.info(f"标签 {hashtag_id} 已获取 {total_fetched} 条内容，继续获取...")
            
        self.logger.info(f"标签 {hashtag_id} 总共获取了 {len(all_topics)} 条内容")
        return all_topics