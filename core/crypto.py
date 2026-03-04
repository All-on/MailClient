# core/crypto.py

# 加密/解密核心模块

import base64
import hashlib
import secrets
import os
from typing import Dict, Tuple, Optional

# 标准的Base64字母表
STANDARD_B64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

# 导入联系人管理器
from .contact_manager import get_contact_manager

class SecureMailCrypto:
    # 安全邮件加密类
    
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = "default_key_123"  # 默认密钥
        
        self.shared_secret = secret_key.encode('utf-8')
    
    def generate_custom_b64_table(self, nonce: bytes) -> str:
        # 创建种子：K + nonce
        seed_data = self.shared_secret + nonce
        seed = hashlib.sha256(seed_data).digest()
        
        # 将标准字母表转换为列表以便重新排列
        alphabet_list = list(STANDARD_B64_ALPHABET)
        
        # 使用种子来打乱字母表（确定性随机排列）
        for i in range(len(alphabet_list)-1, 0, -1):
            # 使用种子中的字节来生成随机索引
            seed_idx = seed[i % len(seed)] + (seed[(i+1) % len(seed)] << 8)
            j = seed_idx % (i + 1)
            alphabet_list[i], alphabet_list[j] = alphabet_list[j], alphabet_list[i]
        
        return ''.join(alphabet_list)
    
    def custom_b64encode(self, data: bytes, b64_table: str) -> str:
        # 先使用标准Base64编码
        std_encoded = base64.b64encode(data).decode('ascii')
        
        # 使用自定义编码表替换
        mapping = dict(zip(STANDARD_B64_ALPHABET, b64_table))
        
        # 替换字符
        custom_encoded = ''.join(mapping.get(c, c) for c in std_encoded)
        
        return custom_encoded
    
    def custom_b64decode(self, data: str, b64_table: str) -> bytes:
        # 创建反向映射字典
        mapping = dict(zip(b64_table, STANDARD_B64_ALPHABET))
        
        # 替换回标准Base64字符
        std_encoded = ''.join(mapping.get(c, c) for c in data)
        
        # 使用标准Base64解码
        return base64.b64decode(std_encoded)
    
    def encrypt_mail_content(self, plaintext: str) -> str:
        # 生成nonce，保证每次加密都不同
        nonce = secrets.token_bytes(16)
        
        # 生成自定义Base64编码表
        b64_table = self.generate_custom_b64_table(nonce)
        
        # 将明文转换为字节
        data_to_encode = plaintext.encode('utf-8')
        
        # 使用自定义Base64编码表编码
        encoded_data = self.custom_b64encode(data_to_encode, b64_table)
        
        # 编码nonce
        encoded_nonce = base64.b64encode(nonce).decode('ascii')
        
        # 创建编码数据结构
        return f"{encoded_nonce}:{encoded_data}"
    
    def encrypt_mail_bytes(self, data: bytes) -> str:
        # 生成nonce（保证每次加密都不同）
        nonce = secrets.token_bytes(16)
        
        # 生成自定义Base64编码表
        b64_table = self.generate_custom_b64_table(nonce)
        
        # 使用自定义Base64编码表编码
        encoded_data = self.custom_b64encode(data, b64_table)
        
        # 编码nonce（使用标准Base64）
        encoded_nonce = base64.b64encode(nonce).decode('ascii')
        
        # 创建编码数据结构
        return f"{encoded_nonce}:{encoded_data}"
    
    def decrypt_mail_content(self, encrypted_content: str) -> str:
        try:
            # 检查是否为我们的加密格式
            if ':' not in encrypted_content:
                return encrypted_content
            
            # 分离nonce和加密数据
            encoded_nonce, encoded_data = encrypted_content.split(':', 1)
            
            # 解码nonce
            nonce = base64.b64decode(encoded_nonce)
            
            # 重新生成相同的Base64编码表
            b64_table = self.generate_custom_b64_table(nonce)
            
            # 使用自定义Base64编码表解码数据
            decoded_data = self.custom_b64decode(encoded_data, b64_table)
            
            # 解码为字符串
            return decoded_data.decode('utf-8')
                
        except Exception as e:
            # 如果解密失败，返回原始内容
            print(f"解密失败: {e}")
            return encrypted_content
    
    def decrypt_mail_bytes(self, encrypted_content: str) -> bytes:
        try:
            # 检查是否为我们的加密格式（包含冒号分隔符）
            if ':' not in encrypted_content:
                return encrypted_content.encode('utf-8')
            
            # 分离nonce和加密数据
            encoded_nonce, encoded_data = encrypted_content.split(':', 1)
            
            # 解码nonce
            nonce = base64.b64decode(encoded_nonce)
            
            # 重新生成相同的Base64编码表
            b64_table = self.generate_custom_b64_table(nonce)
            
            # 使用自定义Base64编码表解码数据
            decoded_data = self.custom_b64decode(encoded_data, b64_table)
            
            return decoded_data
                
        except Exception as e:
            # 如果解密失败，返回原始内容
            print(f"解密失败: {e}")
            return encrypted_content.encode('utf-8')
    
    def is_encrypted_content(self, content: str) -> bool:

        # 我们的加密格式：base64(nonce):base64(data)
        # 检查是否包含冒号分隔符
        if ':' not in content:
            return False
        
        parts = content.split(':', 1)
        if len(parts) != 2:
            return False
        
        # 检查第一部分是否为有效的base64
        try:
            base64.b64decode(parts[0])
            return True
        except:
            return False


