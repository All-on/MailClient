# gui/main_app.py

# 主应用界面

import flet as ft
import asyncio
from .inbox_view import create_inbox_view
from .compose_mail import create_compose_sheet
from .contact_table import create_contact_table_sheet

def create_main_app(page, user_email, user_password):
    # 创建主应用界面 - 函数式组件
    # 状态变量
    compose_sheet = None
    contact_sheet = None
    server_sheet = None

    def show_compose(e):
        # 显示写邮件界面
        nonlocal compose_sheet
        compose_sheet = create_compose_sheet(
            page=page,
            user_email=user_email,
            user_password=user_password,
            on_send_success=on_send_success
        )
        page.overlay.append(compose_sheet)
        compose_sheet.open = True
        page.update()

    def show_contact_table(e):
        # 显示通信表界面 
        nonlocal contact_sheet
        contact_sheet = create_contact_table_sheet(page, user_email)
        page.overlay.append(contact_sheet)
        contact_sheet.open = True
        page.update()

    def show_server_setup(e):
        # 显示服务器设置界面
        nonlocal server_sheet
        from .server_setup_dialog import create_server_setup_dialog
        server_sheet = create_server_setup_dialog(page)
        page.overlay.append(server_sheet)
        server_sheet.open = True
        page.update()

    def on_send_success(message):
        # 邮件发送成功回调
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def logout(e):
        # 退出登录 - 使用底部弹窗
        def confirm_logout(_):
            logout_sheet.open = False
            page.update() # 关闭弹窗

            async def switch_to_login_async():
                # 等待UI动画完成
                await asyncio.sleep(0.1)

                # 清空页面并切换到登录
                # 清除页面状态
                page.controls.clear()
                page.appbar = None
                page.floating_action_button = None
                page.dialog = None
                page.snack_bar = None
                page.overlay.clear()
                # 清除可能存在的自定义属性
                for attr_name in ['mail_detail_dialog', 'logout_dialog', 'about_dialog', 'server_sheet']:
                    if hasattr(page, attr_name):
                        delattr(page, attr_name)
                
                # 确保页面完全更新
                page.update()

                # 创建登录界面
                from .login_view import create_login_view
                
                # 定义一个安全的登录回调
                def safe_login_callback(email, password):
                    try:
                        # 清空页面状态，确保干净
                        page.controls.clear()
                        page.appbar = None
                        page.floating_action_button = None
                        page.dialog = None
                        page.snack_bar = None
                        page.overlay.clear()
                        for attr_name in ['mail_detail_dialog', 'logout_dialog', 'about_dialog', 'server_sheet']:
                            if hasattr(page, attr_name):
                                delattr(page, attr_name)
                        
                        # 确保页面完全更新
                        page.update()
                        
                        create_main_app(page, email, password) 
                        # create_main_app 内部会异步设置UI，无需在此处接收返回值或添加控件
                    except Exception as ex:
                        # 如果重新登录失败，显示错误信息并回到登录页
                        print(f"切换回登录失败: {ex}")
                        print(f"Error details: {type(ex).__name__}: {ex}")

                        page.controls.clear()
                        # 重新创建并添加登录界面
                        page.add(create_login_view(page, safe_login_callback))
                        page.update()

                # 创建登录界面并添加到页面
                login_view = create_login_view(
                    page=page,
                    on_login_success=safe_login_callback
                )
                
                # 再次确保页面是干净的
                page.controls.clear()
                page.add(login_view)
                page.update()

            # 启动异步任务
            page.run_task(switch_to_login_async)

        def cancel_logout(_):
            logout_sheet.open = False
            page.update()

        # 创建底部弹窗
        logout_sheet = ft.BottomSheet(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.ORANGE),
                        ft.Text("确认退出", size=20, weight=ft.FontWeight.BOLD),
                    ], spacing=10),
                    ft.Divider(),
                    ft.Text("确定要退出登录吗？", size=20),
                    ft.Text("您将返回到登录页面", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    ft.Row([
                        ft.OutlinedButton("取消", on_click=cancel_logout),
                        ft.ElevatedButton(
                            "确定退出", on_click=confirm_logout, bgcolor=ft.Colors.RED_500, color=ft.Colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.END, spacing=20)
                ], spacing=10),
                padding=20,
            ),
            open=True
        )
        page.overlay.append(logout_sheet)
        page.update()

    async def setup_main_ui_async():
        # 创建收件箱
        inbox_content = await create_inbox_view(page, user_email, user_password)

        # 创建浮动按钮
        compose_button = ft.FloatingActionButton(
            icon=ft.Icons.CREATE,
            on_click=show_compose
        )

        # 创建顶部应用栏
        app_bar = ft.AppBar(
            title=ft.Text(f"邮件客户端 - {user_email}"),
            bgcolor=ft.Colors.ORANGE,
            actions=[
                ft.PopupMenuButton(
                    icon=ft.Icons.MENU,
                    items=[
                        ft.PopupMenuItem("通信表", icon=ft.Icons.CONTACTS, on_click=show_contact_table),
                        ft.PopupMenuItem("管理自定义服务器", icon=ft.Icons.SETTINGS, on_click=show_server_setup),
                        ft.PopupMenuItem("退出", icon=ft.Icons.LOGOUT, on_click=logout)
                    ]
                )
            ]
        )

        # 创建主内容
        main_content = ft.Column([
            app_bar,
            ft.Container(
                content=inbox_content,
                expand=True,
                padding=20
            )
        ], expand=True)

        # 添加主内容到页面
        page.add(main_content)
        # 设置浮动按钮（写邮件）
        page.floating_action_button = compose_button
        page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED
        page.update() # 确保UI更新

    # 启动异步任务来设置UI
    page.run_task(setup_main_ui_async)