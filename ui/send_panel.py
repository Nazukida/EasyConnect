"""发送面板模块 - 悬浮发送区域"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QCursor


class DeviceButton(QPushButton):
    clicked_with_ip = Signal(str)
    
    def __init__(self, name: str, ip: str, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.name = name
        
        self.setText(f"📤 {name}")
        self.setToolTip(f"发送到 {name} ({ip})")
        self.setStyleSheet("""
            QPushButton {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                color: #e65100;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #ff9800;
                color: white;
            }
            QPushButton:pressed {
                background-color: #f57c00;
            }
        """)
        
        self.clicked.connect(lambda: self.clicked_with_ip.emit(self.ip))


class SendPanel(QWidget):
    """ 悬浮发送面板"""
    
    send_to_device = Signal(str)
    panel_hidden = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = {}
        self._content = ""
        self._content_type = "text"
        self._init_ui()
        self._setup_animation()
    
    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 243, 224, 0.95);
                border-radius: 15px;
                border: 2px solid #ff9800;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(15, 15, 15, 15)
        inner_layout.setSpacing(10)
        title_layout = QHBoxLayout()
        
        title = QLabel("📤 发送到...")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e65100;
            }
        """)
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e65100;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffccbc;
                border-radius: 12px;
            }
        """)
        close_btn.clicked.connect(self.hide_panel)
        title_layout.addWidget(close_btn)
        
        inner_layout.addLayout(title_layout)
        
        self.content_preview = QLabel("准备发送...")
        self.content_preview.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #ffe0b2;
                color: #424242;
            }
        """)
        self.content_preview.setWordWrap(True)
        self.content_preview.setMaximumHeight(60)
        inner_layout.addWidget(self.content_preview)
        
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setContentsMargins(0, 0, 0, 0)
        self.devices_layout.setSpacing(8)
        inner_layout.addWidget(self.devices_container)
        
        self.no_device_label = QLabel("🔍 正在搜索设备...")
        self.no_device_label.setStyleSheet("""
            QLabel {
                color: #9e9e9e;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.no_device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(self.no_device_label)
        
        self.setFixedWidth(280)
    
    def _setup_animation(self):
        self._opacity = 1.0
    
    def set_content(self, content: str, content_type: str = "text"):
        self._content = content
        self._content_type = content_type
        if content_type == "text":
            preview = content[:50] + "..." if len(content) > 50 else content
            self.content_preview.setText(f"📝 {preview}")
        else:
            self.content_preview.setText(f"📁 文件: {content}")
    
    def add_device(self, ip: str, name: str):
        if ip not in self.devices:
            self.devices[ip] = name
            self._refresh_device_buttons()
    
    def remove_device(self, ip: str):
        if ip in self.devices:
            del self.devices[ip]
            self._refresh_device_buttons()
    
    def update_devices(self, devices: dict):
        self.devices = devices.copy()
        self._refresh_device_buttons()
    
    def _refresh_device_buttons(self):
        while self.devices_layout.count():
            item = self.devices_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        if self.devices:
            self.no_device_label.hide()
            for ip, name in self.devices.items():
                btn = DeviceButton(name, ip)
                btn.clicked_with_ip.connect(self._on_device_selected)
                self.devices_layout.addWidget(btn)
        else:
            self.no_device_label.show()
        self.adjustSize()
    
    def _on_device_selected(self, ip: str):
        self.send_to_device.emit(ip)
        self.hide_panel()
    
    def show_panel(self, content: Optional[str] = None, content_type: str = "text"):
        if content:
            self.set_content(content, content_type)
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()
    
    def hide_panel(self):
        self.hide()
        self.panel_hidden.emit()
    
    def get_content(self) -> tuple:
        return self._content, self._content_type
