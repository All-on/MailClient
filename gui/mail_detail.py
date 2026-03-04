# gui/mail_detail.py

# 邮件详情弹窗

import flet as ft
import os
import tempfile
import mimetypes
from datetime import datetime

def create_mail_detail(page, mail_info):
    # 创建邮件详情界面
    
    def close_bottom_sheet(e):
        sheet.open = False
        page.update()
    
    def download_attachment(attachment_data):
        try:
            # 改为当前工作目录
            save_dir = os.getcwd()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = attachment_data.get('filename', 'attachment')
            safe_filename = "".join(c for c in filename if c.isalnum() or c in '._- ').rstrip()
            if not safe_filename:
                safe_filename = f"attachment_{timestamp}"
            
            save_path = os.path.join(save_dir, safe_filename)

            # 避免覆盖：如果文件已存在，加编号
            counter = 1
            original_name = safe_filename
            while os.path.exists(save_path):
                name, ext = os.path.splitext(original_name)
                safe_filename = f"{name}_{counter}{ext}"
                save_path = os.path.join(save_dir, safe_filename)
                counter += 1

            with open(save_path, 'wb') as f:
                f.write(attachment_data['data'])

            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"附件已保存到: {save_path}"),
                action="OK"
            )
            page.snack_bar.open = True

            import platform, subprocess
            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(save_dir)
                elif system == "Darwin":
                    subprocess.Popen(["open", save_dir])
                else:
                    subprocess.Popen(["xdg-open", save_dir])
            except:
                pass

            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"保存附件失败: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
    
    # 构建附件显示组件
    attachments_section = None
    if mail_info.get('has_attachments', False):
        attachments = mail_info.get('attachments', [])
        attachment_widgets = []
        
        for i, attachment in enumerate(attachments):
            filename = attachment.get('filename', f'附件{i+1}')
            size_str = attachment.get('size_str', '未知大小')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            # 根据文件类型选择图标
            if 'image' in content_type:
                icon = ft.Icons.IMAGE
                color = ft.Colors.GREEN
            elif 'pdf' in content_type:
                icon = ft.Icons.PICTURE_AS_PDF
                color = ft.Colors.RED
            elif 'word' in content_type or 'document' in content_type:
                icon = ft.Icons.DESCRIPTION
                color = ft.Colors.BLUE
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                icon = ft.Icons.TABLE_CHART
                color = ft.Colors.GREEN
            elif 'zip' in content_type or 'compressed' in content_type:
                icon = ft.Icons.ARCHIVE
                color = ft.Colors.ORANGE
            else:
                icon = ft.Icons.ATTACH_FILE
                color = ft.Colors.GREY
            
            attachment_widget = ft.Card(
                elevation=0,
                content=ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(icon, color=color),
                        title=ft.Text(
                            filename,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        subtitle=ft.Text(f"大小: {size_str} | 类型: {content_type.split('/')[-1]}"),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            tooltip="下载附件",
                            on_click=lambda e, att=attachment: download_attachment(att)
                        )
                    ),
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    padding=5,
                    margin=ft.Margin(bottom=5, top=0, left=0, right=0)
                )
            )
            attachment_widgets.append(attachment_widget)
        
        attachments_section = ft.Column([
            ft.Text("附件:", weight=ft.FontWeight.BOLD),
            ft.Column(attachment_widgets, spacing=3)
        ], spacing=5)
    
    # 构建可滚动的内容
    content_parts = [
        ft.Row([
            ft.Text("主题:", weight=ft.FontWeight.BOLD, width=80),
            ft.Text(mail_info.get('subject', '无主题'), expand=True)
        ]),
        ft.Row([
            ft.Text("发件人:", weight=ft.FontWeight.BOLD, width=80),
            ft.Text(mail_info.get('from', '未知'), expand=True)
        ]),
        ft.Row([
            ft.Text("收件人:", weight=ft.FontWeight.BOLD, width=80),
            ft.Text(mail_info.get('to', ''), expand=True)
        ]),
        ft.Row([
            ft.Text("时间:", weight=ft.FontWeight.BOLD, width=80),
            ft.Text(mail_info.get('date', '未知'), expand=True)
        ]),
    ]
    
    # 如果有附件，添加附件部分
    if attachments_section:
        content_parts.extend([
            ft.Divider(),
            attachments_section
        ])
    
    content_parts.extend([
        ft.Divider(),
        ft.Text("正文:", weight=ft.FontWeight.BOLD),
        ft.Container(
            content=ft.Text(
                mail_info.get('body', '无正文'),
                selectable=True
            ),
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=10,
            expand=True
        ),
        ft.Divider(),
        ft.Row([ft.FilledButton("关闭", on_click=close_bottom_sheet)], alignment=ft.MainAxisAlignment.END)
    ])
    
    # 创建内容列
    content = ft.Column(content_parts, spacing=10, scroll=ft.ScrollMode.AUTO)
    
    # 创建 BottomSheet
    sheet = ft.BottomSheet(
        ft.Container(
            content=content,
            padding=20,
            width=800,  
            height=700 
        ),
        open=False,
    )

    return sheet