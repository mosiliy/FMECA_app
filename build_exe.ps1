# Сборка FMECA в .exe (PowerShell)
Set-Location $PSScriptRoot

Write-Host "=== FMECA: сборка .exe ===" -ForegroundColor Cyan

pip install -r requirements.txt -r requirements-build.txt -q
if ($LASTEXITCODE -ne 0) { exit 1 }

pyinstaller fmeca_app.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "Готово: dist\FMECA_Analysis\FMECA_Analysis.exe" -ForegroundColor Green
Write-Host "Распространяйте всю папку dist\FMECA_Analysis" -ForegroundColor Yellow
