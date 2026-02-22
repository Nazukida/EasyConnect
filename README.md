# EasyConnect - 局域网文件传输工具

一个跨平台的局域网文件和剪贴板内容传输工具。

## 功能特点

- 🔍 **自动发现** - 使用 mDNS 协议自动发现同一局域网内的设备
- 📁 **文件传输** - 支持拖拽文件快速传输到其他设备
- 📋 **剪贴板同步** - 复制的文字可以快速发送到其他设备
- 🖥️ **跨平台** - 支持 Windows、macOS、Linux、Android
- 🎯 **简单直观** - 右侧发送面板，左侧接收气泡

## 版本

| 平台 | 技术栈 | 目录 |
|------|--------|------|
| Windows/macOS/Linux | Python + PySide6 | `./` (根目录) |
| Android | Kotlin + Material Design | `./android-kotlin/` |

## Windows 桌面版

### 1. 安装依赖（首次运行）

双击运行 `install.bat`，或者手动执行：

```cmd
pip install -r requirements.txt
```

### 2. 运行程序

双击运行 `run.bat`，或者：

```cmd
python main.py
```

### 3. 打包成 EXE（可选）

双击运行 `build_exe.bat`，EXE 文件会生成在 `dist/EasyConnect.exe`

## Android 版本

详见 [android-kotlin/README.md](android-kotlin/README.md)

### 快速编译

```bash
cd android-kotlin
./gradlew assembleDebug
```

APK 生成在 `android-kotlin/app/build/outputs/apk/debug/`

## 环境测试

如果遇到问题，运行环境测试：

```cmd
python test_env.py
```

或双击 `test_env.bat`

## 使用方法

1. 在所有需要传输文件的设备上运行此程序
2. 程序会自动发现局域网内的其他设备
3. **发送文件/文字**：
   - 拖拽文件到右侧面板
   - 复制文字后点击剪贴板按钮
   - 选择目标设备发送
4. **接收文件/文字**：
   - 左侧会弹出气泡提示
   - 文件自动保存到接收目录
   - 文字自动复制到剪贴板

## 项目结构

```
EasyConnect/
├── main.py              # 主程序入口
├── requirements.txt     # 依赖列表
├── config.py           # 配置文件
├── network/            # 网络模块
│   ├── discovery.py    # 设备发现
│   └── transfer.py     # 数据传输
├── ui/                 # 界面模块
│   ├── main_window.py  # 主窗口
│   ├── send_panel.py   # 发送面板
│   └── receive_bubble.py # 接收气泡
└── utils/              # 工具模块
    └── clipboard.py    # 剪贴板处理
```

## 技术栈

- Python 3.8+
- PySide6 (Qt for Python)
- zeroconf (mDNS 设备发现)

## 许可证

MIT License
