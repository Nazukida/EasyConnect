package com.easyconnect.network

import android.util.Log
import com.easyconnect.Config
import com.easyconnect.model.MessageType
import com.easyconnect.model.TransferMessage
import com.google.gson.Gson
import kotlinx.coroutines.*
import java.io.*
import java.net.Socket
import java.nio.ByteBuffer

/** TCP 传输客户端，与桌面版协议兼容 */
class TransferClient {
    companion object {
        private const val TAG = "TransferClient"
        private const val TIMEOUT = 10000
    }
    
    private val deviceName = Config.getDeviceName()
    private val gson = Gson()
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    fun sendText(
        targetIp: String,
        targetPort: Int,
        text: String,
        onSuccess: (() -> Unit)? = null,
        onError: ((String) -> Unit)? = null
    ) {
        scope.launch {
            try {
                Socket().use { socket ->
                    socket.soTimeout = TIMEOUT
                    socket.connect(java.net.InetSocketAddress(targetIp, targetPort), TIMEOUT)
                    
                    val message = TransferMessage(
                        type = MessageType.TEXT,
                        sender = deviceName,
                        content = text
                    )
                    
                    val jsonData = gson.toJson(message).toByteArray(Charsets.UTF_8)
                    
                    val output = DataOutputStream(socket.getOutputStream())
                    val input = socket.getInputStream()
                    
                    // 消息协议: 4字节长度头 + JSON
                    output.writeInt(jsonData.size)
                    output.write(jsonData)
                    output.flush()
                    
                    // 等待ACK
                    val ack = ByteArray(3)
                    val read = input.read(ack)
                    
                    if (read == 3 && String(ack) == "ACK") {
                        Log.i(TAG, "文字发送成功到 $targetIp")
                        withContext(Dispatchers.Main) {
                            onSuccess?.invoke()
                        }
                    } else {
                        throw Exception("未收到确认")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "发送文字失败: ${e.message}")
                withContext(Dispatchers.Main) {
                    onError?.invoke(e.message ?: "发送失败")
                }
            }
        }
    }
    
    fun sendFile(
        targetIp: String,
        targetPort: Int,
        file: File,
        onProgress: ((Long, Long) -> Unit)? = null,
        onSuccess: (() -> Unit)? = null,
        onError: ((String) -> Unit)? = null
    ) {
        scope.launch {
            try {
                if (!file.exists()) {
                    throw FileNotFoundException("文件不存在: ${file.absolutePath}")
                }
                
                val fileName = file.name
                val fileSize = file.length()
                
                Socket().use { socket ->
                    socket.soTimeout = 60000 // 文件传输给更多时间
                    socket.connect(java.net.InetSocketAddress(targetIp, targetPort), TIMEOUT)
                    
                    val output = DataOutputStream(socket.getOutputStream())
                    val input = socket.getInputStream()
                    
                    // 发送文件信息
                    val fileInfo = TransferMessage(
                        type = MessageType.FILE,
                        sender = deviceName,
                        content = fileName,
                        file_size = fileSize
                    )
                    
                    val jsonData = gson.toJson(fileInfo).toByteArray(Charsets.UTF_8)
                    output.writeInt(jsonData.size)
                    output.write(jsonData)
                    output.flush()
                    
                    val ready = ByteArray(5)
                    val readLen = input.read(ready)
                    if (readLen != 5 || String(ready) != "READY") {
                        throw Exception("接收方未准备好")
                    }
                    
                    var sent = 0L
                    FileInputStream(file).use { fis ->
                        val buffer = ByteArray(Config.BUFFER_SIZE)
                        var bytesRead: Int
                        
                        while (fis.read(buffer).also { bytesRead = it } != -1) {
                            output.write(buffer, 0, bytesRead)
                            sent += bytesRead
                            
                            withContext(Dispatchers.Main) {
                                onProgress?.invoke(sent, fileSize)
                            }
                        }
                    }
                    output.flush()
                    
                    val ack = ByteArray(3)
                    val ackRead = input.read(ack)
                    
                    if (ackRead == 3 && String(ack) == "ACK") {
                        Log.i(TAG, "文件发送成功: $fileName")
                        withContext(Dispatchers.Main) {
                            onSuccess?.invoke()
                        }
                    } else {
                        throw Exception("未收到确认")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "发送文件失败: ${e.message}")
                withContext(Dispatchers.Main) {
                    onError?.invoke(e.message ?: "发送失败")
                }
            }
        }
    }
    
    fun cancel() {
        scope.coroutineContext.cancelChildren()
    }
}
