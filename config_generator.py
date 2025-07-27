#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置生成助手工具
帮助用户快速生成ZSXQToWordpress的配置文件
"""

import json
import sys
from typing import Dict, List, Any, Optional
from zsxq_client import ZsxqClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigGenerator:
    """配置生成助手"""
    
    def __init__(self):
        self.config_template = {
            "zsxq": {
                "access_token": "",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "group_id": ""
            },
            "wordpress": {
                "url": "",
                "username": "",
                "password": "",
                "verify_ssl": True
            },
            "qiniu": {
                "access_key": "",
                "secret_key": "",
                "bucket": "",
                "domain": ""
            },
            "sync": {
                "batch_size": 20,
                "delay_seconds": 2,
                "max_retries": 5
            },
            "source": {
                "name": "",
                "url": ""
            },
            "content_mapping": {
                "enable_type_mapping": True,
                "article_types": ["article"],
                "topic_types": ["talk", "q&a-question", "q&a-answer"],
                "topic_settings": {
                    "category": "主题",
                    "max_title_length": 30,
                    "use_custom_post_type": True,
                    "title_prefix": "",
                    "sync_title": False
                },
                "article_settings": {
                    "category": "文章",
                    "sync_title": True
                },
                "enable_column_mapping": True,
                "column_sync_mode": "all",
                "columns": {},
                "auto_discover_columns": True,
                "special_categories": {
                    "digested": "精华",
                    "sticky": "置顶"
                },
                "post_types": {
                    "article": "post",
                    "topic": "post"
                }
            }
        }
    
    def discover_columns(self, access_token: str, group_id: str) -> Dict[str, str]:
        """自动发现专栏信息
        
        Args:
            access_token: 知识星球访问令牌
            group_id: 星球ID
            
        Returns:
            专栏名称到ID的映射字典
        """
        try:
            logger.info("🔍 正在自动发现知识星球专栏...")
            
            # 创建临时客户端
            client = ZsxqClient(access_token, "Mozilla/5.0", group_id)
            
            # 获取专栏映射
            columns_mapping = client.get_columns_mapping()
            
            if columns_mapping:
                logger.info(f"✅ 成功发现 {len(columns_mapping)} 个专栏:")
                for name, column_id in columns_mapping.items():
                    logger.info(f"   📂 {name}")
                return {name: name for name in columns_mapping.keys()}  # 使用名称映射
            else:
                logger.warning("⚠️  未发现任何专栏，请检查访问权限")
                return {}
                
        except Exception as e:
            logger.error(f"❌ 自动发现专栏失败: {e}")
            return {}
    
    def get_group_info(self, access_token: str, group_id: str) -> Dict[str, str]:
        """获取星球基本信息
        
        Args:
            access_token: 知识星球访问令牌
            group_id: 星球ID
            
        Returns:
            星球信息字典
        """
        try:
            logger.info("📡 正在获取知识星球信息...")
            
            client = ZsxqClient(access_token, "Mozilla/5.0", group_id)
            
            # 这里可以扩展获取星球名称等信息
            # 目前先返回基本信息
            return {
                "name": f"星球_{group_id}",
                "url": f"https://t.zsxq.com/groups/{group_id}"
            }
            
        except Exception as e:
            logger.warning(f"⚠️  获取星球信息失败: {e}")
            return {
                "name": "YOUR_ZSXQ_GROUP_NAME",
                "url": "https://t.zsxq.com/YOUR_GROUP_LINK"
            }
    
    def interactive_setup(self) -> Dict[str, Any]:
        """交互式配置生成"""
        
        print("🚀 ZSXQToWordpress 配置生成助手")
        print("=" * 50)
        
        config = self.config_template.copy()
        
        # 1. 知识星球配置
        print("\n📱 知识星球配置")
        print("-" * 20)
        
        access_token = input("请输入知识星球访问令牌 (access_token): ").strip()
        if not access_token:
            print("❌ 访问令牌不能为空")
            return {}
        
        group_id = input("请输入星球ID (group_id): ").strip()
        if not group_id:
            print("❌ 星球ID不能为空")
            return {}
        
        config["zsxq"]["access_token"] = access_token
        config["zsxq"]["group_id"] = group_id
        
        # 获取星球信息
        group_info = self.get_group_info(access_token, group_id)
        config["source"].update(group_info)
        
        # 2. WordPress配置
        print("\n🌐 WordPress配置")
        print("-" * 20)
        
        wp_url = input("请输入WordPress站点的XML-RPC地址 (如: https://your-site.com/xmlrpc.php): ").strip()
        wp_username = input("请输入WordPress用户名: ").strip()
        wp_password = input("请输入WordPress密码: ").strip()
        
        config["wordpress"]["url"] = wp_url
        config["wordpress"]["username"] = wp_username
        config["wordpress"]["password"] = wp_password
        
        # 3. 七牛云配置（可选）
        print("\n☁️  七牛云配置（可选，用于图片存储）")
        print("-" * 20)
        
        use_qiniu = input("是否配置七牛云? (y/n) [默认: n]: ").strip().lower()
        if use_qiniu in ['y', 'yes']:
            qiniu_access = input("请输入七牛云Access Key: ").strip()
            qiniu_secret = input("请输入七牛云Secret Key: ").strip()
            qiniu_bucket = input("请输入七牛云存储空间名: ").strip()
            qiniu_domain = input("请输入七牛云访问域名: ").strip()
            
            config["qiniu"]["access_key"] = qiniu_access
            config["qiniu"]["secret_key"] = qiniu_secret
            config["qiniu"]["bucket"] = qiniu_bucket
            config["qiniu"]["domain"] = qiniu_domain
        
        # 4. 专栏同步配置
        print("\n📂 专栏同步配置")
        print("-" * 20)
        
        sync_mode = input("专栏同步模式 (all=全部专栏, partial=指定专栏) [默认: all]: ").strip().lower()
        if sync_mode not in ['partial']:
            sync_mode = 'all'
        
        config["content_mapping"]["column_sync_mode"] = sync_mode
        
        if sync_mode == 'all':
            print("✅ 已配置为同步所有专栏")
        else:
            print("请配置需要同步的专栏...")
            columns = self.discover_columns(access_token, group_id)
            if columns:
                selected_columns = {}
                print("可用的专栏:")
                for i, name in enumerate(columns.keys(), 1):
                    print(f"  {i}. {name}")
                
                selection = input("请输入专栏编号（用逗号分隔，如: 1,3,5）: ").strip()
                if selection:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        column_names = list(columns.keys())
                        for idx in indices:
                            if 0 <= idx < len(column_names):
                                name = column_names[idx]
                                category = input(f"专栏'{name}'对应的WordPress分类 [默认: {name}]: ").strip() or name
                                selected_columns[name] = category
                        
                        config["content_mapping"]["columns"].update(selected_columns)
                        print(f"✅ 已配置 {len(selected_columns)} 个专栏")
                    except ValueError:
                        print("⚠️  输入格式错误，将使用默认配置")
        
        # 5. 内容类型配置
        print("\n📝 内容类型配置")
        print("-" * 20)
        
        topic_category = input("主题内容的默认WordPress分类 [默认: 主题]: ").strip() or "主题"
        article_category = input("文章内容的默认WordPress分类 [默认: 文章]: ").strip() or "文章"
        
        config["content_mapping"]["topic_settings"]["category"] = topic_category
        config["content_mapping"]["article_settings"]["category"] = article_category
        
        return config
    
    def generate_config_file(self, config: Dict[str, Any], output_path: str = "config.json"):
        """生成配置文件
        
        Args:
            config: 配置字典
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 配置文件已生成: {output_path}")
            print("\n📋 下一步操作:")
            print("1. 检查并调整配置文件")
            print("2. 运行同步命令: python zsxq_to_wordpress.py")
            print("3. 查看同步日志确认效果")
            
        except Exception as e:
            logger.error(f"❌ 生成配置文件失败: {e}")
    
    def validate_config(self, config_path: str) -> bool:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            是否验证通过
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查必要字段
            required_fields = [
                "zsxq.access_token",
                "zsxq.group_id", 
                "wordpress.url",
                "wordpress.username",
                "wordpress.password"
            ]
            
            for field in required_fields:
                keys = field.split('.')
                value = config
                for key in keys:
                    value = value.get(key, {})
                
                if not value:
                    logger.error(f"❌ 必要字段 {field} 未配置")
                    return False
            
            logger.info("✅ 配置文件验证通过")
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ 配置文件不存在: {config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"❌ 配置文件JSON格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 验证配置文件失败: {e}")
            return False


def main():
    """主函数"""
    generator = ConfigGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            config_path = sys.argv[2] if len(sys.argv) > 2 else "config.json"
            generator.validate_config(config_path)
        elif command == "help":
            print("用法:")
            print("  python config_generator.py          # 交互式生成配置")
            print("  python config_generator.py validate # 验证配置文件")
            print("  python config_generator.py help     # 显示帮助")
        else:
            print("❌ 未知命令，使用 'help' 查看用法")
    else:
        # 交互式生成
        config = generator.interactive_setup()
        if config:
            generator.generate_config_file(config)


if __name__ == "__main__":
    main()