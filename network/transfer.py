"""
数据传输模块 - 实现文件和文字的发送与接收
"""
import os
import json
import socket
import threading
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum

import sys
sys.path.append('..')
from config import TRANSFER_PORT, BUFFER_SIZE, RECEIVE_DIR, MessageType, get_device_name


@dataclass
class TransferData:
    """传输数据结构"""
    type: str  # TEXT 或 FILE
    sender: str  # 发送者设备名
    content: str  # 文字内容或文件名
    file_size: int = 0  # 文件大小（仅文件传输时使用）
    file_data: bytes = b''  # 文件数据（仅文件传输时使用）


class FileTransfer:
    """文件/文字发送器"""
    
    def __init__(self):
        self.device_name = get_device_name()
    
    def send_text(self, target_ip: str, target_port: int, text: str, 
                  on_success: Optional[Callable] = None, on_error: Optional[Callable] = None):
        """发送文字到目标设备"""
        def _send():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(10)
                    s.connect((target_ip, target_port))
                    
                    # 构造消息
                    message = {
                        'type': MessageType.TEXT,
                        'sender': self.device_name,
                        'content': text
                    }
                    
                    # 发送 JSON 消息
                    data = json.dumps(message, ensure_ascii=False).encode('utf-8')
                    # 先发送长度（4字节）
                    s.sendall(len(data).to_bytes(4, 'big'))
                    # 再发送数据
                    s.sendall(data)
                    
                    # 等待确认
                    ack = s.recv(3)
                    if ack == b'ACK':
                        print(f"[Transfer] 文字发送成功到 {target_ip}")
                        if on_success:
                            on_success()
                    else:
                        raise Exception("未收到确认")
                        
            except Exception as e:
                print(f"[Transfer] 发送文字失败: {e}")
                if on_error:
                    on_error(str(e))
        
        # 在新线程中发送
        threading.Thread(target=_send, daemon=True).start()
    
    def send_file(self, target_ip: str, target_port: int, file_path: str,
                  on_progress: Optional[Callable] = None, on_success: Optional[Callable] = None, 
                  on_error: Optional[Callable] = None):
        """发送文件到目标设备"""
        def _send():
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(60)  # 文件传输给更多时间
                    s.connect((target_ip, target_port))
                    
                    # 先发送文件信息
                    file_info = {
                        'type': MessageType.FILE,
                        'sender': self.device_name,
                        'content': file_name,
                        'file_size': file_size
                    }
                    
                    info_data = json.dumps(file_info, ensure_ascii=False).encode('utf-8')
                    s.sendall(len(info_data).to_bytes(4, 'big'))
                    s.sendall(info_data)
                    
                    # 等待接收方准备好
                    ready = s.recv(5)
                    if ready != b'READY':
                        raise Exception("接收方未准备好")
                    
                    # 发送文件数据
                    sent = 0
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            s.sendall(chunk)
                            sent += len(chunk)
                            if on_progress:
                                on_progress(sent, file_size)
                    
                    # 等待确认
                    ack = s.recv(3)
                    if ack == b'ACK':
                        print(f"[Transfer] 文件发送成功: {file_name}")
                        if on_success:
                            on_success()
                    else:
                        raise Exception("未收到确认")
                        
            except Exception as e:
                print(f"[Transfer] 发送文件失败: {e}")
                if on_error:
                    on_error(str(e))
        
        threading.Thread(target=_send, daemon=True).start()


