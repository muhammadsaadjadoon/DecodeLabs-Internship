$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
Set-Location $Backend

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    throw "Virtual environment not found. Run scripts\setup_windows.ps1 first."
}

. .\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
