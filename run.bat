@echo off
REM Note: This script must be run in CMD, not PowerShell
REM If in PowerShell, use: cmd /c .\run.bat
chcp 65001 >nul
echo ==========================================
echo FIT Running Data Analyzer
echo Development Environment
echo ==========================================
echo.

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if virtual environment exists
echo [Step 1/4] Checking virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    echo           Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo           Virtual environment created
) else (
    echo           Virtual environment exists
)

REM Activate virtual environment
echo.
echo [Step 2/4] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat

REM Upgrade pip and install dependencies
python -m pip install --upgrade pip -q
pip install -r backend\requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo           Dependencies installed

REM Create data directory
echo.
echo [Step 3/4] Checking data directory...
if not exist "data\activities" (
    mkdir data\activities
    echo           Data directory created
) else (
    echo           Data directory exists
)

if not exist "data\index.json" (
    echo {"activities": [], "updated_at": ""} > data\index.json
)

REM Start server
echo.
echo [Step 4/4] Starting server...
echo.
echo ==========================================
echo Starting server...
echo Access at: http://127.0.0.1:8082
echo Press Ctrl+C to stop server
echo ==========================================
echo.

REM Start FastAPI using virtual environment Python in foreground
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8082 --reload

