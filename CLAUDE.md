# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

ZSXQToWordpress 是一个成熟的知识星球到WordPress内容同步工具，当前版本v1.1.0。项目采用模块化架构，支持全量、增量和并发同步模式。

## 常用命令

### 开发环境设置
```bash
# 安装依赖
pip3 install -r requirements.txt

# 生成配置文件
cp config.example.json config.json
# 编辑config.json填入实际配置

# 一键启动（包含环境检查）
chmod +x quick_start.sh
./quick_start.sh
```

### 运行同步任务
```bash
# 增量同步（推荐日常使用）
python3 zsxq_to_wordpress.py --mode=incremental

# 全量同步（首次运行或需要完整同步时）
python3 zsxq_to_wordpress.py --mode=full

# 并发同步（大批量内容时使用）
python3 zsxq_to_wordpress.py --mode=concurrent --workers=5

# 测试模式（限制处理数量）
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=2 python3 zsxq_to_wordpress.py --mode=full
```

### 配置管理
```bash
# 使用环境变量配置（推荐生产环境）
export ZSXQ_ACCESS_TOKEN="your-token"
export WORDPRESS_USERNAME="your-username"
export WORDPRESS_PASSWORD="your-password"

# 验证SSL证书（生产环境建议开启）
export SSL_VERIFY=true
```

## 架构设计

### 核心模块架构
项目基于接口抽象层(`interfaces.py`)构建，主要模块包括：

1. **数据获取层**
   - `zsxq_client.py`: 知识星球API客户端，实现ContentClient接口
   - 处理API认证、分页获取、限流控制

2. **内容处理层**
   - `content_processor.py`: 内容格式转换，实现ContentProcessor接口
   - 支持文章/片刻分类映射、图片链接替换

3. **发布层**
   - `wordpress_client.py`: WordPress XML-RPC客户端，实现PublishClient接口
   - `qiniu_uploader.py`: 七牛云图片上传，实现StorageClient接口

4. **状态管理层**
   - `sync_state.py`: 同步状态持久化，实现StateManager接口
   - 支持断点续传、避免重复发布

5. **主控制器**
   - `zsxq_to_wordpress.py`: 协调各模块，实现三种同步模式

6. **辅助模块**
   - `config_manager.py`: 配置文件管理，支持环境变量覆盖
   - `log_utils.py`: 敏感信息过滤，确保日志安全
   - `config_generator.py`: 交互式配置文件生成助手
   - `test_optimizations.py`: 性能测试工具

### 关键设计模式
- **策略模式**: 不同同步模式的实现(全量/增量/并发)
- **依赖注入**: 通过接口实现模块解耦
- **线程池**: 并发模式下的批量处理

## 开发注意事项

### 代码架构原则
- 所有核心模块都基于`interfaces.py`中定义的抽象接口
- 遵循单一职责原则，每个模块负责特定功能
- 使用依赖注入实现模块间解耦
- 支持通过环境变量覆盖配置文件中的敏感信息

### API调用限制
- 知识星球API有访问限制，默认请求间隔1秒
- WordPress XML-RPC需要在WordPress后台开启
- 七牛云上传需要配置正确的bucket权限

### 错误处理
- 所有模块都实现了重试机制（默认3次）
- 日志中会自动过滤敏感信息（密码、token等）通过`log_utils.py`模块
- 网络错误会自动重试，API错误会记录并跳过
- 支持并发处理时的线程安全状态管理

### 状态文件
- `sync_state.json`: 记录已同步的topic_id
- `config.json`: 配置文件（不要提交到版本控制）
- 日志文件自动按日期轮转

### 内容映射逻辑
- 根据`content_mapping`配置自动判断内容类型
- 支持基于标题关键词的分类映射
- 图片自动下载并上传到七牛云（如配置）

## 测试和调试

### 调试建议
```bash
# 开启详细日志
python3 zsxq_to_wordpress.py --mode=incremental --verbose

# 使用测试模式限制处理数量
ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=5 python3 zsxq_to_wordpress.py

# 检查同步状态
cat sync_state.json | python -m json.tool

# 配置生成助手（交互式配置）
python3 config_generator.py

# 性能测试（验证优化效果）
python3 test_optimizations.py
```

### 常见问题排查
1. **SSL证书错误**: 设置 `SSL_VERIFY=false`（仅测试环境）
2. **API认证失败**: 检查access_token是否正确
3. **WordPress发布失败**: 确认XML-RPC已开启，用户权限正确
4. **图片上传失败**: 验证七牛云配置和bucket权限

## 扩展开发

### 添加新的内容源
1. 在`interfaces.py`中实现`ContentClient`接口
2. 参考`zsxq_client.py`实现具体逻辑
3. 在主程序中注册新的内容源

### 添加新的发布目标
1. 实现`PublishClient`接口
2. 参考`wordpress_client.py`的实现模式
3. 更新配置结构支持新目标

### 自定义内容处理
1. 继承`ContentProcessor`类
2. 重写`process_content`方法
3. 在配置中指定使用自定义处理器