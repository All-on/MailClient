# core/contact_manager.py

# 通信表管理

import json
import os
import re
from typing import Dict, List, Optional
import tempfile

class ContactManager:
    # 联系人密钥管理器

    def __init__(self, user_email: str):
        self.user_email = user_email.lower()
        # 生成用户特定的通信表文件名 - 使用账户名
        safe_email = re.sub(r'[^\w@.-]', '', self.user_email)
        safe_email = safe_email.replace('@', '_at_')
        safe_email = safe_email.replace('.', '_')
        self.contact_table_file = f"contact_table_{safe_email}.json"
        self.contact_table = self.load_contact_table()

    def load_contact_table(self) -> Dict:
        # 加载密钥表，并进行数据校验与修复
        default_structure = {
            "user_email": self.user_email,
            "contacts": {},  # 邮箱 -> {key: "...", encrypt: True/False}
            "default_key": "default_key_123"  # 用户默认密钥
        }

        try:
            if os.path.exists(self.contact_table_file):
                with open(self.contact_table_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)

                # 检查并修复顶层结构
                if not isinstance(loaded_data, dict):
                    print(f"[WARNING] {self.contact_table_file} 格式错误，顶层不是对象，使用默认结构。")
                    return default_structure
                
                # 确保必要的顶层键存在
                contact_table = {
                    "user_email": loaded_data.get("user_email", self.user_email),
                    "default_key": loaded_data.get("default_key", "default_key_123"),
                    "contacts": loaded_data.get("contacts", {})
                }

                # 修复 contacts 字典，确保每个联系人都是正确的结构
                fixed_contacts = {}
                for email, data in contact_table["contacts"].items():
                    # 如果 data 是旧的字符串格式，尝试修复
                    if isinstance(data, str):
                        # 假设旧格式是直接的密钥字符串
                        fixed_contacts[email] = {
                            "key": data,
                            "encrypt": True  # 默认开启加密
                        }
                        print(f"[INFO] 修复联系人数据: {email} (旧格式)")
                    elif isinstance(data, dict):
                        # 检查新格式字典是否缺少必要字段
                        fixed_contacts[email] = {
                            "key": data.get("key", ""),
                            "encrypt": data.get("encrypt", True)
                        }
                    else:
                        # 如果既不是字符串也不是字典，跳过该条目
                        print(f"[WARNING] 跳过无效的联系人数据: {email}")
                
                contact_table["contacts"] = fixed_contacts

                print(f"[INFO] 成功加载并修复通信表: {self.contact_table_file}")
                return contact_table

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[ERROR] 加载通信表失败: {e}。使用默认结构。")
        except Exception as e:
            print(f"[ERROR] 未知错误加载通信表: {e}。使用默认结构。")

        # 如果文件不存在、格式错误或加载过程出错，返回默认结构
        return default_structure

    def save_contact_table(self):
        # 安全地全量覆盖写入 JSON 文件
        try:
            # 创建临时文件（同目录）
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8',
                delete=False,
                dir=os.path.dirname(self.contact_table_file) or '.',
                suffix='.tmp'
            ) as tmp_file:
                json.dump(self.contact_table, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = tmp_file.name
            # 原子替换（Windows 也支持）
            os.replace(tmp_path, self.contact_table_file)
            print(f"[INFO] 成功保存通信表: {self.contact_table_file}")
        except Exception as e:
            print(f"[ERROR] 保存失败: {e}")
            raise

    def get_key_for_email(self, email: str) -> str:
        # 获取指定邮箱的密钥
        email_lower = email.lower().strip()
        contact_info = self.contact_table.get("contacts", {}).get(email_lower, {})
        key = contact_info.get("key")

        if key:
            return key

        # 然后尝试匹配域名
        if '@' in email_lower:
            domain = email_lower.split('@')[1]
            for contact_email, info in self.contact_table.get("contacts", {}).items():
                if '@' in contact_email and contact_email.split('@')[1] == domain:
                    domain_key = info.get("key")
                    if domain_key:
                        return domain_key

        # 如果都没有匹配，返回默认密钥
        return self.contact_table.get("default_key", "default_key_123")

    def add_contact(self, email: str, secret_key: str, encrypt: bool = True) -> bool:
        # 添加联系人密钥
        email_lower = email.lower().strip()

        # 检查密钥是否有效
        if not secret_key or len(secret_key) < 4:
            return False

        # 确保contacts字典存在
        if "contacts" not in self.contact_table:
            self.contact_table["contacts"] = {}

        # 添加或更新联系人信息
        self.contact_table["contacts"][email_lower] = {
            "key": secret_key,
            "encrypt": encrypt
        }

        self.save_contact_table()
        return True

    def remove_contact(self, email: str) -> bool:
        # 删除联系人
        email_lower = email.lower().strip()
        
        if email_lower in self.contact_table.get("contacts", {}):
            del self.contact_table["contacts"][email_lower]
            self.save_contact_table()
            return True
        
        return False

    def update_default_key(self, new_key: str) -> bool:
        # 更新默认密钥
        if not new_key or len(new_key) < 4:
            return False
        
        self.contact_table["default_key"] = new_key
        self.save_contact_table()
        return True

    def get_all_contacts(self) -> List[Dict]:
        # 获取所有联系人
        contacts = []
        
        for email, info in self.contact_table.get("contacts", {}).items():
            if not isinstance(info, dict):
                # 跳过格式错误的条目
                continue
            
            key = info.get("key", "")
            encrypt = info.get("encrypt", True)
            
            # 隐藏部分密钥
            if len(key) > 6:
                key_display = f"{key[:3]}...{key[-3:]}"
            else:
                key_display = "***"
            
            contacts.append({
                "email": email,
                "key": key,
                "key_display": key_display,
                "key_length": len(key),
                "encrypt": encrypt
            })
        
        return sorted(contacts, key=lambda x: x["email"])

    def has_contact(self, email: str) -> bool:
        # 检查是否有指定邮箱的联系人
        email_lower = email.lower().strip()
        contact_info = self.contact_table.get("contacts", {}).get(email_lower, {})
        # 确保 contact_info 是字典
        return isinstance(contact_info, dict) and bool(contact_info.get("key"))

    def get_default_key(self) -> str:
        # 获取默认密钥
        return self.contact_table.get("default_key", "default_key_123")

    def get_default_key_display(self) -> str:
        # 获取默认密钥的显示形式（隐藏部分字符）
        key = self.get_default_key()
        if len(key) > 6:
            return f"{key[:3]}...{key[-3:]}"
        return "***"

    def should_encrypt(self, email: str) -> bool:
        # 检查是否应该加密发送给指定邮箱的邮件
        email_lower = email.lower().strip()
        contact_info = self.contact_table.get("contacts", {}).get(email_lower, {})
        
        # 如果是字典格式的联系人信息
        if isinstance(contact_info, dict):
            if "encrypt" in contact_info:
                return contact_info["encrypt"]
        
        # 如果联系人没有设置，检查是否有该联系人的密钥
        default_key = self.get_default_key()
        return (self.has_contact(email) or default_key != "default_key_123")

    def get_contact_count(self) -> int:
        # 获取联系人数量
        count = 0
        contacts_dict = self.contact_table.get("contacts", {})
        for email, info in contacts_dict.items():
            if isinstance(info, dict) and info.get("key"):
                count += 1
        return count

    def get_file_path(self) -> str:
        # 获取通信表文件路径
        return self.contact_table_file

# 全局字典，存储不同用户的ContactManager实例
contact_managers = {}

def get_contact_manager(user_email: str) -> ContactManager:
    # 获取或创建指定用户的ContactManager实例
    user_email_lower = user_email.lower()
    if user_email_lower not in contact_managers:
        contact_managers[user_email_lower] = ContactManager(user_email_lower)
    return contact_managers[user_email_lower]

def get_key_for_email(user_email: str, target_email: str) -> str:
    manager = get_contact_manager(user_email)
    return manager.get_key_for_email(target_email)

def add_contact(user_email: str, target_email: str, secret_key: str, encrypt: bool = True) -> bool:
    manager = get_contact_manager(user_email)
    return manager.add_contact(target_email, secret_key, encrypt)

def remove_contact(user_email: str, target_email: str) -> bool:
    manager = get_contact_manager(user_email)
    return manager.remove_contact(target_email)

def get_all_contacts(user_email: str) -> List[Dict]:
    manager = get_contact_manager(user_email)
    return manager.get_all_contacts()

def update_default_key(user_email: str, new_key: str) -> bool:
    manager = get_contact_manager(user_email)
    return manager.update_default_key(new_key)

def get_default_key(user_email: str) -> str:
    manager = get_contact_manager(user_email)
    return manager.get_default_key()

def get_default_key_display(user_email: str) -> str:
    manager = get_contact_manager(user_email)
    return manager.get_default_key_display()

def should_encrypt(user_email: str, target_email: str) -> bool:
    manager = get_contact_manager(user_email)
    return manager.should_encrypt(target_email)

def has_contact(user_email: str, target_email: str) -> bool:
    manager = get_contact_manager(user_email)
    return manager.has_contact(target_email)

def get_contact_table_path(user_email: str) -> str:
    manager = get_contact_manager(user_email)
    return manager.get_file_path()