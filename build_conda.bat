@echo off
chcp 65001 >nul
echo ========================================
echo   EasyConnect Conda 打包工具
echo ========================================
echo.

REM 设置 conda 环境名
set CONDA_ENV=connedev

REM 查找 conda
where conda >nul 2>&1
if errorlevel 1 (
    REM 尝试从常见路径激活
    if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\anaconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\miniconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else if exist "D:\software\anaconda\Scripts\activate.bat" (
        call "D:\software\anaconda\Scripts\activate.bat" %CONDA_ENV%
    ) else (
        echo [错误] 未找到 Conda，请手动在 Anaconda Prompt 中运行 build_exe.bat
        pause
        exit /b 1
    )
) else (
    call conda activate %CONDA_ENV%
)

echo [信息] 当前 Python:
python --version
python -c "import sys; print(sys.executable)"
echo.

REM 调用原打包脚本
call build_exe.bat
