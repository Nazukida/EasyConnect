package com.easyconnect.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.easyconnect.Config
import com.easyconnect.MainActivity
import com.easyconnect.network.DeviceDiscovery
import com.easyconnect.network.TransferServer

/** 前台服务，用于后台保持设备发现和文件接收 */
class TransferService : Service() {
    companion object {
        private const val CHANNEL_ID = "easyconnect_service"
        private const val NOTIFICATION_ID = 100
    }
    
    private var deviceDiscovery: DeviceDiscovery? = null
    private var transferServer: TransferServer? = null
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, createNotification())
        
        // 启动服务组件
        startServices()
        
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun startServices() {
        // 设备发现
        deviceDiscovery = DeviceDiscovery(this).apply {
            start()
        }
        
        // 传输服务器
        transferServer = TransferServer().apply {
            onTextReceived = { sender, text ->
                // 发送广播到 MainActivity
                sendBroadcast(Intent("com.easyconnect.TEXT_RECEIVED").apply {
                    putExtra("sender", sender)
                    putExtra("text", text)
                })
            }
            onFileReceived = { sender, fileName, filePath ->
                sendBroadcast(Intent("com.easyconnect.FILE_RECEIVED").apply {
                    putExtra("sender", sender)
                    putExtra("fileName", fileName)
                    putExtra("filePath", filePath)
                })
            }
            start()
        }
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "EasyConnect 后台服务",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "保持设备发现和文件接收"
                setShowBadge(false)
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("EasyConnect 运行中")
            .setContentText("设备: ${Config.getDeviceName()}")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        deviceDiscovery?.stop()
        transferServer?.stop()
    }
}
