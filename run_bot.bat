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

echo Chon che do chay:
echo [1] Chi tim kiem Desktop / PC  (Nen chay buoi sang / trua)
echo [2] Chi tim kiem Mobile        (Nen chay buoi chieu / toi)
echo [3] Chay ca hai (Desktop roi Mobile)
echo.
set /p choice="Nhap lua chon (1/2/3) [Mac dinh la 1]: "

if "%choice%"=="2" (
    python edge_rewards_bot.py --mode mobile
) else if "%choice%"=="3" (
    python edge_rewards_bot.py --mode all
) else (
    python edge_rewards_bot.py --mode desktop
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
