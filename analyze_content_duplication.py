#!/usr/bin/env python3
"""
内容重复分析工具
分析标题和正文内容的重复问题
"""
import json
import re
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher
from collections import defaultdict


def load_sync_state() -> Dict[str, Any]:
    """加载同步状态文件"""
    try:
        with open('sync_state.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"synced_topics": {}}


def similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()


def analyze_title_content_duplication():
    """分析标题和正文内容重复问题"""
    print("🔍 开始分析标题和内容重复问题...")
    
    sync_state = load_sync_state()
    synced_topics = sync_state.get('synced_topics', {})
    
    print(f"\n📊 数据概览:")
    print(f"- 已同步内容数量: {len(synced_topics)}")
    
    duplication_issues = []
    
    for topic_id, info in synced_topics.items():
        title = info.get('title', '').strip()
        if not title:
            continue
        
        # 分析标题特征
        issue = {
            'topic_id': topic_id,
            'wordpress_id': info.get('wordpress_id'),
            'title': title,
            'title_length': len(title),
            'sync_time': info.get('sync_time'),
            'issues': []
        }
        
        # 1. 检查标题是否被截断
        if title.endswith('…') or title.endswith('...'):
            issue['issues'].append('标题被截断')
        
        # 2. 检查标题是否以空格开头
        if title.startswith(' '):
            issue['issues'].append('标题以空格开头')
            
        # 3. 检查标题长度
        if len(title) < 10:
            issue['issues'].append('标题过短')
        elif len(title) > 50:
            issue['issues'].append('标题过长')
        
        # 4. 检查是否包含正文内容
        # 如果标题包含"。"或包含完整句子，可能是正文内容被当作标题
        if '。' in title or ('，' in title and len(title) > 30):
            issue['issues'].append('标题包含正文内容')
        
        # 5. 检查重复的开头模式
        common_patterns = [
            '近期', '最近', '今天', '昨天', '刚刚', '分享',
            '推荐', '发现', '看到', '听说', '觉得', '认为'
        ]
        for pattern in common_patterns:
            if title.startswith(f' {pattern}') or title.startswith(pattern):
                issue['issues'].append(f'标题以常见词"{pattern}"开头')
                break
        
        if issue['issues']:
            duplication_issues.append(issue)
    
    # 按问题类型分类统计
    issue_stats = defaultdict(int)
    for item in duplication_issues:
        for issue_type in item['issues']:
            issue_stats[issue_type] += 1
    
    print(f"\n⚠️  发现的问题:")
    print(f"- 有问题的内容数量: {len(duplication_issues)} / {len(synced_topics)} ({len(duplication_issues)/len(synced_topics)*100:.1f}%)")
    
    print(f"\n📋 问题类型统计:")
    for issue_type, count in sorted(issue_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"- {issue_type}: {count} 条")
    
    print(f"\n🔍 具体问题示例:")
    for item in duplication_issues[:10]:  # 显示前10个问题
        print(f"\nWP ID {item['wordpress_id']}:")
        print(f"  标题: '{item['title']}'")
        print(f"  问题: {', '.join(item['issues'])}")
    
    return duplication_issues, issue_stats


def analyze_content_patterns():
    """分析内容生成模式"""
    print(f"\n🏷️  内容生成模式分析:")
    
    sync_state = load_sync_state()
    synced_topics = sync_state.get('synced_topics', {})
    
    titles = [info.get('title', '').strip() for info in synced_topics.values()]
    
    # 分析标题开头词汇
    start_words = defaultdict(int)
    for title in titles:
        if title:
            # 移除前导空格并获取第一个词
            clean_title = title.lstrip(' ')
            if clean_title:
                first_word = clean_title.split()[0] if clean_title.split() else clean_title[:5]
                start_words[first_word] += 1
    
    print(f"\n📊 标题开头词频统计（出现2次以上）:")
    for word, count in sorted(start_words.items(), key=lambda x: x[1], reverse=True):
        if count >= 2:
            print(f"  '{word}': {count} 次")
    
    # 分析标题长度分布
    length_distribution = defaultdict(int)
    for title in titles:
        length_range = (len(title) // 10) * 10
        length_distribution[f"{length_range}-{length_range + 9}"] += 1
    
    print(f"\n📏 标题长度分布:")
    for length_range, count in sorted(length_distribution.items()):
        print(f"  {length_range} 字符: {count} 条")


def suggest_improvements():
    """建议改进方案"""
    print(f"\n💡 改进建议:")
    
    print(f"\n1. 配置优化建议:")
    print(f"   - 增加 max_title_length 到 50-60 字符，减少截断")
    print(f"   - 设置更智能的标题生成逻辑")
    print(f"   - 配置标题前缀和后缀处理")
    
    print(f"\n2. 内容处理改进:")
    print(f"   - 从正文提取更有意义的标题")
    print(f"   - 去除标题前的空格和特殊字符")
    print(f"   - 避免将完整句子作为标题")
    
    print(f"\n3. 重复内容检测:")
    print(f"   - 实现标题去重机制")
    print(f"   - 检测相似内容并合并")
    print(f"   - 添加内容质量评估")


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 ZSXQ to WordPress 内容重复分析工具")
    print("=" * 60)
    
    duplication_issues, issue_stats = analyze_title_content_duplication()
    analyze_content_patterns()
    suggest_improvements()
    
    print(f"\n" + "=" * 60)
    print("📈 分析总结:")
    print(f"- 总内容数: {len(load_sync_state().get('synced_topics', {}))}")
    print(f"- 存在问题的内容: {len(duplication_issues)}")
    print(f"- 主要问题: 标题截断 ({issue_stats.get('标题被截断', 0)} 条)")
    print(f"- 需要优化标题生成逻辑和配置参数")
    print("=" * 60)