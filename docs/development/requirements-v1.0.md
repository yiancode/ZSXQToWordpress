# 知识星球WordPress同步工具 v1.0 - 需求文档

## 项目概述

本项目是知识星球WordPress同步工具的v1.0版本，采用最简化的实现方式。通过Python脚本实现知识星球内容到WordPress的自动同步，支持全量同步和增量同步两种模式。

## 核心价值

- 极简部署：单个Python脚本，配置文件驱动
- 快速上手：最少的依赖和配置项
- 核心功能：专注于内容同步的基本需求
- 服务器友好：可直接部署在WordPress服务器上

## 用户角色

- **博主**: 拥有知识星球和WordPress网站的内容创作者

## 功能需求

### 1. 配置管理

**用户故事**: 作为博主，我希望通过简单的配置文件设置所有必要的连接信息，以便快速开始使用同步工具。

#### 1.1 配置文件管理
- **需求**: 提供JSON格式的配置文件管理所有设置
- **验收标准**:
  - WHEN 脚本首次运行 THEN 自动生成config.json模板文件
  - WHEN 配置文件缺失必要项 THEN 脚本显示具体的缺失配置并退出
  - WHEN 配置文件格式错误 THEN 脚本显示JSON格式错误位置
  - IF 配置文件不存在 THEN 脚本创建示例配置文件并提示用户填写

#### 1.2 知识星球配置
- **需求**: 配置知识星球访问凭据
- **验收标准**:
  - WHEN 用户配置access_token THEN 脚本能够验证token有效性
  - WHEN 用户配置group_id THEN 脚本能够访问指定的知识星球
  - WHEN 用户配置user_agent THEN 脚本使用指定的用户代理访问API
  - IF token无效 THEN 脚本显示明确的错误信息和获取方法

#### 1.3 WordPress配置
- **用户故事**: 配置WordPress连接信息
- **验收标准**:
  - WHEN 用户配置WordPress URL、用户名、密码 THEN 脚本能够成功连接WordPress
  - WHEN WordPress连接失败 THEN 脚本显示具体的连接错误信息
  - WHEN XML-RPC被禁用 THEN 脚本提示用户启用XML-RPC功能
  - IF 认证失败 THEN 脚本提示检查用户名和密码

#### 1.4 七牛云配置
- **需求**: 配置七牛云图片存储
- **验收标准**:
  - WHEN 用户配置七牛云AccessKey、SecretKey、Bucket、Domain THEN 脚本能够上传图片并生成正确的访问URL
  - WHEN 七牛云配置错误 THEN 脚本显示具体的配置错误信息
  - WHEN 图片上传失败 THEN 脚本记录错误并使用原始图片链接
  - IF 七牛云配置为空 THEN 脚本跳过图片上传，直接使用原始链接

#### 1.5 同步参数配置
- **需求**: 配置同步过程中的行为参数
- **验收标准**:
  - WHEN 用户配置批处理大小(batch_size) THEN 脚本按指定数量分批获取内容
  - WHEN 用户配置请求延迟(delay_seconds) THEN 脚本在每次API请求后等待指定秒数
  - WHEN 用户配置最大重试次数(max_retries) THEN 脚本在API请求失败后按指定次数重试

### 2. 内容获取与处理

**用户故事**: 作为博主，我希望脚本能够准确获取知识星球的内容并正确处理各种格式，以便在WordPress上完美呈现。

#### 2.1 知识星球内容获取
- **需求**: 从知识星球API获取内容数据
- **验收标准**:
  - WHEN 执行全量同步 THEN 脚本获取所有可访问的帖子内容
  - WHEN 执行增量同步 THEN 脚本只获取上次同步后的新内容
  - WHEN API请求失败 THEN 脚本将以指数退避策略重试（如1s, 2s, 4s...），最多重试5次，失败后记录错误并继续
  - WHEN 内容量大 THEN 脚本支持分页获取避免超时

#### 2.2 内容类型识别和处理
- **需求**: 准确识别知识星球中的不同内容类型并进行相应处理
- **内容类型定义**:
  - **片刻(Moment)**：在知识星球中，没有标题、只有一段文字和几张图片的简短分享，被称为"说说"或"talk"。脚本将这种形式的内容识别为 moment。代码层面的判断依据是：topic 数据中包含 talk 字段，但 talk 字段内部没有 article 对象。
  - **文章(Post)**：
    - 知识星球中带有标题和正文的正式"文章"
    - "问答"类型的帖子
    - "任务打卡"类型的帖子
    - 其他不符合"片刻"标准的任何内容
