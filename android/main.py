"""
EasyConnect Android 版本
基于 Kivy 框架，与桌面版共享核心网络协议
可在 Windows 上运行测试
"""
import os
import sys
import json
import socket
import threading
from typing import Optional, Callable

os.environ['KIVY_TEXT'] = 'pil'  # Windows 兼容性

from kivy.config import Config
Config.set('kivy', 'log_level', 'info')
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.utils import platform
from kivy.core.text import LabelBase

# Windows 中文字体支持
if platform in ('win', 'windows'):
    # 尝试注册中文字体
    try:
        font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微软雅黑
        if os.path.exists(font_path):
            LabelBase.register(name='default', fn_regular=font_path)
    except Exception as e:
        print(f"[Warning] Font registration failed: {e}")

# 尝试导入 zeroconf 
try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    print("[Warning] zeroconf not available, using manual IP input")

# ==================== 配置 ====================
APP_NAME = "EasyConnect"
SERVICE_TYPE = "_easyconnect._tcp.local."
TRANSFER_PORT = 52525
BUFFER_SIZE = 8192

class MessageType:
    TEXT = "TEXT"
    FILE = "FILE"


def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_device_name():
    """获取设备名称"""
    if platform == 'android':
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            return f"{Build.MANUFACTURER} {Build.MODEL}"
        except:
            return "Android Device"
    return socket.gethostname()


# ==================== 网络模块 ====================
class Device:
    """设备信息"""
    def __init__(self, name: str, ip: str, port: int = TRANSFER_PORT):
        self.name = name
        self.ip = ip
        self.port = port


class TransferClient:
    """传输客户端"""
    
    def __init__(self):
        self.device_name = get_device_name()
    
    def send_text(self, target_ip: str, target_port: int, text: str,
                  on_success: Callable = None, on_error: Callable = None):
        """发送文字"""
        def _send():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(10)
                    s.connect((target_ip, target_port))
                    
                    message = {
                        'type': MessageType.TEXT,
                        'sender': self.device_name,
                        'content': text
                    }
                    
                    data = json.dumps(message, ensure_ascii=False).encode('utf-8')
                    s.sendall(len(data).to_bytes(4, 'big'))
                    s.sendall(data)
                    
                    ack = s.recv(3)
                    if ack == b'ACK':
                        if on_success:
                            Clock.schedule_once(lambda dt: on_success(), 0)
                    else:
                        raise Exception("未收到确认")
                        
            except Exception as e:
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)
        
        threading.Thread(target=_send, daemon=True).start()


class TransferServer:
    """传输服务器"""
    
    def __init__(self, port: int = TRANSFER_PORT):
        self.port = port
        self._running = False
        self._on_text_received = None
    
    def set_text_callback(self, callback):
        self._on_text_received = callback
    
    def start(self):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()
    
    def _run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)
        server.settimeout(1)
        
        while self._running:
            try:
                conn, addr = server.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break
        
        server.close()
    
    def _handle(self, conn):
        try:
            conn.settimeout(30)
            
            length_data = conn.recv(4)
            if not length_data:
                return
            
            msg_length = int.from_bytes(length_data, 'big')
            msg_data = b''
            while len(msg_data) < msg_length:
                chunk = conn.recv(min(BUFFER_SIZE, msg_length - len(msg_data)))
                if not chunk:
                    break
                msg_data += chunk
            
            message = json.loads(msg_data.decode('utf-8'))
            
            if message.get('type') == MessageType.TEXT:
                conn.sendall(b'ACK')
                sender = message.get('sender', 'Unknown')
                content = message.get('content', '')
                
                if self._on_text_received:
                    Clock.schedule_once(
                        lambda dt: self._on_text_received(sender, content), 0
                    )
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            conn.close()
    
    def stop(self):
        self._running = False


