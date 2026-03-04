# core/sender.py

# 邮件发送

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from .config import get_smtp_config
from .crypto import encrypt_content, encrypt_attachment
from .contact_manager import get_contact_manager

def send_email(sender_email, password, to, subject, body, attachments=None):
    # 发送邮件（根据通信表决定是否加密正文和附件）

    smtp_cfg = get_smtp_config(sender_email)
    server = smtp_cfg['server']
    port = smtp_cfg['port']
    use_ssl = smtp_cfg.get('ssl', True)

    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(sender_email)

    # 检查是否需要加密
    if contact_manager.should_encrypt(to):
        # 需要加密，使用收件人邮箱作为密钥查找依据
        encrypted_body = encrypt_content(sender_email, body, to)
        is_encrypted = True
    else:
        # 不需要加密，使用原始内容
        encrypted_body = body
        is_encrypted = False

    # 创建邮件
    if attachments:
        msg = MIMEMultipart()
        # 添加正文（可能加密）
        msg.attach(MIMEText(encrypted_body, 'plain', 'utf-8'))

        # 添加附件（加密）
        for filepath in attachments:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                
                # 读取原始文件内容
                with open(filepath, 'rb') as f:
                    original_data = f.read()
                
                # 加密附件内容
                encrypted_data = encrypt_attachment(sender_email, original_data, to)
                
                # 创建加密附件（使用 .secure 扩展名）
                encrypted_filename = filename + '.secure'
                part = MIMEApplication(encrypted_data, _subtype="octet-stream")
                part.add_header('Content-Disposition', 'attachment', filename=encrypted_filename)
                msg.attach(part)
    else:
        msg = MIMEText(encrypted_body, 'plain', 'utf-8')

    # 设置邮件头
    msg['From'] = sender_email
    msg['To'] = to
    msg['Subject'] = Header(subject, 'utf-8')

    # 如果是加密邮件，添加自定义头
    if is_encrypted:
        msg['X-Secure-Mail'] = 'v1.0'

    try:
        if use_ssl:
            s = smtplib.SMTP_SSL(server, port, timeout=15)
        else:
            s = smtplib.SMTP(server, port, timeout=15)
        s.login(sender_email, password)
        s.send_message(msg)
        s.quit()
        msg_type = "加密邮件" if is_encrypted else "普通邮件"
        return {"status": "success", "message": f"{msg_type}发送成功！"}
    except smtplib.SMTPAuthenticationError:
        raise ValueError("认证失败：请检查密码或授权码是否正确")
    except Exception as e:
        raise ValueError(f"发送失败: {str(e)}")