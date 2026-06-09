# Mystic Hub - One-click launcher (backend + frontend)
# Run: .\start.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Mystic Hub - Starting up..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Backend (FastAPI :8000)
Write-Host "[1/2] Starting backend API (port 8000)..." -ForegroundColor Yellow
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv not found at $venvPython" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}
$backend = Start-Process -FilePath $venvPython -ArgumentList "-m","uvicorn","server.main:app","--host","0.0.0.0","--port","8000","--reload" -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 2

# Frontend (Vite :5173)
Write-Host "[2/2] Starting frontend (port 5173)..." -ForegroundColor Yellow
Set-Location (Join-Path $root "apps\web")
$frontend = Start-Process -FilePath "npm" -ArgumentList "run","dev" -PassThru -WindowStyle Minimized
Set-Location $root

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Almanac  : http://localhost:5173/almanac" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop, or close the terminal windows." -ForegroundColor DarkYellow
Write-Host "Backend PID: $($backend.Id) | Frontend PID: $($frontend.Id)" -ForegroundColor DarkYellow

# Keep running, watch child processes
try {
    while ($true) {
        if ($backend.HasExited) {
            Write-Host "Backend exited (code: $($backend.ExitCode))" -ForegroundColor Red
            break
        }
        if ($frontend.HasExited) {
            Write-Host "Frontend exited (code: $($frontend.ExitCode))" -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All stopped." -ForegroundColor Green
}
