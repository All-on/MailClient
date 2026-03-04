# core/email_client.py

# 邮件客户端统一接口

import json
import os
from . import sender
from . import receiver

class EmailClient:
    # 统一的邮件客户端
    
    def __init__(self, email_addr, password):
        self.email_addr = email_addr
        self.password = password
        
    def send_email(self, to, subject, body, attachments=None):
        # 发送邮件（自动加密）
        return sender.send_email(self.email_addr, self.password, to, subject, body, attachments)
    
    def fetch_emails(self, max_count=10):
        # 获取邮件（自动解密）
        return receiver.fetch_emails(self.email_addr, self.password, max_count)
    
    def test_connection(self):
        # 测试连接
        try:
            # 测试发送服务器
            cfg = sender.get_smtp_config(self.email_addr)
            print(f"SMTP配置: {cfg['server']}:{cfg['port']}")
            
            # 测试接收服务器
            cfg = receiver.get_pop3_config(self.email_addr)
            print(f"POP3配置: {cfg['server']}:{cfg['port']}")
            return True
        except Exception as e:
            print(f"配置错误: {e}")
            return False