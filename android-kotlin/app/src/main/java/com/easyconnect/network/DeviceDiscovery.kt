package com.easyconnect.network

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log
import com.easyconnect.Config
import com.easyconnect.model.Device

/**
 * 使用 Android NSD (Network Service Discovery) 实现 mDNS 设备发现
 * 与桌面版的 zeroconf 协议兼容
 */
class DeviceDiscovery(private val context: Context) {
    
    companion object {
        private const val TAG = "DeviceDiscovery"
    }
    
    private var nsdManager: NsdManager? = null
    private var discoveryListener: NsdManager.DiscoveryListener? = null
    private var registrationListener: NsdManager.RegistrationListener? = null
    private var registeredServiceName: String? = null
    
    private val devices = mutableMapOf<String, Device>()
    private val localIp = Config.getLocalIp()
    
    // 回调
    var onDeviceFound: ((Device) -> Unit)? = null
    var onDeviceLost: ((String) -> Unit)? = null
    
    private var isDiscovering = false
    private var isRegistered = false
    
    /**
     * 启动设备发现服务
     */
    fun start() {
        if (nsdManager == null) {
            nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
        }
        
        registerService()
        startDiscovery()
    }
    
    /**
     * 注册本机服务，让其他设备能发现
     */
    private fun registerService() {
        if (isRegistered) return
        
        val serviceInfo = NsdServiceInfo().apply {
            serviceName = "${Config.getDeviceName()}"
            serviceType = Config.SERVICE_TYPE
            port = Config.TRANSFER_PORT
        }
        
        registrationListener = object : NsdManager.RegistrationListener {
            override fun onServiceRegistered(info: NsdServiceInfo) {
                registeredServiceName = info.serviceName
                isRegistered = true
                Log.i(TAG, "服务已注册: ${info.serviceName}")
            }
            
            override fun onRegistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "服务注册失败: $errorCode")
            }
            
            override fun onServiceUnregistered(info: NsdServiceInfo) {
                isRegistered = false
                Log.i(TAG, "服务已注销: ${info.serviceName}")
            }
            
            override fun onUnregistrationFailed(info: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "服务注销失败: $errorCode")
            }
        }
        
        try {
            nsdManager?.registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, registrationListener)
        } catch (e: Exception) {
            Log.e(TAG, "注册服务异常: ${e.message}")
        }
    }
    
    /**
     * 开始发现其他设备
     */
    private fun startDiscovery() {
        if (isDiscovering) return
        
        discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(serviceType: String) {
                isDiscovering = true
                Log.i(TAG, "开始发现服务: $serviceType")
            }
            
            override fun onServiceFound(serviceInfo: NsdServiceInfo) {
                Log.d(TAG, "发现服务: ${serviceInfo.serviceName}")
                
                // 排除自己
                if (serviceInfo.serviceName == registeredServiceName) {
                    return
                }
                
                // 解析服务详情
                resolveService(serviceInfo)
            }
            
            override fun onServiceLost(serviceInfo: NsdServiceInfo) {
                Log.d(TAG, "服务丢失: ${serviceInfo.serviceName}")
                
                // 查找并移除设备
                val deviceToRemove = devices.entries.find { 
                    it.value.name == serviceInfo.serviceName 
                }
                deviceToRemove?.let {
                    devices.remove(it.key)
                    onDeviceLost?.invoke(it.key)
                }
            }
            
            override fun onDiscoveryStopped(serviceType: String) {
                isDiscovering = false
                Log.i(TAG, "停止发现服务")
            }
            
            override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "启动发现失败: $errorCode")
                isDiscovering = false
            }
            
            override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "停止发现失败: $errorCode")
            }
        }
        
        try {
            nsdManager?.discoverServices(Config.SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        } catch (e: Exception) {
            Log.e(TAG, "启动发现异常: ${e.message}")
        }
    }
    
    /**
     * 解析服务详情获取 IP 地址
     */
    private fun resolveService(serviceInfo: NsdServiceInfo) {
        nsdManager?.resolveService(serviceInfo, object : NsdManager.ResolveListener {
            override fun onResolveFailed(info: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "解析服务失败: ${info.serviceName}, errorCode: $errorCode")
            }
            
            override fun onServiceResolved(info: NsdServiceInfo) {
                val ip = info.host?.hostAddress ?: return
                
                // 排除自己
                if (ip == localIp) return
                
                val device = Device(
                    name = info.serviceName,
                    ip = ip,
                    port = info.port
                )
                
                if (!devices.containsKey(ip)) {
                    devices[ip] = device
                    Log.i(TAG, "设备已添加: $device")
                    onDeviceFound?.invoke(device)
                }
            }
        })
    }
    
    /**
     * 停止设备发现服务
     */
    fun stop() {
        // 停止发现
        if (isDiscovering && discoveryListener != null) {
            try {
                nsdManager?.stopServiceDiscovery(discoveryListener)
            } catch (e: Exception) {
                Log.e(TAG, "停止发现异常: ${e.message}")
            }
        }
        
        // 注销服务
        if (isRegistered && registrationListener != null) {
            try {
                nsdManager?.unregisterService(registrationListener)
            } catch (e: Exception) {
                Log.e(TAG, "注销服务异常: ${e.message}")
            }
        }
        
        devices.clear()
        isDiscovering = false
        isRegistered = false
    }
    
    /**
     * 获取所有已发现的设备
     */
    fun getDevices(): List<Device> = devices.values.toList()
    
    /**
     * 根据 IP 获取设备
     */
    fun getDeviceByIp(ip: String): Device? = devices[ip]
}
