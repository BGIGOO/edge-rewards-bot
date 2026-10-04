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

echo --------------------------------------------------------------------
echo CHON TAI KHOAN / PROFILE:
echo [1] Profile 1 (Chinh)
echo [2] Profile 2 (Phu 1)
echo [3] Profile 3 (Tai khoan 3)
echo [4] Profile 4 (Tai khoan 4)
echo [5] Chay lan luot TAT CA 4 Profile
echo --------------------------------------------------------------------
set /p prof="Nhap lua chon tai khoan (1-5) [Mac dinh: 1]: "
if "%prof%"=="" set prof=1
if "%prof%"=="5" set prof=all

python -u edge_rewards_bot.py --mode mobile --profile %prof%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
