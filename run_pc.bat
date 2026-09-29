@echo off
chcp 65001 > nul
title Microsoft Edge Rewards Bot - Desktop (PC)
echo ====================================================================
echo      CHAY BOT MICROSOFT REWARDS - CHE DO DESKTOP (PC)
echo ====================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [LOI] Khong tim thay Python trong he thong!
    pause
    exit /b
)

echo --------------------------------------------------------------------
echo CHON TAI KHOAN / PROFILE:
echo [1] Profile 1 (manhnguyen1745@gmail.com)
echo [2] Profile 2 (manhnguyen1768@gmail.com)
echo [3] Chay ca 2 Profile (Lan luot Profile 1 roi Profile 2)
echo --------------------------------------------------------------------
set /p prof="Nhap lua chon tai khoan (1/2/3) [Mac dinh: 1]: "
if "%prof%"=="" set prof=1

python -u edge_rewards_bot.py --mode desktop --profile %prof%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
