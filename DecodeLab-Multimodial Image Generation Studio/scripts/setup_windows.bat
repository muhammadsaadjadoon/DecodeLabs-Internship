@echo off
setlocal
cd /d "%~dp0.."

if not exist ".env" copy ".env.example" ".env" >nul

cd backend
if not exist ".venv" py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo.
echo Setup complete. Add your API credentials to the root .env file.
endlocal
