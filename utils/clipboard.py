#使用 PySide6 的 QClipboard 实现跨平台支持
import threading
from typing import Callable, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer


class ClipboardManager(QObject):#剪贴板管理器
    # Qt 信号
    clipboard_changed = Signal(str)  # 剪贴板内容变化信号
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.clipboard = app.clipboard()
        self._last_text = ""
        self._monitoring = False
        self._timer: Optional[QTimer] = None
        
        # 回调函数
        self._on_change_callback = None
    
    def get_text(self) -> str:
        """获取剪贴板中的文字"""
        return self.clipboard.text()
    
    def set_text(self, text: str):
        """设置剪贴板文字"""
        self.clipboard.setText(text)
        self._last_text = text  # 更新记录，避免触发自己的变化回调
    
    def has_text(self) -> bool:
        """检查剪贴板是否有文字"""
        return bool(self.clipboard.text())
    
    def start_monitoring(self, on_change: Callable[[str], None] = None,  # type: ignore
                         interval: int = 500):
        """
        开始监控剪贴板变化
        
        Args:
            on_change: 内容变化时的回调函数
            interval: 检查间隔（毫秒）
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._on_change_callback = on_change
        self._last_text = self.get_text()
        
        # 使用 QTimer 定期检查剪贴板
        # 注意：某些系统上 clipboard.dataChanged 信号不可靠
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_clipboard)
        self._timer.start(interval)
        
        print("[Clipboard] 开始监控剪贴板")
    
    def _check_clipboard(self):
        """检查剪贴板是否变化"""
        current_text = self.get_text()
        if current_text != self._last_text and current_text:
            self._last_text = current_text
            print(f"[Clipboard] 检测到新内容: {current_text[:30]}...")
            
            # 发送信号
            self.clipboard_changed.emit(current_text)
            
            # 调用回调
            if self._on_change_callback:
                self._on_change_callback(current_text)
    
    def stop_monitoring(self):
        """停止监控剪贴板"""
        self._monitoring = False
        if self._timer:
            self._timer.stop()
            self._timer = None
        print("[Clipboard] 停止监控剪贴板")
    
    def clear(self):
        """清空剪贴板"""
        self.clipboard.clear()
        self._last_text = ""
