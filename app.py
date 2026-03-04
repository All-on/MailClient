# app.py
import flet as ft
from gui.login_view import create_login_view
from gui.main_app import create_main_app

def main(page: ft.Page):
    # 页面设置
    page.title = "邮件客户端"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 700
    page.window_resizable = True
    page.padding = 0
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def on_login_success(email, password):
        #登录成功回调
        # 清除登录页面
        page.controls.clear()
        create_main_app(page, email, password)

        # 显示欢迎消息
        page.snack_bar = ft.SnackBar(
            ft.Text(f"欢迎，{email}！")
        )
        page.snack_bar.open = True
        page.update()

    # 创建并添加登录界面
    login_content = create_login_view(page, on_login_success)
    page.add(login_content)
    page.update()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")