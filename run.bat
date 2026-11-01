@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
"%PYTHON%" tools\run_quotes.py --delay 2.5 --max-requests 100 %*
set "STATUS=%ERRORLEVEL%"
echo.
if not "%STATUS%"=="0" echo O processo terminou com codigo %STATUS%.
pause
exit /b %STATUS%
