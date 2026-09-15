@echo off
chcp 65001 > nul
title Cai dat va Khoi dong Microsoft Rewards Auto Bot
echo ====================================================================
echo        CAI DAT & KHOI DONG BOT MICROSOFT REWARDS (EDGE AUTO)
echo ====================================================================
echo.

cd /d "%~dp0"

echo [*] Dang kiem tra moi truong Python...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] CHUA CO PYTHON TREN MAY!
    echo.
    echo Huong dan nhanh cho ban:
    echo 1. Truy cap https://www.python.org/downloads/ va tai ban Python moi nhat ve cai dat.
    echo 2. QUAN TRONG: Luc cai dat, NHO TICH CHON o "Add python.exe to PATH" o man hinh dau tien!
    echo 3. Sau khi cai xong, mo lai file nay.
    echo.
    pause
    exit /b
)

echo [✓] Da tim thay Python!
echo.
echo [*] Dang tu dong cai dat thu vien Selenium can thiet (chi mat vai giay lan dau)...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [!] Co the do mang cham, dang thu lai cai dat thu vien...
    python -m pip install selenium webdriver-manager
)

echo [✓] Thu vien da san sang!
echo.
echo ====================================================================
echo           DANG KHOI DONG BOT TU DONG TIM KIEM...
echo ====================================================================
echo.
python edge_rewards_bot.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Chuong trinh ket thuc voi ma loi %ERRORLEVEL%.
    pause
)
