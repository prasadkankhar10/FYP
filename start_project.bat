@echo off
echo ===================================================
echo     Starting Adaptive Review Scheduling System 
echo ===================================================

echo Starting FastAPI Backend...
start cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Starting Vite Frontend...
start cmd /k "cd frontend && npm run dev"

echo Waiting for servers to initialize...
timeout /t 3 >nul

echo Opening browser...
start http://localhost:5173

exit
