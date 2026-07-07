@echo off
echo ===================================================
echo   KHOI DONG YOUTUBE BULK DOWNLOADER
echo ===================================================

:: Kiem tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python chua duoc cai dat tren may tinh cua ban!
    echo Vui long tai va cai dat Python tai: https://www.python.org/downloads/
    pause
    exit /b
)

:: Tao thu mu ao .venv neu chua co
if not exist .venv (
    echo [+] Dang tao moi truong ao (virtual environment)...
    python -m venv .venv
)

:: Kich hoat moi truong ao
call .venv\Scripts\activate

:: Nâng cap pip va cai dat cac thu vien can thiet
echo [+] Dang kiem tra va cai dat thu vien...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Khoi chay Streamlit
echo [+] Dang khoi chay ung dung tren trinh duyet...
streamlit run app.py

pause
