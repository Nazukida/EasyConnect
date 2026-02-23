"""EasyConnect 配置文件"""
import os
import socket
import platform

# 应用信息
APP_NAME = "EasyConnect"
APP_VERSION = "1.0.0"

# 网络配置
SERVICE_TYPE = "_easyconnect._tcp.local."  # mDNS 服务类型
TRANSFER_PORT = 52525
DISCOVERY_PORT = 52526
BUFFER_SIZE = 8192

def get_device_name():
    hostname = socket.gethostname()
    system = platform.system()
    return f"{hostname} ({system})"

def get_local_ip():
    """TCP 连接获取本地 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# 文件接收目录
RECEIVE_DIR = os.path.join(os.path.expanduser("~"), "EasyConnect_Received")
if not os.path.exists(RECEIVE_DIR):
    os.makedirs(RECEIVE_DIR)

# UI配置
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
PANEL_WIDTH = 300

# 消息类型
class MessageType:
    TEXT = "TEXT"
    FILE = "FILE"
    FILE_INFO = "FILE_INFO"
    ACK = "ACK"
