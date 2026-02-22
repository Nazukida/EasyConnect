package com.easyconnect.model

/**
 * 传输消息类型
 */
object MessageType {
    const val TEXT = "TEXT"
    const val FILE = "FILE"
}

/**
 * 传输消息
 */
data class TransferMessage(
    val type: String,
    val sender: String,
    val content: String,
    val file_size: Long = 0
)
