#!/usr/bin/env python3
"""
重置同步状态并应用新配置的工具
用于清理现有状态并重新同步以应用新的标题配置
"""
import json
import os
import subprocess
from datetime import datetime


def backup_sync_state():
    """备份现有的同步状态"""
    if os.path.exists('sync_state.json'):
        backup_name = f'sync_state_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.rename('sync_state.json', backup_name)
        print(f"✅ 已备份同步状态到: {backup_name}")
        return backup_name
    return None


def reset_sync_state():
    """重置同步状态，只保留最新的一条内容作为测试"""
    backup_file = backup_sync_state()
    
    # 创建新的最小状态文件，保留一些关键信息但清空已同步列表
    new_state = {
        "synced_topics": {},
        "last_sync_time": None,
        "sync_history": []
    }
    
    with open('sync_state.json', 'w', encoding='utf-8') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)
    
    print("✅ 同步状态已重置")
    return backup_file


def test_new_config():
    """测试新配置的效果"""
    print("\n🧪 测试新配置效果...")
    print("运行小规模测试同步（2条内容）...")
    
    result = subprocess.run([
        'python3', 'zsxq_to_wordpress.py', 
        '--mode=full', '-v'
    ], env={
        **os.environ,
        'ZSXQ_TEST_MODE': '1',
        'ZSXQ_MAX_TOPICS': '2'
    }, capture_output=True, text=True)
    
    print(f"退出码: {result.returncode}")
    if result.stdout:
        print("输出:")
        print(result.stdout)
    if result.stderr:
        print("错误:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    print("🔄 开始重置同步状态并测试新配置...")
    print("=" * 50)
    
    # 确认操作
    response = input("⚠️  这将清空所有同步状态，重新开始同步。继续吗？ (y/N): ")
    if response.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    # 重置状态
    backup_file = reset_sync_state()
    
    # 测试新配置
    success = test_new_config()
    
    if success:
        print("\n✅ 新配置测试成功！")
        print("现在可以运行完整同步来应用新的标题配置")
        print("\n建议命令:")
        print("ZSXQ_TEST_MODE=1 ZSXQ_MAX_TOPICS=10 python3 zsxq_to_wordpress.py --mode=full -v")
    else:
        print("\n❌ 新配置测试失败")
        if backup_file:
            print(f"如需恢复，可以将 {backup_file} 重命名为 sync_state.json")


if __name__ == "__main__":
    main()