# 全局加密函数，支持根据用户邮箱和目标邮箱获取密钥
def encrypt_content(user_email: str, plaintext: str, to_email: str = None) -> str:
    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(user_email)
    
    # 如果提供了收件人邮箱，检查是否需要加密
    if to_email:
        if not contact_manager.should_encrypt(to_email):
            # 不需要加密，返回原始内容
            return plaintext
    
    # 获取对应的密钥
    if to_email:
        secret_key = contact_manager.get_key_for_email(to_email)
    else:
        # 如果没有提供收件人，使用默认密钥
        secret_key = contact_manager.get_default_key()
    
    # 创建加密实例并加密
    crypto = SecureMailCrypto(secret_key)
    return crypto.encrypt_mail_content(plaintext)

def decrypt_content(user_email: str, encrypted_content: str, from_email: str = None) -> str:
    # 首先检查是否为加密内容
    if ':' not in encrypted_content:
        return encrypted_content
    
    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(user_email)
    
    # 获取对应的密钥
    if from_email:
        secret_key = contact_manager.get_key_for_email(from_email)
    else:
        # 如果没有提供发件人，使用默认密钥
        secret_key = contact_manager.get_default_key()
    
    # 创建加密实例并解密
    crypto = SecureMailCrypto(secret_key)
    return crypto.decrypt_mail_content(encrypted_content)

def encrypt_attachment(user_email: str, attachment_data: bytes, to_email: str = None) -> bytes:
    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(user_email)

    # 如果提供了收件人邮箱，检查是否需要加密
    if to_email:
        if not contact_manager.should_encrypt(to_email):
            # 不需要加密，返回原始内容
            return attachment_data

    # 获取对应的密钥
    if to_email:
        secret_key = contact_manager.get_key_for_email(to_email)
    else:
        # 如果没有提供收件人，使用默认密钥
        secret_key = contact_manager.get_default_key()

    # 创建加密实例并加密
    crypto = SecureMailCrypto(secret_key)
    encrypted_string = crypto.encrypt_mail_bytes(attachment_data) # 使用新的 bytes 方法
    # 返回加密后的字符串的字节形式
    return encrypted_string.encode('latin1', errors='ignore')

def decrypt_attachment(user_email: str, encrypted_attachment_data: bytes, from_email: str = None) -> bytes:
    # 首先检查是否为加密内容（我们的格式是字符串）
    try:
        encrypted_string = encrypted_attachment_data.decode('latin1', errors='ignore')
        if ':' not in encrypted_string:
            # 如果不是我们的加密格式，返回原始内容
            return encrypted_attachment_data
    except UnicodeDecodeError:
        # 如果不能解码为 latin1，说明不是我们加密的，返回原始
        return encrypted_attachment_data

    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(user_email)

    # 获取对应的密钥
    if from_email:
        secret_key = contact_manager.get_key_for_email(from_email)
    else:
        # 如果没有提供发件人，使用默认密钥
        secret_key = contact_manager.get_default_key()

    # 创建加密实例并解密
    crypto = SecureMailCrypto(secret_key)
    decrypted_bytes = crypto.decrypt_mail_bytes(encrypted_string) # 使用新的 bytes 方法
    return decrypted_bytes

def is_encrypted(content: str) -> bool:
    return ':' in content and len(content.split(':', 1)) == 2