@echo off
setlocal
title NEXORA AI Launcher
cd /d "%~dp0"

echo.
echo ==========================================
echo          NEXORA AI - LOCAL STARTUP
echo ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found. Install Python 3.10 or newer and reopen this file.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm was not found. Install Node.js 20.19+ or 22.12+ and reopen this file.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Creating the Python virtual environment...
    python -m venv venv
    if errorlevel 1 goto setup_failed
)

if not exist "venv\Scripts\python.exe" goto setup_failed

if not exist "venv\.nexora-deps-installed" (
    echo Installing backend dependencies for the first run...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto pip_failed
    type nul > "venv\.nexora-deps-installed"
)

if not exist "frontend\node_modules\vite\bin\vite.js" (
    echo Installing frontend dependencies for the first run...
    pushd frontend
    call npm install
    if errorlevel 1 goto npm_failed
    popd
)

if not exist "frontend\.env" (
    if exist "frontend\.env.example" copy /Y "frontend\.env.example" "frontend\.env" >nul
)

echo.
echo Checking the backend...
curl.exe -fsS --max-time 2 "http://127.0.0.1:8000/api/health" >nul 2>&1
if errorlevel 1 (
    echo Starting backend in a separate window...
    start "NEXORA Backend" cmd /k "cd /d ""%~dp0"" && ""%~dp0venv\Scripts\python.exe"" main.py"
    set /a attempts=0
    goto wait_backend
)

:backend_ready
echo Backend is ready.

echo.
echo Checking the frontend...
curl.exe -fsS --max-time 2 "http://127.0.0.1:5173" >nul 2>&1
if errorlevel 1 (
    echo Starting frontend in a separate window...
    start "NEXORA Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"
    set /a attempts=0
    goto wait_frontend
)

:frontend_ready
echo Frontend is ready.
echo.
echo NEXORA AI is running at:
echo http://localhost:5173
echo.
start "" "http://localhost:5173"
echo You can close this launcher window. Keep the Backend and Frontend windows open.
pause
exit /b 0

:wait_backend
timeout /t 2 /nobreak >nul
curl.exe -fsS --max-time 2 "http://127.0.0.1:8000/api/health" >nul 2>&1
if not errorlevel 1 goto backend_ready
set /a attempts+=1
if %attempts% LSS 60 goto wait_backend
echo.
echo ERROR: Backend did not become ready within 2 minutes.
echo Check the NEXORA Backend window for the Python error.
pause
exit /b 1

:wait_frontend
timeout /t 2 /nobreak >nul
curl.exe -fsS --max-time 2 "http://127.0.0.1:5173" >nul 2>&1
if not errorlevel 1 goto frontend_ready
set /a attempts+=1
if %attempts% LSS 45 goto wait_frontend
echo.
echo ERROR: Frontend did not become ready within 90 seconds.
echo Check the NEXORA Frontend window for the Vite or Node.js error.
pause
exit /b 1

:setup_failed
echo.
echo ERROR: Could not create the Python virtual environment.
echo Check that Python is installed and available in PATH.
pause
exit /b 1

:pip_failed
echo.
echo ERROR: Backend dependency installation failed.
echo Check the pip output above, then run START-NEXORA.bat again.
pause
exit /b 1

:npm_failed
popd
echo.
echo ERROR: Frontend dependency installation failed.
echo Check the npm output above, then run START-NEXORA.bat again.
pause
exit /b 1
