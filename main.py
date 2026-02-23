"""EasyConnect 主程序入口"""
import sys
import os
import signal
import atexit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QThread

from config import APP_NAME, TRANSFER_PORT, get_device_name, get_local_ip
from network.discovery import DeviceDiscovery, Device
from network.transfer import FileTransfer, TransferServer
from ui.main_window import MainWindow
from ui.send_panel import SendPanel
from ui.receive_bubble import BubbleManager
from utils.clipboard import ClipboardManager


class EasyConnectApp(QObject):
    """应用主类，整合所有模块"""
    
    device_found_signal = Signal(str, str)  # ip, name
    device_lost_signal = Signal(str)  # ip
    text_received_signal = Signal(str, str)  # sender, text
    file_received_signal = Signal(str, str, str)  # sender, filename, filepath
    transfer_progress_signal = Signal(str, int, int)  # filename, current, total
    send_success_signal = Signal()
    send_error_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self._stopped = False
        
        # 创建应用
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        
        # 连接退出信号
        self.app.aboutToQuit.connect(self._on_about_to_quit)
        
        # 初始化组件
        self._init_network()
        self._init_ui()
        self._connect_signals()
        
        print(f"[App] EasyConnect 启动中...")
        print(f"[App] 设备名: {get_device_name()}")
        print(f"[App] IP地址: {get_local_ip()}")
    
    def _init_network(self):
        self.discovery = DeviceDiscovery()
        self.discovery.set_callbacks(
            on_found=self._on_device_found,
            on_lost=self._on_device_lost
        )
        self.transfer = FileTransfer()
        self.server = TransferServer(TRANSFER_PORT)
        self.server.set_callbacks(
            on_text=self._on_text_received,
            on_file=self._on_file_received,
            on_progress=self._on_transfer_progress
        )
    
    def _init_ui(self):
        self.main_window = MainWindow()
        self.send_panel = SendPanel()
        self.bubble_manager = BubbleManager()
        self.clipboard_manager = ClipboardManager(self.app)
    
    def _connect_signals(self):
        self.device_found_signal.connect(self.main_window.add_device)
        self.device_lost_signal.connect(self.main_window.remove_device)
        self.text_received_signal.connect(self._handle_text_received)
        self.file_received_signal.connect(self._handle_file_received)
        self.main_window.send_text_requested.connect(self._send_text)
        self.main_window.send_file_requested.connect(self._send_file)
        self.send_panel.send_to_device.connect(self._on_send_panel_device_selected)
        self.send_success_signal.connect(self._on_send_success)
        self.send_error_signal.connect(self._on_send_error)
        self.clipboard_manager.clipboard_changed.connect(self._on_clipboard_changed)
    
    def _on_device_found(self, device: Device):
        self.send_panel.add_device(device.ip, device.name)
        self.device_found_signal.emit(device.ip, device.name)
    
    def _on_device_lost(self, ip: str):
        self.send_panel.remove_device(ip)
        self.device_lost_signal.emit(ip)
    
    def _on_text_received(self, sender: str, text: str):
        self.text_received_signal.emit(sender, text)
    
    def _on_file_received(self, sender: str, filename: str, filepath: str):
        self.file_received_signal.emit(sender, filename, filepath)
    
    def _on_transfer_progress(self, filename: str, current: int, total: int):
        self.transfer_progress_signal.emit(filename, current, total)
    
    @Slot(str, str)
    def _handle_text_received(self, sender: str, text: str):
        """处理文字接收"""
        self.bubble_manager.show_text_bubble(sender, text)
        self.main_window.add_receive_item(sender, text, is_file=False)
        self.clipboard_manager.set_text(text)
    
    @Slot(str, str, str)
    def _handle_file_received(self, sender: str, filename: str, filepath: str):
        """处理文件接收"""
        self.bubble_manager.show_file_bubble(sender, filename, filepath)
        self.main_window.add_receive_item(sender, filename, is_file=True)
    
    @Slot(str, str)
    def _send_text(self, target_ip: str, text: str):
        device = self.discovery.get_device_by_ip(target_ip)
        port = device.port if device else TRANSFER_PORT
        self.transfer.send_text(
            target_ip, port, text,
            on_success=lambda: self.send_success_signal.emit(),
            on_error=lambda e: self.send_error_signal.emit(e)
        )
    
    @Slot(str, str)
    def _send_file(self, target_ip: str, file_path: str):
        device = self.discovery.get_device_by_ip(target_ip)
        port = device.port if device else TRANSFER_PORT
        self.transfer.send_file(
            target_ip, port, file_path,
            on_progress=lambda c, t: self.main_window.update_progress(c, t),
            on_success=lambda: self.send_success_signal.emit(),
            on_error=lambda e: self.send_error_signal.emit(e)
        )
    
    @Slot(str)
    def _on_send_panel_device_selected(self, ip: str):
        content, content_type = self.send_panel.get_content()
        if content_type == "text":
            self._send_text(ip, content)
        else:
            self._send_file(ip, content)
    
    @Slot()
    def _on_send_success(self):
        self.main_window.statusBar().showMessage("发送成功！", 3000)
    
    @Slot(str)
    def _on_send_error(self, error: str):
        self.main_window.statusBar().showMessage(f"发送失败: {error}", 5000)
    
    @Slot(str)
    def _on_clipboard_changed(self, text: str):
        preview = text[:30] + "..." if len(text) > 30 else text
        self.main_window.statusBar().showMessage(f"剪贴板: {preview}", 2000)
    
    def start(self):
        """启动应用"""
        self.discovery.start()
        self.server.start()
        self.clipboard_manager.start_monitoring()
        self.main_window.show()
        print("[App] EasyConnect 已启动")
        return self.app.exec()
    
    def stop(self):
        """停止应用"""
        if self._stopped:
            return
        self._stopped = True
        
        print("[App] 1. 开始关闭，停止剪贴板监控...")
        try:
            self.clipboard_manager.stop_monitoring()
        except Exception as e:
            print(f"[App] 停止剪贴板监控出错: {e}")
        
        print("[App] 2. 停止传输服务器...")
        try:
            self.server.stop()
        except Exception as e:
            print(f"[App] 停止服务器出错: {e}")
        
        print("[App] 3. 停止设备发现服务...")
        try:
            self.discovery.stop()
        except Exception as e:
            print(f"[App] 停止发现服务出错: {e}")
        
        print("[App] 4. 清理气泡...")
        try:
            self.bubble_manager.clear_all()
        except Exception as e:
            print(f"[App] 清理气泡出错: {e}")
        
        print("[App] 5. 隐藏系统托盘...")
        try:
            if hasattr(self.main_window, 'tray_icon') and self.main_window.tray_icon:
                self.main_window.tray_icon.hide()
        except Exception as e:
            print(f"[App] 隐藏托盘出错: {e}")
        
        print("[App] 6. 所有组件已停止！")
    
    @Slot()
    def _on_about_to_quit(self):
        """应用即将退出时的清理"""
        print("[App] 收到退出信号，开始清理...")
        self.stop()
        print("[App] 强制终止进程...")
        os._exit(0)


# 全局应用实例（用于信号处理）
_app_instance = None


def _signal_handler(signum, frame):
    """处理 Ctrl+C 等信号"""
    print("\n[App] 收到退出信号，正在关闭...")
    if _app_instance:
        _app_instance.stop()
    # 强制退出
    import os
    os._exit(0)


def main():
    """主函数"""
    global _app_instance
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    app = EasyConnectApp()
    _app_instance = app
    
    # 注册退出时的清理
    atexit.register(app.stop)
    
    # 执行主循环
    exit_code = app.start()
    
    # 主循环退出后，确保清理
    print("[Final] 界面已关闭，执行最后的清理...")
    app.stop()
    
    # 强制结束进程
    os._exit(exit_code)


if __name__ == "__main__":
    main()
