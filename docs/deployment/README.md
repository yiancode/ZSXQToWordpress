# 部署指南

知识星球到WordPress同步工具的完整部署文档。

## 目录

- [快速部署](#快速部署)
- [环境要求](#环境要求)
- [配置文件](#配置文件)
- [生产环境部署](#生产环境部署)
- [Docker部署](#docker部署)
- [云服务部署](#云服务部署)
- [监控和维护](#监控和维护)

## 快速部署

### 1. 环境准备

```bash
# 确保Python 3.8+
python3 --version

# 克隆项目
git clone https://github.com/your-username/ZSXQToWordpress.git
cd ZSXQToWordpress

# 安装依赖
pip3 install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置文件
nano config.json
```

### 3. 一键启动

```bash
# 使用一键启动脚本
chmod +x quick_start.sh
./quick_start.sh
```

## 环境要求

### 系统要求
- **操作系统**: Linux, macOS, Windows
- **Python**: 3.8+
- **内存**: 最低512MB，推荐1GB+
- **存储**: 最低100MB可用空间

### 依赖包
- requests >= 2.31.0
- python-wordpress-xmlrpc >= 2.3
- qiniu >= 7.13.0 (可选)
- python-dateutil >= 2.8.2

## 配置文件

### 基本配置

```json
{
  "zsxq": {
    "access_token": "your_access_token",
    "user_agent": "Mozilla/5.0 ...",
    "group_id": "your_group_id"
  },
  "wordpress": {
    "url": "https://your-site.com/xmlrpc.php",
    "username": "your_username", 
    "password": "your_app_password",
    "verify_ssl": true
  }
}
```

### 环境变量配置

**推荐在生产环境使用环境变量：**

```bash
# 知识星球配置
export ZSXQ_ACCESS_TOKEN="your_token"
export ZSXQ_GROUP_ID="your_group_id"

# WordPress配置
export WORDPRESS_URL="https://your-site.com/xmlrpc.php"
export WORDPRESS_USERNAME="your_username"
export WORDPRESS_PASSWORD="your_password"
export WORDPRESS_VERIFY_SSL="true"

# 七牛云配置（可选）
export QINIU_ACCESS_KEY="your_access_key"
export QINIU_SECRET_KEY="your_secret_key"
export QINIU_BUCKET="your_bucket"
export QINIU_DOMAIN="your_domain"
```

## 生产环境部署

### 1. 服务化部署

创建systemd服务文件 `/etc/systemd/system/zsxq-sync.service`：

```ini
[Unit]
Description=ZSXQ to WordPress Sync Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/zsxq-to-wordpress
Environment=PYTHONPATH=/opt/zsxq-to-wordpress
EnvironmentFile=/opt/zsxq-to-wordpress/.env
ExecStart=/usr/bin/python3 /opt/zsxq-to-wordpress/zsxq_to_wordpress.py --mode=incremental
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable zsxq-sync
sudo systemctl start zsxq-sync
```

### 2. Cron定时任务

```bash
# 编辑cron任务
crontab -e

# 添加定时同步任务
# 每小时执行增量同步
0 * * * * cd /opt/zsxq-to-wordpress && python3 zsxq_to_wordpress.py --mode=incremental >> /var/log/zsxq-sync.log 2>&1

# 每天凌晨2点执行全量同步
0 2 * * * cd /opt/zsxq-to-wordpress && python3 zsxq_to_wordpress.py --mode=full >> /var/log/zsxq-sync.log 2>&1
```

### 3. 日志轮转

创建日志轮转配置 `/etc/logrotate.d/zsxq-sync`：

```
/var/log/zsxq-sync.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

## Docker部署

### 1. Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 zsxq && chown -R zsxq:zsxq /app
USER zsxq

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

CMD ["python3", "zsxq_to_wordpress.py", "--mode=incremental"]
```

### 2. docker-compose.yml

```yaml
version: '3.8'

services:
  zsxq-sync:
    build: .
    container_name: zsxq-sync
    restart: unless-stopped
    environment:
      - ZSXQ_ACCESS_TOKEN=${ZSXQ_ACCESS_TOKEN}
      - ZSXQ_GROUP_ID=${ZSXQ_GROUP_ID}
      - WORDPRESS_URL=${WORDPRESS_URL}
      - WORDPRESS_USERNAME=${WORDPRESS_USERNAME}
      - WORDPRESS_PASSWORD=${WORDPRESS_PASSWORD}
    volumes:
      - ./sync_state.json:/app/sync_state.json
      - ./logs:/app/logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. 启动Docker服务

```bash
# 创建环境变量文件
cp .env.example .env
# 编辑.env文件填入实际配置

# 构建和启动
docker-compose up -d

# 查看日志
docker-compose logs -f zsxq-sync
```

## 云服务部署

### AWS EC2部署

1. **启动EC2实例**
   - 选择Ubuntu 20.04 LTS
   - t3.micro或更高配置
   - 配置安全组开放必要端口

2. **安装和配置**
   ```bash
   # 连接到实例
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装Python和依赖
   sudo apt install python3-pip git -y
   
   # 克隆和部署
   git clone https://github.com/your-username/ZSXQToWordpress.git
   cd ZSXQToWordpress
   pip3 install -r requirements.txt
   ```

### 阿里云ECS部署

类似AWS EC2，选择合适的实例规格和镜像。

### VPS部署

适用于各种VPS服务商：

```bash
# 基本环境安装
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 使用Docker部署
git clone https://github.com/your-username/ZSXQToWordpress.git
cd ZSXQToWordpress
docker-compose up -d
```

## 监控和维护

### 1. 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

LOG_FILE="/var/log/zsxq-sync.log"
ERROR_COUNT=$(tail -n 100 "$LOG_FILE" | grep -c "ERROR")

if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "检测到过多错误，可能需要人工干预"
    # 发送告警通知
    curl -X POST "https://your-webhook-url" -d "text=ZSXQ同步服务出现异常"
fi
```

### 2. 监控指标

重要监控项：
- 同步成功率
- API响应时间  
- 错误日志数量
- 磁盘空间使用
- 内存使用情况

### 3. 备份策略

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/zsxq-sync/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份配置和状态文件
cp config.json sync_state.json "$BACKUP_DIR/"

# 备份日志（最近7天）
find /var/log -name "*zsxq*" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# 清理30天前的备份
find /backup/zsxq-sync -type d -mtime +30 -exec rm -rf {} \;
```

## 故障排除

常见部署问题请参考 [故障排除文档](../troubleshooting/README.md)。

## 安全建议

1. **网络安全**: 使用防火墙限制访问
2. **密钥管理**: 使用环境变量存储敏感信息
3. **权限控制**: 使用最小权限原则
4. **更新维护**: 定期更新依赖和系统

更多安全配置请参考 [安全文档](../security/README.md)。