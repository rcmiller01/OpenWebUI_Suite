@echo off
REM Policy Guardrails Service Startup Script for Windows

echo Starting Policy Guardrails Service...

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%~dp0src

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start the service
echo Starting FastAPI server on port 8113...
uvicorn src.app:app --host 0.0.0.0 --port 8113 --reload
