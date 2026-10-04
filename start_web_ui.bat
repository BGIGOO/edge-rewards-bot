@echo off
chcp 65001 > nul
title Microsoft Rewards Auto Bot - Web UI Dashboard
echo ====================================================================
echo        KHOI DONG GIAO DIEN WEB QUAN LY DA TAI KHOAN REWARDS
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

echo [*] Kiem tra thu vien he thong...
python -c "import starlette, uvicorn, selenium" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Dang cai dat cac thu vien can thiet...
    python -m pip install -r requirements.txt
)

echo.
echo ====================================================================
echo [OK] He thong san sang!
echo Dang khoi dong Web Server tai: http://127.0.0.1:5000
echo ====================================================================
echo.

python web_server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Server da dung lai voi ma loi %ERRORLEVEL%.
    pause
)
