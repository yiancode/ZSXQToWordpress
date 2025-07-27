#!/usr/bin/env python3
"""
日志安全模块
负责过滤日志中的敏感信息
"""
import re
import logging
from typing import List, Dict, Any


class SensitiveFilter(logging.Filter):
    """敏感信息过滤器"""
    
    def __init__(self, patterns: List[str] = None):
        """初始化过滤器
        
        Args:
            patterns: 需要过滤的敏感信息模式列表
        """
        super().__init__()
        self.patterns = patterns or []
        self._init_default_patterns()
        
    def _init_default_patterns(self):
        """初始化默认的敏感信息模式"""
        default_patterns = [
            # API密钥和令牌
            (r'(access_token|token|api_key|apikey)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1=***'),
            (r'(secret_key|secret|password|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'\1=***'),
            
            # WordPress密码
            (r'(password=)([^&\s]+)', r'\1***'),
            
            # URL中的认证信息
            (r'(https?://)([^:]+):([^@]+)@', r'\1***:***@'),
            
            # Cookie中的access_token
            (r'(Cookie:\s*zsxq_access_token=)([^;\s]+)', r'\1***'),
            
            # 七牛云密钥
            (r'(access_key|secret_key)(["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1\2***'),
            
            # IP地址（可选）
            # (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '***.***.***'),
            
            # 邮箱地址（可选）
            # (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***@***.***'),
        ]
        
        self.patterns.extend(default_patterns)
        
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            是否通过过滤
        """
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.patterns:
                msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
            record.msg = msg
            
        # 处理args中的敏感信息
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.patterns:
                    arg_str = re.sub(pattern, replacement, arg_str, flags=re.IGNORECASE)
                filtered_args.append(arg_str)
            record.args = tuple(filtered_args)
            
        return True


class SafeLogger:
    """安全日志记录器工厂"""
    
    @staticmethod
    def setup_safe_logging(logger_name: str = None, 
                          level: int = logging.INFO,
                          additional_patterns: List[str] = None) -> logging.Logger:
        """设置安全的日志记录器
        
        Args:
            logger_name: 日志记录器名称
            level: 日志级别
            additional_patterns: 额外的敏感信息模式
            
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(logger_name)
        
        # 添加敏感信息过滤器
        sensitive_filter = SensitiveFilter(additional_patterns)
        
        # 应用过滤器到所有处理器
        for handler in logger.handlers:
            handler.addFilter(sensitive_filter)
            
        # 如果没有处理器，添加默认处理器
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.addFilter(sensitive_filter)
            logger.addHandler(handler)
            
        logger.setLevel(level)
        return logger


def mask_sensitive_dict(data: Dict[str, Any], 
                       sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """掩码字典中的敏感信息
    
    Args:
        data: 原始字典
        sensitive_keys: 敏感键列表
        
    Returns:
        掩码后的字典副本
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'pwd', 'secret', 'token', 'key', 
            'access_token', 'secret_key', 'api_key'
        ]
    
    masked_data = {}
    for key, value in data.items():
        if any(sk in key.lower() for sk in sensitive_keys):
            if isinstance(value, str) and value:
                masked_data[key] = '***'
            else:
                masked_data[key] = value
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_dict(value, sensitive_keys)
        else:
            masked_data[key] = value
            
    return masked_data