# ==================== UI 组件 ====================
class DeviceCard(BoxLayout):
    """设备卡片"""
    
    def __init__(self, device: Device, on_click: Callable, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = 10
        self.spacing = 10
        
        self.device = device
        
        # 设备信息
        info = BoxLayout(orientation='vertical')
        info.add_widget(Label(
            text=device.name,
            font_size=16,
            halign='left',
            color=(0.2, 0.2, 0.2, 1)
        ))
        info.add_widget(Label(
            text=device.ip,
            font_size=12,
            halign='left',
            color=(0.5, 0.5, 0.5, 1)
        ))
        self.add_widget(info)
        
        # 发送按钮
        btn = Button(
            text='发送',
            size_hint_x=0.3,
            background_color=(1, 0.6, 0, 1)
        )
        btn.bind(on_press=lambda x: on_click(device))
        self.add_widget(btn)


class MessageBubble(BoxLayout):
    """消息气泡"""
    
    def __init__(self, sender: str, content: str, is_received: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = 10
        self.spacing = 5
        
        # 发送者
        self.add_widget(Label(
            text=f"{'收到' if is_received else '发送'} - {sender}",
            font_size=12,
            size_hint_y=None,
            height=20,
            color=(0.5, 0.5, 0.5, 1)
        ))
        
        # 内容
        content_label = Label(
            text=content[:200] + ('...' if len(content) > 200 else ''),
            font_size=14,
            size_hint_y=None,
            text_size=(None, None),
            color=(0.2, 0.2, 0.2, 1)
        )
        content_label.bind(texture_size=lambda *x: setattr(content_label, 'height', content_label.texture_size[1]))
        self.add_widget(content_label)
        
        # 复制按钮
        if is_received:
            copy_btn = Button(
                text='复制',
                size_hint_y=None,
                height=30,
                background_color=(0.3, 0.7, 0.3, 1)
            )
            copy_btn.bind(on_press=lambda x: self._copy(content))
            self.add_widget(copy_btn)
        
        self.height = 100
    
    def _copy(self, text):
        Clipboard.copy(text)


# ==================== 主应用 ====================
class EasyConnectApp(App):
    """EasyConnect Android 应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.devices = {}  # ip -> Device
        self.transfer_client = TransferClient()
        self.transfer_server = TransferServer()
        self.zeroconf = None
        self.browser = None
    
    def build(self):
        self.title = APP_NAME
        
        # 主布局
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题栏
        header = BoxLayout(size_hint_y=None, height=50)
        header.add_widget(Label(
            text=f'📡 {APP_NAME}',
            font_size=20,
            color=(0.2, 0.5, 0.8, 1)
        ))
        root.add_widget(header)
        
        # 本机信息
        local_info = BoxLayout(size_hint_y=None, height=40)
        self.ip_label = Label(
            text=f'本机IP: {get_local_ip()}',
            font_size=14,
            color=(0.4, 0.4, 0.4, 1)
        )
        local_info.add_widget(self.ip_label)
        root.add_widget(local_info)
        
        # 创建选项卡式布局
        tabs = BoxLayout(size_hint_y=None, height=40, spacing=5)
        
        self.tab_devices = Button(text='设备', background_color=(0.2, 0.5, 0.8, 1))
        self.tab_send = Button(text='发送', background_color=(0.5, 0.5, 0.5, 1))
        self.tab_receive = Button(text='接收', background_color=(0.5, 0.5, 0.5, 1))
        
        self.tab_devices.bind(on_press=lambda x: self.show_tab('devices'))
        self.tab_send.bind(on_press=lambda x: self.show_tab('send'))
        self.tab_receive.bind(on_press=lambda x: self.show_tab('receive'))
        
        tabs.add_widget(self.tab_devices)
        tabs.add_widget(self.tab_send)
        tabs.add_widget(self.tab_receive)
        root.add_widget(tabs)
        
        # 内容区域
        self.content_area = BoxLayout()
        root.add_widget(self.content_area)
        
        # 创建各个页面
        self._create_devices_page()
        self._create_send_page()
        self._create_receive_page()
        
        # 默认显示设备页
        self.show_tab('devices')
        
        return root
    
    def _create_devices_page(self):
        """创建设备列表页"""
        self.devices_page = BoxLayout(orientation='vertical', spacing=10)
        
        # 手动添加设备
        add_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
        self.ip_input = TextInput(
            hint_text='输入目标IP地址',
            multiline=False,
            size_hint_x=0.7
        )
        add_btn = Button(
            text='添加',
            size_hint_x=0.3,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        add_btn.bind(on_press=self._add_manual_device)
        add_layout.add_widget(self.ip_input)
        add_layout.add_widget(add_btn)
        self.devices_page.add_widget(add_layout)
        
        # 设备列表
        self.devices_scroll = ScrollView()
        self.devices_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.devices_list.bind(minimum_height=self.devices_list.setter('height'))
        self.devices_scroll.add_widget(self.devices_list)
        self.devices_page.add_widget(self.devices_scroll)
        
        # 刷新按钮
        refresh_btn = Button(
            text='🔄 刷新设备',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.5, 0.8, 1)
        )
        refresh_btn.bind(on_press=lambda x: self._refresh_devices())
        self.devices_page.add_widget(refresh_btn)
    
    def _create_send_page(self):
        """创建发送页"""
        self.send_page = BoxLayout(orientation='vertical', spacing=10)
        
        # 文字输入
        self.send_page.add_widget(Label(
            text='发送文字:',
            size_hint_y=None,
            height=30,
            halign='left'
        ))
        
        self.text_input = TextInput(
            hint_text='输入要发送的文字...',
            multiline=True,
            size_hint_y=0.4
        )
        self.send_page.add_widget(self.text_input)
        
        # 从剪贴板粘贴
        paste_btn = Button(
            text='📋 粘贴剪贴板',
            size_hint_y=None,
            height=50,
            background_color=(0.4, 0.6, 0.8, 1)
        )
        paste_btn.bind(on_press=self._paste_clipboard)
        self.send_page.add_widget(paste_btn)
        
        # 目标设备选择
        self.send_page.add_widget(Label(
            text='选择目标设备:',
            size_hint_y=None,
            height=30
        ))
        
        self.target_scroll = ScrollView(size_hint_y=0.4)
        self.target_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.target_list.bind(minimum_height=self.target_list.setter('height'))
        self.target_scroll.add_widget(self.target_list)
        self.send_page.add_widget(self.target_scroll)
    
    def _create_receive_page(self):
        """创建接收页"""
        self.receive_page = BoxLayout(orientation='vertical', spacing=10)
        
        # 接收历史
        self.receive_page.add_widget(Label(
            text='📥 接收历史:',
            size_hint_y=None,
            height=30
        ))
        
        self.receive_scroll = ScrollView()
        self.receive_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.receive_list.bind(minimum_height=self.receive_list.setter('height'))
        self.receive_scroll.add_widget(self.receive_list)
        self.receive_page.add_widget(self.receive_scroll)
        
        # 清空按钮
        clear_btn = Button(
            text='🗑️ 清空历史',
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.3, 0.3, 1)
        )
        clear_btn.bind(on_press=lambda x: self.receive_list.clear_widgets())
        self.receive_page.add_widget(clear_btn)
    
    def show_tab(self, tab_name):
        """切换选项卡"""
        self.content_area.clear_widgets()
        
        # 重置按钮颜色
        self.tab_devices.background_color = (0.5, 0.5, 0.5, 1)
        self.tab_send.background_color = (0.5, 0.5, 0.5, 1)
        self.tab_receive.background_color = (0.5, 0.5, 0.5, 1)
        
        if tab_name == 'devices':
            self.content_area.add_widget(self.devices_page)
            self.tab_devices.background_color = (0.2, 0.5, 0.8, 1)
            self._update_devices_list()
        elif tab_name == 'send':
            self.content_area.add_widget(self.send_page)
            self.tab_send.background_color = (1, 0.6, 0, 1)
            self._update_target_list()
        elif tab_name == 'receive':
            self.content_area.add_widget(self.receive_page)
            self.tab_receive.background_color = (0.3, 0.7, 0.3, 1)
    
    def _add_manual_device(self, *args):
        """手动添加设备"""
        ip = self.ip_input.text.strip()
        if ip:
            device = Device(name=f"设备 ({ip})", ip=ip)
            self.devices[ip] = device
            self._update_devices_list()
            self.ip_input.text = ''
    
    def _update_devices_list(self):
        """更新设备列表"""
        self.devices_list.clear_widgets()
        for ip, device in self.devices.items():
            card = DeviceCard(device, self._on_device_click)
            self.devices_list.add_widget(card)
        
        if not self.devices:
            self.devices_list.add_widget(Label(
                text='暂无设备\n请手动添加IP或等待自动发现',
                size_hint_y=None,
                height=100,
                color=(0.5, 0.5, 0.5, 1)
            ))
    
    def _update_target_list(self):
        """更新发送目标列表"""
        self.target_list.clear_widgets()
        for ip, device in self.devices.items():
            card = DeviceCard(device, self._send_to_device)
            self.target_list.add_widget(card)
    
    def _on_device_click(self, device: Device):
        """设备点击事件"""
        self.show_tab('send')
    
    def _send_to_device(self, device: Device):
        """发送到设备"""
        text = self.text_input.text.strip()
        if not text:
            self._show_popup('提示', '请输入要发送的文字')
            return
        
        self.transfer_client.send_text(
            device.ip, device.port, text,
            on_success=lambda: self._on_send_success(device),
            on_error=lambda e: self._show_popup('发送失败', str(e))
        )
    
    def _on_send_success(self, device: Device):
        """发送成功"""
        self._show_popup('成功', f'已发送到 {device.name}')
        self.text_input.text = ''
    
    def _paste_clipboard(self, *args):
        """粘贴剪贴板内容"""
        text = Clipboard.paste()
        if text:
            self.text_input.text = text
        else:
            self._show_popup('提示', '剪贴板为空')
    
    def _on_text_received(self, sender: str, content: str):
        """收到文字"""
        bubble = MessageBubble(sender, content, is_received=True)
        self.receive_list.add_widget(bubble, index=0)
        
        # 自动复制到剪贴板
        Clipboard.copy(content)
        
        # 显示通知
        self._show_popup('收到文字', f'来自 {sender}\n已复制到剪贴板')
    
    def _refresh_devices(self):
        """刷新设备列表"""
        self._update_devices_list()
        self._show_popup('提示', '设备列表已刷新')
    
    def _show_popup(self, title: str, message: str):
        """显示弹窗"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        
        btn = Button(text='确定', size_hint_y=None, height=50)
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def on_start(self):
        """应用启动"""
        # 启动接收服务器
        self.transfer_server.set_text_callback(self._on_text_received)
        self.transfer_server.start()
        
        # 启动设备发现 (如果可用)
        if ZEROCONF_AVAILABLE:
            try:
                self._start_discovery()
            except:
                pass
    
    def on_stop(self):
        """应用停止"""
        self.transfer_server.stop()
        if self.zeroconf:
            self.zeroconf.close()
    
    def _start_discovery(self):
        """启动设备发现"""
        if not ZEROCONF_AVAILABLE:
            return
        
        class Listener(ServiceListener):
            def __init__(self, app):
                self.app = app
                self.local_ip = get_local_ip()
            
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info:
                    addresses = info.parsed_addresses()
                    if addresses:
                        ip = addresses[0]
                        if ip != self.local_ip:
                            device = Device(
                                name=info.server.rstrip('.') if info.server else name,
                                ip=ip,
                                port=info.port or TRANSFER_PORT
                            )
                            self.app.devices[ip] = device
                            Clock.schedule_once(lambda dt: self.app._update_devices_list(), 0)
            
            def remove_service(self, zc, type_, name):
                pass
            
            def update_service(self, zc, type_, name):
                pass
        
        self.zeroconf = Zeroconf()
        
        # 注册服务
        local_ip = get_local_ip()
        self.service_info = ServiceInfo(
            SERVICE_TYPE,
            f"{get_device_name()}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=TRANSFER_PORT,
            properties={'version': '1.0'}
        )
        self.zeroconf.register_service(self.service_info)
        
        # 浏览服务
        self.browser = ServiceBrowser(self.zeroconf, SERVICE_TYPE, Listener(self))


if __name__ == '__main__':
    EasyConnectApp().run()
