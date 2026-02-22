"""
EasyConnect 环境测试脚本
检查所有依赖是否正确安装
"""
import sys
import os

print("=" * 50)
print("  EasyConnect 环境测试")
print("=" * 50)
print()

errors = []
warnings = []

# 1. Python 版本检查
print(f"[检查] Python 版本: {sys.version}")
if sys.version_info < (3, 8):
    errors.append("Python 版本需要 3.8 或更高")
else:
    print("       ✓ Python 版本 OK")

# 2. PySide6 检查
print("\n[检查] PySide6 (桌面版 GUI)...")
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    print("       ✓ PySide6 OK")
except ImportError as e:
    errors.append(f"PySide6 未安装: {e}")
    print(f"       ✗ PySide6 未安装")
    print("       请运行: pip install PySide6")

# 3. zeroconf 检查
print("\n[检查] zeroconf (设备发现)...")
try:
    from zeroconf import Zeroconf
    print("       ✓ zeroconf OK")
except ImportError as e:
    errors.append(f"zeroconf 未安装: {e}")
    print(f"       ✗ zeroconf 未安装")
    print("       请运行: pip install zeroconf")

# 4. Kivy 检查 (Android 版测试)
print("\n[检查] Kivy (Android 版/可选)...")
try:
    # 设置环境变量避免 Kivy 启动窗口
    os.environ['KIVY_NO_CONSOLELOG'] = '1'
    from kivy.app import App
    print("       ✓ Kivy OK")
except ImportError as e:
    warnings.append(f"Kivy 未安装 (仅影响 Android 版测试): {e}")
    print(f"       ! Kivy 未安装 (可选，仅影响 Android 版本)")
    print("       如需测试 Android 版: pip install kivy")

# 5. 网络测试
print("\n[检查] 网络功能...")
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"       ✓ 本机 IP: {local_ip}")
except Exception as e:
    warnings.append(f"无法获取本机 IP: {e}")
    print(f"       ! 无法获取本机 IP: {e}")

# 6. 接收目录检查
print("\n[检查] 接收目录...")
receive_dir = os.path.join(os.path.expanduser("~"), "EasyConnect_Received")
if not os.path.exists(receive_dir):
    try:
        os.makedirs(receive_dir)
        print(f"       ✓ 已创建接收目录: {receive_dir}")
    except Exception as e:
        warnings.append(f"无法创建接收目录: {e}")
        print(f"       ! 无法创建接收目录: {e}")
else:
    print(f"       ✓ 接收目录已存在: {receive_dir}")

# 7. PyInstaller 检查 (打包用)
print("\n[检查] PyInstaller (打包 EXE/可选)...")
try:
    import PyInstaller
    print(f"       ✓ PyInstaller {PyInstaller.__version__}")
except ImportError:
    warnings.append("PyInstaller 未安装 (仅影响打包)")
    print("       ! PyInstaller 未安装")
    print("       如需打包 EXE: pip install pyinstaller")

# 结果汇总
print("\n" + "=" * 50)
if errors:
    print("❌ 检测到错误:")
    for e in errors:
        print(f"   - {e}")
    print("\n请安装缺失的依赖后再运行程序。")
    print("可以运行: pip install -r requirements.txt")
elif warnings:
    print("✓ 核心依赖完整，但有一些可选组件未安装:")
    for w in warnings:
        print(f"   - {w}")
    print("\n可以正常运行桌面版！")
else:
    print("✓ 所有检查通过！")
    print("可以运行: python main.py")

print("=" * 50)

# 如果核心依赖完整，询问是否启动
if not errors:
    print("\n是否现在启动 EasyConnect? (y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            print("\n正在启动...")
            os.system("python main.py")
    except:
        pass
