# gui/mail_item.py

# 单个邮件列表项

import flet as ft
from .mail_detail import create_mail_detail

def create_mail_item(page, mail_info, user_email):
    # 创建邮件列表项 - 使用自定义布局而不是 ListTile
    def show_detail(e):
        # 显示邮件详情
        detail_view = create_mail_detail(page, mail_info)
        page.overlay.append(detail_view)
        detail_view.open = True
        page.update()
    
    # 格式化日期
    date_str = mail_info.get('date', '')
    if ' ' in date_str:
        date_str = date_str.split(' ')[0]
    
    # 获取主题，确保不为空
    subject = mail_info.get('subject', '无主题')
    if not subject or subject == "(无主题)":
        subject = "无主题"
    
    # 获取发件人
    sender = mail_info.get('from', '未知')
    # 如果发件人太长，截断
    if len(sender) > 30:
        sender = sender[:27] + "..."
    
    # 获取正文预览
    body_preview = mail_info.get('body', '')
    if len(body_preview) > 60:
        body_preview = body_preview[:57] + '...'
    
    # 构建邮件项内容
    content = ft.Container(
        content=ft.Row([
            # 左侧：邮件图标
            ft.Container(
                content=ft.Icon(ft.Icons.MAIL, color=ft.Colors.BLUE),
                width=40,
                alignment=ft.Alignment.CENTER
            ),
            
            # 中间：邮件信息
            ft.Column([
                # 主题行
                ft.Row([
                    ft.Text(
                        subject,
                        weight=ft.FontWeight.BOLD,
                        size=14,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True
                    ),
                    # 如果有附件，显示附件图标
                    ft.Row([
                        ft.Icon(ft.Icons.ATTACH_FILE, size=12, color=ft.Colors.BLUE) if mail_info.get('has_attachments', False) else ft.Container(),
                        ft.Text(
                            f"{mail_info.get('attachment_count', 0)}",
                            size=10,
                            color=ft.Colors.BLUE
                        ) if mail_info.get('has_attachments', False) else ft.Container()
                    ], spacing=2) if mail_info.get('has_attachments', False) else ft.Container()
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                # 发件人
                ft.Text(
                    f"发件人: {sender}",
                    size=12,
                    color=ft.Colors.GREY_700,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
            
                # 正文预览
                ft.Text(
                    body_preview,
                    size=12,
                    color=ft.Colors.GREY_600,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS
                )
            ], spacing=3, expand=True),
            
            # 右侧：日期
            ft.Container(
                content=ft.Text(date_str, size=12, color=ft.Colors.GREY_600),
                padding=ft.Padding(left=10, right=5, top=0, bottom=0),
                alignment=ft.Alignment.CENTER_RIGHT
            )
        ], 
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True),
        padding=10,
        on_click=show_detail,
        border_radius=5,
        bgcolor=ft.Colors.WHITE,
        ink=True  # 添加点击效果
    )
    
    return ft.Card(
        elevation=1,
        content=content,
        margin=ft.Margin(bottom=5, top=0, left=0, right=0)
    )