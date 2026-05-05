@echo off
echo ===================================================
echo     Starting Adaptive Review Scheduling System 
echo ===================================================

echo.
echo Starting FastAPI Backend...
start cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload"

echo.
echo Starting Vite Frontend...
start cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo     Servers are starting in separate windows!
echo     Frontend: http://localhost:5173
echo     Backend:  http://127.0.0.1:8000/docs
echo ===================================================
pause
