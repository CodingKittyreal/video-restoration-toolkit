@echo off
title ProPainter Watermark Remover — Setup
cd /d "%~dp0"
echo.
echo  ========================================
echo    ProPainter Watermark Remover — Setup
echo  ========================================
echo.

echo  [1/4] Creating Python virtual environment...
py -3.12 -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Python 3.12 not found. Please install Python 3.12.
    pause
    exit /b 1
)
echo  Done.
echo.

echo  [2/4] Installing PyTorch with CUDA 12.8...
".venv\Scripts\pip.exe" install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Failed to install PyTorch. Check your internet connection.
    pause
    exit /b 1
)
echo  Done.
echo.

echo  [3/4] Installing dependencies...
".venv\Scripts\pip.exe" install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  Done.
echo.

echo  [4/4] Cloning ProPainter repository...
if not exist "ProPainter" (
    git clone https://github.com/sczhou/ProPainter.git ProPainter
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Failed to clone ProPainter. Check your internet connection and git installation.
        pause
        exit /b 1
    )
) else (
    echo  ProPainter already exists, skipping clone.
)
echo  Done.
echo.

echo  ========================================
echo    Setup complete! Run 'run.bat' to start
echo  ========================================
echo.
pause
