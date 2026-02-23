"""设备发现模块 - mDNS (zeroconf) 实现"""
import socket
import threading
from typing import Dict, Callable, Optional
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

import sys
sys.path.append('..')
from config import SERVICE_TYPE, TRANSFER_PORT, get_device_name, get_local_ip


class Device:
    """发现的设备"""
    def __init__(self, name: str, ip: str, port: int):
        self.name = name
        self.ip = ip
        self.port = port
    
    def __repr__(self):
        return f"Device({self.name}, {self.ip}:{self.port})"
    
    def __eq__(self, other):
        if isinstance(other, Device):
            return self.ip == other.ip and self.port == other.port
        return False
    
    def __hash__(self):
        return hash((self.ip, self.port))


class DeviceListener(ServiceListener):
    """mDNS 服务监听器"""
    
    def __init__(self, on_add: Callable, on_remove: Callable, local_ip: str):
        self.on_add = on_add
        self.on_remove = on_remove
        self.local_ip = local_ip
    
    def add_service(self, zc: Zeroconf, type_: str, name: str):
        info = zc.get_service_info(type_, name)
        if info:
            addresses = info.parsed_addresses()
            if addresses:
                ip = addresses[0]
                if ip != self.local_ip:
                    device = Device(
                        name=info.server.rstrip('.') if info.server else name,
                        ip=ip,
                        port=info.port or 52525
                    )
                    self.on_add(device)
    
    def remove_service(self, zc: Zeroconf, type_: str, name: str):
        self.on_remove(name)
    
    def update_service(self, zc: Zeroconf, type_: str, name: str):
        self.add_service(zc, type_, name)


class DeviceDiscovery:
    """设备发现管理器"""
    
    def __init__(self):
        self.zeroconf: Optional[Zeroconf] = None
        self.browser: Optional[ServiceBrowser] = None
        self.service_info: Optional[ServiceInfo] = None
        self.devices: Dict[str, Device] = {}  # ip -> Device
        self.local_ip = get_local_ip()
        self.device_name = get_device_name()
        
        # 回调函数
        self._on_device_found = None
        self._on_device_lost = None
        
        self._running = False
    
    def set_callbacks(self, on_found: Callable[[Device], None], 
                      on_lost: Callable[[str], None]):
        self._on_device_found = on_found
        self._on_device_lost = on_lost
    
    def _on_device_add(self, device: Device):
        if device.ip not in self.devices:
            self.devices[device.ip] = device
            print(f"[Discovery] 发现设备: {device}")
            if self._on_device_found:
                self._on_device_found(device)
    
    def _on_device_remove(self, name: str):
        """ 移除设备"""
        to_remove = None
        for ip, device in self.devices.items():
            if device.name in name or name in device.name:
                to_remove = ip
                break
        
        if to_remove:
            removed_device = self.devices.pop(to_remove)
            print(f"[Discovery] 设备离线: {removed_device}")
            if self._on_device_lost:
                self._on_device_lost(to_remove)
    
    def start(self):
        """启动设备发现服务"""
        if self._running:
            return
        self._running = True
        self.zeroconf = Zeroconf(interfaces=['0.0.0.0'])
        self._register_service()
        
        # 开始浏览其他设备
        listener = DeviceListener(
            on_add=self._on_device_add,
            on_remove=self._on_device_remove,
            local_ip=self.local_ip
        )
        self.browser = ServiceBrowser(self.zeroconf, SERVICE_TYPE, listener)
        
        print(f"[Discovery] 服务已启动 - {self.device_name} ({self.local_ip})")
    
    def _register_service(self):
        """mDNS 注册本机服务"""
        self.service_info = ServiceInfo(
            SERVICE_TYPE,
            f"{self.device_name}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(self.local_ip)],
            port=TRANSFER_PORT,
            properties={
                'version': '1.0',
                'device': self.device_name
            },
            server=f"{self.device_name.replace(' ', '_')}.local."
        )
        self.zeroconf.register_service(self.service_info)
        print(f"[Discovery] 已注册服务: {self.device_name}")
    
    def stop(self):
        """停止设备发现服务"""
        if not self._running:
            return
        
        self._running = False
        
        try:
            # 先取消浏览器
            if self.browser:
                self.browser.cancel()
                self.browser = None
        except Exception as e:
            print(f"[Discovery] 停止浏览器出错: {e}")
        
        try:
            # 注销服务
            if self.service_info and self.zeroconf:
                self.zeroconf.unregister_service(self.service_info)
                self.service_info = None
        except Exception as e:
            print(f"[Discovery] 注销服务出错: {e}")
        
        try:
            # 关闭 zeroconf
            if self.zeroconf:
                self.zeroconf.close()
                self.zeroconf = None
        except Exception as e:
            print(f"[Discovery] 关闭 zeroconf 出错: {e}")
        
        self.devices.clear()
        print("[Discovery] 服务已停止")
    
    def get_devices(self) -> list:
        """获取当前发现的所有设备列表"""
        return list(self.devices.values())
    
    def get_device_by_ip(self, ip: str) -> Optional[Device]:
        """根据IP获取设备"""
        return self.devices.get(ip)
