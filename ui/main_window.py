"""
主窗口模块
"""
import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QFileDialog, QProgressBar, QSplitter,
    QFrame, QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction

import sys
sys.path.append('..')
from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, RECEIVE_DIR, get_local_ip, get_device_name


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号
    send_text_requested = Signal(str, str)  # (target_ip, text)
    send_file_requested = Signal(str, str)  # (target_ip, file_path)
    
    def __init__(self):
        super().__init__()
        self.devices = {}  # ip -> device_name
        self._init_ui()
        self._init_tray()
    
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"{APP_NAME} - {get_device_name()}")
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        
        # 主布局 - 水平分割
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧 - 接收区域
        left_panel = self._create_receive_panel()
        
        # 中间 - 设备列表
        center_panel = self._create_device_panel()
        
        # 右侧 - 发送区域
        right_panel = self._create_send_panel()
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([150, 200, 200])
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage(f"本机IP: {get_local_ip()}")
    
    def _create_receive_panel(self) -> QFrame:
        """创建接收面板（左侧）"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border-radius: 8px;
                border: 1px solid #c8e6c9;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # 标题
        title = QLabel("📥 接收区")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e7d32;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 接收历史列表
        self.receive_list = QListWidget()
        self.receive_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 4px;
                border: 1px solid #c8e6c9;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:hover {
                background-color: #f1f8e9;
            }
        """)
        layout.addWidget(self.receive_list)
        
        # 打开接收文件夹按钮
        open_folder_btn = QPushButton("📁 打开接收文件夹")
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
        """)
        open_folder_btn.clicked.connect(self._open_receive_folder)
        layout.addWidget(open_folder_btn)
        
        return frame
    
    def _create_device_panel(self) -> QFrame:
        """创建设备列表面板（中间）"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
                border: 1px solid #bbdefb;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # 标题
        title = QLabel("🖥️ 在线设备")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1565c0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 设备列表
        self.device_list = QListWidget()
        self.device_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border-radius: 4px;
                border: 1px solid #bbdefb;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.device_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新设备")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_devices)
        layout.addWidget(refresh_btn)
        
        return frame
    
    def _create_send_panel(self) -> QFrame:
        """创建发送面板（右侧）"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border-radius: 8px;
                border: 1px solid #ffe0b2;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # 标题
        title = QLabel("📤 发送区")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e65100;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 文字输入区
        text_label = QLabel("发送文字:")
        text_label.setStyleSheet("color: #e65100; font-weight: bold;")
        layout.addWidget(text_label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("输入要发送的文字，或直接复制内容...\n也可以拖拽文件到此处")
        self.text_input.setMaximumHeight(120)
        self.text_input.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border-radius: 4px;
                border: 1px solid #ffe0b2;
                padding: 5px;
                color: #000000;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.text_input)
        
        # 发送文字按钮
        send_text_btn = QPushButton("📝 发送文字")
        send_text_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        send_text_btn.clicked.connect(self._send_text)
        layout.addWidget(send_text_btn)
        
        # 从剪贴板发送
        send_clipboard_btn = QPushButton("📋 发送剪贴板内容")
        send_clipboard_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffb74d;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffa726;
            }
        """)
        send_clipboard_btn.clicked.connect(self._send_clipboard)
        layout.addWidget(send_clipboard_btn)
        
        layout.addSpacing(10)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #ffe0b2;")
        layout.addWidget(line)
        
        layout.addSpacing(10)
        
        # 文件发送区
        file_label = QLabel("发送文件:")
        file_label.setStyleSheet("color: #e65100; font-weight: bold;")
        layout.addWidget(file_label)
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 10px;
                border-radius: 4px;
                border: 1px dashed #ffe0b2;
                color: #757575;
            }
        """)
        self.file_path_label.setWordWrap(True)
        layout.addWidget(self.file_path_label)
        
        # 选择文件按钮
        select_file_btn = QPushButton("📂 选择文件")
        select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        select_file_btn.clicked.connect(self._select_file)
        layout.addWidget(select_file_btn)
        
        # 发送文件按钮
        send_file_btn = QPushButton("📤 发送文件")
        send_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #e65100;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #bf360c;
            }
        """)
        send_file_btn.clicked.connect(self._send_file)
        layout.addWidget(send_file_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ffe0b2;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ff9800;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        return frame
    
    def _init_tray(self):
        """初始化系统托盘"""
        # 检查系统是否支持托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        # 使用默认图标（实际应用中应该使用自定义图标）
        self.tray_icon.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        ))
        self.tray_icon.setToolTip(APP_NAME)
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()
    
    def _tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def closeEvent(self, event):
        """窗口关闭事件 - 真正退出程序"""
        # 隐藏系统托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        # 显式调用 quit 触发 aboutToQuit 信号
        QApplication.quit()
        event.accept()
    
    # 拖放支持
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        mime = event.mimeData()
        
        if mime.hasUrls():
            # 文件拖入
            for url in mime.urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self.selected_file = file_path
                    self.file_path_label.setText(os.path.basename(file_path))
                    self.file_path_label.setStyleSheet("""
                        QLabel {
                            background-color: #fff8e1;
                            padding: 10px;
                            border-radius: 4px;
                            border: 1px solid #ff9800;
                            color: #e65100;
                        }
                    """)
                    break
        elif mime.hasText():
            # 文字拖入
            self.text_input.setText(mime.text())
    
    # 槽函数
    def _open_receive_folder(self):
        """打开接收文件夹"""
        if os.path.exists(RECEIVE_DIR):
            os.startfile(RECEIVE_DIR) if os.name == 'nt' else os.system(f'open "{RECEIVE_DIR}"')
    
    def _refresh_devices(self):
        """刷新设备列表"""
        # 这个方法会被外部调用更新
        pass
    
    def _get_selected_device_ip(self) -> Optional[str]:
        """获取选中的设备IP"""
        item = self.device_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def _send_text(self):
        """发送文字"""
        text = self.text_input.toPlainText().strip()
        if not text:
            self.statusBar().showMessage("请输入要发送的文字", 3000)
            return
        
        target_ip = self._get_selected_device_ip()
        if not target_ip:
            self.statusBar().showMessage("请选择目标设备", 3000)
            return
        
        self.send_text_requested.emit(target_ip, text)
        self.text_input.clear()
    
    def _send_clipboard(self):
        """发送剪贴板内容"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.text_input.setText(text)
            self._send_text()
        else:
            self.statusBar().showMessage("剪贴板为空", 3000)
    
    def _select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.selected_file = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.file_path_label.setStyleSheet("""
                QLabel {
                    background-color: #fff8e1;
                    padding: 10px;
                    border-radius: 4px;
                    border: 1px solid #ff9800;
                    color: #e65100;
                }
            """)
    
    def _send_file(self):
        """发送文件"""
        if not hasattr(self, 'selected_file') or not self.selected_file:
            self.statusBar().showMessage("请先选择文件", 3000)
            return
        
        target_ip = self._get_selected_device_ip()
        if not target_ip:
            self.statusBar().showMessage("请选择目标设备", 3000)
            return
        
        self.send_file_requested.emit(target_ip, self.selected_file)
    
    # 公共方法
    @Slot(str, str)
    def add_device(self, ip: str, name: str):
        """添加设备到列表"""
        if ip not in self.devices:
            self.devices[ip] = name
            item = QListWidgetItem(f"🖥️ {name}\n   {ip}")
            item.setData(Qt.ItemDataRole.UserRole, ip)
            self.device_list.addItem(item)
            self.statusBar().showMessage(f"发现设备: {name}", 3000)
    
    @Slot(str)
    def remove_device(self, ip: str):
        """从列表移除设备"""
        if ip in self.devices:
            del self.devices[ip]
            for i in range(self.device_list.count()):
                item = self.device_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == ip:
                    self.device_list.takeItem(i)
                    break
    
    @Slot(str, str)
    def add_receive_item(self, sender: str, content: str, is_file: bool = False):
        """添加接收记录"""
        icon = "📁" if is_file else "📝"
        item = QListWidgetItem(f"{icon} 来自 {sender}\n   {content[:50]}...")
        self.receive_list.insertItem(0, item)
        
        # 托盘通知
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                f"收到{'文件' if is_file else '文字'}",
                f"来自 {sender}: {content[:30]}...",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    @Slot(int, int)
    def update_progress(self, current: int, total: int):
        """更新进度条"""
        if total > 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            if current >= total:
                self.progress_bar.setVisible(False)
