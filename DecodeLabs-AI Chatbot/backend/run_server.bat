@echo off
setlocal
if not exist .env (
  copy .env.example .env >nul
)
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
