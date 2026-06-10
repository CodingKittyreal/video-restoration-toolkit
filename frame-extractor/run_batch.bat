@echo off
title Batch Last Frame Extractor
cd /d "%~dp0"
echo Launching Batch Last Frame Extractor...
py batch_last_frame.py
if %errorlevel% neq 0 (
    echo.
    echo Script failed with error code %errorlevel%
    pause
)
