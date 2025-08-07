# 安全文档

知识星球到WordPress同步工具的安全配置和最佳实践指南。

## 目录

- [安全概述](#安全概述)
- [认证和授权](#认证和授权)
- [数据传输安全](#数据传输安全)
- [密钥管理](#密钥管理)
- [输入验证](#输入验证)
- [日志安全](#日志安全)
- [部署安全](#部署安全)
- [安全检查清单](#安全检查清单)

## 安全概述

### 安全威胁模型

本工具面临的主要安全威胁：

1. **认证凭据泄露**: access_token、密码等敏感信息
2. **中间人攻击**: 网络传输过程中的数据窃取
3. **注入攻击**: 恶意内容注入到WordPress
4. **权限滥用**: 过度的API访问权限
5. **日志泄露**: 日志文件中包含敏感信息

### 安全等级分类

- **机密信息**: access_token、密码、API密钥
- **敏感信息**: 用户名、群组ID、内容数据
- **公开信息**: 配置模板、文档、版本信息

## 认证和授权

### 知识星球认证

#### 安全的token获取

```python
# ❌ 不安全：硬编码token
access_token = "abcd1234_your_real_token"

# ✅ 安全：使用环境变量
import os
access_token = os.environ.get('ZSXQ_ACCESS_TOKEN')
if not access_token:
    raise ValueError("必须设置 ZSXQ_ACCESS_TOKEN 环境变量")
```

#### Token安全存储

```bash
# 设置严格的文件权限
chmod 600 ~/.env
chown $USER ~/.env

# .env文件内容
ZSXQ_ACCESS_TOKEN=your_token_here
ZSXQ_GROUP_ID=your_group_id
```

#### Token轮换策略

- 定期更换access_token（建议每30天）
- 使用不同的token用于不同环境（开发/测试/生产）
- 监控token使用情况，及时发现异常

### WordPress认证

#### 应用密码（推荐）

```json
{
  "wordpress": {
    "url": "https://your-site.com/xmlrpc.php",
    "username": "your_username",
    "password": "abcd efgh ijkl mnop",  // 应用密码格式
    "verify_ssl": true
  }
}
```

#### 双重认证支持

```python
class SecureWordPressClient(WordPressClient):
    def __init__(self, url, username, password, totp_secret=None):
        super().__init__(url, username, password)
        self.totp_secret = totp_secret
    
    def authenticate_with_2fa(self):
        if self.totp_secret:
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        return None
```

## 数据传输安全

### SSL/TLS配置

#### 强制HTTPS

```python
class SecureSession(requests.Session):
    def __init__(self):
        super().__init__()
        # 只允许HTTPS连接
        self.mount('http://', HTTPAdapter(max_retries=0))
        
        # 配置SSL上下文
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2
```

#### 证书验证

```python
# ❌ 危险：禁用SSL验证
requests.get(url, verify=False)

# ✅ 安全：启用SSL验证
requests.get(url, verify=True)

# ✅ 更安全：指定证书文件
requests.get(url, verify='/path/to/ca-bundle.crt')
```

#### SSL配置最佳实践

```python
import ssl
import urllib3

class SecureConfig:
    @staticmethod
    def setup_ssl_security():
        # 禁用不安全的SSL版本
        ssl.PROTOCOL_TLS_CLIENT.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # 配置安全的密码套件
        ssl.PROTOCOL_TLS_CLIENT.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM')
        
        # 只在开发环境禁用SSL警告
        if os.environ.get('ENVIRONMENT') == 'development':
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### 网络代理安全

```python
# 企业环境代理配置
proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'https://proxy.company.com:8080'
}

# 代理认证（如需要）
proxies_with_auth = {
    'http': 'http://user:pass@proxy.company.com:8080',
    'https': 'https://user:pass@proxy.company.com:8080'
}

session = requests.Session()
session.proxies.update(proxies)
```

## 密钥管理

### 环境变量管理

#### 安全的环境变量设置

```bash
# 生产环境
export ZSXQ_ACCESS_TOKEN="$(cat /etc/secrets/zsxq_token)"
export WORDPRESS_PASSWORD="$(cat /etc/secrets/wp_password)"

# 使用专用的secrets管理工具
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id zsxq/access-token --query SecretString --output text

# Azure Key Vault  
az keyvault secret show --vault-name MyVault --name zsxq-token --query value -o tsv

# HashiCorp Vault
vault kv get -field=access_token secret/zsxq
```

#### 配置文件加密

```python
from cryptography.fernet import Fernet

class EncryptedConfig:
    def __init__(self, key_file='config.key'):
        self.key = self._load_or_generate_key(key_file)
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self, key_file):
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
    
    def encrypt_config(self, config_data):
        encrypted = self.cipher.encrypt(json.dumps(config_data).encode())
        return encrypted
    
    def decrypt_config(self, encrypted_data):
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
```

### 密钥轮换

```python
class KeyRotationManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.rotation_interval = 30 * 24 * 3600  # 30天
    
    def should_rotate_keys(self):
        last_rotation = self.config_manager.get_last_key_rotation()
        if not last_rotation:
            return True
        return time.time() - last_rotation > self.rotation_interval
    
    def rotate_zsxq_token(self):
        # 实现token轮换逻辑
        # 1. 获取新token
        # 2. 验证新token有效性
        # 3. 更新配置
        # 4. 记录轮换时间
        pass
```

## 输入验证

### 内容过滤

```python
import html
import re
from urllib.parse import urlparse

class ContentSanitizer:
    # 危险的HTML标签
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'form', 
        'input', 'button', 'meta', 'link', 'style'
    ]
    
    # 危险的协议
    DANGEROUS_PROTOCOLS = ['javascript:', 'data:', 'vbscript:', 'about:']
    
    @classmethod
    def sanitize_html(cls, content):
        """清理HTML内容"""
        if not content:
            return content
        
        # HTML编码特殊字符
        content = html.escape(content, quote=False)
        
        # 移除危险标签
        for tag in cls.DANGEROUS_TAGS:
            pattern = f'<{tag}[^>]*>.*?</{tag}>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
            # 移除自闭合标签
            pattern = f'<{tag}[^>]*/?>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    @classmethod
    def validate_url(cls, url):
        """验证URL安全性"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # 检查协议
            if parsed.scheme.lower() + ':' in cls.DANGEROUS_PROTOCOLS:
                return False
            
            # 只允许HTTP/HTTPS
            if parsed.scheme.lower() not in ['http', 'https']:
                return False
            
            # 检查主机名（防止SSRF）
            if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
                return False
            
            # 检查私有IP地址
            import ipaddress
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback:
                    return False
            except ValueError:
                pass  # 不是IP地址，继续检查
            
            return True
        except Exception:
            return False
    
    @classmethod
    def sanitize_title(cls, title):
        """清理标题"""
        if not title:
            return "无标题"
        
        # 限制长度
        title = title[:200]
        
        # 移除控制字符
        title = ''.join(char for char in title if ord(char) >= 32)
        
        # HTML编码
        title = html.escape(title)
        
        return title.strip()
```

### API输入验证

```python
from typing import Any, Dict
import jsonschema

class APIValidator:
    ZSXQ_TOPIC_SCHEMA = {
        "type": "object",
        "properties": {
            "topic_id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
            "talk": {
                "type": "object", 
                "properties": {
                    "text": {"type": "string", "maxLength": 10000},
                    "images": {
                        "type": "array",
                        "items": {"type": "string", "format": "uri"}
                    }
                }
            }
        },
        "required": ["topic_id"]
    }
    
    @classmethod
    def validate_topic(cls, topic_data: Dict[str, Any]) -> bool:
        """验证主题数据格式"""
        try:
            jsonschema.validate(topic_data, cls.ZSXQ_TOPIC_SCHEMA)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"主题数据验证失败: {e}")
            return False
```

## 日志安全

### 敏感信息过滤

扩展现有的 `SensitiveFilter` 类：

```python
class AdvancedSensitiveFilter(SensitiveFilter):
    def __init__(self):
        super().__init__()
        # 添加更多敏感信息模式
        additional_patterns = [
            # 信用卡号
            (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '****-****-****-****'),
            
            # 身份证号
            (r'\b\d{17}[\dX]\b', '******************'),
            
            # 电话号码
            (r'\b1[3-9]\d{9}\b', '***********'),
            
            # IPv4地址（可选）
            (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '***.***.***.***'),
            
            # JWT Token
            (r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*', '***JWT_TOKEN***'),
            
            # 数据库连接字符串
            (r'(mongodb|mysql|postgresql)://[^\s]+', r'\1://***:***@***/***'),
        ]
        
        self.patterns.extend(additional_patterns)
```

### 安全日志配置

```python
import logging
import logging.handlers
from pathlib import Path

class SecureLogConfig:
    @staticmethod
    def setup_secure_logging(log_dir='/var/log/zsxq-sync', max_size=10*1024*1024):
        # 创建日志目录并设置权限
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        os.chmod(log_dir, 0o750)
        
        # 配置安全的文件处理器
        log_file = Path(log_dir) / 'zsxq_sync.log'
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=5
        )
        
        # 设置文件权限（只有所有者可读写）
        if log_file.exists():
            os.chmod(log_file, 0o640)
        
        # 添加敏感信息过滤器
        handler.addFilter(AdvancedSensitiveFilter())
        
        # 配置格式器（包含更多上下文信息）
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        return handler
```

### 审计日志

```python
class SecurityAuditLogger:
    def __init__(self):
        self.audit_logger = logging.getLogger('security.audit')
        
        # 单独的审计日志文件
        handler = logging.FileHandler('/var/log/zsxq-sync/security.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        ))
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def log_authentication(self, username, success, ip_address=None):
        """记录认证事件"""
        status = "SUCCESS" if success else "FAILURE"
        message = f"Authentication {status} - User: {username}"
        if ip_address:
            message += f" - IP: {ip_address}"
        
        self.audit_logger.info(message)
    
    def log_api_access(self, endpoint, user, response_code):
        """记录API访问"""
        self.audit_logger.info(
            f"API Access - Endpoint: {endpoint} - "
            f"User: {user} - Response: {response_code}"
        )
    
    def log_security_event(self, event_type, details):
        """记录安全事件"""
        self.audit_logger.warning(
            f"Security Event - Type: {event_type} - Details: {details}"
        )
```

## 部署安全

### 容器安全

```dockerfile
FROM python:3.9-slim

# 使用非root用户
RUN groupadd -r zsxq && useradd -r -g zsxq zsxq

# 设置工作目录
WORKDIR /app

# 安装依赖（使用特定版本）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --upgrade pip \
    && rm -rf /root/.cache/pip

# 复制应用文件并设置权限
COPY --chown=zsxq:zsxq . .
RUN chmod 755 /app \
    && chmod 644 /app/*.py \
    && chmod 600 /app/config.json

# 切换到非root用户
USER zsxq

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# 启动应用
CMD ["python3", "zsxq_to_wordpress.py"]
```

### 网络安全

```yaml
# docker-compose.yml
version: '3.8'

services:
  zsxq-sync:
    build: .
    networks:
      - zsxq-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

networks:
  zsxq-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 文件系统安全

```bash
#!/bin/bash
# 设置安全的文件权限

# 应用目录
chown -R zsxq:zsxq /opt/zsxq-to-wordpress
chmod 755 /opt/zsxq-to-wordpress
chmod 644 /opt/zsxq-to-wordpress/*.py
chmod 755 /opt/zsxq-to-wordpress/*.sh

# 配置文件
chmod 600 /opt/zsxq-to-wordpress/config.json
chmod 600 /opt/zsxq-to-wordpress/.env

# 日志目录
mkdir -p /var/log/zsxq-sync
chown zsxq:zsxq /var/log/zsxq-sync
chmod 750 /var/log/zsxq-sync

# 状态文件
touch /opt/zsxq-to-wordpress/sync_state.json
chown zsxq:zsxq /opt/zsxq-to-wordpress/sync_state.json
chmod 644 /opt/zsxq-to-wordpress/sync_state.json
```

## 安全检查清单

### 部署前检查

- [ ] **认证配置**
  - [ ] 使用环境变量存储敏感信息
  - [ ] access_token 不在代码中硬编码
  - [ ] WordPress使用应用密码
  - [ ] 配置了适当的权限等级

- [ ] **传输安全**
  - [ ] 启用SSL/TLS验证
  - [ ] 使用最新的TLS版本
  - [ ] 配置了安全的密码套件
  - [ ] 代理配置（如适用）正确

- [ ] **输入验证**
  - [ ] 实现了内容过滤
  - [ ] URL验证机制工作正常
  - [ ] 标题长度限制生效
  - [ ] 危险标签被过滤

- [ ] **日志安全**
  - [ ] 敏感信息过滤器已启用
  - [ ] 日志文件权限设置正确
  - [ ] 配置了日志轮转
  - [ ] 审计日志独立存储

- [ ] **部署安全**
  - [ ] 使用非root用户运行
  - [ ] 容器安全配置（如适用）
  - [ ] 网络隔离设置
  - [ ] 文件权限配置正确

### 运行时监控

```python
class SecurityMonitor:
    def __init__(self):
        self.failed_auth_count = 0
        self.last_failed_auth = None
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
    
    def check_authentication_failures(self):
        """监控认证失败"""
        if self.failed_auth_count > 5:
            # 触发安全告警
            self.send_security_alert("频繁认证失败")
            return True
        return False
    
    def scan_content_for_threats(self, content):
        """扫描内容中的安全威胁"""
        threats = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                threats.append(pattern)
        
        if threats:
            self.send_security_alert(f"检测到可疑内容: {threats}")
        
        return len(threats) == 0
    
    def send_security_alert(self, message):
        """发送安全告警"""
        # 实现告警通知机制
        logger.critical(f"SECURITY ALERT: {message}")
        # 可以集成邮件、短信、Webhook等通知方式
```

### 定期安全审计

```bash
#!/bin/bash
# security_audit.sh

echo "=== ZSXQ同步工具安全审计 ==="

# 检查文件权限
echo "1. 检查文件权限..."
find /opt/zsxq-to-wordpress -type f -perm /o+w -exec ls -la {} \;

# 检查配置文件
echo "2. 检查配置安全性..."
if grep -E "(password|token|key).*=" /opt/zsxq-to-wordpress/config.json 2>/dev/null; then
    echo "警告：配置文件中包含明文密码"
fi

# 检查日志文件
echo "3. 检查日志安全性..."
if grep -E "(password|token|key)" /var/log/zsxq-sync/*.log 2>/dev/null; then
    echo "警告：日志文件中包含敏感信息"
fi

# 检查网络连接
echo "4. 检查网络安全..."
netstat -tlnp | grep python

# 检查运行用户
echo "5. 检查运行用户..."
ps aux | grep zsxq_to_wordpress.py

echo "安全审计完成"
```

通过遵循这些安全最佳实践，可以显著降低系统的安全风险，保护敏感数据和用户隐私。建议定期进行安全审计和更新，确保系统始终处于安全状态。