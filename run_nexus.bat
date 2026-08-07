@echo off
echo ==========================================
echo Starting Nexus ERP - The Ultimate AI Suite
echo ==========================================

echo Installing dependencies...
pip install -r requirements.txt --no-warn-script-location

echo Starting Web Server...
python -m uvicorn main:app --reload --port 8000

pause
