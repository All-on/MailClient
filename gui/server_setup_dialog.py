# gui/server_setup_dialog.py

# 自定义服务器设置弹窗

import flet as ft
from core.config import add_email_provider, get_all_supported_domains, load_user_config, remove_email_provider, get_builtin_domains, get_custom_domains

def create_server_setup_dialog(page):
    # 创建自定义服务器设置对话框
    # 表单字段
    domain_field = ft.TextField(label="邮箱域名", hint_text="例如: ybsmailcow.xyz", width=300)
    smtp_server_field = ft.TextField(label="SMTP 服务器", hint_text="例如: smtp.ybsmailcow.xyz", width=300)
    smtp_port_field = ft.TextField(label="SMTP 端口", hint_text="例如: 587", width=150, input_filter=ft.NumbersOnlyInputFilter())
    smtp_ssl_switch = ft.Switch(label="SMTP 使用 SSL", value=True)
    pop3_server_field = ft.TextField(label="POP3 服务器", hint_text="例如: pop3.ybsmailcow.xyz", width=300)
    pop3_port_field = ft.TextField(label="POP3 端口", hint_text="例如: 995", width=150, input_filter=ft.NumbersOnlyInputFilter())
    pop3_ssl_switch = ft.Switch(label="POP3 使用 SSL", value=True)
    status_text = ft.Text("", color=ft.Colors.BLUE)

    # 用于显示用户自定义服务器列表的控件
    custom_servers_list = ft.ListView([], expand=True, spacing=10, padding=10, auto_scroll=True)

    def refresh_custom_servers_list():
        # 刷新自定义服务器列表，仅显示user_config.json中的内容
        custom_servers_list.controls.clear()
        
        # 获取内置和自定义域名列表
        builtin_domains = get_builtin_domains()
        custom_domains = get_custom_domains()
        
        # 首先显示自定义服务器配置
        if not custom_domains:
            custom_servers_list.controls.append(
                ft.Text("暂无自定义服务器配置", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            # 加载用户配置
            user_config = load_user_config()
            
            # 按域名排序显示
            sorted_domains = sorted(custom_domains)
            for domain in sorted_domains:
                config = user_config.get(domain, {})
                smtp_conf = config.get('smtp', {})
                pop3_conf = config.get('pop3', {})
                
                server_card = ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.DNS, color=ft.Colors.BLUE),
                        title=ft.Text(f"@{domain}", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Column([
                            ft.Text(f"SMTP: {smtp_conf.get('server', 'N/A')}:{smtp_conf.get('port', 'N/A')} ({'SSL' if smtp_conf.get('ssl') else 'No SSL'})", size=12),
                            ft.Text(f"POP3: {pop3_conf.get('server', 'N/A')}:{pop3_conf.get('port', 'N/A')} ({'SSL' if pop3_conf.get('ssl') else 'No SSL'})", size=12),
                        ], spacing=2),
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER,
                            icon_color=ft.Colors.RED,
                            tooltip=f"删除 @{domain}",
                            on_click=lambda e, d=domain: delete_custom_server(d)
                        ),
                    )
                )
                custom_servers_list.controls.append(server_card)
        
        page.update()

    def save_server_config(e):
        domain = domain_field.value.strip().lower()
        smtp_server = smtp_server_field.value.strip()
        smtp_port_str = smtp_port_field.value.strip()
        smtp_ssl = smtp_ssl_switch.value
        pop3_server = pop3_server_field.value.strip()
        pop3_port_str = pop3_port_field.value.strip()
        pop3_ssl = pop3_ssl_switch.value

        # 检查是否为空
        if not domain:
            status_text.value = "请输入邮箱域名"
            status_text.color = ft.Colors.RED
            page.update()
            return
            
        if not domain.startswith('@'):
            domain = domain.lstrip('@')
        
        # 检查是否已存在
        all_domains = get_all_supported_domains()
        if domain in all_domains:
            status_text.value = f"域名 @{domain} 已存在"
            status_text.color = ft.Colors.RED
            page.update()
            return

        if not all([smtp_server, smtp_port_str, pop3_server, pop3_port_str]):
            status_text.value = "请填写所有必填项"
            status_text.color = ft.Colors.RED
            page.update()
            return

        try:
            smtp_port = int(smtp_port_str)
            pop3_port = int(pop3_port_str)
        except ValueError:
            status_text.value = "端口号必须是数字"
            status_text.color = ft.Colors.RED
            page.update()
            return

        smtp_config = {
            "server": smtp_server,
            "port": smtp_port,
            "ssl": smtp_ssl
        }
        pop3_config = {
            "server": pop3_server,
            "port": pop3_port,
            "ssl": pop3_ssl
        }

        try:
            # 添加配置到 user_config.json
            success = add_email_provider(domain, smtp_config, pop3_config)
            if success:
                status_text.value = f"服务器配置已保存: @{domain}"
                status_text.color = ft.Colors.GREEN
                # 清空表单
                domain_field.value = ""
                smtp_server_field.value = ""
                smtp_port_field.value = ""
                smtp_ssl_switch.value = True
                pop3_server_field.value = ""
                pop3_port_field.value = ""
                pop3_ssl_switch.value = True
                # 刷新列表
                refresh_custom_servers_list()
            else:
                status_text.value = "保存失败"
                status_text.color = ft.Colors.RED
        except Exception as ex:
            status_text.value = f"保存失败: {str(ex)}"
            status_text.color = ft.Colors.RED
        page.update()

    def delete_custom_server(domain: str):
        # 删除指定域名的自定义服务器配置
        try:
            # 检查是否为内置配置
            builtin_domains = get_builtin_domains()
            if domain in builtin_domains:
                status_text.value = f"内置配置 @{domain} 无法删除"
                status_text.color = ft.Colors.ORANGE
                page.update()
                return
                
            success = remove_email_provider(domain.strip().lower())
            if success:
                status_text.value = f"服务器配置已删除: @{domain}"
                status_text.color = ft.Colors.ORANGE
                # 刷新列表
                refresh_custom_servers_list()
            else:
                status_text.value = f"删除失败: @{domain} 不存在"
                status_text.color = ft.Colors.RED
        except Exception as ex:
            status_text.value = f"删除失败: {str(ex)}"
            status_text.color = ft.Colors.RED
        page.update()

    def close_dialog(e):
        server_dialog.open = False
        page.update()

    # 初始化时刷新列表
    refresh_custom_servers_list()   

    # 对话框内容
    dialog_content = ft.Column([
        ft.Row([
            ft.Text("自定义邮箱服务器", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                on_click=close_dialog,
                icon_color=ft.Colors.GREY
            )
        ]),
        ft.Divider(),
        ft.Text("添加新服务器", size=16, weight=ft.FontWeight.BOLD),
        domain_field,
        ft.Text("SMTP 设置", size=14, weight=ft.FontWeight.NORMAL),
        smtp_server_field,
        ft.Row([smtp_port_field, smtp_ssl_switch]),
        ft.Divider(),
        ft.Text("POP3 设置", size=14, weight=ft.FontWeight.NORMAL),
        pop3_server_field,
        ft.Row([pop3_port_field, pop3_ssl_switch]),
        ft.Row([ft.ElevatedButton("保存", on_click=save_server_config)], alignment=ft.MainAxisAlignment.END),
        ft.Divider(),
        ft.Row([ft.Text("服务器配置列表", size=16, weight=ft.FontWeight.BOLD)]),
        ft.Container(
            content=custom_servers_list,
            height=300, 
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
        ),
        status_text,

        ft.Divider(),
        ft.Row([
            ft.Container(expand=True), 
            ft.TextButton("关闭", on_click=close_dialog), 
        ], alignment=ft.MainAxisAlignment.END),
    ], spacing=15, scroll=ft.ScrollMode.AUTO, width=600, height=700)

    server_dialog = ft.AlertDialog(
        modal=True,
        title=None,
        content=dialog_content,
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return server_dialog