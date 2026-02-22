"""
EasyConnect Windows EXE 打包脚本
使用 PyInstaller 将程序打包成单个 exe 文件
"""
import os
import subprocess
import sys

def build():
    """执行打包"""
    print("=" * 50)
    print("  EasyConnect Windows EXE 打包工具")
    print("=" * 50)
    
    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
        print(f"[√] PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[√] PyInstaller 安装完成")
    
    # PyInstaller 参数
    args = [
        "pyinstaller",
        "--name=EasyConnect",           # 程序名称
        "--onefile",                     # 打包成单个文件
        "--windowed",                    # 无控制台窗口 (GUI程序)
        "--icon=icon.ico",               # 图标文件 (如果有的话)
        "--add-data=config.py;.",        # 包含配置文件
        "--hidden-import=zeroconf",      # 隐藏导入
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets", 
        "--hidden-import=PySide6.QtGui",
        "--clean",                       # 清理临时文件
        "--noconfirm",                   # 不确认覆盖
        "main.py"                        # 入口文件
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists("icon.ico"):
        args = [arg for arg in args if not arg.startswith("--icon")]
        print("[!] 未找到 icon.ico，将使用默认图标")
    
    print("\n[*] 开始打包...")
    print(f"[*] 命令: {' '.join(args)}\n")
    
    # 执行打包
    result = subprocess.run(args, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("[√] 打包成功!")
        print(f"[√] EXE 文件位置: dist/EasyConnect.exe")
        print("=" * 50)
    else:
        print("\n[×] 打包失败，请检查错误信息")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(build())