- **验收标准**:
  - WHEN topic数据包含talk字段且无article对象 THEN 识别为片刻类型
  - WHEN topic数据包含article对象或属于问答类型 THEN 识别为文章类型
  - WHEN 片刻内容处理 THEN 自动生成简短标题，保持简洁格式
  - WHEN 文章内容处理 THEN 保持完整结构和格式
  - IF 内容类型无法确定 THEN 默认按文章类型处理

#### 2.3 内容格式处理
- **需求**: 将知识星球内容转换为WordPress兼容格式
- **验收标准**:
  - WHEN 内容包含@提及 THEN 转换为普通文本显示
  - WHEN 内容包含话题标签 THEN 转换为WordPress标签
  - WHEN 内容包含链接 THEN 保持链接的可点击性
  - WHEN 知识星球内容格式(如加粗、列表) THEN 尽可能转换为等效的Markdown格式
  - IF 内容格式异常 THEN 脚本记录警告并尽可能处理

#### 2.4 图片处理
- **需求**: 处理知识星球中的图片并上传到七牛云
- **验收标准**:
  - WHEN 内容包含图片 THEN 脚本自动下载图片到临时目录
  - WHEN 图片下载成功 THEN 脚本上传图片到七牛云并获取访问链接
  - WHEN 图片上传成功 THEN WordPress文章中使用七牛云链接
  - WHEN 图片处理完成 THEN 脚本清理临时图片文件
  - IF 图片上传失败 THEN 脚本使用原始图片链接并记录警告

### 3. WordPress集成

**用户故事**: 作为博主，我希望处理后的内容能够自动发布到WordPress，并保持良好的组织结构。

#### 3.1 文章发布
- **需求**: 将处理后的内容发布为WordPress文章
- **验收标准**:
  - WHEN 内容处理完成 THEN 脚本自动创建WordPress文章
  - WHEN 文章标题为空 THEN 脚本使用内容前50字符作为标题
  - WHEN 文章发布成功 THEN 脚本记录文章ID和发布时间
  - WHEN 文章发布失败 THEN 脚本记录错误信息并跳过该文章
  - IF WordPress连接中断 THEN 脚本暂停并等待连接恢复

#### 3.2 分类和标签管理
- **需求**: 自动管理WordPress的分类和标签
- **验收标准**:
  - WHEN 发布文章 THEN 脚本自动添加"知识星球"分类
  - WHEN 内容包含话题标签 THEN 脚本在WordPress中创建对应标签
  - WHEN 标签不存在 THEN 脚本自动创建新标签
  - WHEN 精华内容 THEN 脚本添加"精华"标签
  - IF 分类创建失败 THEN 脚本使用默认分类并记录警告

#### 3.3 重复内容检测
- **需求**: 避免重复导入已同步的内容
- **验收标准**:
  - WHEN 执行同步 THEN 脚本通过查询状态文件中的记录，检查内容是否已发布
  - WHEN 内容已存在 THEN 脚本跳过该内容的导入
  - WHEN 内容有更新 THEN (v1.0暂不处理) 脚本跳过该内容的更新，以避免复杂性。未来版本可支持更新。
  - WHEN 检测到重复 THEN 脚本在日志中记录跳过信息
  - IF 检测逻辑不确定 THEN 脚本跳过导入并记录警告

### 4. 同步模式

**用户故事**: 作为博主，我希望能够选择不同的同步模式，以便根据需要进行全量或增量同步。

#### 4.1 全量同步
- **需求**: 同步知识星球的所有内容
- **验收标准**:
  - WHEN 执行全量同步 THEN 脚本获取所有可访问的帖子
  - WHEN 全量同步开始 THEN 脚本显示预计处理的文章数量
  - WHEN 同步进行中 THEN 脚本显示当前进度和处理状态
  - WHEN 全量同步完成 THEN 脚本显示同步统计信息
  - IF 同步中断 THEN 脚本在状态文件中记录最后一个成功同步帖子的时间戳，支持从该断点续传

#### 4.2 增量同步
- **需求**: 只同步上次同步后的新内容
- **验收标准**:
  - WHEN 执行增量同步 THEN 脚本只获取最后同步时间之后的内容
  - WHEN 首次运行增量同步 THEN 脚本提示用户选择起始时间或执行全量同步
  - WHEN 增量同步完成 THEN 脚本更新最后同步时间记录
  - WHEN 没有新内容 THEN 脚本显示"无新内容需要同步"
  - IF 时间记录丢失 THEN 脚本提示用户选择同步模式

### 5. 日志和监控

**用户故事**: 作为博主，我希望能够了解同步过程的详细信息和结果，以便监控和排查问题。