class TransferServer:
    """传输接收服务器"""
    
    def __init__(self, port: int = TRANSFER_PORT):
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # 新增：记录所有活跃的客户端连接
        self._active_connections: set = set()
        self._lock = threading.Lock()
        
        # 回调函数
        self._on_text_received = None
        self._on_file_received = None
        self._on_progress = None
    
    def set_callbacks(self, 
                      on_text: Callable[[str, str], None],  # (sender, text)
                      on_file: Callable[[str, str, str], None],  # (sender, filename, filepath)
                      on_progress: Optional[Callable[[str, int, int], None]] = None):  # (filename, received, total)
        """设置接收回调"""
        self._on_text_received = on_text
        self._on_file_received = on_file
        self._on_progress = on_progress
    
    def start(self):
        """启动接收服务器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        print(f"[Server] 传输服务器已启动，端口: {self.port}")
    
    def _run_server(self):
        """运行服务器主循环"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1)  # 设置超时以便能够优雅退出
        
        while self._running:
            try:
                conn, addr = self.server_socket.accept()
                # 记录连接
                with self._lock:
                    self._active_connections.add(conn)
                # 为每个连接创建新线程处理
                threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[Server] 接受连接错误: {e}")
    
    def _handle_client(self, conn: socket.socket, addr: tuple):
        """处理客户端连接"""
        try:
            conn.settimeout(60)
            
            # 读取消息长度
            length_data = conn.recv(4)
            if not length_data:
                return
            
            msg_length = int.from_bytes(length_data, 'big')
            
            # 读取消息内容
            msg_data = b''
            while len(msg_data) < msg_length:
                chunk = conn.recv(min(BUFFER_SIZE, msg_length - len(msg_data)))
                if not chunk:
                    break
                msg_data += chunk
            
            # 解析 JSON
            message = json.loads(msg_data.decode('utf-8'))
            msg_type = message.get('type')
            sender = message.get('sender', 'Unknown')
            content = message.get('content', '')
            
            if msg_type == MessageType.TEXT:
                # 处理文字消息
                print(f"[Server] 收到文字来自 {sender}: {content[:50]}...")
                conn.sendall(b'ACK')
                if self._on_text_received:
                    self._on_text_received(sender, content)
                    
            elif msg_type == MessageType.FILE:
                # 处理文件传输
                file_size = message.get('file_size', 0)
                file_name = content
                
                # 告诉发送方准备好了
                conn.sendall(b'READY')
                
                # 接收文件数据
                file_path = os.path.join(RECEIVE_DIR, file_name)
                # 如果文件已存在，添加数字后缀
                base, ext = os.path.splitext(file_path)
                counter = 1
                while os.path.exists(file_path):
                    file_path = f"{base}_{counter}{ext}"
                    counter += 1
                
                received = 0
                with open(file_path, 'wb') as f:
                    while received < file_size:
                        chunk = conn.recv(min(BUFFER_SIZE, file_size - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                        if self._on_progress:
                            self._on_progress(file_name, received, file_size)
                
                conn.sendall(b'ACK')
                print(f"[Server] 文件接收完成: {file_path}")
                
                if self._on_file_received:
                    self._on_file_received(sender, file_name, file_path)
                    
        except Exception as e:
            print(f"[Server] 处理客户端错误: {e}")
        finally:
            # 连接结束时移除
            with self._lock:
                if conn in self._active_connections:
                    self._active_connections.discard(conn)
            try:
                conn.close()
            except:
                pass
    
    def stop(self):
        """停止服务器并强制关闭所有连接"""
        print("[Server] 正在停止服务器并清理连接...")
        self._running = False
        
        # 1. 强制关闭所有正在进行的客户端连接
        with self._lock:
            for conn in self._active_connections:
                try:
                    conn.shutdown(socket.SHUT_RDWR)  # 停止收发
                except:
                    pass
                try:
                    conn.close()
                except:
                    pass
            self._active_connections.clear()
        
        # 2. 关闭主监听 socket
        if self.server_socket:
            try:
                # 在 Windows 上有时仅仅 close 不够，需要 shutdown
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"[Server] 关闭 socket 出错: {e}")
            self.server_socket = None
        
        # 3. 等待线程结束（带超时）
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                print("[Server] 警告: 服务器线程未能及时停止")
        self._thread = None
        
        print("[Server] 传输服务器已停止")
