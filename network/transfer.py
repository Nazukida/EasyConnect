"""数据传输模块 - 文件和文字的发送与接收"""
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
    type: str
    sender: str
    content: str
    file_size: int = 0
    file_data: bytes = b''


class FileTransfer:
    """TCP 发送器"""
    
    def __init__(self):
        self.device_name = get_device_name()
    
    def send_text(self, target_ip: str, target_port: int, text: str, 
                  on_success: Optional[Callable] = None, on_error: Optional[Callable] = None):
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
                    
                    # 消息协议: 4字节长度头 + JSON
                    data = json.dumps(message, ensure_ascii=False).encode('utf-8')
                    s.sendall(len(data).to_bytes(4, 'big'))
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
        
        # 异步发送
        threading.Thread(target=_send, daemon=True).start()
    
    def send_file(self, target_ip: str, target_port: int, file_path: str,
                  on_progress: Optional[Callable] = None, on_success: Optional[Callable] = None, 
                  on_error: Optional[Callable] = None):
        def _send():
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(60)  # 文件传输给更多时间
                    s.connect((target_ip, target_port))
                    
                    file_info = {
                        'type': MessageType.FILE,
                        'sender': self.device_name,
                        'content': file_name,
                        'file_size': file_size
                    }
                    
                    info_data = json.dumps(file_info, ensure_ascii=False).encode('utf-8')
                    s.sendall(len(info_data).to_bytes(4, 'big'))
                    s.sendall(info_data)
                    
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
    """TCP 接收服务器"""
    
    def __init__(self, port: int = TRANSFER_PORT):
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # 新增：记录所有活跃的客户端连接
        self._active_connections: set = set()
        self._lock = threading.Lock()
        self._on_text_received = None
        self._on_file_received = None
        self._on_progress = None
    
    def set_callbacks(self, 
                      on_text: Callable[[str, str], None],  # (sender, text)
                      on_file: Callable[[str, str, str], None],  # (sender, filename, filepath)
                      on_progress: Optional[Callable[[str, int, int], None]] = None):
        self._on_text_received = on_text
        self._on_file_received = on_file
        self._on_progress = on_progress
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        print(f"[Server] 传输服务器已启动，端口: {self.port}")
    
    def _run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1)  # 超时便于优雅退出
        
        while self._running:
            try:
                conn, addr = self.server_socket.accept()
                with self._lock:
                    self._active_connections.add(conn)
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
        try:
            conn.settimeout(60)
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
            msg_type = message.get('type')
            sender = message.get('sender', 'Unknown')
            content = message.get('content', '')
            
            if msg_type == MessageType.TEXT:
                print(f"[Server] 收到文字来自 {sender}: {content[:50]}...")
                conn.sendall(b'ACK')
                if self._on_text_received:
                    self._on_text_received(sender, content)
                    
            elif msg_type == MessageType.FILE:
                file_size = message.get('file_size', 0)
                file_name = content
                conn.sendall(b'READY')
                
                # 生成唯一文件名
                file_path = os.path.join(RECEIVE_DIR, file_name)
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
            with self._lock:
                if conn in self._active_connections:
                    self._active_connections.discard(conn)
            try:
                conn.close()
            except:
                pass
    
    def stop(self):
        """ 停止服务器"""
        print("[Server] 正在停止服务器并清理连接...")
        self._running = False
        
        # 关闭所有客户端连接
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
        
        # 关闭主监听 socket
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
