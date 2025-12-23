@echo off
REM ============================================================================
REM LOCAL FLASK DEPLOYMENT SCRIPT (Windows)
REM ============================================================================
REM This script sets up and runs the Flask application natively (without Docker)
REM Author: AI Assistant
REM ============================================================================

echo ==================================================
echo   Homework 1 - Local Flask Deployment (Windows)
echo ==================================================
echo.

REM ============================================================================
REM STEP 1: Environment Setup
REM ============================================================================
echo [1/6] Checking environment setup...

if not exist .env (
    if exist .env.local (
        echo   -^> Copying .env.local to .env
        copy .env.local .env >nul
    ) else (
        echo   X ERROR: No .env or .env.local file found!
        echo     Create .env.local with your configuration first.
        exit /b 1
    )
) else (
    echo   √ .env file found
)

REM ============================================================================
REM STEP 2: Python Environment
REM ============================================================================
echo.
echo [2/6] Checking Python environment...

if not exist venv (
    echo   -^> Creating virtual environment...
    python -m venv venv
    echo   √ Virtual environment created
) else (
    echo   √ Virtual environment exists
)

echo   -^> Activating virtual environment...
call venv\Scripts\activate.bat

REM ============================================================================
REM STEP 3: Install Dependencies
REM ============================================================================
echo.
echo [3/6] Installing Python dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
echo   √ Dependencies installed

REM ============================================================================
REM STEP 4: PostgreSQL Check
REM ============================================================================
echo.
echo [4/6] Checking PostgreSQL...

where psql >nul 2>nul
if errorlevel 1 (
    echo   X ERROR: PostgreSQL is not installed or not in PATH!
    echo.
    echo   Install PostgreSQL:
    echo     - Download from https://www.postgresql.org/download/windows/
    echo     - Or use: winget install PostgreSQL.PostgreSQL
    echo.
    pause
    exit /b 1
)

pg_isready >nul 2>nul
if errorlevel 1 (
    echo   ! WARNING: PostgreSQL service may not be running
    echo.
    echo   Start PostgreSQL:
    echo     - Open Services (services.msc)
    echo     - Find "postgresql" service
    echo     - Click "Start"
    echo.
    set /p continue="  Do you want to continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo   √ PostgreSQL is running
)

REM ============================================================================
REM STEP 5: Database Setup
REM ============================================================================
echo.
echo [5/6] Setting up database...

REM Load DATABASE_NAME from .env
for /f "tokens=2 delims==" %%a in ('findstr /r "^DATABASE_NAME=" .env') do set DATABASE_NAME=%%a
for /f "tokens=2 delims==" %%a in ('findstr /r "^DATABASE_USER=" .env') do set DATABASE_USER=%%a

if "%DATABASE_NAME%"=="" set DATABASE_NAME=homework1_local
if "%DATABASE_USER%"=="" set DATABASE_USER=postgres

REM Check if database exists
psql -U %DATABASE_USER% -lqt | findstr /c:"%DATABASE_NAME%" >nul 2>nul
if errorlevel 1 (
    echo   -^> Creating database: %DATABASE_NAME%
    createdb -U %DATABASE_USER% %DATABASE_NAME% >nul 2>nul
    if errorlevel 1 (
        echo   i Database creation may require different credentials
        echo     Run manually: createdb -U postgres %DATABASE_NAME%
    ) else (
        echo   √ Database created
    )
) else (
    echo   √ Database exists: %DATABASE_NAME%
)

REM ============================================================================
REM STEP 6: Start Flask Application
REM ============================================================================
echo.
echo [6/6] Starting Flask application...
echo.

REM Load FLASK_HOST and FLASK_PORT from .env
for /f "tokens=2 delims==" %%a in ('findstr /r "^FLASK_HOST=" .env') do set FLASK_HOST=%%a
for /f "tokens=2 delims==" %%a in ('findstr /r "^FLASK_PORT=" .env') do set FLASK_PORT=%%a

if "%FLASK_HOST%"=="" set FLASK_HOST=127.0.0.1
if "%FLASK_PORT%"=="" set FLASK_PORT=8080

echo ==================================================
echo   Application starting on http://%FLASK_HOST%:%FLASK_PORT%
echo ==================================================
echo.
echo   Press Ctrl+C to stop the server
echo.

REM Run Flask with hot reload enabled
python app.py

pause
