"""接收气泡模块 - 屏幕左侧通知气泡"""
import os
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QApplication, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, 
    QEasingCurve, QPoint, QSequentialAnimationGroup
)
from PySide6.QtGui import QCursor

import sys
sys.path.append('..')
from config import RECEIVE_DIR


class ReceiveBubble(QWidget):
    """接收通知气泡"""
    clicked = Signal()
    closed = Signal()
    copy_requested = Signal(str)
    open_file_requested = Signal(str)
    
    def __init__(self, sender_name: str, content: str, content_type: str = "text", 
                 file_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        
        self.sender_name = sender_name
        self.content = content
        self.content_type = content_type
        self.file_path = file_path
        self._auto_close_timer: Optional[QTimer] = None
        
        self._init_ui()
        self._setup_animation()
    
    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(232, 245, 233, 0.98);
                border-radius: 12px;
                border: 2px solid #4caf50;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(8)
        title_layout = QHBoxLayout()
        
        icon = "📁" if self.content_type == "file" else "📝"
        title = QLabel(f"{icon} 收到{'文件' if self.content_type == 'file' else '文字'}")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #2e7d32;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
                border-radius: 10px;
            }
        """)
        close_btn.clicked.connect(self.close_bubble)
        title_layout.addWidget(close_btn)
        
        inner_layout.addLayout(title_layout)
        
        sender_label = QLabel(f"来自: {self.sender_name}")
        sender_label.setStyleSheet("""
            QLabel {
                color: #558b2f;
                font-size: 12px;
            }
        """)
        inner_layout.addWidget(sender_label)
        
        if self.content_type == "text":
            preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        else:
            preview = self.content
            
        content_label = QLabel(preview)
        content_label.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #c8e6c9;
                color: #424242;
            }
        """)
        content_label.setWordWrap(True)
        content_label.setMaximumWidth(250)
        inner_layout.addWidget(content_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        if self.content_type == "text":
            copy_btn = QPushButton("📋 复制")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #43a047;
                }
            """)
            copy_btn.clicked.connect(self._copy_text)
            btn_layout.addWidget(copy_btn)
        else:
            open_btn = QPushButton("📂 打开")
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #43a047;
                }
            """)
            open_btn.clicked.connect(self._open_file)
            btn_layout.addWidget(open_btn)
            
            folder_btn = QPushButton("📁 文件夹")
            folder_btn.setStyleSheet("""
                QPushButton {
                    background-color: #66bb6a;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #57a05a;
                }
            """)
            folder_btn.clicked.connect(self._open_folder)
            btn_layout.addWidget(folder_btn)
        
        btn_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        
        self.setFixedWidth(280)
        self.adjustSize()
    
    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
    
    def _copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content)
        self.copy_requested.emit(self.content)
        self.close_bubble()
    
    def _open_file(self):
        if self.file_path and os.path.exists(self.file_path):
            if os.name == 'nt':
                os.startfile(self.file_path)
            else:
                os.system(f'open "{self.file_path}"')
            self.open_file_requested.emit(self.file_path)
        self.close_bubble()
    
    def _open_folder(self):
        if self.file_path:
            folder = os.path.dirname(self.file_path)
            if os.path.exists(folder):
                if os.name == 'nt':
                    os.startfile(folder)
                else:
                    os.system(f'open "{folder}"')
        self.close_bubble()
    
    def show_bubble(self, duration: int = 8000):
        """duration: 自动关闭时间(ms)，0表示不自动关闭"""
        self.show()
        self.raise_()
        
        # 设置自动关闭
        if duration > 0:
            self._auto_close_timer = QTimer(self)
            self._auto_close_timer.setSingleShot(True)
            self._auto_close_timer.timeout.connect(self._fade_out)
            self._auto_close_timer.start(duration)
    
    def _fade_out(self):
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.fade_animation.finished.connect(self.close_bubble)
        self.fade_animation.start()
    
    def close_bubble(self):
        if self._auto_close_timer:
            self._auto_close_timer.stop()
        self.closed.emit()
        self.close()
    
    def enterEvent(self, event):
        if self._auto_close_timer:
            self._auto_close_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if self._auto_close_timer:
            self._auto_close_timer.start(3000)
        super().leaveEvent(event)


class BubbleManager:
    """气泡位置管理器"""
    
    def __init__(self):
        self.bubbles: list[ReceiveBubble] = []
        self._base_y = 100  # 起始Y位置
        self._spacing = 10  # 气泡间距
        self._margin = 20
    
    def show_text_bubble(self, sender: str, text: str) -> ReceiveBubble:
        bubble = ReceiveBubble(sender, text, "text")
        return self._show_bubble(bubble)
    
    def show_file_bubble(self, sender: str, filename: str, 
                         file_path: str) -> ReceiveBubble:
        bubble = ReceiveBubble(sender, filename, "file", file_path)
        return self._show_bubble(bubble)
    
    def _show_bubble(self, bubble: ReceiveBubble) -> ReceiveBubble:
        bubble.closed.connect(lambda: self._remove_bubble(bubble))
        screen = QApplication.primaryScreen().geometry()
        x = self._margin
        y = self._calculate_y_position()
        bubble.move(x, y)
        bubble.show_bubble()
        self.bubbles.append(bubble)
        return bubble
    
    def _calculate_y_position(self) -> int:
        if not self.bubbles:
            return self._base_y
        last_bubble = self.bubbles[-1]
        return last_bubble.y() + last_bubble.height() + self._spacing
    
    def _remove_bubble(self, bubble: ReceiveBubble):
        if bubble in self.bubbles:
            self.bubbles.remove(bubble)
            self._rearrange_bubbles()
    
    def _rearrange_bubbles(self):
        y = self._base_y
        for bubble in self.bubbles:
            if bubble.isVisible():
                animation = QPropertyAnimation(bubble, b"pos")
                animation.setDuration(200)
                animation.setStartValue(bubble.pos())
                animation.setEndValue(QPoint(bubble.x(), y))
                animation.setEasingCurve(QEasingCurve.Type.OutQuad)
                animation.start()
                y += bubble.height() + self._spacing
    
    def clear_all(self):
        """清除所有气泡"""
        for bubble in self.bubbles[:]:
            bubble.close_bubble()
        self.bubbles.clear()