#### 5.1 日志记录
- **需求**: 记录同步过程的详细信息
- **验收标准**:
  - WHEN 脚本运行 THEN 自动创建日志文件记录所有操作
  - WHEN 发生错误 THEN 日志记录详细的错误信息和堆栈
  - WHEN 同步成功 THEN 日志记录成功的文章标题和ID
  - WHEN 日志文件过大 THEN 脚本自动轮转日志文件
  - IF 日志写入失败 THEN 脚本在控制台输出重要信息

#### 5.2 进度显示
- **需求**: 实时显示同步进度
- **验收标准**:
  - WHEN 同步开始 THEN 脚本显示总文章数和当前进度
  - WHEN 处理文章 THEN 脚本显示当前文章标题和处理状态
  - WHEN 遇到错误 THEN 脚本显示错误信息但继续处理其他文章
  - WHEN 同步完成 THEN 脚本显示成功、失败、跳过的文章统计
  - IF 处理时间过长 THEN 脚本显示预计剩余时间

#### 5.3 状态记录
- **需求**: 记录同步状态和历史
- **验收标准**:
  - WHEN 同步完成 THEN 脚本将同步记录保存到状态文件
  - WHEN 查看状态 THEN 脚本显示最后同步时间和结果统计
  - WHEN 状态文件损坏 THEN 脚本备份损坏文件，并提示用户风险，让用户选择强制全量同步或退出
  - WHEN 多次同步 THEN 脚本保留最近10次的同步记录
  - IF 状态文件不存在 THEN 脚本创建新的状态文件

## 技术约束

- 使用Python 3.7+开发
- 依赖库：requests, python-wordpress-xmlrpc, qiniu
- 配置文件使用JSON格式
- 日志文件使用标准的logging模块
- 状态文件使用JSON格式存储
- 支持Linux、macOS、Windows运行
- 单文件脚本，便于部署和维护

## 部署要求

- Python 3.7+环境
- 网络访问：能够访问知识星球API、WordPress站点、七牛云
- 文件权限：能够读写配置文件、日志文件、状态文件
- 内存要求：最少256MB可用内存
- 存储要求：临时图片存储空间（根据图片数量而定）

## 配置文件示例

```json
{
  "zsxq": {
    "access_token": "YOUR_ZSXQ_ACCESS_TOKEN",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "group_id": "YOUR_ZSXQ_GROUP_ID"
  },
  "wordpress": {
    "url": "https://example.com/xmlrpc.php",
    "username": "your_wordpress_username",
    "password": "your_wordpress_password"
  },
  "qiniu": {
    "access_key": "YOUR_QINIU_ACCESS_KEY",
    "secret_key": "YOUR_QINIU_SECRET_KEY",
    "bucket": "your_qiniu_bucket_name",
    "domain": "your_qiniu_domain"
  },
  "sync": {
    "batch_size": 20,
    "delay_seconds": 2,
    "max_retries": 5
  }
}
```

## 使用方式

```bash
# 全量同步
python zsxq_sync.py --mode full

# 增量同步
python zsxq_sync.py --mode incremental

# 查看状态
python zsxq_sync.py --status

# 查看帮助
python zsxq_sync.py --help
```

## 定时同步部署方案

### 方案一：宝塔面板计划任务（推荐）

适用于部署在宝塔面板的用户，无需修改代码即可实现定时同步。

**配置步骤**：
1. 在宝塔面板创建 Python 项目，上传同步脚本
2. 确保安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 在"计划任务"中添加 Shell 脚本类型任务
4. 脚本内容：
   ```bash
   cd /www/wwwroot/zsxq-sync
   /usr/bin/python3 zsxq_to_wordpress.py --mode incremental >> /www/wwwlogs/zsxq_sync_cron.log 2>&1
   ```
5. 执行周期设置建议：
   - 高频更新：每30分钟
   - 常规更新：每1小时  
   - 低频更新：每天1-2次

### 方案二：守护进程脚本

适用于需要更灵活控制的场景，创建 `zsxq_daemon.py` 作为常驻进程。

**实现示例**：
```python
#!/usr/bin/env python3
import time
import subprocess
import json
import logging
from datetime import datetime

def run_sync():
    """执行增量同步"""
    try:
        result = subprocess.run(
            ['python3', 'zsxq_to_wordpress.py', '--mode', 'incremental'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info(f"同步成功: {datetime.now()}")
        else:
            logging.error(f"同步失败: {result.stderr}")
    except Exception as e:
        logging.error(f"执行同步时出错: {e}")

def main():
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/www/wwwlogs/zsxq_daemon.log'),
            logging.StreamHandler()
        ]
    )
    
    # 读取配置
    with open('daemon_config.json', 'r') as f:
        config = json.load(f)
    
    interval = config.get('sync_interval', 3600)  # 默认1小时
    
    logging.info(f"守护进程启动，同步间隔: {interval}秒")
    
    while True:
        run_sync()
        time.sleep(interval)

if __name__ == '__main__':
    main()
```

