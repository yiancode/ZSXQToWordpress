# 接口定义文档

项目中所有组件的抽象接口定义。

## BaseClient 基础客户端接口

所有客户端的基类，定义了基本的连接管理方法。

### 方法

#### `validate_connection() -> bool`
验证客户端连接是否有效。

**返回值:**
- `bool`: 连接是否成功

#### `close() -> None`
关闭连接并清理资源。

## ContentClient 内容获取接口

继承自 `BaseClient`，用于获取内容数据。

### 方法

#### `get_content(content_id: str) -> Dict[str, Any]`
获取单个内容。

**参数:**
- `content_id` (str): 内容ID

**返回值:**
- `Dict[str, Any]`: 内容数据

#### `get_all_content(batch_size: int = 20, start_time: Optional[Any] = None, max_items: Optional[int] = None) -> List[Dict[str, Any]]`
获取所有内容。

**参数:**
- `batch_size` (int): 每批次大小，默认20
- `start_time` (Optional[Any]): 开始时间
- `max_items` (Optional[int]): 最大数量

**返回值:**
- `List[Dict[str, Any]]`: 内容列表

## PublishClient 发布客户端接口

继承自 `BaseClient`，用于发布内容。

### 方法

#### `create_post(title: str, content: str, categories: Optional[List[str]] = None, tags: Optional[List[str]] = None, status: str = 'publish') -> str`
创建文章。

**参数:**
- `title` (str): 标题
- `content` (str): 内容
- `categories` (Optional[List[str]]): 分类列表
- `tags` (Optional[List[str]]): 标签列表
- `status` (str): 发布状态，默认'publish'

**返回值:**
- `str`: 文章ID

#### `post_exists(title: str) -> bool`
检查文章是否存在。

**参数:**
- `title` (str): 文章标题

**返回值:**
- `bool`: 是否存在

## StorageClient 存储客户端接口

继承自 `BaseClient`，用于文件存储。

### 方法

#### `upload_file(local_path: str, remote_key: Optional[str] = None) -> Optional[str]`
上传文件。

**参数:**
- `local_path` (str): 本地文件路径
- `remote_key` (Optional[str]): 远程存储键名

**返回值:**
- `Optional[str]`: 访问URL，失败返回None

#### `download_file(url: str) -> Optional[str]`
下载文件。

**参数:**
- `url` (str): 文件URL

**返回值:**
- `Optional[str]`: 本地文件路径，失败返回None

## ContentProcessor 内容处理器接口

处理内容转换的抽象接口。

### 方法

#### `process_content(raw_content: Dict[str, Any]) -> Dict[str, Any]`
处理原始内容。

**参数:**
- `raw_content` (Dict[str, Any]): 原始内容数据

**返回值:**
- `Dict[str, Any]`: 处理后的内容数据

## StateManager 状态管理器接口

管理同步状态的抽象接口。

### 方法

#### `is_synced(item_id: str) -> bool`
检查是否已同步。

**参数:**
- `item_id` (str): 项目ID

**返回值:**
- `bool`: 是否已同步

#### `mark_synced(item_id: str, **kwargs) -> None`
标记为已同步。

**参数:**
- `item_id` (str): 项目ID
- `**kwargs`: 其他相关信息

#### `save() -> None`
保存状态到存储。

#### `load() -> None`
从存储加载状态。

## 实现示例

```python
class MyContentClient(ContentClient):
    def validate_connection(self) -> bool:
        # 实现连接验证逻辑
        return True
    
    def close(self) -> None:
        # 实现资源清理逻辑
        pass
    
    def get_content(self, content_id: str) -> Dict[str, Any]:
        # 实现获取单个内容的逻辑
        return {}
    
    def get_all_content(self, batch_size: int = 20, start_time=None, max_items=None):
        # 实现获取所有内容的逻辑
        return []
```