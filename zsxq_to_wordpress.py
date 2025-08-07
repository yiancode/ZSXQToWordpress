#!/usr/bin/env python3
"""
知识星球到WordPress同步工具
主程序入口
"""
import os
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from config_manager import Config, ConfigError
from zsxq_client import ZsxqClient, ZsxqAPIError
from wordpress_client import WordPressClient, WordPressError
from qiniu_uploader import QiniuUploader
from content_processor import ContentProcessor
from sync_state import SyncState, SyncStateError
from log_utils import SensitiveFilter


def setup_logging(verbose: bool = False):
    """设置日志配置
    
    Args:
        verbose: 是否显示详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建敏感信息过滤器
    sensitive_filter = SensitiveFilter()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    console_handler.addFilter(sensitive_filter)  # 添加过滤器
    
    # 文件处理器
    file_handler = logging.FileHandler('zsxq_sync.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(sensitive_filter)  # 添加过滤器
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 调整第三方库日志级别，避免兼容性问题
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('urllib3.util.retry').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('qiniu').setLevel(logging.INFO)
    

class ZsxqToWordPressSync:
    """知识星球到WordPress同步器"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化同步器
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = Config(config_path)
        try:
            self.config.load()
            self.logger.info("配置文件加载成功")
        except ConfigError as e:
            self.logger.error(f"配置错误: {e}")
            sys.exit(1)
            
        # 初始化各个组件
        self._init_components()
        
        # 并发控制
        self._sync_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
    def _init_components(self):
        """初始化各个组件"""
        # 知识星球客户端
        self.zsxq_client = ZsxqClient(
            access_token=self.config.zsxq['access_token'],
            user_agent=self.config.zsxq['user_agent'],
            group_id=self.config.zsxq['group_id'],
            max_retries=self.config.sync['max_retries'],
            delay_seconds=self.config.sync['delay_seconds']
        )
        
        # WordPress客户端
        self.wp_client = WordPressClient(
            url=self.config.wordpress['url'],
            username=self.config.wordpress['username'],
            password=self.config.wordpress['password'],
            verify_ssl=self.config.wordpress.get('verify_ssl', True)
        )
        
        # 七牛云上传器（可选）
        self.qiniu_uploader = None
        if self.config.has_qiniu():
            self.qiniu_uploader = QiniuUploader(
                access_key=self.config.qiniu['access_key'],
                secret_key=self.config.qiniu['secret_key'],
                bucket=self.config.qiniu['bucket'],
                domain=self.config.qiniu['domain']
            )
            self.logger.info("七牛云配置已启用")
        else:
            self.logger.warning("七牛云未配置，图片将使用原始链接")
            
        # 内容处理器
        self.content_processor = ContentProcessor(self.config.data, self.zsxq_client)
        
        # 同步状态管理
        self.sync_state = SyncState()
        
    def validate_connections(self) -> bool:
        """验证所有连接
        
        Returns:
            是否所有连接都有效
        """
        self.logger.info("开始验证连接...")
        
        # 验证知识星球连接
        if not self.zsxq_client.validate_connection():
            self.logger.error("无法连接到知识星球，请检查access_token和group_id")
            return False
        self.logger.info("✓ 知识星球连接成功")
        
        # 验证WordPress连接
        if not self.wp_client.validate_connection():
            self.logger.error("无法连接到WordPress，请检查URL、用户名和密码")
            return False
        self.logger.info("✓ WordPress连接成功")
        
        # 验证七牛云（如果配置了）
        if self.qiniu_uploader:
            if not self.qiniu_uploader.validate_config():
                self.logger.warning("七牛云配置验证失败，将使用原始图片链接")
                self.qiniu_uploader = None
            else:
                self.logger.info("✓ 七牛云配置验证成功")
                
        return True
        
    def sync_topic(self, topic: Dict[str, Any]) -> bool:
        """同步单个主题
        
        Args:
            topic: 主题数据
            
        Returns:
            是否同步成功
        """
        topic_id = str(topic.get('topic_id', ''))
        
        # 检查是否已同步
        if self.sync_state.is_synced(topic_id):
            self.logger.info(f"主题 {topic_id} 已同步，跳过")
            return False
            
        try:
            # 获取配置
            fetch_article_details = self.config.sync.get('fetch_article_details', True)
            detail_fetch_retries = self.config.sync.get('detail_fetch_retries', 2)
            
            # 处理内容 - 对文章类型获取详细信息
            content_type = self.content_processor._determine_content_type(topic)
            if content_type == 'article' and fetch_article_details:
                topic_id = str(topic.get('topic_id', ''))
                self.logger.info(f"检测到文章类型，获取详细内容: {topic_id}")
                
                # 获取详细的主题信息（带重试机制）
                for attempt in range(detail_fetch_retries):
                    try:
                        detailed_topic = self.zsxq_client.get_topic_detail(topic_id)
                        if detailed_topic:
                            # 使用详细信息替换原始topic数据
                            topic = detailed_topic
                            self.logger.info(f"成功获取详细内容，内容长度: {len(str(detailed_topic))}")
                            break
                        else:
                            self.logger.warning(f"无法获取主题 {topic_id} 的详细信息，使用原始数据")
                            break
                    except Exception as e:
                        if attempt == detail_fetch_retries - 1:
                            self.logger.error(f"获取主题 {topic_id} 详细信息失败（已重试{detail_fetch_retries}次）: {e}，使用原始数据")
                        else:
                            self.logger.warning(f"获取主题 {topic_id} 详细信息失败（第{attempt+1}次尝试）: {e}")
                            time.sleep(1)  # 重试前等待1秒
            
            # 处理内容
            article = self.content_processor.process_topic(topic)
            self.logger.info(f"处理主题: {article['title']}")

            # 应用来自 sync_target 的分类覆盖
            sync_target_info = topic.get('_sync_target', {})
            if sync_target_info.get('category_override'):
                override_category = sync_target_info['category_override']
                article['categories'] = [override_category]
                self.logger.info(f"应用分类覆盖: {override_category}")
            
            # 检查WordPress中是否已存在相同标题的文章
            if self.wp_client.post_exists(article['title']):
                self.logger.warning(f"WordPress中已存在相同标题的文章: {article['title']}")
                # 仍然标记为已同步，避免下次重复检查
                self.sync_state.mark_synced(
                    topic_id,
                    'duplicate',
                    article['title'],
                    article['create_time']
                )
                return False
                
            # 处理图片 - 使用批量处理优化
            processed_images = {}
            
            if article['images'] and self.qiniu_uploader:
                self.logger.info(f"批量处理 {len(article['images'])} 张图片...")
                # 使用批量处理方法
                processed_images = self.qiniu_uploader.process_images_batch(
                    article['images'],
                    max_workers=min(3, len(article['images']))  # 动态调整并发数
                )
                    
            # 格式化最终内容
            final_content = self.content_processor.format_article_with_images(
                article, processed_images
            )
            
            # 发布到WordPress - 根据内容类型选择创建方法
            content_type = article.get('content_type', 'article')
            
            if content_type == 'short_content':
                # 创建主题类型内容 - 转换为WordPress客户端期望的格式
                article_for_wp = {
                    'title': article['title'],
                    'content': final_content,
                    'categories': article['categories'],
                    'tags': article['tags'],
                    'content_type': 'topic',  # WordPress客户端期望的类型
                    'post_type': article.get('post_type', 'post'),  # 传递post_type配置
                    'create_time': article.get('create_time', '')
                }
                wp_id = self.wp_client._create_topic(article_for_wp)
            else:
                # 创建文章类型
                article_for_wp = {
                    'title': article['title'],
                    'content': final_content,
                    'categories': article['categories'],
                    'tags': article['tags'],
                    'content_type': 'article',
                    'post_type': article.get('post_type', 'post'),  # 传递post_type配置
                    'create_time': article.get('create_time', '')
                }
                wp_id = self.wp_client._create_article(article_for_wp)
            
            # 标记为已同步
            self.sync_state.mark_synced(
                topic_id,
                wp_id,
                article['title'],
                article['create_time']
            )
            
            self.logger.info(f"✓ 成功同步: {article['title']} (WP ID: {wp_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"同步主题 {topic_id} 时发生错误: {e}")
            return False
            
    def _fetch_all_target_topics(self, start_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """根据sync_targets配置获取所有主题"""
        sync_targets = self.config.data.get('content_mapping', {}).get('sync_targets', [])
        all_topics = []
        seen_topic_ids = set()

        max_topics_per_target = None
        if os.environ.get('ZSXQ_TEST_MODE'):
            max_topics_per_target = int(os.environ.get('ZSXQ_MAX_TOPICS', '2'))
            self.logger.info(f"测试模式：每个目标最多同步 {max_topics_per_target} 条内容")

        for target in sync_targets:
            if not target.get('enabled'):
                continue

            target_type = target.get('type')
            target_value = target.get('value')
            target_name = target.get('name', f"{target_type}:{target_value}")
            self.logger.info(f"开始处理同步目标: {target_name}")

            try:
                topics = []
                if target_type == 'scope':
                    topics = self.zsxq_client.get_all_topics(
                        batch_size=self.config.sync['batch_size'],
                        start_time=start_time,
                        max_topics=max_topics_per_target,
                        scope=target_value
                    )
                elif target_type == 'column':
                    topics = self.zsxq_client.get_all_topics_by_column(
                        column_id=target_value,
                        batch_size=self.config.sync['batch_size'],
                        start_time=start_time,
                        max_topics=max_topics_per_target
                    )
                elif target_type == 'hashtag':
                    topics = self.zsxq_client.get_all_topics_by_hashtag(
                        hashtag_id=target_value,
                        batch_size=self.config.sync['batch_size'],
                        start_time=start_time,
                        max_topics=max_topics_per_target
                    )
                
                for topic in topics:
                    topic_id = str(topic.get('topic_id'))
                    if topic_id not in seen_topic_ids:
                        topic['_sync_target'] = target  # 附加来源信息
                        all_topics.append(topic)
                        seen_topic_ids.add(topic_id)

                self.logger.info(f"目标 {target_name} 获取到 {len(topics)} 个新主题")

            except ZsxqAPIError as e:
                self.logger.error(f"从目标 {target_name} 获取主题失败: {e}")
                continue
        
        # 按创建时间降序排序
        all_topics.sort(key=lambda x: x.get('create_time', ''), reverse=True)
        self.logger.info(f"所有目标总共获取到 {len(all_topics)} 个去重后的主题")
        return all_topics

    def sync_full(self):
        """执行全量同步"""
        self.logger.info("开始执行全量同步...")
        
        try:
            topics = self._fetch_all_target_topics()
        except Exception as e:
            self.logger.error(f"获取所有目标内容时发生严重错误: {e}")
            return
            
        # 同步统计
        stats = {
            'total': len(topics),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 逐个同步
        for i, topic in enumerate(topics, 1):
            self.logger.info(f"处理进度: {i}/{stats['total']}")
            
            result = self.sync_topic(topic)
            if result:
                stats['success'] += 1
            elif self.sync_state.is_synced(str(topic.get('topic_id', ''))):
                stats['skipped'] += 1
            else:
                stats['failed'] += 1
                
            # 保存状态（每处理10个或最后一个时保存）
            if i % 10 == 0 or i == stats['total']:
                self.sync_state.save()
                
        # 更新最后同步时间
        self.sync_state.update_last_sync_time()
        
        # 记录同步结果
        self.sync_state.add_sync_record(stats)
        self.sync_state.save()
        
        # 显示统计
        self.logger.info(
            f"\n全量同步完成！\n"
            f"总计: {stats['total']}\n"
            f"成功: {stats['success']}\n"
            f"跳过: {stats['skipped']}\n"
            f"失败: {stats['failed']}"
        )
        
    def sync_incremental(self):
        """执行增量同步"""
        self.logger.info("开始执行增量同步...")
        
        # 获取最后同步时间
        last_sync_time = self.sync_state.get_last_sync_time()
        if not last_sync_time:
            self.logger.warning("没有找到上次同步时间，将执行全量同步")
            return self.sync_full()
            
        self.logger.info(f"上次同步时间: {last_sync_time}")
        
        # 获取新内容
        try:
            topics = self._fetch_all_target_topics(start_time=last_sync_time)
            self.logger.info(f"增量同步：获取到 {len(topics)} 个新主题")
        except Exception as e:
            self.logger.error(f"获取所有目标内容时发生严重错误: {e}")
            return
            
        if not topics:
            self.logger.info("没有新内容需要同步")
            return
            
        # 同步统计
        stats = {
            'total': len(topics),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 逐个同步
        for i, topic in enumerate(topics, 1):
            self.logger.info(f"处理进度: {i}/{stats['total']}")
            
            result = self.sync_topic(topic)
            if result:
                stats['success'] += 1
            elif self.sync_state.is_synced(str(topic.get('topic_id', ''))):
                stats['skipped'] += 1
            else:
                stats['failed'] += 1
                
            # 保存状态
            if i % 10 == 0 or i == stats['total']:
                self.sync_state.save()
                
        # 更新最后同步时间
        self.sync_state.update_last_sync_time()
        
        # 记录同步结果
        self.sync_state.add_sync_record(stats)
        self.sync_state.save()
        
        # 显示统计
        self.logger.info(
            f"\n增量同步完成！\n"
            f"总计: {stats['total']}\n"
            f"成功: {stats['success']}\n"
            f"跳过: {stats['skipped']}\n"
            f"失败: {stats['failed']}"
        )
        
    def sync_topic_safe(self, topic: Dict[str, Any], stats: Dict[str, int]) -> bool:
        """线程安全的同步单个主题
        
        Args:
            topic: 主题数据
            stats: 统计数据（线程共享）
            
        Returns:
            是否同步成功
        """
        topic_id = str(topic.get('topic_id', ''))
        
        # 使用锁保护状态检查和更新
        with self._sync_lock:
            if self.sync_state.is_synced(topic_id):
                self.logger.info(f"主题 {topic_id} 已同步，跳过")
                with self._stats_lock:
                    stats['skipped'] += 1
                return False
        
        try:
            result = self.sync_topic(topic)
            
            # 更新统计
            with self._stats_lock:
                if result:
                    stats['success'] += 1
                else:
                    if self.sync_state.is_synced(topic_id):
                        stats['skipped'] += 1
                    else:
                        stats['failed'] += 1
                        
            return result
            
        except Exception as e:
            self.logger.error(f"同步主题 {topic_id} 时发生错误: {e}")
            with self._stats_lock:
                stats['failed'] += 1
            return False
            
    def sync_full_concurrent(self, max_workers: int = 3):
        """执行并发全量同步
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.logger.info(f"开始执行并发全量同步，最大工作线程数: {max_workers}")
        
        # 获取所有主题
        try:
            topics = self._fetch_all_target_topics()
        except Exception as e:
            self.logger.error(f"获取所有目标内容时发生严重错误: {e}")
            return
            
        # 同步统计（线程共享）
        stats = {
            'total': len(topics),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = []
            for i, topic in enumerate(topics):
                future = executor.submit(self.sync_topic_safe, topic, stats)
                futures.append((future, i + 1, topic))
                
            # 处理完成的任务
            for future, index, topic in futures:
                try:
                    future.result()
                    self.logger.info(f"进度: {index}/{stats['total']} - "
                                   f"成功: {stats['success']}, "
                                   f"失败: {stats['failed']}, "
                                   f"跳过: {stats['skipped']}")
                    
                    # 定期保存状态
                    if index % 10 == 0:
                        with self._sync_lock:
                            self.sync_state.save()
                            
                except Exception as e:
                    self.logger.error(f"处理任务时发生错误: {e}")
                    
        # 更新最后同步时间
        self.sync_state.update_last_sync_time()
        
        # 记录同步结果
        self.sync_state.add_sync_record(stats)
        self.sync_state.save()
        
        # 显示统计
        self.logger.info(
            f"\n并发全量同步完成！\n"
            f"总计: {stats['total']}\n"
            f"成功: {stats['success']}\n"
            f"跳过: {stats['skipped']}\n"
            f"失败: {stats['failed']}"
        )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='知识星球到WordPress内容同步工具'
    )
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental', 'concurrent'],
        default='incremental',
        help='同步模式：full(全量) 或 incremental(增量) 或 concurrent(并发全量)'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='配置文件路径'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='并发模式下的最大工作线程数（默认: 3）'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='跳过连接验证直接开始同步（用于调试）'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 创建同步器
    syncer = ZsxqToWordPressSync(args.config)
    
    # 验证连接（除非指定跳过）
    if not args.skip_validation:
        if not syncer.validate_connections():
            logging.error("连接验证失败，请检查配置")
            sys.exit(1)
    else:
        logging.warning("已跳过连接验证，直接开始同步")
        
    # 执行同步
    try:
        if args.mode == 'full':
            syncer.sync_full()
        elif args.mode == 'concurrent':
            syncer.sync_full_concurrent(max_workers=args.workers)
        else:
            syncer.sync_incremental()
    except KeyboardInterrupt:
        logging.warning("\n同步被用户中断")
    except Exception as e:
        logging.error(f"同步过程中发生错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()