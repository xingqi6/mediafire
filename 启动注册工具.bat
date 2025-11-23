@echo off
chcp 65001 >nul
title MediaFire 自动注册工具

echo.
echo ================================================================
echo            MediaFire 自动注册工具 - Windows 版
echo ================================================================
echo.
echo 正在检查环境...
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python
    echo.
    echo 请先安装 Python 3.9 或更高版本:
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [✓] Python 已安装
python --version

:: 检查依赖
echo.
echo 正在检查依赖包...
python -c "import selenium" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 缺少依赖包,正在安装...
    echo.
    pip install selenium webdriver-manager colorama
    if %errorlevel% neq 0 (
        echo.
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [✓] 依赖包完整
echo.

:: 运行脚本
echo 启动注册工具...
echo.
python register_windows.py

:: 结束
if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序异常退出
)

echo.
pause
