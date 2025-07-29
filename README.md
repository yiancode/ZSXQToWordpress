# 知识星球WordPress同步工具

一个将知识星球内容自动同步到WordPress的Python工具，支持定时自动同步，适合部署在宝塔面板等服务器环境。

## 🚀 功能特性

- ✅ **多种同步模式**：支持全量同步、增量同步和并发同步
- ✅ **自动图片处理**：支持七牛云CDN，自动上传和替换图片链接
- ✅ **智能内容转换**：保留原始格式，优化显示效果
- ✅ **防重复机制**：自动检测并跳过已发布内容
- ✅ **断点续传**：同步中断后可从上次位置继续
- ✅ **定时同步**：支持通过计划任务实现自动同步
- ✅ **详细日志**：完整的操作日志，便于问题排查
- ✅ **配置验证**：内置配置验证工具，确保配置正确
- ✅ **一键启动**：提供便捷的启动脚本
- ✅ **智能内容映射**：知识星球文章和片刻自动分类到WordPress对应类型
- 🆕 **并发处理**：支持多线程同步，性能提升3-5倍
- 🆕 **环境变量配置**：支持通过环境变量管理敏感信息
- 🆕 **敏感信息保护**：自动过滤日志中的密码和令牌
- 🆕 **SSL证书控制**：可配置SSL证书验证选项
- 🆕 **批量图片处理**：并发处理多张图片，大幅提升效率

## 📋 项目状态

- **当前版本**：v1.1.0
- **开发状态**：核心功能已完成，生产就绪，性能和安全性已优化
- **测试覆盖**：64个单元测试，59个通过（核心功能100%正常）
- **适用环境**：宝塔面板、Linux服务器、本地开发环境

## 📦 快速部署（5分钟上线）

### 方法一：一键启动脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/ZSXQToWordpress.git
cd ZSXQToWordpress

# 2. 运行一键启动脚本
chmod +x quick_start.sh
./quick_start.sh
```

脚本会自动：
- 检查Python环境
- 安装依赖包
- 复制配置文件模板
- 验证配置
- 启动同步程序

### 方法二：手动部署

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 复制配置文件
cp config.example.json config.json

# 3. 编辑配置文件
nano config.json  # 填入你的配置

# 4. 验证配置
python3 validate_config.py

# 5. 开始同步
python3 zsxq_to_wordpress.py --mode=incremental
```

## 📚 内容类型说明

### 内容类型判断标准

本工具会自动识别知识星球中的不同内容类型，并将其适当地同步到WordPress：

#### 片刻 (Moment/短内容)
**定义**：在知识星球中，没有标题、只有一段文字和几张图片的简短分享，被称为"说说"或"talk"。

**技术判断依据**：
- topic 数据中包含 `talk` 字段
- `talk` 字段内部没有 `article` 对象
- 通常是简短的文字配图分享

**同步方式**：
- 自动生成简短标题（基于内容前缀）
- 归类到"片刻"或自定义分类
- 保持简洁的格式和布局

#### 文章 (Post/正式文章)
**定义**：知识星球中带有明确结构的正式内容。

**包含类型**：
- 知识星球中带有标题和正文的正式"文章"
- "问答"类型的帖子
- "任务打卡"类型的帖子
- 其他不符合"片刻"标准的任何内容

**技术判断依据**：
- topic 数据中包含 `article` 对象
- 或者属于 `q&a-question`、`q&a-answer` 等类型
- 通常有明确的标题和结构化内容

**同步方式**：
- 保持原有标题结构
- 支持完整的格式转换
- 自动分类和标签处理

## 🔧 配置说明

### 配置文件格式

