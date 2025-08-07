# 知识星球客户端 API

`ZsxqClient` 实现了 `ContentClient` 接口，用于与知识星球API进行交互。

## 初始化

```python
from zsxq_client import ZsxqClient

client = ZsxqClient(
    access_token="your_access_token",
    user_agent="your_user_agent", 
    group_id="your_group_id",
    max_retries=5,
    delay_seconds=5
)
```

### 参数说明

- `access_token` (str): 知识星球访问令牌
- `user_agent` (str): 用户代理字符串
- `group_id` (str): 群组ID
- `max_retries` (int): 最大重试次数，默认5
- `delay_seconds` (int): 请求延迟秒数，默认5

## 主要方法

### `validate_connection() -> bool`
验证与知识星球的连接是否有效。

```python
if client.validate_connection():
    print("连接成功")
else:
    print("连接失败")
```

### `get_topics(count: int = 20, end_time: str = None) -> List[Dict[str, Any]]`
获取主题列表。

**参数:**
- `count` (int): 获取数量，默认20
- `end_time` (str): 结束时间，ISO格式

**返回值:**
- `List[Dict[str, Any]]`: 主题列表

```python
topics = client.get_topics(count=10)
for topic in topics:
    print(f"主题: {topic['talk']['title']}")
```

### `get_topic_detail(topic_id: str) -> Dict[str, Any]`
获取主题详情。

**参数:**
- `topic_id` (str): 主题ID

**返回值:**
- `Dict[str, Any]`: 主题详情

```python
detail = client.get_topic_detail("12345")
print(f"详细内容: {detail}")
```

### `get_all_content(batch_size: int = 20, start_time=None, max_items=None) -> List[Dict[str, Any]]`
获取所有内容（分批获取）。

**参数:**
- `batch_size` (int): 每批次大小
- `start_time`: 开始时间（未实现）
- `max_items` (int): 最大获取数量

**返回值:**
- `List[Dict[str, Any]]`: 所有内容列表

```python
# 获取最多100个内容
all_content = client.get_all_content(batch_size=20, max_items=100)
print(f"总共获取了 {len(all_content)} 个内容")
```

### `get_target_topics(**kwargs) -> List[Dict[str, Any]]`
根据配置获取目标主题。

支持以下同步目标：
- `scope`: all(所有内容) 或 digests(精华内容)
- `column`: 专栏ID
- `hashtag`: 标签ID

**返回值:**
- `List[Dict[str, Any]]`: 目标主题列表

```python
# 获取精华内容
digests = client.get_target_topics(scope="digests")

# 获取指定专栏内容
column_content = client.get_target_topics(column_id="column_12345")
```

## 错误处理

### ZsxqAPIError
知识星球API相关错误。

```python
from zsxq_client import ZsxqAPIError

try:
    topics = client.get_topics()
except ZsxqAPIError as e:
    print(f"API错误: {e}")
```

## 常见错误码

- `401`: 认证失败，检查access_token
- `429`: 请求频率过高，会自动重试
- `1059`: 临时错误，会自动重试

## 使用建议

1. **频率控制**: 默认每次请求间隔5秒，避免触发频率限制
2. **重试机制**: 内置重试机制，会自动处理临时错误
3. **连接验证**: 使用前建议先调用 `validate_connection()` 验证
4. **资源清理**: 使用完毕后调用 `close()` 方法清理资源

```python
# 推荐使用方式
try:
    client = ZsxqClient(...)
    
    if not client.validate_connection():
        raise Exception("连接失败")
    
    # 进行操作
    topics = client.get_all_content()
    
finally:
    client.close()
```