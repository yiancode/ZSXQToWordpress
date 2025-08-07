# API 文档

知识星球到WordPress同步工具的API接口文档。

## 目录

- [接口概览](interfaces.md) - 所有接口的抽象定义
- [知识星球客户端](zsxq-client.md) - 知识星球API接口文档
- [WordPress客户端](wordpress-client.md) - WordPress XML-RPC接口文档
- [七牛云客户端](qiniu-client.md) - 七牛云存储接口文档
- [内容处理器](content-processor.md) - 内容转换处理接口
- [状态管理器](state-manager.md) - 同步状态管理接口

## 快速开始

```python
from zsxq_client import ZsxqClient
from wordpress_client import WordPressClient

# 初始化客户端
zsxq = ZsxqClient(access_token="your_token", user_agent="your_agent", group_id="group_id")
wp = WordPressClient(url="https://your-site.com/xmlrpc.php", username="user", password="pass")

# 验证连接
if zsxq.validate_connection() and wp.validate_connection():
    print("连接成功")
```

## 错误处理

所有API调用都应该包含适当的错误处理：

```python
try:
    topics = zsxq.get_all_content(batch_size=20)
except ZsxqAPIError as e:
    logger.error(f"知识星球API错误: {e}")
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise
```

## API限制和注意事项

- 知识星球API有频率限制，建议使用适当的延迟
- WordPress XML-RPC需要在后台启用
- 七牛云上传需要正确的bucket权限配置