@echo off
setlocal
rem Car Damage AI: installs what is missing, then starts http://localhost:8000
cd /d "%~dp0"
set "LOG=%~dp0setup-log.txt"
set "CHECK=import fastapi, uvicorn, PIL, ultralytics"
echo.
echo  Car Damage AI
echo  =============
echo.

rem --- 1. Python -------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 goto :no_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto :old_python

rem --- 2. Virtual environment ------------------------------------------------
if exist ".venv\Scripts\python.exe" goto :have_venv
echo  Creating the Python environment in backend\.venv ...
python -m venv .venv
if errorlevel 1 goto :fail
:have_venv

rem --- 3. Packages: installed if any are missing, which also repairs an interrupted install
".venv\Scripts\python.exe" -c "%CHECK%" >nul 2>nul
if not errorlevel 1 goto :have_packages
echo  Installing FastAPI, ultralytics and PyTorch, about 300 MB.
echo  The first time this takes 5 to 15 minutes. Keep this window open.
echo.
".venv\Scripts\python.exe" -m pip install --upgrade pip --log "%LOG%"
".venv\Scripts\python.exe" -m pip install -r requirements.txt --prefer-binary --timeout 120 --retries 10 --log "%LOG%"
if errorlevel 1 goto :install_failed
".venv\Scripts\python.exe" -c "%CHECK%" 2>>"%LOG%"
if errorlevel 1 goto :install_failed
echo.
echo  Packages installed.
:have_packages

rem --- 4. Model weights ------------------------------------------------------
if exist "models\car_damage_yolo11n_improved.pt" goto :have_model
echo.
echo  Model weights not found: backend\models\car_damage_yolo11n_improved.pt
echo  Copy them from Google Drive: MyDrive\Car_Damage_AI\models\
echo  The app will open, but detection stays off until the file is there.
echo.
:have_model

rem --- 5. Check the app loads, then start it --------------------------------
".venv\Scripts\python.exe" -c "import app.main" 2>"%~dp0startup-error.txt"
if errorlevel 1 goto :app_failed
del "%~dp0startup-error.txt" >nul 2>nul

echo.
echo  Starting. Your browser opens http://localhost:8000 in a few seconds.
echo  Keep this window open while you use the app. Press Ctrl+C to stop.
echo.
start "" /min powershell -NoProfile -Command "Start-Sleep -Seconds 8; Start-Process 'http://localhost:8000'"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto :fail
goto :eof

:no_python
echo  Python was not found. Install Python 3.12 from https://www.python.org/downloads/
echo  and tick "Add python.exe to PATH" in the installer. Then run this file again.
goto :fail

:old_python
echo  This app needs Python 3.10 or newer. Install Python 3.12 from https://www.python.org/downloads/
goto :fail

:install_failed
echo.
echo  The package install did not finish. Details are in backend\setup-log.txt
echo  Check the internet connection and run this file again: it carries on from where it stopped.
goto :fail

:app_failed
echo  The app could not start:
type "%~dp0startup-error.txt"
goto :fail

:fail
echo.
echo  Something went wrong. Take a screenshot of this window if you need help.
pause
exit /b 1
