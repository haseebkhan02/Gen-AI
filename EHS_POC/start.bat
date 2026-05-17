@echo off
REM start.bat - Start EHS AI POC on Windows

echo Starting EHS AI POC...

if not exist .env (
    echo Please Create .env and edit .env and add your GROQ_API_KEY
    echo Get a free key at: https://console.groq.com
    pause
)

echo Starting FastAPI backend on port 8000...
start "EHS Backend" cmd /k "cd backend && python main.py"

timeout /t 4 /nobreak > nul

echo Starting Streamlit frontend on port 8501...
start "EHS Frontend" cmd /k "cd frontend && streamlit run app.py"


echo.
echo  EHS AI POC is running!
echo    Frontend: http://localhost:8501
echo    Backend API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
pause
