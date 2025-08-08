# ContentProcessor 内容处理器

内容处理器负责将知识星球内容转换为WordPress格式，处理各种特殊格式和媒体文件。

## 概述

`ContentProcessor` 类是同步工具的核心组件，负责：

- 内容类型识别（文章 vs 片刻）
- 知识星球特殊格式转换
- 图片和媒体文件处理
- HTML标签清理和优化
- 标题生成和去重

## 核心方法

### process_topic(topic)

处理单个知识星球主题，返回WordPress格式的内容数据。

```python
def process_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
    """处理单个主题，转换为WordPress内容格式
    
    Args:
        topic: 知识星球主题数据
        
    Returns:
        处理后的内容数据，包含：
        - topic_id: 主题ID
        - title: 标题
        - content: 处理后的HTML内容
        - images: 图片URL列表
        - tags: 标签列表
        - categories: 分类列表
        - content_type: 'article' 或 'short_content'
        - post_type: WordPress文章类型
    """
```

### 内容类型判断

系统会根据以下规则自动判断内容类型：

#### 片刻 (short_content)
- `topic.talk` 存在但 `topic.talk.article` 不存在
- 通常是简短的文字分享配图片

#### 文章 (article)
- `topic.talk.article` 存在（正式文章）
- 问答类型内容（q&a-question, q&a-answer）
- 其他有结构化内容的类型

## 特殊格式处理

### 知识星球自定义标签

#### 图片标签处理
```html
<!-- 输入：知识星球自定义标签 -->
<e type="image" src="https://example.com/image.jpg" title="图片描述" iid="12345"/>

<!-- 输出：标准HTML -->
<img src="https://cdn.doip.cc/processed_image.jpg" alt="图片描述">
```

#### Hashtag标签处理
```html
<!-- 输入：知识星球hashtag标签 -->
<e type="hashtag" hid="123" title="%23AI编程%23"/>

<!-- 输出：简洁文本格式 -->
#AI编程#
```

#### 文本格式标签
- `<e type="text_bold">` → `**粗体文本**`
- `<e type="text_italic">` → `*斜体文本*`
- `<e type="text_delete">` → `~~删除线文本~~`

### URL解码处理

所有URL编码的内容都会自动解码：
- `%23` → `#`
- `%20` → 空格
- 其他标准URL编码字符

## 图片处理功能

### 图片提取和转换

```python
def _extract_images(self, topic: Dict[str, Any]) -> List[str]:
    """递归提取主题中的所有图片URL
    
    优先级顺序：
    1. large (大图)
    2. original (原图)
    3. thumbnail (缩略图)
    4. url (直接URL)
    """
```

### 图片格式化

```python
def format_article_with_images(self, article: Dict[str, Any], 
                             processed_images: Dict[str, str]) -> str:
    """将处理后的图片整合到文章内容中
    
    功能：
    - 替换内容中的原始图片URL为CDN URL
    - 将未嵌入的图片添加到内容末尾
    - 生成标准的HTML img标签
    """
```

## 标签和分类处理

### 标签提取

支持多种hashtag格式：
- HTML格式：`<e type="hashtag" title="%23标签%23"/>`
- 普通格式：`#标签名#`
- 自动去重和清理

### 分类映射

根据配置自动分类：
- 专栏映射（如果启用）
- 特殊分类（精华、置顶）
- 默认分类（基于内容类型）

## 标题生成策略

### 智能标题生成

```python
def _generate_title(self, topic: Dict[str, Any]) -> str:
    """智能生成文章标题
    
    策略：
    1. 使用内容第一行（如果适合作标题）
    2. 智能截断（在合适位置）
    3. 关键词提取
    4. 时间戳标题（最后选择）
    """
```

### 去重机制

- 自动检测标题与内容首行重复
- 支持完全匹配、截断匹配、模糊匹配
- 智能移除重复内容

## 内容清理功能

### 知识星球页脚清理

自动移除知识星球特有的页脚信息：
- `——发布于 xxx 2024-01-01 12:00:00`
- `—发布于 xxx 2024-01-01 12:00:00`
- `发布于 xxx 2024-01-01 12:00:00`

### HTML标签处理

- 移除不安全的HTML标签
- 规范化段落结构
- 保留语义化内容

## 配置选项

### 内容映射配置

```json
{
  "content_mapping": {
    "article_settings": {
      "sync_title": true,
      "placeholder_title": "无标题文章",
      "default_classification": "Article"
    },
    "topic_settings": {
      "sync_title": true,
      "placeholder_title": "片刻",
      "title_prefix": "[片刻]",
      "max_title_length": 30,
      "default_classification": "Trending",
      "use_custom_post_type": true
    },
    "post_types": {
      "article": "post",
      "topic": "moment"
    }
  }
}
```

## 使用示例

```python
from content_processor import ContentProcessor

# 初始化处理器
processor = ContentProcessor(config=config, zsxq_client=zsxq_client)

# 处理单个主题
topic_data = {...}  # 来自知识星球API
processed_content = processor.process_topic(topic_data)

# 格式化带图片的内容
if processed_content['images']:
    # 假设图片已经通过七牛云处理
    processed_images = {...}  # 原始URL -> CDN URL映射
    final_content = processor.format_article_with_images(
        processed_content, 
        processed_images
    )
```

## 错误处理

处理器内置了完善的错误处理机制：

- URL解析错误：使用默认值
- 日期解析错误：提供详细错误信息
- 图片处理错误：跳过问题图片，继续处理其他内容
- HTML解析错误：清理有问题的标签

## 性能优化

### 正则表达式预编译

所有常用的正则表达式都在初始化时预编译：

```python
self._re_image_link = re.compile(r'<e type="image"[^>]*/>')
self._re_hashtag = re.compile(r'<e type="hashtag"[^>]*>#([^<]+)#</e>')
# ... 更多预编译正则表达式
```

### 批量处理支持

- 支持批量图片处理
- 递归内容提取优化
- 内存高效的文本处理

## 最新修复 (v1.1.0)

### doip.cc 显示问题修复

1. **自定义HTML标签处理**
   - 修复 `<e type="image">` 标签显示问题
   - 修复 `<e type="hashtag">` 标签显示问题
   - 正确转换为标准HTML元素

2. **图片显示优化**
   - 图片正确转换为标准 `<img>` 标签
   - 支持CDN链接替换
   - 修复列表页面图片显示异常

3. **内容处理增强**
   - 改进URL解码逻辑
   - 优化图片嵌入机制
   - 简化hashtag处理流程

这些修复确保了从知识星球同步到WordPress的内容能够在doip.cc等网站上正确显示，解决了图片显示为HTML标签、hashtag无法正确渲染等问题。