package com.easyconnect.network

import android.os.Environment
import android.util.Log
import com.easyconnect.Config
import com.easyconnect.model.MessageType
import com.easyconnect.model.TransferMessage
import com.google.gson.Gson
import kotlinx.coroutines.*
import java.io.*
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketException
import java.net.SocketTimeoutException
import java.util.concurrent.CopyOnWriteArraySet

/** TCP 接收服务器，与桌面版协议兼容 */
class TransferServer(private val port: Int = Config.TRANSFER_PORT) {
    companion object {
        private const val TAG = "TransferServer"
    }
    
    private var serverSocket: ServerSocket? = null
    private var isRunning = false
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val activeConnections = CopyOnWriteArraySet<Socket>()
    private val gson = Gson()
    
    private val receiveDir: File by lazy {
        val dir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
            "EasyConnect"
        )
        if (!dir.exists()) dir.mkdirs()
        dir
    }
    
    // 回调
    var onTextReceived: ((sender: String, text: String) -> Unit)? = null
    var onFileReceived: ((sender: String, fileName: String, filePath: String) -> Unit)? = null
    var onFileProgress: ((fileName: String, received: Long, total: Long) -> Unit)? = null
    
    fun start() {
        if (isRunning) return
        
        isRunning = true
        scope.launch {
            try {
                serverSocket = ServerSocket(port).apply {
                    reuseAddress = true
                    soTimeout = 1000  // 便于检查 isRunning
                }
                
                Log.i(TAG, "传输服务器已启动，端口: $port")
                
                while (isRunning) {
                    try {
                        val client = serverSocket?.accept() ?: break
                        activeConnections.add(client)
                        
                        launch {
                            handleClient(client)
                        }
                    } catch (e: SocketTimeoutException) {
                        continue
                    } catch (e: SocketException) {
                        if (isRunning) Log.e(TAG, "Socket 异常: ${e.message}")
                        break
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "服务器启动失败: ${e.message}")
            }
        }
    }
    
    private suspend fun handleClient(socket: Socket) {
        try {
            socket.soTimeout = 60000
            
            val input = DataInputStream(socket.getInputStream())
            val output = socket.getOutputStream()
            
            // 读取消息长度（4字节大端序）
            val msgLength = input.readInt()
            
            // 读取消息内容
            val msgData = ByteArray(msgLength)
            var totalRead = 0
            while (totalRead < msgLength) {
                val read = input.read(msgData, totalRead, msgLength - totalRead)
                if (read == -1) break
                totalRead += read
            }
            
            // 解析 JSON
            val jsonStr = String(msgData, Charsets.UTF_8)
            val message = gson.fromJson(jsonStr, TransferMessage::class.java)
            
            when (message.type) {
                MessageType.TEXT -> handleTextMessage(message, output)
                MessageType.FILE -> handleFileMessage(message, input, output)
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "处理客户端错误: ${e.message}")
        } finally {
            activeConnections.remove(socket)
            try {
                socket.close()
            } catch (e: Exception) {
                // 忽略关闭异常
            }
        }
    }
    
    private suspend fun handleTextMessage(message: TransferMessage, output: OutputStream) {
        Log.i(TAG, "收到文字来自 ${message.sender}: ${message.content.take(50)}..."))
        
        // 发送确认
        output.write("ACK".toByteArray())
        output.flush()
        
        // 回调到主线程
        withContext(Dispatchers.Main) {
            onTextReceived?.invoke(message.sender, message.content)
        }
    }
    
    private suspend fun handleFileMessage(
        message: TransferMessage, 
        input: DataInputStream,
        output: OutputStream
    ) {
        val fileName = message.content
        val fileSize = message.file_size
        
        Log.i(TAG, "开始接收文件: $fileName ($fileSize bytes)")
        output.write("READY".toByteArray())
        output.flush()
        
        var targetFile = File(receiveDir, fileName)
        var counter = 1
        val nameWithoutExt = fileName.substringBeforeLast(".")
        val ext = if (fileName.contains(".")) ".${fileName.substringAfterLast(".")}" else ""
        
        while (targetFile.exists()) {
            targetFile = File(receiveDir, "${nameWithoutExt}_$counter$ext")
            counter++
        }
        
        var received = 0L
        FileOutputStream(targetFile).use { fos ->
            val buffer = ByteArray(Config.BUFFER_SIZE)
            
            while (received < fileSize) {
                val toRead = minOf(Config.BUFFER_SIZE.toLong(), fileSize - received).toInt()
                val bytesRead = input.read(buffer, 0, toRead)
                
                if (bytesRead == -1) break
                
                fos.write(buffer, 0, bytesRead)
                received += bytesRead
                
                }
            }
        }
        
        output.write("ACK".toByteArray())
        output.flush()
        Log.i(TAG, "文件接收完成: ${targetFile.absolutePath}")
        
        // 回调到主线程
        withContext(Dispatchers.Main) {
            onFileReceived?.invoke(message.sender, fileName, targetFile.absolutePath)
        }
    }
    
    fun stop() {
        Log.i(TAG, "正在停止服务器...")
        isRunning = false
        for (conn in activeConnections) {
            try {
                conn.shutdownInput()
                conn.shutdownOutput()
                conn.close()
            } catch (e: Exception) { }
        }
        activeConnections.clear()
        try {
            serverSocket?.close()
        } catch (e: Exception) { }
        serverSocket = null
        scope.coroutineContext.cancelChildren()
        Log.i(TAG, "传输服务器已停止")
    }
}
