@echo off
setlocal
cd /d "%~dp0"

py -3.11 -m pip install --upgrade pip
if errorlevel 1 goto :error
py -3.11 -m pip install -r requirements-dev.txt
if errorlevel 1 goto :error
py -3.11 -m pytest -m "not integration"
if errorlevel 1 goto :error
py -3.11 -m PyInstaller --noconfirm --clean --onefile --windowed --name "kDrive-Link-Manager" --paths src run_app.py
if errorlevel 1 goto :error

echo.
echo Build complete: dist\kDrive-Link-Manager.exe
exit /b 0

:error
echo.
echo Build failed. Review the messages above.
exit /b 1

