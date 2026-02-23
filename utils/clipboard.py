#使用 PySide6 QClipboard 实现跨平台支持
import threading
from typing import Callable, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer


class ClipboardManager(QObject):
    clipboard_changed = Signal(str)
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.clipboard = app.clipboard()
        self._last_text = ""
        self._monitoring = False
        self._timer: Optional[QTimer] = None
        self._on_change_callback = None
    
    def get_text(self) -> str:
        return self.clipboard.text()
    
    def set_text(self, text: str):
        self.clipboard.setText(text)
        self._last_text = text
    
    def has_text(self) -> bool:
        return bool(self.clipboard.text())
    
    def start_monitoring(self, on_change: Callable[[str], None] = None,  # type: ignore
                         interval: int = 500):
        """开始监控剪贴板变化"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._on_change_callback = on_change
        self._last_text = self.get_text()
        
        # QTimer 定期检查剪贴板
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_clipboard)
        self._timer.start(interval)
        print("[Clipboard] 开始监控剪贴板")
    
    def _check_clipboard(self):
        current_text = self.get_text()
        if current_text != self._last_text and current_text:
            self._last_text = current_text
            print(f"[Clipboard] 检测到新内容: {current_text[:30]}...")
            self.clipboard_changed.emit(current_text)
            if self._on_change_callback:
                self._on_change_callback(current_text)
    
    def stop_monitoring(self):
        self._monitoring = False
        if self._timer:
            self._timer.stop()
            self._timer = None
        print("[Clipboard] 停止监控剪贴板")
    
    def clear(self):
        self.clipboard.clear()
        self._last_text = ""
