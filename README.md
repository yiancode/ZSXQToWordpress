# 知识星球到WordPress同步工具

一个将知识星球内容同步到WordPress的Python脚本工具。

## 功能特性

- ✅ 支持全量同步和增量同步
- ✅ 自动处理图片上传（支持七牛云）
- ✅ 内容格式转换（保留段落、处理@提及、话题标签等）
- ✅ 重复内容检测，避免重复发布
- ✅ 同步状态管理，支持断点续传
- ✅ 详细的日志记录

## 安装

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

## 使用方法

### 全量同步
```bash
python zsxq_to_wordpress.py --mode=full
```

### 增量同步（默认）
```bash
python zsxq_to_wordpress.py
```

### 使用自定义配置文件
```bash
python zsxq_to_wordpress.py --config=myconfig.json
```

### 显示详细日志
```bash
python zsxq_to_wordpress.py -v
```

## 文件说明

- `zsxq_to_wordpress.py` - 主程序入口
- `config_manager.py` - 配置管理模块
- `zsxq_client.py` - 知识星球API客户端
- `wordpress_client.py` - WordPress XML-RPC客户端
- `qiniu_uploader.py` - 七牛云图片上传模块
- `content_processor.py` - 内容处理和转换模块
- `sync_state.py` - 同步状态管理模块
- `sync_state.json` - 同步状态记录文件（自动生成）
- `zsxq_sync.log` - 运行日志文件（自动生成）

## 注意事项

1. 首次运行建议使用增量同步模式测试
2. 同步状态文件 `sync_state.json` 很重要，不要随意删除
3. 如果需要重新同步所有内容，可以删除 `sync_state.json` 文件
4. 建议定期备份 `sync_state.json` 文件

## 常见问题

### Q: XML-RPC连接失败
A: 请确保WordPress已启用XML-RPC功能。可以在WordPress后台安装并启用 "XML-RPC" 相关插件。

### Q: 知识星球认证失败
A: access_token可能已过期，请重新获取。

### Q: 图片上传失败
A: 检查七牛云配置是否正确，或者暂时不配置七牛云，使用原始图片链接。

### Q: 如何避免重复发布？
A: 脚本会自动检查标题是否已存在，并记录已同步的topic_id。

## 开发计划

- [ ] 支持更多图片存储服务
- [ ] 支持自定义内容转换规则
- [ ] 支持多个知识星球同步
- [ ] Web管理界面

## 许可证

MIT License