# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

ZSXQToWordpress 是一个知识星球到WordPress内容同步工具，目前处于需求设计阶段。项目有两个版本规划：

1. **v1.0 简化版**（推荐先实现）：单脚本实现，4天开发计划
2. **完整版**：Web界面管理，7天AI辅助开发计划

## 开发指导

### 版本选择
建议先从 v1.0 版本开始实现（参考 `docs/requirements-v1.0.md`），这是一个单文件Python脚本，功能更聚焦。

### v1.0 版本技术要求
- Python 3.7+
- 核心依赖：requests, python-wordpress-xmlrpc, qiniu
- 配置文件：JSON格式
- 执行方式：命令行脚本

### 核心功能实现顺序
1. 配置文件加载和验证
2. 知识星球API认证和内容获取
3. WordPress XML-RPC连接和测试
4. 图片处理（下载、上传到七牛云）
5. 内容转换和发布
6. 同步状态管理（避免重复发布）

### 开发方法
项目采用TDD（测试驱动开发）方法，每个功能都应该：
1. 先写测试用例
2. 实现功能让测试通过
3. 重构优化代码

### 项目结构建议（v1.0）
```
├── zsxq_to_wordpress.py    # 主脚本
├── config.json            # 配置文件模板
├── requirements.txt       # Python依赖
├── tests/                 # 测试目录
│   └── test_sync.py      # 单元测试
└── sync_state.json       # 同步状态记录（运行时生成）
```

### 关键实现要点

1. **知识星球API调用**
   - 需要正确的认证headers
   - 注意API限流处理
   - 支持分页获取内容

2. **WordPress发布**
   - 使用XML-RPC接口
   - 处理分类映射
   - 保留原始格式

3. **图片处理**
   - 下载知识星球图片
   - 上传到七牛云
   - 替换文章中的图片链接

4. **状态管理**
   - 记录已同步的topic_id
   - 支持断点续传
   - 避免重复发布

### 测试命令（实现后）
```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 执行同步（全量）
python zsxq_to_wordpress.py --mode=full

# 执行同步（增量）
python zsxq_to_wordpress.py --mode=incremental
```

### AI辅助开发流程
使用项目中的 `.claude/commands/` 工作流：
- `/spec` - 查看和理解需求规格
- `/code` - 生成代码实现
- `/test` - 创建测试用例
- `/debug` - 调试问题

### 注意事项
1. 优先实现核心同步功能，UI和高级特性后续迭代
2. 确保API密钥等敏感信息只存在配置文件中，不要硬编码
3. 添加适当的错误处理和日志记录
4. 考虑知识星球API的限流策略