**daemon_config.json 示例**：
```json
{
  "sync_interval": 3600,
  "log_level": "INFO"
}
```

### 方案三：系统级定时任务

对于Linux服务器，也可以使用系统的 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每小时执行）
0 * * * * cd /path/to/zsxq-sync && /usr/bin/python3 zsxq_to_wordpress.py --mode incremental >> sync.log 2>&1
```

### 部署配置建议

**宝塔环境路径**：
- 项目目录：`/www/wwwroot/zsxq-sync/`
- Python路径：`/usr/bin/python3` 或 `/www/server/pyenv/versions/3.x.x/bin/python`
- 日志文件：`/www/wwwlogs/zsxq_sync.log`
- 状态文件：`/www/wwwroot/zsxq-sync/sync_state.json`

**性能优化建议**：
1. 在访问量低的时段执行同步（如凌晨2-6点）
2. 设置合理的请求延迟（delay_seconds）避免触发API限制
3. 定期清理日志文件避免占用过多空间
4. 使用日志轮转机制管理日志文件大小

**监控建议**：
1. 设置同步失败的邮件通知
2. 监控日志文件中的错误信息
3. 定期检查同步状态文件的更新时间
4. 使用宝塔的监控功能查看脚本执行情况

**安全建议**：
1. 确保配置文件权限为 600（仅所有者可读写）
2. 不要在日志中记录敏感信息（如token、密码）
3. 定期更新知识星球的access_token
4. 使用HTTPS连接WordPress

## 验收标准

### 基本功能验收
- 能够成功连接知识星球、WordPress和七牛云
- 能够同步文本、图片、链接等不同类型的内容
- 全量同步和增量同步功能正常
- 重复内容检测有效

### 性能验收
- 同步100篇文章的时间不超过10分钟
- 内存使用不超过256MB
- 图片处理不影响整体同步速度

### 稳定性验收
- 网络异常时能够自动重试
- 单个文章处理失败不影响其他文章
- 脚本异常退出后能够从断点继续

## 项目里程碑

### 第一天：核心脚本开发
- 完成配置文件管理和验证
- 实现知识星球API调用
- 实现基础的内容处理逻辑

### 第二天：WordPress集成
- 实现WordPress文章发布功能
- 添加分类和标签管理
- 实现重复内容检测

### 第三天：图片处理和优化
- 集成七牛云图片上传
- 完善错误处理和重试机制
- 添加日志和进度显示

### 第四天：测试和完善
- 全面测试各种场景
- 优化性能和用户体验
- 完善文档和使用说明

## 风险评估

### 技术风险
- 知识星球API限制或变化
- WordPress XML-RPC兼容性问题
- 七牛云服务稳定性

### 缓解措施
- 实现完善的错误处理和重试机制
- 提供详细的错误信息和解决建议
- 支持配置调整以适应不同环境
- 提供完整的使用文档和FAQ

## 附录A：如何获取七牛云配置

为了获取 `access_key`, `secret_key`, `bucket`, 和 `domain`，请按照以下步骤操作：

1.  **登录七牛云控制台**
    -   访问 [https://portal.qiniu.com/](https://portal.qiniu.com/) 并登录您的账户。

2.  **获取 Access Key (AK) 和 Secret Key (SK)**
    -   登录后，将鼠标悬停在右上角的头像上，在下拉菜单中点击 **密钥管理**。
    -   您会看到一组 **AccessKey** 和 **SecretKey**。请复制并妥善保管它们。这就是配置文件中需要的 `access_key` 和 `secret_key`。

3.  **创建存储空间 (Bucket)**
    -   在左侧导航栏中，找到并点击 **对象存储Kodo**。
    -   点击 **空间管理**，然后点击 **新建空间** 按钮。
    -   **空间名称**: 输入一个唯一的名称，例如 `your-unique-bucket-name`。这就是配置文件中的 `bucket`。
    -   **存储区域**: 选择一个适合您的地理位置的区域。
    -   **访问控制**: **非常重要**，请选择 **公开空间**，这样上传的图片才能被公开访问。
    -   点击 **确定创建**。

4.  **获取测试域名 (Domain)**
    -   创建成功后，在 **空间管理** 列表中找到您刚刚创建的空间，点击它的名称进入管理页面。
    -   在空间管理页面中，点击 **域名管理** 标签页。
    -   您会看到一个系统分配的 **测试域名**，格式通常是 `xxxx.qiniudns.com` 或类似的。
    -   复制这个域名。这就是配置文件中需要的 `domain`。

将以上获取到的四个值填入 `config.json` 文件中的 `qiniu` 部分即可。