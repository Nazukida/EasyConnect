@echo off
chcp 65001 >nul
echo ========================================
echo   EasyConnect Windows EXE 打包工具
echo ========================================
echo.

REM 检查是否有 conda 环境变量
where conda >nul 2>&1
if %errorlevel%==0 (
    echo [提示] 检测到 Conda，如果您使用 conda 环境，请在 Anaconda Prompt 中运行此脚本
    echo [提示] 或者使用命令: conda activate connedev ^&^& build_exe.bat
    echo.
)

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo [提示] 如果使用 conda，请先运行: conda activate connedev
    pause
    exit /b 1
)

echo [信息] 使用 Python:
python --version
python -c "import sys; print(sys.executable)"
echo.

REM 安装/更新 PyInstaller
echo [1/3] 检查 PyInstaller...
pip install pyinstaller -q
pip install pyinstaller -q

REM 清理旧文件
if exist "dist\EasyConnect.exe" del "dist\EasyConnect.exe"
if exist "build" rmdir /s /q "build"
if exist "EasyConnect.spec" del "EasyConnect.spec"

REM 执行打包
echo [2/3] 开始打包...
echo.

pyinstaller --name=EasyConnect ^
    --onefile ^
    --windowed ^
    --add-data "config.py;." ^
    --hidden-import=zeroconf ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --clean ^
    --noconfirm ^
    main.py

echo.
if exist "dist\EasyConnect.exe" (
    echo [3/3] 打包成功!
    echo.
    echo ========================================
    echo   EXE 文件: dist\EasyConnect.exe
    echo ========================================
) else (
    echo [错误] 打包失败
)

echo.
pause
