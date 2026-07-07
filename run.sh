#!/bin/bash
echo "==================================================="
echo "  KHOI DONG YOUTUBE BULK DOWNLOADER"
echo "==================================================="

# Kiem tra Python
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 chua duoc cai dat!"
    exit 1
fi

# Tao moi truong ao .venv neu chua co
if [ ! -d ".venv" ]; then
    echo "[+] Dang tao moi truong ao..."
    python3 -m venv .venv
fi

# Kich hoat
source .venv/bin/activate

# Nâng cap pip va cai dat
echo "[+] Dang cai dat thu vien..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Chay Streamlit
echo "[+] Dang khoi chay ung dung..."
streamlit run app.py
