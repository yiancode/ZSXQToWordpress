#!/usr/bin/env python3
"""
测试优化效果
"""
import time
import re
from content_processor import ContentProcessor

def test_regex_performance():
    """测试正则表达式预编译性能提升"""
    print("=== 测试正则表达式性能 ===")
    
    # 测试数据
    test_text = """
    <e type="mention">@张三</e> 分享了一篇文章
    <e type="hashtag" title="%23Python开发%23" />
    <e type="text_bold" title="重要提示" />这是一段测试文本
    <e type="text_italic" title="引用内容" />
    <e type="web" href="https://example.com/article" title="查看原文" />
    """ * 50  # 重复50次模拟较长的文章
    
    # 使用预编译的正则表达式
    processor = ContentProcessor()
    start = time.time()
    for _ in range(100):
        processed = processor._process_zsxq_tags(test_text)
    optimized_time = time.time() - start
    
    # 使用未优化的方式（模拟旧版本）
    start = time.time()
    for _ in range(100):
        processed = test_text
        processed = re.sub(r'<e type="text_bold" title="([^"]*)"[^>]*/>', r'**\1**', processed)
        processed = re.sub(r'<e type="text_italic" title="([^"]*)"[^>]*/>', r'*\1*', processed)
        processed = re.sub(r'<e type="text_delete" title="([^"]*)"[^>]*/>', r'~~\1~~', processed)
        processed = re.sub(r'<e type="[^"]*" title="([^"]*)"[^>]*/>', r'\1', processed)
    unoptimized_time = time.time() - start
    
    print(f"优化后处理100次耗时: {optimized_time:.4f}秒")
    print(f"优化前处理100次耗时: {unoptimized_time:.4f}秒")
    print(f"性能提升: {((unoptimized_time - optimized_time) / unoptimized_time * 100):.1f}%")
    print()

def test_import_optimization():
    """测试导入优化"""
    print("=== 测试导入优化 ===")
    
    # 检查是否有重复导入
    with open('content_processor.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 统计import语句
    imports = {}
    import_lines = re.findall(r'^import\s+(\S+)', content, re.MULTILINE)
    from_imports = re.findall(r'^from\s+(\S+)\s+import', content, re.MULTILINE)
    
    all_imports = import_lines + from_imports
    for imp in all_imports:
        imports[imp] = imports.get(imp, 0) + 1
    
    # 检查重复
    duplicates = {k: v for k, v in imports.items() if v > 1}
    if duplicates:
        print("发现重复导入:")
        for module, count in duplicates.items():
            print(f"  {module}: {count}次")
    else:
        print("✓ 没有发现重复导入")
    print()

def test_config_options():
    """测试新配置选项"""
    print("=== 测试配置选项 ===")
    
    # 测试配置
    config = {
        'sync': {
            'fetch_article_details': True,
            'detail_fetch_retries': 3
        }
    }
    
    # 测试默认值
    fetch_details = config['sync'].get('fetch_article_details', True)
    retries = config['sync'].get('detail_fetch_retries', 2)
    
    print(f"fetch_article_details: {fetch_details} (默认: True)")
    print(f"detail_fetch_retries: {retries} (默认: 2)")
    
    # 测试禁用情况
    config['sync']['fetch_article_details'] = False
    fetch_details = config['sync'].get('fetch_article_details', True)
    print(f"\n禁用后 fetch_article_details: {fetch_details}")
    print()

def test_footer_removal():
    """测试页脚清理功能"""
    print("=== 测试页脚清理 ===")
    
    processor = ContentProcessor()
    
    test_cases = [
        "这是正文内容\n\n—— 发布于 知识星球 2024-01-15 10:30:45",
        "这是正文内容\n\n— 发布于 我的星球 2024-01-15 10:30:45",
        "这是正文内容\n\n发布于 技术分享 2024-01-15 10:30:45",
    ]
    
    for i, text in enumerate(test_cases, 1):
        cleaned = processor._remove_zsxq_footer(text)
        print(f"测试用例{i}: {'✓ 已清理' if cleaned != text else '✗ 未清理'}")
        if cleaned != text:
            print(f"  原文: {repr(text)}")
            print(f"  清理后: {repr(cleaned)}")
    print()

if __name__ == "__main__":
    print("开始测试优化效果...\n")
    
    test_regex_performance()
    test_import_optimization()
    test_config_options()
    test_footer_removal()
    
    print("测试完成！")