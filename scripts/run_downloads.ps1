# Run vision dataset downloads one at a time with live terminal output.
# Usage: From project root, run: .\scripts\run_downloads.ps1
# Or: pwsh -File scripts/run_downloads.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "=== Download 1/2: chest_xray ===" -ForegroundColor Cyan
python -u scripts/download_vision_weights.py chest_xray
if ($LASTEXITCODE -ne 0) {
    Write-Host "Chest X-ray download failed (exit $LASTEXITCODE). Fix and re-run." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== Download 2/2: skin_lesion ===" -ForegroundColor Cyan
python -u scripts/download_vision_weights.py skin_lesion
if ($LASTEXITCODE -ne 0) {
    Write-Host "Skin lesion download failed (exit $LASTEXITCODE). Fix and re-run." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "All downloads complete. Next: python scripts/train_vision_models.py" -ForegroundColor Green
