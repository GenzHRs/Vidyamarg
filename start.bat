@echo off
echo Starting VidyamargAI Backend and Frontend...
start "VidyamargAI Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
start "VidyamargAI Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"
echo.
echo Both services have been started in separate windows:
echo - Frontend: http://localhost:3000
echo - Backend:  http://127.0.0.1:8000
echo - API Docs: http://127.0.0.1:8000/docs
