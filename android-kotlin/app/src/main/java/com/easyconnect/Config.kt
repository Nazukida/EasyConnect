package com.easyconnect

import android.os.Build
import java.net.InetAddress
import java.net.NetworkInterface
import java.net.Socket

/**
 * 应用配置
 */
object Config {
    const val APP_NAME = "EasyConnect"
    const val APP_VERSION = "1.0.0"
    
    // 网络配置
    const val SERVICE_TYPE = "_easyconnect._tcp."  // NSD 服务类型
    const val SERVICE_NAME = "EasyConnect"
    const val TRANSFER_PORT = 52525
    const val BUFFER_SIZE = 8192
    
    /**
     * 获取设备名称
     */
    fun getDeviceName(): String {
        val manufacturer = Build.MANUFACTURER
        val model = Build.MODEL
        return if (model.startsWith(manufacturer, ignoreCase = true)) {
            model.replaceFirstChar { it.uppercase() }
        } else {
            "$manufacturer $model"
        }
    }
    
    /**
     * 获取本地 IP 地址
     */
    fun getLocalIp(): String {
        try {
            // 方法1：通过连接获取
            Socket().use { socket ->
                socket.connect(java.net.InetSocketAddress("8.8.8.8", 80), 1000)
                return socket.localAddress.hostAddress ?: "127.0.0.1"
            }
        } catch (e: Exception) {
            // 方法2：遍历网络接口
            try {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    if (networkInterface.isLoopback || !networkInterface.isUp) continue
                    
                    val addresses = networkInterface.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        if (address is java.net.Inet4Address && !address.isLoopbackAddress) {
                            return address.hostAddress ?: continue
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        return "127.0.0.1"
    }
}
