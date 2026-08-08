@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\doctor.py
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python scripts\doctor.py
  ) else (
    where py >nul 2>nul
    if not errorlevel 1 (
      py -3 scripts\doctor.py
    ) else (
      echo Python not found. Run install.bat first, or install Python 3.10+ from https://www.python.org/downloads/
    )
  )
)
set "OVS_RC=%errorlevel%"
call :maybe_pause %*
exit /b %OVS_RC%

:maybe_pause
rem Match /nopause anywhere in the arguments. /c: forces findstr to treat
rem the search string as a literal (a bare "/nopause" would be parsed as
rem an option and never match).
echo %* | findstr /i /c:"/nopause" >nul
if not errorlevel 1 exit /b 0
if defined OVS_NO_PAUSE exit /b 0
if defined CI exit /b 0
pause
exit /b 0
