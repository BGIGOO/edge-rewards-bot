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

echo [*] Kiem tra thu vien can thiet...
python -c "import selenium, webdriver_manager" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Dang tu dong cai dat cac goi can thiet...
    python -m pip install -r requirements.txt
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

echo.
echo --------------------------------------------------------------------
echo CHON CHE DO TIM KIEM:
echo [1] Chi tim kiem Desktop / PC  (Nen chay buoi sang / trua)
echo [2] Chi tim kiem Mobile        (Nen chay buoi chieu / toi)
echo [3] Chay ca hai (Desktop roi Mobile)
echo --------------------------------------------------------------------
set /p choice="Nhap lua chon che do (1/2/3) [Mac dinh: 1]: "

if "%choice%"=="2" (
    set selected_mode=mobile
) else if "%choice%"=="3" (
    set selected_mode=all
) else (
    set selected_mode=desktop
)

python -u edge_rewards_bot.py --profile %prof% --mode %selected_mode%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh dung lai voi ma loi %ERRORLEVEL%.
    pause
)
