# EasyConnect 打包指南

本文档介绍如何将 EasyConnect 打包成 Windows EXE 和 Android APK。

---

## 📦 Windows EXE 打包

### 方法一：使用打包脚本（推荐）

```cmd
# 直接双击运行
build_exe.bat
```

或者：

```cmd
python build_exe.py
```

### 方法二：手动打包

```cmd
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 执行打包命令
pyinstaller --name=EasyConnect --onefile --windowed --add-data "config.py;." --hidden-import=zeroconf --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtWidgets --hidden-import=PySide6.QtGui main.py
```

### 打包结果

- EXE 文件位置: `dist/EasyConnect.exe`
- 双击即可运行，无需安装 Python

---

## 📱 Android APK 打包

由于 PySide6 不支持 Android，Android 版本使用 Kivy 框架重写，位于 `android/` 目录。

### 方法一：使用 WSL（Windows 用户推荐）

```bash
# 1. 安装 WSL (管理员 PowerShell)
wsl --install

# 2. 重启后打开 Ubuntu，安装依赖
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev

# 3. 安装 Python 包
pip3 install buildozer cython kivy

# 4. 进入项目目录（假设项目在 D:\RE0\EasyConnect）
cd /mnt/d/RE0/EasyConnect/android

# 5. 开始打包（首次约需 30 分钟下载 SDK）
buildozer android debug

# 6. APK 在 bin/ 目录
ls bin/*.apk
```

### 方法二：使用 Google Colab（免费云端）

1. 打开 [Google Colab](https://colab.research.google.com)
2. 新建笔记本
3. 运行以下代码：

```python
# Cell 1: 安装依赖
!pip install buildozer cython
!sudo apt-get update -qq
!sudo apt-get install -y -qq git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev

# Cell 2: 上传文件
# 点击左侧文件图标，上传 android/main.py 和 android/buildozer.spec

# Cell 3: 打包
%cd /content
!buildozer android debug

# Cell 4: 下载 APK
from google.colab import files
import glob
apk_files = glob.glob('bin/*.apk')
if apk_files:
    files.download(apk_files[0])
```

### 方法三：使用 GitHub Actions（自动化）

1. 将项目推送到 GitHub
2. 进入仓库的 Actions 页面
3. 手动触发 "Build Android APK" 工作流
4. 下载生成的 APK

---

## 🔧 常见问题

### EXE 打包问题

**Q: 打包后 EXE 文件很大？**
A: PySide6 自带 Qt 库，单文件约 50-80MB 是正常的。

**Q: 杀毒软件报毒？**
A: PyInstaller 打包的 EXE 可能被误报，添加信任即可。

### APK 打包问题

**Q: Buildozer 下载很慢？**
A: 首次需要下载约 2GB 的 Android SDK/NDK，建议使用稳定网络。

**Q: 打包失败 "SDK license not accepted"？**
A: 在 buildozer.spec 中确保 `android.accept_sdk_license = True`

**Q: APK 安装后无法发现设备？**
A: 
1. 确保手机和电脑在同一 WiFi
2. 部分路由器阻止 mDNS，手动输入 IP 地址
3. 检查手机防火墙设置

---

## 📁 打包后的文件结构

```
EasyConnect/
├── dist/
│   └── EasyConnect.exe      # Windows 可执行文件
└── android/
    └── bin/
        └── easyconnect-*.apk # Android 安装包
```

---

## 💡 提示

- Windows EXE 可以直接分发，接收方无需安装任何软件
- Android APK 需要在手机上允许"安装未知来源应用"
- 两个版本使用相同的网络协议，可以互相通信