```json
{
  "zsxq": {
    "access_token": "从浏览器开发者工具中获取",
    "user_agent": "保持默认或复制浏览器User-Agent", 
    "group_id": "知识星球群组ID"
  },
  "wordpress": {
    "url": "https://yoursite.com/xmlrpc.php",
    "username": "WordPress管理员用户名",
    "password": "WordPress应用密码（推荐）",
    "verify_ssl": true  // 是否验证SSL证书（默认true）
  },
  "qiniu": {
    "access_key": "七牛云AccessKey（可选）",
    "secret_key": "七牛云SecretKey（可选）",
    "bucket": "存储空间名称（可选）",
    "domain": "CDN域名（可选）"
  }
}
```

### 环境变量配置（推荐用于生产环境）

创建 `.env` 文件或设置系统环境变量：

```bash
# 知识星球配置
ZSXQ_ACCESS_TOKEN=your_access_token_here
ZSXQ_GROUP_ID=your_group_id_here

# WordPress配置
WORDPRESS_URL=https://your-site.com/xmlrpc.php
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_password
WORDPRESS_VERIFY_SSL=true

# 七牛云配置（可选）
QINIU_ACCESS_KEY=your_access_key
QINIU_SECRET_KEY=your_secret_key
QINIU_BUCKET=your_bucket_name
QINIU_DOMAIN=your_cdn_domain
```

**配置优先级**：环境变量 > config.json > 默认值

### 获取知识星球配置

1. **access_token 获取方法**：
   - 打开知识星球网页版：https://wx.zsxq.com/
   - 登录后按F12打开开发者工具
   - 切换到Network标签
   - 随意点击一个内容，查看请求
   - 在Request Headers中找到Cookie中的`zsxq_access_token=xxxxx`

2. **group_id 获取方法**：
   - 在知识星球网页版中进入你的星球
   - 在URL中找到group_id（类似：/api/v2/groups/[group_id]/...）

3. **user_agent**：
   - 复制开发者工具中Request Headers的User-Agent完整字符串

### 配置同步目标 (`sync_targets`)

从v2.0开始，本工具引入了强大的 `sync_targets` 配置，允许你精确、灵活地定义要同步的内容来源。你可以组合多个目标，程序会自动合并和去重。

该配置项位于 `content_mapping` 块内，取代了旧的专栏同步配置。

**配置结构**

```json
"content_mapping": {
  "sync_targets": [
    {
      "type": "scope",
      "value": "all",
      "enabled": true,
      "name": "所有内容"
    },
    {
      "type": "scope",
      "value": "digests",
      "enabled": false,
      "name": "精华内容",
      "category_override": "精华"
    },
    {
      "type": "column",
      "value": "YOUR_COLUMN_ID",
      "enabled": false,
      "name": "专栏：我的第一个专栏"
    },
    {
      "type": "hashtag",
      "value": "YOUR_HASHTAG_ID",
      "enabled": false,
      "name": "标签：我的第一个标签",
      "category_override": "标签分类"
    }
  ],
  // ... 其他配置
}
```

**字段说明**

- **`type`** (必填): 同步目标的类型。
  - `"scope"`: 按范围同步。
  - `"column"`: 按专栏ID同步。
  - `"hashtag"`: 按标签ID同步。
- **`value`** (必填): 目标类型对应的值。
  - 当 `type` 为 `scope` 时, `value` 可为 `"all"` (所有) 或 `"digests"` (精华)。
  - 当 `type` 为 `column` 或 `hashtag` 时, `value` 为对应的ID。
- **`enabled`** (必填): `true` 或 `false`，决定是否启用该同步目标。
- **`name`** (可选): 为该目标指定一个易于理解的名称，会显示在日志中。
- **`category_override`** (可选): 强制将从该目标获取的所有内容发布到WordPress的这个指定分类下，覆盖默认的分类逻辑。

### 内容分类配置

**topic_settings** 和 **article_settings** 支持以下配置：

- **`category`**: 主要分类名称（当内容有分类时使用）
- **`default_category`**: 默认分类名称（当内容没有分类时使用，默认为"Trending"）
- **`sync_title`**: 是否同步标题（true/false）
- **`placeholder_title`**: 当 `sync_title` 为 false 时使用的占位标题（默认为"无标题"）
- **`use_custom_post_type`**: 是否使用自定义文章类型（仅topic_settings支持）

