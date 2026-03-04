# gui/compose_mail.py

# 写邮件弹窗

import flet as ft
from core.email_client import EmailClient
import tkinter as tk
from tkinter import filedialog
import threading

def create_compose_sheet(page, user_email, user_password, on_send_success):
    # 创建写邮件界面
    
    to_field = ft.TextField(label="收件人", hint_text="输入邮箱地址", width=600)
    subject_field = ft.TextField(label="主题", hint_text="邮件主题", width=600)
    body_field = ft.TextField(
        label="正文",
        hint_text="输入邮件内容",
        multiline=True,
        min_lines=10,
        max_lines=20,
        width=600
    )

    selected_attachments = []  # 存储绝对路径
    attachments_display = ft.Column(spacing=5)

    def open_file_dialog():
        # 在子线程中打开 tkinter 文件选择器
        def _select_files():
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)  # 置顶
            files = filedialog.askopenfilenames(
                title="选择邮件附件",
                filetypes=[("所有文件", "*.*")]
            )
            root.destroy()
            
            if files:
                # 回到主线程更新 Flet UI
                def update_ui():
                    for f in files:
                        if f not in selected_attachments:
                            selected_attachments.append(f)
                    # 刷新附件显示
                    attachments_display.controls.clear()
                    for path in selected_attachments:
                        filename = path.split("/")[-1].split("\\")[-1]
                        row = ft.Row([
                            ft.Text(filename, size=12),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=14,
                                on_click=lambda _, p=path: remove_attachment(p)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        attachments_display.controls.append(row)
                    page.update()
                
                # 安全地回到 Flet 主线程
                page.loop.call_soon_threadsafe(update_ui)

        # 启动子线程（避免阻塞 Flet UI）
        thread = threading.Thread(target=_select_files, daemon=True)
        thread.start()

    def remove_attachment(file_path):
        if file_path in selected_attachments:
            selected_attachments.remove(file_path)
        attachments_display.controls.clear()
        for path in selected_attachments:
            filename = path.split("/")[-1].split("\\")[-1]
            row = ft.Row([
                ft.Text(filename, size=12),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=14,
                    on_click=lambda _, p=path: remove_attachment(p)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            attachments_display.controls.append(row)
        page.update()

    # 添加附件按钮
    add_attachment_btn = ft.ElevatedButton(
        "添加附件",
        icon=ft.Icons.ATTACH_FILE,
        on_click=lambda _: open_file_dialog()
    )

    status_text = ft.Text("", color=ft.Colors.RED)

    def send_mail(e):
        to_email = to_field.value.strip()
        subject = subject_field.value
        body = body_field.value
        attachments = selected_attachments.copy()

        if not to_email or '@' not in to_email:
            status_text.value = "请输入有效的收件人邮箱"
            page.update()
            return
        if not subject:
            status_text.value = "请输入邮件主题"
            page.update()
            return
        if not body:
            status_text.value = "请输入邮件正文"
            page.update()
            return

        status_text.value = "正在发送..."
        status_text.color = ft.Colors.BLUE
        page.update()
        try:
            client = EmailClient(user_email, user_password)
            result = client.send_email(to_email, subject, body, attachments=attachments)
            on_send_success(result["message"])
            close_dialog(None)
        except Exception as ex:
            status_text.value = f"发送失败: {str(ex)}"
            status_text.color = ft.Colors.RED
            page.update()

    def close_dialog(e):
        dlg.open = False
        page.update()

    content_column = ft.Column([
        to_field,
        subject_field,
        body_field,
        ft.Divider(),
        ft.Row([add_attachment_btn], alignment=ft.MainAxisAlignment.START),
        attachments_display,
        status_text,
    ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("写邮件"),
        content=ft.Container(content=content_column, width=600, height=450, padding=10),
        actions=[
            ft.ElevatedButton("发送", icon="send", on_click=send_mail),
            ft.TextButton("取消", on_click=close_dialog)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.dialog = dlg
    dlg.open = True
    page.update()
    return dlg