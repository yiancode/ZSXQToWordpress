#!/bin/bash
# 快速启动脚本 - ZSXQToWordPress

set -e  # 遇到错误立即退出

echo "🚀 ZSXQToWordPress 快速启动脚本"
echo "=================================="

# 检查Python版本
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python版本: $PYTHON_VERSION"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到pip3"
    exit 1
fi

# 安装依赖
echo ""
echo "安装Python依赖包..."
pip3 install -r requirements.txt

# 检查配置文件
echo ""
echo "检查配置文件..."
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        echo "⚠️  未找到config.json，复制示例配置文件..."
        cp config.example.json config.json
        echo "📝 请编辑 config.json 填入正确的配置信息："
        echo "   - 知识星球 access_token 和 group_id"
        echo "   - WordPress URL、用户名和密码"
        echo "   - 七牛云配置（可选）"
        echo ""
        echo "配置完成后重新运行此脚本"
        exit 0
    else
        echo "❌ 错误: 未找到配置文件模板"
        exit 1
    fi
fi

# 验证配置
echo ""
echo "验证配置..."
if ! python3 validate_config.py; then
    echo "❌ 配置验证失败，请检查 config.json"
    exit 1
fi

# 选择运行模式
echo ""
echo "选择运行模式:"
echo "1) 增量同步 (推荐)"
echo "2) 全量同步 (首次使用或重建)"
echo "3) 测试模式 (只同步2条内容)"

read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "开始增量同步..."
        python3 zsxq_to_wordpress.py --mode=incremental -v
        ;;
    2)
        echo "开始全量同步..."
        python3 zsxq_to_wordpress.py --mode=full -v
        ;;
    3)
        echo "开始测试同步..."
        ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=2 python3 zsxq_to_wordpress.py --mode=full -v
        ;;
    *)
        echo "无效选择，退出"
        exit 1
        ;;
esac

echo ""
echo "🎉 同步完成！"
echo ""
echo "后续使用:"
echo "  增量同步: python3 zsxq_to_wordpress.py --mode=incremental"
echo "  全量同步: python3 zsxq_to_wordpress.py --mode=full"
echo "  查看日志: tail -f zsxq_sync.log"
echo "  同步状态: cat sync_state.json"