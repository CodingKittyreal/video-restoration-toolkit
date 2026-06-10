@echo off
title ProPainter Watermark Remover
cd /d "%~dp0"
echo.
echo  ========================================
echo    ProPainter Watermark Remover v1.2
echo  ========================================
echo.
echo  Starting application...
echo.
".venv\Scripts\python.exe" app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo  [ERROR] Application crashed. Check the error above.
    echo.
    pause
)
