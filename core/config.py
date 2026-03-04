# core/config.py

# 邮箱服务器配置管理器

import json
import os
import sys

def get_resource_path(relative_path):
    # 获取资源文件的绝对路径，支持打包后访问
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    # 如果是在打包环境中，资源文件在上一级目录
    if hasattr(sys, '_MEIPASS'):
        # 检查资源文件是否在当前位置
        full_path = os.path.join(base_path, relative_path)
        if not os.path.exists(full_path):
            # 尝试在上二级目录查找（因为PyInstaller可能会改变目录结构）
            base_path = os.path.join(base_path, "..")
    return os.path.join(base_path, relative_path)

def load_builtin_config():
    # 加载内置的邮箱配置 (来自 info.json)
    try:
        config_path = get_resource_path('info.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('email_providers', {})
    except FileNotFoundError:
        print("[WARNING] 内置配置文件 info.json 未找到。")
        return {}
    except json.JSONDecodeError:
        print("[ERROR] 内置配置文件 info.json 格式错误。")
        return {}

def load_user_config():
    # 加载用户自定义的邮箱配置 (来自 user_config.json)
    config_path = 'user_config.json' # 用户配置文件放在当前工作目录
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('email_providers', {})
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # 如果用户配置文件不存在或格式错误，返回空字典
    return {}

def load_email_config():
    # 加载合并后的邮箱配置 (内置 + 用户)
    builtin_config = load_builtin_config()
    user_config = load_user_config()
    # 合并配置，用户配置优先级更高，可以覆盖内置配置
    merged_config = {**builtin_config, **user_config}
    return merged_config

def get_smtp_config(email):
    # 获取指定邮箱的SMTP配置
    domain = email.split('@')[-1].lower()
    config = load_email_config()
    if domain not in config:
        raise ValueError(f"不支持的邮箱：{domain}")
    return config[domain]['smtp']

def get_pop3_config(email):
    # 获取指定邮箱的POP3配置
    domain = email.split('@')[-1].lower()
    config = load_email_config()
    if domain not in config:
        raise ValueError(f"不支持的邮箱：{domain}")
    return config[domain]['pop3']

def add_email_provider(domain, smtp_config, pop3_config):
    # 添加新的邮箱提供商配置到 user_config.json
    config_path = 'user_config.json'
    
    # 确保端口是整数
    try:
        smtp_config["port"] = int(smtp_config.get("port", 0))
        pop3_config["port"] = int(pop3_config.get("port", 0))
    except (ValueError, TypeError):
        raise ValueError("端口号必须是数字")
    
    # 加载现有用户配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {"email_providers": {}}
    
    # 确保配置格式正确
    if "email_providers" not in config:
        config["email_providers"] = {}
    
    # 添加/更新新配置
    config['email_providers'][domain] = {
        'smtp': smtp_config,
        'pop3': pop3_config
    }
    
    # 保存用户配置
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return True

def remove_email_provider(domain):
    # 从 user_config.json 中删除指定域名的邮箱提供商配置
    config_path = 'user_config.json'
    
    # 加载现有用户配置
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            return False
    except json.JSONDecodeError:
        return False
    
    # 检查是否有要删除的域名
    email_providers = config.get('email_providers', {})
    if domain in email_providers:
        del email_providers[domain]
        config['email_providers'] = email_providers
        
        # 保存修改后的用户配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    
    return False

def is_custom_server(domain):
    # 检查指定域名是否为自定义服务器（在user_config.json中）
    user_config = load_user_config()
    return domain in user_config

def get_all_supported_domains():
    # 获取所有支持的邮箱域名列表（内置 + 用户）
    config = load_email_config()
    return list(config.keys())

def get_builtin_domains():
    # 获取内置支持的域名列表
    config = load_builtin_config()
    return list(config.keys())

def get_custom_domains():
    # 获取用户自定义的域名列表
    config = load_user_config()
    return list(config.keys())