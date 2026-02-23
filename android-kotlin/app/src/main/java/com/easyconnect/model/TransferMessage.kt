package com.easyconnect.model

object MessageType {
    const val TEXT = "TEXT"
    const val FILE = "FILE"
}

data class TransferMessage(
    val type: String,
    val sender: String,
    val content: String,
    val file_size: Long = 0
)
