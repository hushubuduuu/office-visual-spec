@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\doctor.py
) else (
  python scripts\doctor.py
)
set "OVS_RC=%errorlevel%"
call :maybe_pause %*
exit /b %OVS_RC%

:maybe_pause
if /i "%~1"=="/nopause" exit /b 0
if defined OVS_NO_PAUSE exit /b 0
if defined CI exit /b 0
pause
exit /b 0
