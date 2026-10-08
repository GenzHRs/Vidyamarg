# Start VidyamargAI Backend and Frontend
$root = $PSScriptRoot

Write-Host "Starting VidyamargAI..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm.cmd run dev"

Write-Host "Services started:" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