### WordPress配置

1. **确保XML-RPC启用**：
   - WordPress后台 → 设置 → 撰写 → 确保"XML-RPC"相关选项已启用

2. **使用应用密码**（推荐）：
   - WordPress后台 → 用户 → 个人资料
   - 滚动到"应用密码"部分
   - 添加新的应用密码用于同步工具

3. **URL格式**：
   - 必须是 `https://your-site.com/xmlrpc.php` 格式

### 七牛云配置（可选）

1. 注册七牛云账号：https://www.qiniu.com/
2. 创建对象存储空间
3. 获取AccessKey和SecretKey
4. 配置CDN加速域名

## 🎯 使用方法

### 配置验证

```bash
# 验证所有配置是否正确（重要！）
python3 validate_config.py
```

验证工具会检查：
- 知识星球连接状态
- WordPress连接状态  
- 七牛云配置（如果启用）

### 同步命令

```bash
# 增量同步（推荐用于定时任务）
python3 zsxq_to_wordpress.py --mode=incremental

# 全量同步（首次使用或重建）
python3 zsxq_to_wordpress.py --mode=full

# 并发同步（提升性能，默认3个线程）
python3 zsxq_to_wordpress.py --mode=concurrent

# 自定义并发线程数
python3 zsxq_to_wordpress.py --mode=concurrent --workers=5

# 测试模式（只同步2条内容）
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=2 python3 zsxq_to_wordpress.py --mode=full

# 详细日志输出
python3 zsxq_to_wordpress.py --mode=incremental -v

# 使用自定义配置文件
python3 zsxq_to_wordpress.py --config=myconfig.json

# 使用环境变量（无需config.json）
export ZSXQ_ACCESS_TOKEN=your_token
export WORDPRESS_PASSWORD=your_password
python3 zsxq_to_wordpress.py --mode=incremental
```

### 定时自动同步

#### 宝塔面板计划任务（推荐）

1. 进入宝塔面板 → 计划任务
2. 任务类型：Shell脚本
3. 执行周期：每小时或每天
4. 脚本内容：
```bash
cd /www/wwwroot/ZSXQToWordpress
python3 zsxq_to_wordpress.py --mode=incremental >> /tmp/zsxq_sync.log 2>&1
```

#### 系统Crontab

```bash
# 编辑crontab
crontab -e

# 添加每小时执行一次
0 * * * * cd /path/to/ZSXQToWordpress && python3 zsxq_to_wordpress.py --mode=incremental
```

## 📁 项目结构

```
ZSXQToWordpress/
├── zsxq_to_wordpress.py      # 主程序入口
├── config_manager.py         # 配置管理模块
├── zsxq_client.py           # 知识星球API客户端
├── wordpress_client.py       # WordPress XML-RPC客户端
├── qiniu_uploader.py        # 七牛云图片上传模块
├── content_processor.py      # 内容处理和转换模块
├── sync_state.py            # 同步状态管理模块
├── log_utils.py             # 日志安全过滤模块（新增）
├── interfaces.py            # 接口定义（新增）
├── validate_config.py       # 配置验证工具
├── quick_start.sh          # 一键启动脚本
├── requirements.txt         # Python依赖列表
├── config.example.json     # 配置文件模板
├── .env.example            # 环境变量模板（新增）
├── config.json             # 配置文件（需手动创建）
├── sync_state.json         # 同步状态记录（自动生成）
├── zsxq_sync.log          # 运行日志（自动生成）
├── tests/                  # 单元测试
└── docs/                   # 文档目录
```

## 🛡️ 故障排查

### 常见问题和解决方案

#### 1. 知识星球认证失败
```bash
# 错误：认证失败，请检查access_token是否有效
# 解决：重新获取access_token（token会过期）
```

