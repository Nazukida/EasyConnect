@echo off
chcp 65001 >nul
echo ========================================
echo   EasyConnect - 局域网文件传输工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查并安装依赖
echo [1/2] 检查依赖...
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包（首次运行需要几分钟）...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [2/2] 启动 EasyConnect...
echo.
python main.py

pause
