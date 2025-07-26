# 知识星球到WordPress同步工具

一个将知识星球内容自动同步到WordPress的Python工具，支持定时自动同步，适合部署在宝塔面板等服务器环境。

## 🚀 功能特性

- ✅ **多种同步模式**：支持全量同步和增量同步
- ✅ **自动图片处理**：支持七牛云CDN，自动上传和替换图片链接
- ✅ **智能内容转换**：保留原始格式，优化显示效果
- ✅ **防重复机制**：自动检测并跳过已发布内容
- ✅ **断点续传**：同步中断后可从上次位置继续
- ✅ **定时同步**：支持通过计划任务实现自动同步
- ✅ **详细日志**：完整的操作日志，便于问题排查

## 📋 项目状态

- **当前版本**：v1.0.0-beta
- **开发状态**：核心功能已完成，待生产环境测试
- **适用环境**：宝塔面板、Linux服务器、本地开发环境

## 📦 安装部署

### 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ZSXQToWordpress.git
cd ZSXQToWordpress
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 复制配置文件模板：
```bash
cp config.example.json config.json
```

4. 编辑 `config.json`，填入你的配置信息。

## 配置说明

### 获取知识星球配置

1. **access_token**: 
   - 登录知识星球网页版
   - 打开开发者工具（F12）
   - 在Network标签页中找到任意API请求
   - 在请求的Cookie中找到 `zsxq_access_token` 的值

2. **group_id**: 
   - 在知识星球网页版中进入你的星球
   - URL中的数字即为group_id
   - 例如：`https://wx.zsxq.com/dweb2/index/group/88885121521552`

3. **user_agent**: 
   - 使用你浏览器的User-Agent（可在开发者工具的Network中查看）

### WordPress配置

1. 确保WordPress已启用XML-RPC功能
2. 使用WordPress的管理员账号
3. URL应该是 `https://your-site.com/xmlrpc.php` 格式

### 七牛云配置（可选）

如果需要使用七牛云存储图片，请参考文档中的"附录A：如何获取七牛云配置"。

## 🔧 使用方法

### 基本命令

```bash
# 全量同步（同步所有历史内容）
python zsxq_to_wordpress.py --mode=full

# 增量同步（只同步新内容，默认模式）
python zsxq_to_wordpress.py

# 使用自定义配置文件
python zsxq_to_wordpress.py --config=myconfig.json

# 显示详细日志
python zsxq_to_wordpress.py -v
```

### 定时自动同步

#### 方案一：宝塔面板计划任务（推荐）

1. 在宝塔面板上传项目文件到 `/www/wwwroot/zsxq-sync/`
2. 创建计划任务，任务类型选择"Shell脚本"
3. 脚本内容：
```bash
cd /www/wwwroot/zsxq-sync
/usr/bin/python3 zsxq_to_wordpress.py --mode incremental >> /www/wwwlogs/zsxq_sync.log 2>&1
```
4. 设置执行周期（建议每小时一次）

#### 方案二：Linux Crontab

```bash
# 编辑定时任务
crontab -e

# 添加定时任务（每小时执行一次）
0 * * * * cd /path/to/zsxq-sync && python3 zsxq_to_wordpress.py >> sync.log 2>&1
```

详细的定时同步配置请参考 [部署文档](docs/requirements-v1.0.md#定时同步部署方案)

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
├── requirements.txt         # Python依赖列表
├── config.json             # 配置文件（需手动创建）
├── sync_state.json         # 同步状态记录（自动生成）
├── zsxq_sync.log          # 运行日志（自动生成）
└── docs/
    ├── requirements-v1.0.md    # 详细需求文档
    └── development-progress.md # 开发进度文档
```

## ⚠️ 注意事项

1. **首次使用**：建议先用增量模式测试几篇文章，确认效果后再执行全量同步
2. **状态文件**：`sync_state.json` 记录了同步历史，请勿随意删除
3. **重新同步**：如需重新同步所有内容，删除 `sync_state.json` 文件即可
4. **定期备份**：建议定期备份 `sync_state.json` 文件
5. **API限制**：知识星球有访问频率限制，脚本已内置延时机制

## 常见问题

### Q: XML-RPC连接失败
A: 请确保WordPress已启用XML-RPC功能。可以在WordPress后台安装并启用 "XML-RPC" 相关插件。

### Q: 知识星球认证失败
A: access_token可能已过期，请重新获取。

### Q: 图片上传失败
A: 检查七牛云配置是否正确，或者暂时不配置七牛云，使用原始图片链接。

### Q: 如何避免重复发布？
A: 脚本会自动检查标题是否已存在，并记录已同步的topic_id。

## 🔨 开发计划

### v1.0 (当前版本)
- [x] 核心同步功能
- [x] 图片上传支持
- [x] 状态管理
- [x] 定时同步方案
- [ ] 生产环境测试
- [ ] 用户文档完善

### v2.0 (规划中)
- [ ] Web管理界面
- [ ] 多知识星球支持
- [ ] 更多云存储支持（阿里云OSS、腾讯云COS等）
- [ ] 内容过滤规则
- [ ] 同步统计报表

## 📝 文档

- [需求文档 v1.0](docs/requirements-v1.0.md) - 详细的功能需求和技术规格
- [开发进度](docs/development-progress.md) - 当前开发状态和计划
- [七牛云配置指南](docs/requirements-v1.0.md#附录a如何获取七牛云配置) - 七牛云详细配置步骤

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License