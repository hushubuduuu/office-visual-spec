@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Please install Python 3.10 or newer first.
  echo   Windows: winget install Python.Python.3.12
  echo   or download from https://www.python.org/downloads/
  echo Then run this script again.
  call :maybe_pause %*
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    call :maybe_pause %*
    exit /b 1
  )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if defined OVS_PIP_INDEX (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt --index-url "%OVS_PIP_INDEX%"
) else (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt --timeout 30
)
if errorlevel 1 if not defined OVS_PIP_INDEX (
  echo First attempt failed. Retrying with Tsinghua mirror...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt --timeout 60 --index-url https://pypi.tuna.tsinghua.edu.cn/simple
)
if errorlevel 1 (
  echo Dependency installation failed. See messages above.
  call :maybe_pause %*
  exit /b 1
)

echo Setup complete. Running environment doctor...
".venv\Scripts\python.exe" scripts\doctor.py
set "OVS_RC=%errorlevel%"
call :maybe_pause %*
exit /b %OVS_RC%

:maybe_pause
if /i "%~1"=="/nopause" exit /b 0
if defined OVS_NO_PAUSE exit /b 0
if defined CI exit /b 0
pause
exit /b 0