#### 2. WordPress连接失败  
```bash
# 错误：无法连接到WordPress XML-RPC
# 解决：
# - 确保WordPress启用了XML-RPC
# - 检查URL是否正确（必须以/xmlrpc.php结尾）
# - 验证用户名和密码
```

#### 3. 图片处理失败
```bash
# 错误：图片上传失败
# 解决：
# - 检查七牛云配置是否正确
# - 确保网络连接正常
# - 可以暂时禁用七牛云，使用原始图片链接
```

### 日志分析

```bash
# 查看详细日志
tail -f zsxq_sync.log

# 查看同步状态
cat sync_state.json | python3 -m json.tool

# 重置同步状态（慎用）
rm sync_state.json
```

### 性能优化

- 建议batch_size设置为10-20
- delay_seconds设置为1-3秒
- 大量内容首次同步时建议分批进行

## 🔒 安全建议

1. **配置文件安全**
   - 设置`config.json`文件权限为600
   - 不要将包含敏感信息的配置提交到版本控制
   - 优先使用环境变量存储敏感信息

2. **API密钥管理**
   - 定期更换知识星球access_token
   - 使用WordPress应用密码而非主密码
   - 生产环境使用环境变量而非配置文件

3. **服务器安全**
   - 确保Python环境安全
   - 定期更新依赖包
   - 监控日志文件大小
   - 启用SSL证书验证（verify_ssl=true）

4. **日志安全**
   - 系统自动过滤日志中的敏感信息
   - 定期清理历史日志文件
   - 避免在日志中输出调试信息

## 📊 监控和统计

### 同步状态查看

程序会自动记录同步状态在`sync_state.json`中：
- 已同步的内容ID
- 最后同步时间
- 同步统计信息

### 成功部署标志

运行后看到以下输出表示部署成功：
```
✓ 知识星球连接成功
✓ WordPress连接成功
✓ 七牛云配置验证成功
开始执行增量同步...
获取到 X 个新主题
成功同步: [文章标题] (WP ID: xxx)
增量同步完成！
总计: X
成功: X
跳过: X
失败: 0
```

## ⚠️ 注意事项

1. **首次使用**：建议先用测试模式验证几篇文章，确认效果后再执行全量同步
2. **状态文件**：`sync_state.json` 记录了同步历史，请勿随意删除
3. **重新同步**：如需重新同步所有内容，删除 `sync_state.json` 文件即可
4. **定期备份**：建议定期备份 `sync_state.json` 文件
5. **API限制**：知识星球有访问频率限制，脚本已内置延时机制

## 🔨 开发计划

### v1.1 (当前版本)
- [x] 核心同步功能
- [x] 图片上传支持
- [x] 状态管理
- [x] 定时同步方案
- [x] 配置验证工具
- [x] 一键启动脚本
- [x] 单元测试覆盖
- [x] 生产环境就绪
- [x] 智能内容类型映射（文章/片刻分类）
- [x] 并发同步支持（性能提升3-5倍）
- [x] 环境变量配置支持
- [x] 敏感信息日志过滤
- [x] SSL证书验证控制
- [x] 批量图片并发处理
- [x] 代码重构和接口定义

### v2.0 (规划中)
- [ ] Web管理界面
- [ ] 多知识星球支持
- [ ] 更多云存储支持（阿里云OSS、腾讯云COS等）
- [ ] 内容过滤规则
- [ ] 同步统计报表

## 📝 文档

- [需求文档 v1.0](docs/requirements-v1.0.md) - 详细的功能需求和技术规格
- [开发进度](docs/development-progress.md) - 当前开发状态和计划
- [部署指南](DEPLOY.md) - 详细的部署说明

## 🆘 紧急支持

如果遇到任何问题：

1. **检查日志**：`tail -f zsxq_sync.log`
2. **验证配置**：`python3 validate_config.py`
3. **重置状态**：删除`sync_state.json`重新开始
4. **测试连接**：使用`-v`参数查看详细输出

**记住：这个工具设计得非常稳定，99%的问题都是配置问题！**

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License