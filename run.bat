@echo off
chcp 65001 >nul
title AgyWatch - Autonomous Git & CI Watchdog Daemon

echo =====================================================================
echo  👁️  AGYWATCH - AUTONOMOUS GIT ^& CI WATCHDOG FOR ANTIGRAVITY
echo =====================================================================

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Không tìm thấy Python trong hệ thống PATH!
    pause
    exit /b 1
)

if not exist config.json (
    echo [INFO] Chưa tìm thấy file config.json. Đang khởi động trình cài đặt...
    python setup.py
    if not exist config.json (
        echo [ERROR] Cài đặt chưa hoàn tất. Đang thoát.
        pause
        exit /b 1
    )
)

echo [INFO] Đang khởi chạy AgyWatch Daemon...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Tiến trình AgyWatch dừng với mã lỗi %ERRORLEVEL%.
    pause
)
