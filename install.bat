@echo off
chcp 65001 >nul
echo ========================================
echo   EasyConnect 依赖安装
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo 请从 https://www.python.org/downloads/ 下载安装
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 升级 pip...
python -m pip install --upgrade pip -q

echo [2/3] 安装核心依赖...
pip install PySide6 zeroconf ifaddr -q
if errorlevel 1 (
    echo [错误] 核心依赖安装失败
    pause
    exit /b 1
)

echo [3/3] 安装可选依赖...
pip install pyinstaller -q

echo.
echo ========================================
echo   安装完成!
echo ========================================
echo.
echo 运行程序: python main.py
echo 或双击:   run.bat
echo.
echo 打包 EXE: build_exe.bat
echo.
pause
