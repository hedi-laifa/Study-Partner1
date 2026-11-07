@echo off
echo Starting StudyMate Full Stack...
start "StudyMate Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "StudyMate Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 >nul
start http://localhost:5173/login
echo Application launched!
