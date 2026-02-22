package com.easyconnect

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.easyconnect.databinding.ActivityMainBinding
import com.easyconnect.model.Device
import com.easyconnect.network.DeviceDiscovery
import com.easyconnect.network.TransferClient
import com.easyconnect.network.TransferServer
import com.easyconnect.ui.DeviceAdapter
import java.io.File
import java.io.FileOutputStream

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    
    // 网络组件
    private lateinit var deviceDiscovery: DeviceDiscovery
    private lateinit var transferClient: TransferClient
    private lateinit var transferServer: TransferServer
    
    // UI 组件
    private lateinit var deviceAdapter: DeviceAdapter
    private var selectedDevice: Device? = null
    
    // 通知
    private val channelId = "easyconnect_channel"
    private var notificationId = 1
    
    // 文件选择
    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { sendFile(it) }
    }
    
    // 权限请求
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.all { it.value }
        if (allGranted) {
            startServices()
        } else {
            Toast.makeText(this, "需要权限才能正常工作", Toast.LENGTH_LONG).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        createNotificationChannel()
        checkPermissions()
    }
    
    private fun setupUI() {
        // 工具栏
        setSupportActionBar(binding.toolbar)
        
        // 本机信息
        binding.tvDeviceName.text = Config.getDeviceName()
        binding.tvLocalIp.text = "IP: ${Config.getLocalIp()}"
        
        // 设备列表
        deviceAdapter = DeviceAdapter { device ->
            selectedDevice = device
            Toast.makeText(this, "已选择: ${device.name}", Toast.LENGTH_SHORT).show()
        }
        
        binding.rvDevices.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = deviceAdapter
        }
        
        // 刷新按钮
        binding.btnRefresh.setOnClickListener {
            refreshDevices()
        }
        
        // 发送文字按钮
        binding.btnSendText.setOnClickListener {
            sendText()
        }
        
        // 发送文件按钮
        binding.btnSendFile.setOnClickListener {
            if (selectedDevice == null) {
                Toast.makeText(this, "请先选择一个设备", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            filePickerLauncher.launch("*/*")
        }
    }
    
    private fun checkPermissions() {
        val permissions = mutableListOf<String>()
        
        // 网络权限（Android 自动授予）
        
        // 通知权限 (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        
        // 存储权限
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
            }
        }
        
        if (permissions.isNotEmpty()) {
            permissionLauncher.launch(permissions.toTypedArray())
        } else {
            startServices()
        }
    }
    
    private fun startServices() {
        // 初始化网络组件
        deviceDiscovery = DeviceDiscovery(this)
        transferClient = TransferClient()
        transferServer = TransferServer()
        
        // 设置回调
        deviceDiscovery.onDeviceFound = { device ->
            runOnUiThread {
                updateDeviceList()
            }
        }
        
        deviceDiscovery.onDeviceLost = { ip ->
            runOnUiThread {
                if (selectedDevice?.ip == ip) {
                    selectedDevice = null
                    deviceAdapter.clearSelection()
                }
                updateDeviceList()
            }
        }
        
        transferServer.onTextReceived = { sender, text ->
            runOnUiThread {
                showReceivedTextDialog(sender, text)
            }
        }
        
        transferServer.onFileReceived = { sender, fileName, filePath ->
            runOnUiThread {
                showReceivedFileDialog(sender, fileName, filePath)
            }
        }
        
        // 启动服务
        deviceDiscovery.start()
        transferServer.start()
    }
    
    private fun updateDeviceList() {
        val devices = deviceDiscovery.getDevices()
        deviceAdapter.submitList(devices)
        
        binding.tvNoDevices.visibility = if (devices.isEmpty()) View.VISIBLE else View.GONE
        binding.rvDevices.visibility = if (devices.isEmpty()) View.GONE else View.VISIBLE
    }
    
    private fun refreshDevices() {
        Toast.makeText(this, "正在刷新设备列表...", Toast.LENGTH_SHORT).show()
        deviceDiscovery.stop()
        deviceDiscovery.start()
    }
    
    private fun sendText() {
        val device = selectedDevice
        if (device == null) {
            Toast.makeText(this, "请先选择一个设备", Toast.LENGTH_SHORT).show()
            return
        }
        
        val text = binding.etMessage.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "请输入要发送的内容", Toast.LENGTH_SHORT).show()
            return
        }
        
        transferClient.sendText(
            targetIp = device.ip,
            targetPort = device.port,
            text = text,
            onSuccess = {
                Toast.makeText(this, "发送成功", Toast.LENGTH_SHORT).show()
                binding.etMessage.text?.clear()
            },
            onError = { error ->
                Toast.makeText(this, "发送失败: $error", Toast.LENGTH_SHORT).show()
            }
        )
    }
    
    private fun sendFile(uri: Uri) {
        val device = selectedDevice ?: return
        
        // 将 Uri 复制到缓存目录
        val fileName = getFileName(uri) ?: "file"
        val cacheFile = File(cacheDir, fileName)
        
        try {
            contentResolver.openInputStream(uri)?.use { input ->
                FileOutputStream(cacheFile).use { output ->
                    input.copyTo(output)
                }
            }
            
            transferClient.sendFile(
                targetIp = device.ip,
                targetPort = device.port,
                file = cacheFile,
                onProgress = { sent, total ->
                    // 可以显示进度
                },
                onSuccess = {
                    Toast.makeText(this, "文件发送成功", Toast.LENGTH_SHORT).show()
                    cacheFile.delete()
                },
                onError = { error ->
                    Toast.makeText(this, "发送失败: $error", Toast.LENGTH_SHORT).show()
                    cacheFile.delete()
                }
            )
        } catch (e: Exception) {
            Toast.makeText(this, "读取文件失败: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun getFileName(uri: Uri): String? {
        var result: String? = null
        if (uri.scheme == "content") {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if (index >= 0) {
                        result = cursor.getString(index)
                    }
                }
            }
        }
        if (result == null) {
            result = uri.path
            val cut = result?.lastIndexOf('/')
            if (cut != null && cut != -1) {
                result = result?.substring(cut + 1)
            }
        }
        return result
    }
    
    private fun showReceivedTextDialog(sender: String, text: String) {
        showNotification("收到文字", "来自 $sender")
        
        AlertDialog.Builder(this)
            .setTitle("收到文字 - 来自 $sender")
            .setMessage(text)
            .setPositiveButton("复制") { _, _ ->
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                clipboard.setPrimaryClip(ClipData.newPlainText("EasyConnect", text))
                Toast.makeText(this, "已复制到剪贴板", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("关闭", null)
            .show()
    }
    
    private fun showReceivedFileDialog(sender: String, fileName: String, filePath: String) {
        showNotification("收到文件", "$fileName 来自 $sender")
        
        AlertDialog.Builder(this)
            .setTitle("收到文件 - 来自 $sender")
            .setMessage("文件: $fileName\n\n已保存到: $filePath")
            .setPositiveButton("打开") { _, _ ->
                openFile(filePath)
            }
            .setNegativeButton("关闭", null)
            .show()
    }
    
    private fun openFile(filePath: String) {
        try {
            val file = File(filePath)
            val uri = FileProvider.getUriForFile(
                this,
                "${packageName}.fileprovider",
                file
            )
            
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, contentResolver.getType(uri) ?: "*/*")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            
            startActivity(Intent.createChooser(intent, "打开文件"))
        } catch (e: Exception) {
            Toast.makeText(this, "无法打开文件: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "EasyConnect 通知",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "接收文件和文字时的通知"
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun showNotification(title: String, content: String) {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) 
            != PackageManager.PERMISSION_GRANTED) {
            return
        }
        
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(content)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(this).notify(notificationId++, notification)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        // 停止服务
        if (::deviceDiscovery.isInitialized) {
            deviceDiscovery.stop()
        }
        if (::transferServer.isInitialized) {
            transferServer.stop()
        }
        if (::transferClient.isInitialized) {
            transferClient.cancel()
        }
    }
}
