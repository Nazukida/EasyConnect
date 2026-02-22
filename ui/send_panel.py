"""
发送面板模块 - 屏幕右侧的悬浮发送区域
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QCursor


class DeviceButton(QPushButton):
    """设备按钮"""
    
    clicked_with_ip = Signal(str)  # 点击时发送IP
    
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
    """
    发送面板 - 可以作为悬浮窗口显示在屏幕右侧
    当有内容需要发送时，显示设备列表供用户选择
    """
    
    # 信号
    send_to_device = Signal(str)  # 发送到指定设备IP
    panel_hidden = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = {}  # ip -> name
        self._content = ""  # 要发送的内容
        self._content_type = "text"  # text 或 file
        
        self._init_ui()
        self._setup_animation()
    
    def _init_ui(self):
        """初始化界面"""
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主容器
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
        
        # 容器内部布局
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(15, 15, 15, 15)
        inner_layout.setSpacing(10)
        
        # 标题栏
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
        
        # 内容预览
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
        
        # 设备列表容器
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setContentsMargins(0, 0, 0, 0)
        self.devices_layout.setSpacing(8)
        inner_layout.addWidget(self.devices_container)
        
        # 无设备提示
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
        """设置动画"""
        self._opacity = 1.0
    
    def set_content(self, content: str, content_type: str = "text"):
        """设置要发送的内容"""
        self._content = content
        self._content_type = content_type
        
        # 更新预览
        if content_type == "text":
            preview = content[:50] + "..." if len(content) > 50 else content
            self.content_preview.setText(f"📝 {preview}")
        else:
            self.content_preview.setText(f"📁 文件: {content}")
    
    def add_device(self, ip: str, name: str):
        """添加设备"""
        if ip not in self.devices:
            self.devices[ip] = name
            self._refresh_device_buttons()
    
    def remove_device(self, ip: str):
        """移除设备"""
        if ip in self.devices:
            del self.devices[ip]
            self._refresh_device_buttons()
    
    def update_devices(self, devices: dict):
        """更新设备列表"""
        self.devices = devices.copy()
        self._refresh_device_buttons()
    
    def _refresh_device_buttons(self):
        """刷新设备按钮"""
        # 清除现有按钮
        while self.devices_layout.count():
            item = self.devices_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 添加新按钮
        if self.devices:
            self.no_device_label.hide()
            for ip, name in self.devices.items():
                btn = DeviceButton(name, ip)
                btn.clicked_with_ip.connect(self._on_device_selected)
                self.devices_layout.addWidget(btn)
        else:
            self.no_device_label.show()
        
        # 调整大小
        self.adjustSize()
    
    def _on_device_selected(self, ip: str):
        """设备被选中"""
        self.send_to_device.emit(ip)
        self.hide_panel()
    
    def show_panel(self, content: Optional[str] = None, content_type: str = "text"):
        """显示面板"""
        if content:
            self.set_content(content, content_type)
        
        # 定位到屏幕右侧
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.show()
        self.raise_()
    
    def hide_panel(self):
        """隐藏面板"""
        self.hide()
        self.panel_hidden.emit()
    
    def get_content(self) -> tuple:
        """获取当前内容"""
        return self._content, self._content_type
