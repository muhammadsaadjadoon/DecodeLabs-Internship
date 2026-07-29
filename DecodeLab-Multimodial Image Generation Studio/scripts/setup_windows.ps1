$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Set-Location (Join-Path $Root "backend")
if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

Write-Host "Setup complete. Add your API credentials to the root .env file." -ForegroundColor Green
