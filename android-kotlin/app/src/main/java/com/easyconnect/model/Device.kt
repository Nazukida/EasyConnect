package com.easyconnect.model

/**
 * 发现的设备
 */
data class Device(
    val name: String,
    val ip: String,
    val port: Int = 52525
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is Device) return false
        return ip == other.ip && port == other.port
    }
    
    override fun hashCode(): Int {
        return ip.hashCode() * 31 + port
    }
}
