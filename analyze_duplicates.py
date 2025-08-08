#!/usr/bin/env python3
"""
标题重复分析工具
分析主题、文章、片刻是否存在标题重复问题
"""
import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Any
import requests
from config_manager import Config
from wordpress_client import WordPressClient


def load_sync_state() -> Dict[str, Any]:
    """加载同步状态文件"""
    try:
        with open('sync_state.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"synced_topics": {}}


def analyze_title_duplicates():
    """分析标题重复情况"""
    print("🔍 开始分析标题重复情况...")
    
    # 1. 分析sync_state.json中的标题
    sync_state = load_sync_state()
    synced_topics = sync_state.get('synced_topics', {})
    
    print(f"\n📊 同步状态文件分析:")
    print(f"- 已同步主题数量: {len(synced_topics)}")
    
    # 提取标题
    titles = []
    title_to_ids = defaultdict(list)
    
    for topic_id, info in synced_topics.items():
        title = info.get('title', '').strip()
        if title:
            titles.append(title)
            title_to_ids[title].append({
                'topic_id': topic_id,
                'wordpress_id': info.get('wordpress_id'),
                'sync_time': info.get('sync_time')
            })
    
    # 统计标题重复情况
    title_counts = Counter(titles)
    duplicates = {title: count for title, count in title_counts.items() if count > 1}
    
    print(f"\n🔄 标题重复分析:")
    print(f"- 总标题数: {len(titles)}")
    print(f"- 唯一标题数: {len(title_counts)}")
    print(f"- 重复标题数: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️  发现重复标题:")
        for title, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
            print(f"   '{title}' - 出现 {count} 次")
            for item in title_to_ids[title]:
                print(f"     → Topic ID: {item['topic_id']}, WP ID: {item['wordpress_id']}")
    else:
        print("\n✅ 未发现重复标题")
    
    # 2. 通过WordPress API分析发布内容
    try:
        print(f"\n🔗 WordPress内容分析:")
        config = Config()
        wp_client = WordPressClient(config)
        
        # 获取最近发布的内容分析
        print("- 正在获取WordPress文章...")
        
        # 这里我们分析一下标题格式
        print("- WordPress连接分析跳过")
        
    except Exception as e:
        print(f"WordPress分析失败: {e}")
    
    # 3. 分析标题格式
    print(f"\n📝 标题格式分析:")
    short_titles = [title for title in titles if len(title.strip()) < 20]
    long_titles = [title for title in titles if len(title.strip()) >= 50]
    placeholder_titles = [title for title in titles if title.strip() in ['', ' ', '无标题']]
    
    print(f"- 短标题（<20字符）: {len(short_titles)} 个")
    print(f"- 长标题（≥50字符）: {len(long_titles)} 个")
    print(f"- 占位标题: {len(placeholder_titles)} 个")
    
    if short_titles[:5]:
        print("   短标题示例:")
        for title in short_titles[:5]:
            print(f"     '{title}'")
    
    # 4. 分析标题生成模式
    print(f"\n🏷️  标题生成模式分析:")
    
    # 分析以空格开头的标题
    space_prefix_titles = [title for title in titles if title.startswith(' ')]
    print(f"- 以空格开头的标题: {len(space_prefix_titles)} 个")
    
    # 分析截断标题（以...结尾）
    truncated_titles = [title for title in titles if title.endswith('…') or title.endswith('...')]
    print(f"- 被截断的标题: {len(truncated_titles)} 个")
    
    if truncated_titles[:3]:
        print("   截断标题示例:")
        for title in truncated_titles[:3]:
            print(f"     '{title}'")
    
    return {
        'total_titles': len(titles),
        'unique_titles': len(title_counts),
        'duplicates': duplicates,
        'short_titles': len(short_titles),
        'long_titles': len(long_titles),
        'placeholder_titles': len(placeholder_titles),
        'space_prefix_titles': len(space_prefix_titles),
        'truncated_titles': len(truncated_titles)
    }


def analyze_content_types():
    """分析内容类型分布"""
    print(f"\n📋 内容类型分析:")
    
    try:
        config = Config()
        config_data = config._config  # 直接访问私有属性
        content_mapping = config_data.get('content_mapping', {})
        
        print(f"- 启用类型映射: {content_mapping.get('enable_type_mapping', False)}")
        print(f"- 文章类型: {content_mapping.get('article_types', [])}")
        print(f"- 主题类型: {content_mapping.get('topic_types', [])}")
        
        topic_settings = content_mapping.get('topic_settings', {})
        article_settings = content_mapping.get('article_settings', {})
        
        print(f"\n主题设置:")
        print(f"- 同步标题: {topic_settings.get('sync_title', True)}")
        print(f"- 占位标题: '{topic_settings.get('placeholder_title', '无标题')}'")
        print(f"- 最大标题长度: {topic_settings.get('max_title_length', 30)}")
        
        print(f"\n文章设置:")
        print(f"- 同步标题: {article_settings.get('sync_title', True)}")
        print(f"- 占位标题: '{article_settings.get('placeholder_title', '无标题')}'")
    except Exception as e:
        print(f"配置分析失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("📊 ZSXQ to WordPress 标题重复分析工具")
    print("=" * 60)
    
    results = analyze_title_duplicates()
    analyze_content_types()
    
    print(f"\n" + "=" * 60)
    print("📈 分析总结:")
    print(f"- 已同步内容: {results['total_titles']} 条")
    print(f"- 标题去重率: {results['unique_titles']}/{results['total_titles']} ({results['unique_titles']/results['total_titles']*100:.1f}%)")
    
    if results['duplicates']:
        print(f"- ⚠️  发现 {len(results['duplicates'])} 个重复标题")
    else:
        print("- ✅ 无标题重复问题")
    
    print("=" * 60)