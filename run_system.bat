@echo off
setlocal
color 0A
title AI EMPLOYEE TRACKER - DUY TAN UNIVERSITY

echo ======================================================
echo       HE THONG GIAM SAT NHAN VIEN AI (OPENVINO)
echo                TRANN HAT QUY - DTU 2026
echo ======================================================

:: 1. Kiem tra moi truong ao
if not exist ".venv" (
    echo [!] Khong thay .venv. Dang tao moi...
    python -m venv .venv
)

echo [*] Dang kich hoat moi truong ao...
call .venv\Scripts\activate

:: 2. Kiem tra thu vien
echo [*] Dang kiem tra va cap nhat thu vien...
pip install -r requirements.txt --quiet

:: 3. Khoi chay
echo [*] Dang ham nong OpenVINO va khoi chay Server...
echo ------------------------------------------------------
echo GHI CHU: 
echo - Vui long doi 15-20 giay de AI Engine khoi dong.
echo - Trinh duyet se tu dong mo trang chu.
echo ------------------------------------------------------

:: Mo trinh duyet (doi 5 giay)
timeout /t 5 /nobreak >nul
start "" http://127.0.0.1:5000

:: Chay Python
python app.py

pause