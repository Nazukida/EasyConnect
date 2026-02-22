# EasyConnect Android (Kotlin)

局域网文件和文字传输工具的 Android 版本，使用 Kotlin 和 Material Design 3 构建。

## 功能特性

- 🔍 **设备自动发现**: 使用 Android NSD (mDNS) 自动发现局域网内的其他 EasyConnect 设备
- 📝 **文字传输**: 快速发送和接收文字内容
- 📁 **文件传输**: 支持发送任意类型的文件
- 🔔 **通知提醒**: 收到文件或文字时弹出通知
- 🎨 **Material Design 3**: 现代化的 UI 设计

## 系统要求

- Android 7.0 (API 24) 或更高版本
- 连接到局域网 (WiFi)

## 编译说明

### 前置条件

1. Android Studio Hedgehog (2023.1.1) 或更新版本
2. JDK 17
3. Android SDK 34

### 编译步骤

1. 在 Android Studio 中打开 `android-kotlin` 目录
2. 等待 Gradle 同步完成（首次会自动下载依赖）
3. 点击 Build > Build Bundle(s) / APK(s) > Build APK(s)
4. APK 将生成在 `app/build/outputs/apk/debug/` 目录

### 命令行编译

首次使用命令行编译，需要先初始化 Gradle Wrapper：

```bash
# 进入项目目录
cd android-kotlin

# 如果没有 gradle-wrapper.jar，先用本地 Gradle 初始化
gradle wrapper

# 编译 Debug APK
./gradlew assembleDebug

# 编译 Release APK (需要签名配置)
./gradlew assembleRelease

# 安装到连接的设备
./gradlew installDebug
```

> **推荐**: 直接使用 Android Studio 打开项目，会自动处理所有依赖和 Gradle 配置。

## 项目结构

```
app/src/main/
├── java/com/easyconnect/
│   ├── MainActivity.kt          # 主界面
│   ├── Config.kt                # 配置和工具类
│   ├── model/
│   │   ├── Device.kt            # 设备数据类
│   │   └── TransferMessage.kt   # 传输消息数据类
│   ├── network/
│   │   ├── DeviceDiscovery.kt   # mDNS 设备发现
│   │   ├── TransferClient.kt    # 发送客户端
│   │   └── TransferServer.kt    # 接收服务器
│   ├── service/
│   │   └── TransferService.kt   # 前台服务
│   └── ui/
│       └── DeviceAdapter.kt     # 设备列表适配器
└── res/
    ├── layout/
    │   ├── activity_main.xml    # 主界面布局
    │   └── item_device.xml      # 设备列表项布局
    └── values/
        ├── strings.xml          # 字符串资源
        ├── colors.xml           # 颜色定义
        └── themes.xml           # 主题样式
```

## 通信协议

与桌面版完全兼容的协议：

- **服务发现**: mDNS 服务类型 `_easyconnect._tcp.local.`
- **传输端口**: TCP 52525
- **消息格式**: 4字节长度头 (大端序) + JSON 消息体

### 消息类型

```json
// 文字消息
{
  "type": "text",
  "sender": "设备名称",
  "content": "文字内容"
}

// 文件消息
{
  "type": "file", 
  "sender": "设备名称",
  "content": "文件名",
  "file_size": 12345
}
```

## 权限说明

| 权限 | 用途 |
|------|------|
| INTERNET | 网络通信 |
| ACCESS_NETWORK_STATE | 检查网络状态 |
| ACCESS_WIFI_STATE | 获取 WiFi 信息 |
| CHANGE_WIFI_MULTICAST_STATE | mDNS 多播 |
| READ_EXTERNAL_STORAGE | 读取文件 |
| WRITE_EXTERNAL_STORAGE | 保存文件 |
| POST_NOTIFICATIONS | 显示通知 |
| FOREGROUND_SERVICE | 后台服务 |

## 注意事项

1. 确保手机和其他设备连接到同一个 WiFi 网络
2. 某些路由器可能禁用了多播，会影响设备发现
3. 首次运行需要授予必要权限

## License

MIT License
