# Setup venv and install all backend dependencies.
# Run from project root: .\scripts\setup_venv.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$RequirementsPath = Join-Path $ProjectRoot "backend\requirements.txt"

Write-Host "Project root: $ProjectRoot" -ForegroundColor Cyan

# Create venv if missing
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating venv at $VenvPath..." -ForegroundColor Yellow
    python -m venv $VenvPath
} else {
    Write-Host "Venv already exists at $VenvPath" -ForegroundColor Green
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\pip.exe"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip

# Install requirements
Write-Host "Installing backend requirements..." -ForegroundColor Yellow
& $PipExe install -r $RequirementsPath

# Verify env
Write-Host "Running verify_env.py..." -ForegroundColor Yellow
$env:PYTHONPATH = Join-Path $ProjectRoot "backend"
& $PythonExe (Join-Path $ProjectRoot "scripts\verify_env.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "verify_env failed. Check errors above." -ForegroundColor Red
    exit 1
}

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
