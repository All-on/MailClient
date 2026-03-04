# gui/inbox_view.py

# 收件箱主视图

import flet as ft
import asyncio
from concurrent.futures import ThreadPoolExecutor
from core.email_client import EmailClient
from .mail_item import create_mail_item

async def create_inbox_view(page, user_email, user_password):
    # 创建收件箱界面 - 异步流式加载 - 函数式组件

    # 邮件列表
    mail_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=10
    )

    # 状态显示
    status_text = ft.Text("", color=ft.Colors.BLUE)

    # 刷新按钮
    refresh_button = ft.ElevatedButton(
        "刷新收件箱",
        icon="refresh",
        on_click=lambda e: page.run_task(refresh_emails)
    )
    
    # 倒计时文本控件
    countdown_text_control = ft.Text("10秒", size=14)
    
    # 刷新指示器 - 将显示在按钮位置
    refresh_indicator = ft.Container(
        content=ft.Row([
            ft.ProgressRing(width=20, height=20),
            countdown_text_control
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
        visible=False
    )

    # 异步任务引用和状态
    refresh_task = None
    countdown_task = None
    is_refreshing = False
    should_stop_countdown = False

    async def fetch_and_append_mails_async(max_count=20):
        # 异步获取邮件并逐个追加到列表 - 通过线程池执行同步任务
        # 创建一个线程池执行器
        executor = ThreadPoolExecutor(max_workers=1) # 限制并发数
        client = EmailClient(user_email, user_password)
        try:
            # 将同步的 fetch_emails 操作提交到线程池中执行
            emails = await asyncio.get_event_loop().run_in_executor(
                executor, client.fetch_emails, max_count
            )
            
            if emails:
                status_text.value = f"开始加载 {len(emails)} 封邮件..."
                status_text.color = ft.Colors.BLUE
                page.update()
                mail_list.controls.clear()
                page.update()

                for i, mail in enumerate(emails):
                    # 创建邮件项并添加到列表
                    mail_item_control = create_mail_item(page, mail, user_email)
                    mail_list.controls.append(mail_item_control)

                    # 每加载3封邮件更新一次状态，避免过于频繁
                    if (i + 1) % 3 == 0 or i == len(emails) - 1:
                        status_text.value = f"已加载 {i+1}/{len(emails)} 封邮件"
                        page.update()

                status_text.value = f"已成功加载 {len(emails)} 封邮件"
                status_text.color = ft.Colors.GREEN
            else:
                status_text.value = "收件箱为空"
                status_text.color = ft.Colors.GREY
        except Exception as ex:
            status_text.value = f"获取邮件失败: {str(ex)}"
            status_text.color = ft.Colors.RED
        finally:
            # 告诉倒计时任务可以停止了
            nonlocal should_stop_countdown
            should_stop_countdown = True
            # 关闭线程池
            executor.shutdown(wait=False) # 不等待当前任务完成就关闭，资源管理交给系统

    async def start_countdown():
        # 启动倒计时
        try:
            for i in range(10, 0, -1):
                # 检查是否需要停止倒计时
                if should_stop_countdown:
                    break
                
                # 更新倒计时文本
                countdown_text_control.value = f"{i}秒"
                
                # 根据剩余时间改变颜色
                if i <= 3:
                    countdown_text_control.color = ft.Colors.RED
                elif i <= 6:
                    countdown_text_control.color = ft.Colors.ORANGE
                else:
                    countdown_text_control.color = ft.Colors.BLUE
                
                page.update()
                await asyncio.sleep(1)
            
            # 10秒后如果还在刷新，显示"稍等"
            if not should_stop_countdown:
                countdown_text_control.value = "稍等"
                countdown_text_control.color = ft.Colors.ORANGE
                page.update()
                
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            print("倒计时任务被取消")
        except Exception as e:
            print(f"倒计时任务异常: {e}")

    async def refresh_emails(e=None):
        # 刷新邮件列表
        nonlocal refresh_task, countdown_task, is_refreshing, should_stop_countdown
        
        # 防止重复刷新
        if is_refreshing:
            return
        
        is_refreshing = True
        should_stop_countdown = False  # 重置停止标志
        
        # 切换显示：隐藏按钮，显示刷新指示器
        refresh_button.visible = False
        refresh_indicator.visible = True
        
        # 重置倒计时文本
        countdown_text_control.value = "10秒"
        countdown_text_control.color = ft.Colors.BLUE
        
        status_text.value = "正在获取邮件..."
        status_text.color = ft.Colors.BLUE
        page.update()

        try:
            # 清空列表
            mail_list.controls.clear()
            page.update()
            
            # 同时启动倒计时和邮件获取任务
            countdown_task = asyncio.create_task(start_countdown())
            refresh_task = asyncio.create_task(fetch_and_append_mails_async(max_count=20))
            
            # 等待邮件获取任务完成
            await refresh_task
            
            # 邮件获取完成后，如果倒计时还在运行，告诉它停止
            should_stop_countdown = True
            
            # 等待一小段时间，确保倒计时任务收到停止信号
            await asyncio.sleep(0.1)
            
        except asyncio.CancelledError:
            # 如果任务被取消
            status_text.value = "刷新已取消"
            status_text.color = ft.Colors.ORANGE
        except Exception as e:
            # 其他异常
            status_text.value = f"刷新异常: {str(e)}"
            status_text.color = ft.Colors.RED
        finally:
            # 确保状态恢复
            is_refreshing = False
            should_stop_countdown = True
            
            # 取消倒计时任务（如果还在运行）
            if countdown_task and not countdown_task.done():
                countdown_task.cancel()
            
            # 恢复UI显示
            refresh_button.visible = True
            refresh_indicator.visible = False
            
            # 确保页面更新
            page.update()

    # 创建界面内容
    content = ft.Column([
        # 顶部工具栏
        ft.Container(
            content=ft.Row([
                ft.Text("收件箱", size=24, weight=ft.FontWeight.BOLD),
                # 使用Stack来切换按钮和指示器
                ft.Stack([
                    ft.Container(content=refresh_button),
                    refresh_indicator
                ], width=150, height=40)  # 固定宽度高度，确保布局稳定
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.only(bottom=10)
        ),
        # 状态栏
        status_text,
        # 邮件列表
        ft.Container(
            content=mail_list,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            expand=True
        )
    ], expand=True)

    # 首次自动刷新
    async def auto_refresh():
        await asyncio.sleep(0.1)  # 等待界面渲染完成
        await refresh_emails()

    page.run_task(auto_refresh)

    return content