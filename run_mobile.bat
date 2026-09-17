@echo off
chcp 65001 > nul
title Microsoft Edge Rewards Bot - Mobile (Android)
echo ====================================================================
echo      CHAY BOT MICROSOFT REWARDS - CHE DO MOBILE (DIEN THOAI)
echo ====================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [LOI] Khong tim thay Python trong he thong!
    pause
    exit /b
)

python edge_rewards_bot.py --mode mobile

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
