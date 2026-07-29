@echo off
setlocal
cd /d "%~dp0..\backend"

if not exist ".venv\Scripts\activate.bat" (
  echo Virtual environment not found. Run scripts\setup_windows.bat first.
  exit /b 1
)

call .venv\Scripts\activate.bat
uvicorn main:app --reload --host 127.0.0.1 --port 8000
endlocal
