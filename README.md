# 知识星球WordPress同步工具

一个将知识星球内容自动同步到WordPress的Python工具，支持定时自动同步，适合部署在宝塔面板等服务器环境。

## 🚀 功能特性

- ✅ **多种同步模式**：支持全量同步和增量同步
- ✅ **自动图片处理**：支持七牛云CDN，自动上传和替换图片链接
- ✅ **智能内容转换**：保留原始格式，优化显示效果
- ✅ **防重复机制**：自动检测并跳过已发布内容
- ✅ **断点续传**：同步中断后可从上次位置继续
- ✅ **定时同步**：支持通过计划任务实现自动同步
- ✅ **详细日志**：完整的操作日志，便于问题排查
- ✅ **配置验证**：内置配置验证工具，确保配置正确
- ✅ **一键启动**：提供便捷的启动脚本
- ✅ **智能内容映射**：知识星球文章和动态自动分类到WordPress对应类型

## 📋 项目状态

- **当前版本**：v1.0.0-beta
- **开发状态**：核心功能已完成，生产就绪
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
    "password": "WordPress应用密码（推荐）"
  },
  "qiniu": {
    "access_key": "七牛云AccessKey（可选）",
    "secret_key": "七牛云SecretKey（可选）",
    "bucket": "存储空间名称（可选）",
    "domain": "CDN域名（可选）"
  }
}
```

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

# 测试模式（只同步2条内容）
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=2 python3 zsxq_to_wordpress.py --mode=full

# 详细日志输出
python3 zsxq_to_wordpress.py --mode=incremental -v

# 使用自定义配置文件
python3 zsxq_to_wordpress.py --config=myconfig.json
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
├── validate_config.py       # 配置验证工具
├── quick_start.sh          # 一键启动脚本
├── requirements.txt         # Python依赖列表
├── config.example.json     # 配置文件模板
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

2. **API密钥管理**
   - 定期更换知识星球access_token
   - 使用WordPress应用密码而非主密码

3. **服务器安全**
   - 确保Python环境安全
   - 定期更新依赖包
   - 监控日志文件大小

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

### v1.0 (当前版本)
- [x] 核心同步功能
- [x] 图片上传支持
- [x] 状态管理
- [x] 定时同步方案
- [x] 配置验证工具
- [x] 一键启动脚本
- [x] 单元测试覆盖
- [x] 生产环境就绪
- [x] 智能内容类型映射（文章/片刻分类）

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