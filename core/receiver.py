# core/receiver.py

# 邮件接收

import poplib
import email
import json
import os
import base64
from email.header import decode_header
from email.utils import parseaddr
from .config import get_pop3_config
from .crypto import decrypt_content, decrypt_attachment, is_encrypted
from .contact_manager import get_contact_manager

def decode_str(s):
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    fragments = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            fragment = fragment.decode(encoding or 'utf-8', errors='replace')
        fragments.append(fragment)
    return ''.join(fragments)

def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            # 跳过附件
            if "attachment" in content_disposition:
                continue
            content_type = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or 'utf-8'
                text = payload.decode(charset, errors='replace')
                if content_type == "text/plain":
                    return text  # 优先返回纯文本
                elif content_type == "text/html" and not body:
                    body = text  # 暂存 HTML，以防无纯文本
            except Exception:
                continue
        # 如果没找到 text/plain，回退到 HTML
        return body
    else:
        # 非 multipart 邮件
        try:
            payload = msg.get_payload(decode=True)
            if payload is None:
                return ""
            charset = msg.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
        except Exception:
            return ""

def format_size(size):
    # 格式化文件大小
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_attachments_with_decrypt(msg, email_addr, from_addr):
    # 提取邮件的所有附件（并尝试解密）
    attachments = []
    if not msg.is_multipart():
        return attachments

    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(email_addr)

    for part in msg.walk():
        cd = part.get("Content-Disposition", "")
        if cd and "attachment" in cd.lower():
            try:
                # 获取附件文件名
                filename = part.get_filename()
                if filename:
                    filename = decode_str(filename)
                else:
                    filename = "未命名附件.bin"

                # 获取附件内容
                payload = part.get_payload(decode=True)
                if payload is None:
                    # 如果附件是base64编码的
                    payload = part.get_payload()
                    if isinstance(payload, str):
                        payload = base64.b64decode(payload)
                    elif isinstance(payload, list):
                        payload = ''.join(payload).encode()

                if payload:
                    # 检查是否为加密附件（以 .secure 结尾）
                    is_encrypted_attachment = filename.endswith('.secure')
                    original_filename = filename[:-7] if is_encrypted_attachment else filename  # 去掉 .secure 后缀
                    
                    # 如果是加密附件，尝试解密
                    if is_encrypted_attachment:
                        # 检查是否有发件人的密钥用于解密附件
                        if contact_manager.has_contact(from_addr) or contact_manager.should_encrypt(from_addr):
                            try:
                                decrypted_payload = decrypt_attachment(email_addr, payload, from_addr)
                                payload = decrypted_payload
                                filename = original_filename  # 恢复原始文件名
                            except Exception as e:
                                print(f"附件解密失败: {e}")
                                # 保留加密附件名，标记为失败
                                filename = f"[解密失败] {filename}"
                        else:
                            # 没有密钥，保留加密附件名
                            filename = f"[无密钥] {filename}"

                    # 获取文件大小
                    size = len(payload)
                    size_str = format_size(size)
                    # 获取MIME类型
                    content_type = part.get_content_type()

                    attachments.append({
                        "filename": filename,
                        "data": payload,
                        "size": size,
                        "size_str": size_str,
                        "content_type": content_type
                    })
            except Exception as e:
                print(f"解析附件失败: {e}")
                continue
    return attachments


def fetch_emails(email_addr, password, max_count=10):
    pop3_cfg = get_pop3_config(email_addr)
    server = pop3_cfg['server']
    port = pop3_cfg['port']
    use_ssl = pop3_cfg.get('ssl', True)

    try:
        if use_ssl:
            pop_conn = poplib.POP3_SSL(server, port, timeout=15)
        else:
            pop_conn = poplib.POP3(server, port, timeout=15)
        pop_conn.user(email_addr)
        pop_conn.pass_(password)
        total_messages = len(pop_conn.list()[1])
        start_index = max(1, total_messages - max_count + 1)
        end_index = total_messages
        messages = []
        for i in range(start_index, end_index + 1):
            messages.append(pop_conn.retr(i))
        pop_conn.quit()

        emails = []
        for i, (response, lines, octets) in enumerate(reversed(messages)):
            raw_email = b"\n".join(lines)
            msg = email.message_from_bytes(raw_email)

            # 解析发件人名称和地址
            from_header = decode_str(msg.get("From", ""))
            from_name, from_addr = parseaddr(from_header)

            # 获取原始邮件正文
            raw_body = get_body(msg)

            # 获取当前用户的ContactManager
            contact_manager = get_contact_manager(email_addr)

            # 检查邮件头中是否有安全标识
            has_security_header = msg.get('X-Secure-Mail') is not None

            # 尝试解密邮件正文
            is_secure = False
            decrypted_body = raw_body
            if (has_security_header or is_encrypted(raw_body)) and from_addr:
                # 检查是否有发件人的密钥
                if contact_manager.has_contact(from_addr) or contact_manager.should_encrypt(from_addr):
                    try:
                        # 尝试使用发件人邮箱作为密钥查找依据进行解密
                        decrypted_body = decrypt_content(email_addr, raw_body, from_addr)
                        is_secure = True
                    except Exception as e:
                        # 解密失败，保留原始内容
                        print(f"解密失败: {e}")
                        decrypted_body = f"[解密失败] 请检查通信表中是否有发件人 {from_addr} 的密钥"
                        is_secure = False

            # 获取附件（已内置解密逻辑）
            attachments = get_attachments_with_decrypt(msg, email_addr, from_addr)

            mail_info = {
                "id": str(i + 1),
                "from": from_header,
                "from_name": from_name,
                "from_addr": from_addr,
                "to": decode_str(msg.get("To", "")),
                "subject": decode_str(msg.get("Subject", "(无主题)")) or "(无主题)",
                "date": msg.get("Date", ""),
                "body": decrypted_body,
                "is_secure": is_secure,
                "has_attachments": len(attachments) > 0,
                "attachments": attachments,
                "attachment_count": len(attachments)
            }
            emails.append(mail_info)

        return emails
    except Exception as e:
        raise ValueError(f"接收失败: {str(e)}")