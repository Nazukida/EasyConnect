"""
UI 模块初始化
"""
from .main_window import MainWindow
from .send_panel import SendPanel
from .receive_bubble import ReceiveBubble, BubbleManager

__all__ = ['MainWindow', 'SendPanel', 'ReceiveBubble', 'BubbleManager']
