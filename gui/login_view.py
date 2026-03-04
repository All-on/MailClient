# gui/login_view.py

# 登录界面

import flet as ft
import os
import sys
from core.config import get_all_supported_domains, get_builtin_domains, get_custom_domains

def get_resource_path(relative_path):
    # 获取资源文件的绝对路径，支持打包后访问
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_login_view(page, on_login_success):
    # 创建登录界面 - 函数式组件

    # 使用字符串图标名称，避免属性错误
    email_field = ft.TextField(
        label="邮箱地址",
        hint_text="例如: user@qq.com",
        width=350,
        prefix_icon=ft.Icons.MAIL_OUTLINE
    )
    password_field = ft.TextField(
        label="密码/授权码",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK_OUTLINE
    )
    login_button = ft.ElevatedButton(
        "登录",
        icon=ft.Icons.LOGIN,
        on_click=lambda e: handle_login(e),
        width=200
    )
    status_text = ft.Text("", color=ft.Colors.RED)
    supported_hint = ft.Text(
        "",
        size=12,
        color=ft.Colors.GREY_700,
        text_align=ft.TextAlign.CENTER,
        width=400
    )

    # 获取支持的邮箱类型
    def update_supported_list():
        try:
            # 获取所有支持的域名
            supported_domains = get_all_supported_domains()
            builtin_domains = get_builtin_domains()
            custom_domains = get_custom_domains()

            if supported_domains:
                supported_text = "、".join(f"@{d}" for d in sorted(supported_domains))
                hint_text = f"支持的邮箱：{supported_text}"
                # 添加统计信息
                hint_text += f" ({len(builtin_domains)}内置"
                if custom_domains:
                    hint_text += f", {len(custom_domains)}自定义)"
                else:
                    hint_text += ")"
                supported_hint.value = hint_text
            else:
                supported_hint.value = "暂无支持的邮箱，请添加自定义服务器"
        except Exception as e:
            print(f"加载支持列表失败: {e}")
            supported_hint.value = "（无法加载支持列表）"

    update_supported_list() # 初始化

    # 引入服务器设置对话框
    from .server_setup_dialog import create_server_setup_dialog
    server_dialog = create_server_setup_dialog(page)
    page.overlay.append(server_dialog)

    def show_server_setup(e):
        server_dialog.open = True
        page.update()

    # 处理登录逻辑
    def handle_login(e):
        # 不再需要防重复点击标志
        email = email_field.value.strip()
        password = password_field.value.strip()

        if not email or '@' not in email:
            status_text.value = "请输入有效的邮箱地址"
            page.update()
            return

        if not password:
            status_text.value = "请输入密码或授权码"
            page.update()
            return

        login_button.disabled = True
        login_button.text = "登录中..."
        status_text.value = "正在登录..."
        page.update()

        login_button.disabled = False
        login_button.text = "登录"
        status_text.value = "登录成功，正在跳转..."
        page.update()

        # 直接调用成功的回调
        on_login_success(email, password)

    # 创建界面布局
    try:
        # 尝试加载图片
        img_path = get_resource_path('assets/images/logo.png')
        if os.path.exists(img_path):
            mail_icon = ft.Image(
                src=img_path,
                width=120,
                height=120,
                fit="contain"
            )
        else:
            # 如果图片不存在，使用图标
            mail_icon = ft.Icon(ft.Icons.MAIL, size=80, color=ft.Colors.BLUE)
    except:
        # 如果出错，使用图标
        mail_icon = ft.Icon(ft.Icons.MAIL, size=80, color=ft.Colors.BLUE)

    # 构建内容
    content = ft.Column([
        mail_icon,
        ft.Text("邮件客户端", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        email_field,
        password_field,
        supported_hint,
        ft.Row([ 
            ft.TextButton("管理自定义服务器", on_click=show_server_setup),
        ], alignment=ft.MainAxisAlignment.CENTER),
        status_text,
        ft.Container(
            content=login_button,
            alignment=ft.Alignment.CENTER,
            padding=ft.padding.only(top=10) # 减少上方间距
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, width=400)

    return content