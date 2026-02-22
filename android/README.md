# EasyConnect Android 版本

这是 EasyConnect 的 Android 版本，使用 Kivy 框架开发。

## 环境要求

### 在 Linux/WSL 上打包 (推荐)

由于 Buildozer 主要支持 Linux，建议在 Linux 或 WSL (Windows Subsystem for Linux) 上进行 Android 打包。

```bash
# 1. 安装依赖 (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 2. 安装 Buildozer 和 Cython
pip3 install buildozer cython kivy

# 3. 进入 android 目录
cd android

# 4. 初始化 (首次运行会自动下载 Android SDK/NDK)
buildozer android debug

# 5. APK 文件会生成在 bin/ 目录
```

### 在 Windows 上打包

Windows 上可以使用以下方式：

#### 方式一：使用 WSL (推荐)

```powershell
# 1. 安装 WSL
wsl --install

# 2. 在 WSL 中按照 Linux 步骤操作
```

#### 方式二：使用 Google Colab (免费云端)

1. 打开 Google Colab: https://colab.research.google.com
2. 新建笔记本，运行以下代码：

```python
# 安装依赖
!pip install buildozer cython

# 安装系统包
!sudo apt-get update
!sudo apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 上传你的 main.py 和 buildozer.spec

# 运行打包
!buildozer android debug

# 下载 APK
from google.colab import files
files.download('bin/easyconnect-1.0.0-arm64-v8a_armeabi-v7a-debug.apk')
```

#### 方式三：使用 GitHub Actions (CI/CD)

创建 `.github/workflows/build-android.yml` 文件，推送到 GitHub 后自动构建。

## 项目结构

```
android/
├── main.py           # Kivy 应用主程序
├── buildozer.spec    # Buildozer 配置文件
└── README.md         # 本文档
```

## 功能说明

- 📡 自动发现局域网内的设备
- 📝 发送/接收文字
- 📋 自动复制到剪贴板
- 🔗 手动添加 IP 地址

## 注意事项

1. 确保手机和电脑在同一局域网
2. 部分路由器可能阻止 mDNS，此时需要手动输入 IP
3. 首次打包需要下载约 2GB 的 SDK/NDK，请耐心等待

## 测试

在打包前，可以在电脑上测试 Kivy 应用：

```bash
pip install kivy
python main.py
```
