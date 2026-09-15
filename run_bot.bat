@echo off
chcp 65001 > nul
title Microsoft Edge Rewards Auto Bot
echo ====================================================================
echo        KHOI DONG BOT MICROSOFT REWARDS (EDGE AUTO SEARCH)
echo ====================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [LOI] Khong tim thay Python trong he thong!
    echo Vui long cai dat Python va tich chon "Add Python to PATH".
    pause
    exit /b
)

python edge_rewards_bot.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
