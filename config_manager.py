#!/usr/bin/env python3
"""
配置管理模块
负责加载、验证和管理配置文件
支持环境变量覆盖敏感配置
"""
import json
import os
from typing import Dict, Any, Optional
import logging


class ConfigError(Exception):
    """配置相关的错误"""
    pass


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def load(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise ConfigError(f"配置文件不存在: {self.config_path}")
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}")
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
            
        self._validate()
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖配置"""
        # 知识星球配置
        if 'ZSXQ_ACCESS_TOKEN' in os.environ:
            self._config.setdefault('zsxq', {})['access_token'] = os.environ['ZSXQ_ACCESS_TOKEN']
            self.logger.info("使用环境变量 ZSXQ_ACCESS_TOKEN")
        
        if 'ZSXQ_GROUP_ID' in os.environ:
            self._config.setdefault('zsxq', {})['group_id'] = os.environ['ZSXQ_GROUP_ID']
            self.logger.info("使用环境变量 ZSXQ_GROUP_ID")
        
        # WordPress配置
        if 'WORDPRESS_URL' in os.environ:
            self._config.setdefault('wordpress', {})['url'] = os.environ['WORDPRESS_URL']
            self.logger.info("使用环境变量 WORDPRESS_URL")
            
        if 'WORDPRESS_USERNAME' in os.environ:
            self._config.setdefault('wordpress', {})['username'] = os.environ['WORDPRESS_USERNAME']
            self.logger.info("使用环境变量 WORDPRESS_USERNAME")
            
        if 'WORDPRESS_PASSWORD' in os.environ:
            self._config.setdefault('wordpress', {})['password'] = os.environ['WORDPRESS_PASSWORD']
            self.logger.info("使用环境变量 WORDPRESS_PASSWORD")
        
        if 'WORDPRESS_VERIFY_SSL' in os.environ:
            value = os.environ['WORDPRESS_VERIFY_SSL'].lower()
            self._config.setdefault('wordpress', {})['verify_ssl'] = value not in ['false', '0', 'no']
            self.logger.info(f"使用环境变量 WORDPRESS_VERIFY_SSL: {value}")
        
        # 七牛云配置
        if 'QINIU_ACCESS_KEY' in os.environ:
            self._config.setdefault('qiniu', {})['access_key'] = os.environ['QINIU_ACCESS_KEY']
            self.logger.info("使用环境变量 QINIU_ACCESS_KEY")
            
        if 'QINIU_SECRET_KEY' in os.environ:
            self._config.setdefault('qiniu', {})['secret_key'] = os.environ['QINIU_SECRET_KEY']
            self.logger.info("使用环境变量 QINIU_SECRET_KEY")
            
        if 'QINIU_BUCKET' in os.environ:
            self._config.setdefault('qiniu', {})['bucket'] = os.environ['QINIU_BUCKET']
            self.logger.info("使用环境变量 QINIU_BUCKET")
            
        if 'QINIU_DOMAIN' in os.environ:
            self._config.setdefault('qiniu', {})['domain'] = os.environ['QINIU_DOMAIN']
            self.logger.info("使用环境变量 QINIU_DOMAIN")
        
    def _validate(self) -> None:
        """验证配置的必要字段"""
        # 验证知识星球配置
        zsxq = self._config.get('zsxq', {})
        if not zsxq.get('access_token'):
            raise ConfigError("缺少知识星球 access_token")
        if not zsxq.get('group_id'):
            raise ConfigError("缺少知识星球 group_id")
        if not zsxq.get('user_agent'):
            raise ConfigError("缺少知识星球 user_agent")
            
        # 验证WordPress配置
        wp = self._config.get('wordpress', {})
        if not wp.get('url'):
            raise ConfigError("缺少WordPress URL")
        if not wp.get('username'):
            raise ConfigError("缺少WordPress用户名")
        if not wp.get('password'):
            raise ConfigError("缺少WordPress密码")
            
        # 验证同步配置
        sync = self._config.get('sync', {})
        if sync.get('batch_size', 20) <= 0:
            raise ConfigError("batch_size必须大于0")
        if sync.get('delay_seconds', 2) < 0:
            raise ConfigError("delay_seconds不能为负数")
        if sync.get('max_retries', 5) < 0:
            raise ConfigError("max_retries不能为负数")
            
    @property
    def zsxq(self) -> Dict[str, Any]:
        """获取知识星球配置"""
        return self._config.get('zsxq', {})
        
    @property
    def wordpress(self) -> Dict[str, Any]:
        """获取WordPress配置"""
        return self._config.get('wordpress', {})
        
    @property
    def qiniu(self) -> Dict[str, Any]:
        """获取七牛云配置"""
        return self._config.get('qiniu', {})
        
    @property
    def sync(self) -> Dict[str, Any]:
        """获取同步配置"""
        return self._config.get('sync', {
            'batch_size': 20,
            'delay_seconds': 2,
            'max_retries': 5
        })
        
    def has_qiniu(self) -> bool:
        """检查是否配置了七牛云"""
        qiniu = self.qiniu
        return all([
            qiniu.get('access_key'),
            qiniu.get('secret_key'),
            qiniu.get('bucket'),
            qiniu.get('domain')
        ])
        
    @property
    def data(self) -> Dict[str, Any]:
        """获取完整的配置数据"""
        return self._config