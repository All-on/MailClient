# gui/contact_table.py

# 通信表管理界面

import flet as ft
import os
from core.contact_manager import get_contact_manager

def create_contact_table_sheet(page, user_email):
    # 创建通信表管理界面
    
    # 获取当前用户的ContactManager
    contact_manager = get_contact_manager(user_email)
    
    # 状态变量
    current_view = "main"
    
    # 联系人列表控件
    contacts_grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=200,
        child_aspect_ratio=2.0,
        spacing=10,
        run_spacing=10,
    )
    
    # 表单字段
    email_field = ft.TextField(
        label="邮箱地址",
        hint_text="例如: user@qq.com",
        width=300,
        prefix_icon=ft.Icons.MAIL
    )
    
    key_field = ft.TextField(
        label="共享密钥",
        hint_text="输入共享密钥",
        password=True,
        can_reveal_password=True,
        width=300,
        prefix_icon=ft.Icons.KEY
    )
    
    default_key_field = ft.TextField(
        label="默认密钥",
        hint_text="输入新的默认密钥",
        password=True,
        can_reveal_password=True,
        width=300
    )
    
    # 状态文本
    status_text = ft.Text("", color=ft.Colors.BLUE)
    status_info = ft.Text("", size=12, color=ft.Colors.BLUE)
    
    def load_contacts():
        # 加载联系人列表
        contacts_grid.controls.clear()
        
        contacts = contact_manager.get_all_contacts()
        
        if contacts:
            for contact in contacts:
                # 创建联系人卡片
                contact_card = ft.Card(
                    elevation=2,
                    content=ft.Container(
                        content=ft.Column([
                            # 邮箱
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.BLUE),
                                ft.Text(
                                    contact["email"].split('@')[0][:10] + "..." if len(contact["email"].split('@')[0]) > 10 else contact["email"].split('@')[0],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                )
                            ], spacing=5),
                            
                            # 域名
                            ft.Text(
                                f"@{contact['email'].split('@')[1]}" if '@' in contact["email"] else "",
                                size=10,
                                color=ft.Colors.GREY_600
                            ),
                            
                            # 密钥预览
                            ft.Row([
                                ft.Icon(ft.Icons.KEY, size=12, color=ft.Colors.ORANGE),
                                ft.Text(
                                    contact["key_display"],
                                    size=10,
                                    color=ft.Colors.GREY_700
                                )
                            ], spacing=3),
                            
                            # 删除按钮
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_size=16,
                                    icon_color=ft.Colors.RED,
                                    tooltip="删除联系人",
                                    on_click=lambda e, email=contact["email"]: delete_contact(email)
                                ),
                                alignment=ft.Alignment.CENTER
                            )
                        ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=10,
                        width=190,
                        height=110,
                        border_radius=5,
                        bgcolor=ft.Colors.WHITE
                    )
                )
                contacts_grid.controls.append(contact_card)
        else:
            contacts_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=ft.Colors.GREY, size=40),
                        ft.Text("暂无联系人", color=ft.Colors.GREY),
                        ft.Text("点击上方添加按钮", size=12, color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                    width=400
                )
            )
        
        # 确保页面更新
        if page:
            page.update()
    
    def delete_contact(email: str):
        # 删除联系人 - 使用复制覆盖方式确保保存
        try:
            # 备份原始数据
            original_contacts = contact_manager.contact_table.copy()
            
            # 尝试删除
            if contact_manager.remove_contact(email):
                # 验证删除是否成功
                if email.lower() not in contact_manager.contact_table.get("contacts", {}):
                    status_text.value = f"已删除联系人: {email}"
                    status_text.color = ft.Colors.GREEN
                    
                    # 重新加载列表
                    load_contacts()
                    update_status()
                    
                    # 显示成功消息
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"已成功删除联系人: {email}"),
                        action="OK"
                    )
                    page.snack_bar.open = True
                else:
                    # 删除失败，恢复备份
                    contact_manager.contact_table = original_contacts
                    contact_manager.save_contact_table()
                    status_text.value = "删除失败：联系人仍存在"
                    status_text.color = ft.Colors.RED
            else:
                status_text.value = "删除失败"
                status_text.color = ft.Colors.RED
                
        except Exception as e:
            status_text.value = f"删除失败: {str(e)}"
            status_text.color = ft.Colors.RED
            print(f"删除联系人异常: {e}")
        
        if page:
            page.update()
    
    def add_new_contact(e):
        # 添加新联系人
        email = email_field.value.strip()
        key = key_field.value.strip()
        
        # 验证输入
        if not email or '@' not in email:
            status_text.value = "请输入有效的邮箱地址"
            status_text.color = ft.Colors.RED
            page.update()
            return
        
        if not key:
            status_text.value = "请输入共享密钥"
            status_text.color = ft.Colors.RED
            page.update()
            return
        
        if len(key) < 4:
            status_text.value = "密钥长度至少为4个字符"
            status_text.color = ft.Colors.RED
            page.update()
            return
        
        # 添加联系人
        if contact_manager.add_contact(email, key):
            status_text.value = f"已添加联系人: {email}"
            status_text.color = ft.Colors.GREEN
            
            # 清空表单
            email_field.value = ""
            key_field.value = ""
            
            # 重新加载列表
            load_contacts()
            update_status()
        else:
            status_text.value = "添加失败"
            status_text.color = ft.Colors.RED
        
        page.update()
    
    def update_status():
        # 更新状态信息
        contact_count = contact_manager.get_contact_count()
        default_key_display = contact_manager.get_default_key_display()
        
        status_info.value = f"联系人: {contact_count} 个 | 默认密钥: {default_key_display}"
        
        if page:
            page.update()
    
    def show_main_view():
        # 显示主视图
        current_view = "main"
        
        # 重新构建主视图内容
        content = ft.Column([
            ft.Row([
                ft.Text("通信表管理", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"({user_email})", size=12, color=ft.Colors.GREY_600),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    on_click=close_sheet,
                    icon_color=ft.Colors.GREY
                )
            ]),
            ft.Divider(),
            
            # 状态信息
            ft.Row([
                status_info,
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "编辑默认密钥",
                    icon=ft.Icons.EDIT,
                    on_click=lambda e: show_edit_default_key_view(),  # 使用 lambda 包装
                    height=40
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(),
            
            # 添加联系人表单
            ft.Text("添加新联系人", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([email_field], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([key_field], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([
                ft.ElevatedButton(
                    "添加联系人",
                    icon=ft.Icons.ADD,
                    on_click=add_new_contact,
                    height=40
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            status_text,
            ft.Divider(),
            
            # 联系人网格
            ft.Text("联系人密钥表", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=contacts_grid,
                height=200,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                padding=10
            ),
            
            ft.Divider(),
            ft.Text("说明:", size=14, weight=ft.FontWeight.BOLD),
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO, size=12, color=ft.Colors.BLUE),
                    ft.Text("默认密钥用于加密发送给未在通信表中的邮箱的邮件，若无改动则不加密", size=12, color=ft.Colors.GREY_600)
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.INFO, size=12, color=ft.Colors.BLUE),
                    ft.Text("通信表中的密钥优先级高于默认密钥", size=12, color=ft.Colors.GREY_600)
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.INFO, size=12, color=ft.Colors.BLUE),
                    ft.Text("发送邮件时会自动使用对应的密钥加密", size=12, color=ft.Colors.GREY_600)
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.INFO, size=12, color=ft.Colors.BLUE),
                    ft.Text("接收邮件时会自动尝试用发件人的密钥解密", size=12, color=ft.Colors.GREY_600)
                ])
            ], spacing=3),
            
            ft.Row([
                ft.ElevatedButton("关闭", on_click=close_sheet, height=40)
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        sheet_container.content = content
        page.update()
    
    def show_edit_default_key_view(e=None):
        # 显示编辑默认密钥视图

        nonlocal current_view
        current_view = "edit_default_key"
        
        # 获取当前默认密钥
        current_key = contact_manager.get_default_key()
        default_key_field.value = current_key
        
        edit_status_text = ft.Text("", color=ft.Colors.BLUE)
        
        def save_default_key(e):
            new_key = default_key_field.value.strip()
            if not new_key:
                edit_status_text.value = "请输入默认密钥"
                edit_status_text.color = ft.Colors.RED
                page.update()
                return
            
            if len(new_key) < 4:
                edit_status_text.value = "密钥长度至少为4个字符"
                edit_status_text.color = ft.Colors.RED
                page.update()
                return
            
            # 备份原始密钥
            original_key = contact_manager.get_default_key()
            
            # 尝试更新
            if contact_manager.update_default_key(new_key):
                # 验证更新是否成功
                if contact_manager.get_default_key() == new_key:
                    edit_status_text.value = "默认密钥已更新"
                    edit_status_text.color = ft.Colors.GREEN
                    
                    # 显示成功消息
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("默认密钥已成功更新"),
                        action="OK"
                    )
                    page.snack_bar.open = True
                    
                    # 延迟返回主视图
                    def return_to_main():
                        show_main_view()
                        update_status()
                    
                    import threading
                    timer = threading.Timer(1.0, return_to_main)
                    timer.daemon = True
                    timer.start()
                else:
                    # 恢复原始密钥
                    contact_manager.contact_table["default_key"] = original_key
                    contact_manager.save_contact_table()
                    edit_status_text.value = "更新失败：密钥未改变"
                    edit_status_text.color = ft.Colors.RED
            else:
                edit_status_text.value = "更新失败"
                edit_status_text.color = ft.Colors.RED
            
            page.update()
        
        def cancel_edit(e):
            show_main_view()
        
        content = ft.Column([
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: show_main_view(),
                    icon_color=ft.Colors.BLUE
                ),
                ft.Text("编辑默认密钥", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    on_click=close_sheet,
                    icon_color=ft.Colors.GREY
                )
            ]),
            ft.Divider(),
            
            ft.Text("默认密钥用于加密发送给未在通信表中的邮箱的邮件", size=12),
            ft.Text("建议使用长度至少8个字符的复杂密钥", size=12, color=ft.Colors.GREY_600),
            ft.Divider(),
            
            default_key_field,
            ft.Text("密钥长度至少4个字符", size=11, color=ft.Colors.GREY_500),
            edit_status_text,
            
            ft.Row([
                ft.OutlinedButton("取消", on_click=cancel_edit, width=120),
                ft.ElevatedButton("保存", on_click=save_default_key, width=120)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            
            ft.Divider(),
            ft.Text("当前用户: ", size=12, weight=ft.FontWeight.BOLD),
            ft.Text(user_email, size=12, color=ft.Colors.BLUE),
            ft.Text(f"通信表文件: {contact_manager.contact_table_file}", size=10, color=ft.Colors.GREY_600),
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        sheet_container.content = content
        page.update()
    
    def close_sheet(e):
        # 关闭通信表界面
        contact_sheet.open = False
        page.update()
    
    # 创建容器用于动态切换内容
    sheet_container = ft.Container(
        padding=20,
        width=650,
        height=600
    )
    
    # 创建 BottomSheet
    contact_sheet = ft.BottomSheet(
        sheet_container,
        open=False
    )
    
    # 初始化数据
    load_contacts()
    update_status()
    show_main_view()
    
    return contact_sheet