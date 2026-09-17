# STAIROVER Controller PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " STAIROVER: Hand Gesture Controlled Stair-Climbing Rover" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $rootDir

Write-Host "`n[1/2] Starting Python Gesture Recognition Service on port 8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\gesture-service'; python -u app.py"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting React Mission Control Dashboard on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev"

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " Both subsystems launched!" -ForegroundColor Yellow
Write-Host " Dashboard URL: http://localhost:5173" -ForegroundColor White
Write-Host " API & Video:  http://localhost:8001" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor Cyan
