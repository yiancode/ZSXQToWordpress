# 故障排除指南

知识星球到WordPress同步工具的常见问题解决方案。

## 目录

- [快速诊断](#快速诊断)
- [配置问题](#配置问题)
- [连接问题](#连接问题)
- [同步问题](#同步问题)
- [性能问题](#性能问题)
- [错误代码参考](#错误代码参考)
- [日志分析](#日志分析)
- [紧急情况处理](#紧急情况处理)

## 快速诊断

### 健康检查清单

运行以下命令进行基本诊断：

```bash
# 1. 检查Python版本
python3 --version

# 2. 检查依赖
pip3 show requests python-wordpress-xmlrpc qiniu python-dateutil

# 3. 检查配置文件
python3 -c "import json; print(json.load(open('config.json')))"

# 4. 测试网络连接
python3 -c "
import requests
try:
    r = requests.get('https://api.zsxq.com', timeout=10)
    print(f'知识星球API连通性: {r.status_code}')
    r = requests.get('https://your-wordpress-site.com', timeout=10)  
    print(f'WordPress连通性: {r.status_code}')
except Exception as e:
    print(f'网络连接问题: {e}')
"
```

## 配置问题

### Q: 配置文件加载失败

**错误信息**: `ConfigError: 配置文件不存在: config.json`

**解决方案**:
```bash
# 检查配置文件是否存在
ls -la config.json

# 如果不存在，从模板复制
cp config.example.json config.json

# 编辑配置文件
nano config.json
```

### Q: 环境变量不生效

**错误信息**: `缺少知识星球 access_token`

**解决方案**:
```bash
# 检查环境变量
echo $ZSXQ_ACCESS_TOKEN
echo $WORDPRESS_USERNAME

# 临时设置环境变量
export ZSXQ_ACCESS_TOKEN="your_token_here"

# 永久设��（添加到 ~/.bashrc）
echo 'export ZSXQ_ACCESS_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

### Q: JSON配置格式错误

**错误信息**: `配置文件格式错误: Expecting ',' delimiter`

**解决方案**:
```bash
# 使用Python验证JSON格式
python3 -m json.tool config.json

# 常见格式错误：
# 1. 缺少逗号
# 2. 多余的逗号
# 3. 引号不匹配
# 4. 中文引号
```

## 连接问题

### Q: 知识星球API认证失败

**错误信息**: `认证失败，请检查access_token是否有效`

**解决方案**:

1. **检查token有效性**:
```bash
curl -H "Cookie: zsxq_access_token=YOUR_TOKEN" \
     -H "User-Agent: YOUR_USER_AGENT" \
     "https://api.zsxq.com/v2/groups/YOUR_GROUP_ID/topics?count=1"
```

2. **更新token**:
   - 登录知识星球网页版
   - 检查开发者工具中的Cookie
   - 更新config.json中的access_token

3. **检查User-Agent**:
   - 确保使用真实的浏览器User-Agent
   - 避免使用明显的爬虫标识

### Q: WordPress连接失败

**错误信息**: `WordPress连接失败: 401 Unauthorized`

**解决方案**:

1. **检查XML-RPC是否启用**:
```bash
curl -X POST https://your-site.com/xmlrpc.php \
     -H "Content-Type: application/xml" \
     -d "<?xml version='1.0'?><methodCall><methodName>system.listMethods</methodName></methodCall>"
```

2. **验证用户权限**:
   - 确保用户具有发布文章权限
   - 建议使用应用密码而非普通密码

3. **SSL证书问题**:
```python
# 临时禁用SSL验证（仅用于测试）
export WORDPRESS_VERIFY_SSL=false
```

### Q: 网络超时

**错误信息**: `请求失败: Connection timeout`

**解决方案**:

1. **检查网络连通性**:
```bash
ping api.zsxq.com
ping your-wordpress-site.com
```

2. **调整超时设置**:
```python
# 在代码中增加超时时间
session.timeout = (30, 60)  # 连接超时30秒，读取超时60秒
```

3. **使用代理**:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

## 同步问题

### Q: 内容显示问题（最新修复 v1.1.0）

**现象**: doip.cc等WordPress站点上出现以下问题：
- 图片显示为HTML标签而不是实际图片
- hashtag标签显示为原始HTML代码
- 自定义元素 `<e type="image">` 和 `<e type="hashtag">` 无法正确渲染
- 长内容展开功能不完善

**错误示例**:
```html
<!-- 在页面上显示为文本而不是图片 -->
<e type="image" src="https://cdn.doip.cc/image.jpg" title="%E5%9B%BE%E7%89%87"/>

<!-- hashtag标签也显示为原始代码 -->
<e type="hashtag" hid="123" title="%23AI%E7%BC%96%E7%A8%8B%23"/>
```

**解决方案** (已在v1.1.0中修复):

1. **自动标签转换**:
   - `<e type="image">` 自动转换为标准 `<img>` 标签
   - `<e type="hashtag">` 自动转换为 `#标签#` 文本格式
   - URL自动解码处理

2. **在content_processor.py中的修复**:
```python
# 图片标签处理
self._re_image_link = re.compile(r'<e type="image"[^>]*/>')
processed = self._re_image_link.sub(self._replace_image_tag, processed)

# hashtag标签处理  
processed = self._process_hashtag_tags(processed)
```

3. **验证修复效果**:
```bash
# 同步测试内容
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=5 python3 zsxq_to_wordpress.py --mode=full

# 检查WordPress站点
# - 图片正常显示
# - hashtag标签正常显示
# - 无HTML源代码显示
```

**注意事项**:
- 这些修复仅影响新同步的内容
- 已同步的历史内容不会被自动更新
- 如需更新历史内容，可删除sync_state.json中的相关记录后重新同步

### Q: WordPress主题HTML渲染问题

**现象**: 在WordPress前端页面中出现以下问题：
- HTML标记语言显示为原始文本而不是渲染效果
- 图片在列表页面不显示
- 来源链接格式解析错误，显示异常字符

**错误示例**:
```html
<!-- 显示原始HTML代码而不是渲染效果 -->
"https://cdn.doip.cc/...jpg\" alt=\"图片\" style=\"max-width: 100%; height: auto;\">

<!-- 来源链接格式异常 -->
—— 发布于 <a class="\" target=\"_blank\">易安AI编程·副业 2025-08-XX XX:XX:XX
```

**根本原因**: 
WordPress主题对复杂HTML结构解析不兼容，特别是包含嵌套标签和特殊字符的链接。

**解决方案**:

1. **简化HTML结构**:
```python
# 修改content_processor.py中的图片处理
# 原来的复杂结构
# content += f'\n\n<p><img src="{new_url}" alt="图片" style="max-width: 100%; height: auto;"></p>'

# 简化后的结构  
content += '\n\n<p>' + '</p>\n\n<p>'.join(image_html) + '</p>'
```

2. **优化链接处理**:
```python
# 使用简化的链接格式避免解析问题
def _replace_simple_link(self, match):
    if self._is_image_url(url):
        return f'[图片: {url}]'  # 图片使用纯文本格式
    else:
        return f'<a href="{url}">{link_text}</a>'  # 链接使用标准格式
```

3. **配置来源信息显示**:
```json
{
  "sync": {
    "add_source_footer": false  // 关闭来源信息避免解析问题
  }
}
```

**验证方法**:
```bash
# 运行测试同步
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=5 python3 zsxq_to_wordpress.py --mode=full

# 检查WordPress前端页面
# 确认HTML正确渲染，图片正常显示，无异常字符
```

### Q: 知识星球文章链接内容不完整

**现象**: 同步的内容只有摘要，没有获取文章详情页的完整内容

**解决方案**: 
系统已自动检测文章链接并获取完整内容：

```python
# 在_process_article方法中自动检测和获取
if 'article' in talk_data and talk_data['article'] and self.zsxq_client:
    article_url = article_data.get('article_url', '')
    if article_url:
        # 提取文章ID并获取完整内容
        topic_id_match = re.search(r'/topics/(\d+)', article_url)
        if topic_id_match:
            full_article = self.zsxq_client.get_topic_detail(article_topic_id)
            # 使用完整内容替换摘要
```

### Q: 内容同步不完整

**现象**: 部分内容没有同步到WordPress

**排查步骤**:

1. **检查同步状态**:
```bash
# 查看状态文件
cat sync_state.json | python3 -m json.tool

# 检查最近同步记录
python3 -c "
import json
state = json.load(open('sync_state.json'))
print(f'上次同步时间: {state.get(\"last_sync_time\")}')
print(f'已同步数量: {len(state.get(\"synced_topics\", {}))}')
"
```

2. **检查日志中的错误**:
```bash
# 查看最近的错误
tail -n 100 zsxq_sync.log | grep ERROR

# 按时间查看日志
grep "$(date +%Y-%m-%d)" zsxq_sync.log
```

3. **手动重试失败项**:
```bash
# 删除状态文件中的特定项目，强制重新同步
python3 -c "
import json
state = json.load(open('sync_state.json'))
if 'failed_topic_id' in state['synced_topics']:
    del state['synced_topics']['failed_topic_id']
    json.dump(state, open('sync_state.json', 'w'), indent=2)
    print('已移除失败项目，将在下次同步时重试')
"
```

### Q: 图片上传失败

**错误信息**: `七牛云上传失败` 或 `图片下载失败`

**解决方案**:

1. **七牛云配置检查**:
```python
from qiniu import Auth
auth = Auth('access_key', 'secret_key')
token = auth.upload_token('bucket_name', 'test_key', 3600)
print(f'Token生成成功: {token[:20]}...')
```

2. **网络问题排查**:
```bash
# 测试图片URL可访问性
curl -I "https://image-url-from-zsxq.com/image.jpg"

# 测试七牛云上传
curl -H "Authorization: UpToken YOUR_TOKEN" \
     -F "file=@test.jpg" \
     -F "key=test" \
     https://upload.qiniup.com
```

3. **跳过图片上传**:
```json
{
  "qiniu": {
    "access_key": "",
    "secret_key": "", 
    "bucket": "",
    "domain": ""
  }
}
```

### Q: 同步速度太慢

**现象**: 同步1000个内容需要数小时

**优化方案**:

1. **调整API延迟**:
```python
# 在zsxq_client.py中修改
self.delay_seconds = 2  # 从5秒降低到2秒
```

2. **启用并发同步**:
```bash
python3 zsxq_to_wordpress.py --mode=concurrent --workers=3
```

3. **分批处理**:
```bash
# 限制每次同步数量
ZSXQ_MAX_TOPICS=50 python3 zsxq_to_wordpress.py --mode=incremental
```

## 性能问题

### Q: 内存使用过高

**现象**: Python进程占用大量内存

**解决方案**:

1. **检查内存使用**:
```bash
# 监控内存使用
top -p $(pgrep -f zsxq_to_wordpress.py)

# 使用内存分析工具
python3 -m memory_profiler zsxq_to_wordpress.py
```

2. **优化内存使用**:
```python
# 分批处理大数据集
def process_in_batches(items, batch_size=100):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
        # 强制垃圾回收
        import gc
        gc.collect()
```

### Q: CPU使用率过高

**现象**: CPU长时间保持高使用率

**解决方案**:

1. **降低并发数**:
```bash
python3 zsxq_to_wordpress.py --mode=concurrent --workers=2
```

2. **增加处理间隔**:
```python
import time
time.sleep(0.1)  # 在循环中添加短暂休眠
```

## 错误代码参考

### 知识星球API错误

| 错误代码 | 含义 | 解决方案 |
|---------|------|----------|
| 401 | 认证失败 | 检查access_token |
| 429 | 请求频率过高 | 增加延迟时间 |
| 1059 | 临时错误 | 自动重试，无需干预 |
| 403 | 权限不足 | 检查群组访问权限 |

### WordPress错误

| 错误代码 | 含义 | 解决方案 |
|---------|------|----------|
| 401 | 认证失败 | 检查用户名密码 |
| 403 | 权限不足 | 检查用户权限 |
| 500 | 服务器错误 | 检查WordPress配置 |
| XML-RPC服务未启用 | XML-RPC被禁用 | 启用XML-RPC功能 |

## 日志分析

### 常用日志查看命令

```bash
# 查看实时日志
tail -f zsxq_sync.log

# 按级别过滤日志
grep "ERROR" zsxq_sync.log
grep "WARNING" zsxq_sync.log

# 按时间范围查看
grep "2024-01-01 10:" zsxq_sync.log

# 统计错误数量
grep -c "ERROR" zsxq_sync.log

# 查看最近的同步结果
grep "同步完成" zsxq_sync.log | tail -10
```

### 日志级别说明

- **DEBUG**: 详细调试信息
- **INFO**: 一般信息，如同步进度
- **WARNING**: 警告信息，不影响运行
- **ERROR**: 错误信息，需要关注
- **CRITICAL**: 严重错误，程序可能停止

## 紧急情况处理

### 系统完全无法启动

1. **检查基本环境**:
```bash
python3 --version
pip3 list
```

2. **重新安装依赖**:
```bash
pip3 install -r requirements.txt --force-reinstall
```

3. **使用测试模式**:
```bash
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=1 python3 zsxq_to_wordpress.py --mode=full --verbose
```

### 大量内容同步失败

1. **停止当前同步**:
```bash
pkill -f zsxq_to_wordpress.py
```

2. **备份状态文件**:
```bash
cp sync_state.json sync_state.json.backup.$(date +%Y%m%d_%H%M%S)
```

3. **重置同步状态**（慎用）:
```bash
echo '{"synced_topics": {}, "last_sync_time": null, "sync_history": []}' > sync_state.json
```

### 获取技术支持

如果以上方案都无法解决问题，请：

1. **收集信息**:
   - 错误日志（最近100行）
   - 配置文件（敏感信息已遮蔽）
   - Python和依赖版本信息
   - 操作系统信息

2. **创建Issue**:
   - 访问项目GitHub仓库
   - 创建新的Issue
   - 详细描述问题和已尝试的解决方案

3. **联系方式**:
   - GitHub Issues（推荐）
   - 项目文档中的联系信息