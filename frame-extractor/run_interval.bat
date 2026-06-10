@echo off
title Interval Frame Extractor
cd /d "%~dp0"
echo Launching Interval Frame Extractor...
py interval_extractor.py
if %errorlevel% neq 0 (
    echo.
    echo Script failed with error code %errorlevel%
    pause
)
