@echo off
chcp 65001 >nul
echo ============================================
echo TikTok Downloader - Installation
echo ============================================
echo.

:: Python check
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to add Python to PATH
    pause
    exit /b 1
)
python --version
echo.

:: Creating virtual environment
echo [2/4] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

:: Activation and installing dependencies
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

:: yt-dlp check
echo [4/4] Checking yt-dlp...
if exist "C:\Tools\VidDownload\yt-dlp.exe" (
    echo yt-dlp found: C:\Tools\VidDownload\yt-dlp.exe
    C:\Tools\VidDownload\yt-dlp.exe --version
) else (
    echo [WARNING] yt-dlp not found at C:\Tools\VidDownload\yt-dlp.exe
    echo.
    echo Download yt-dlp:
    echo 1. Go to https://github.com/yt-dlp/yt-dlp/releases
    echo 2. Download yt-dlp.exe
    echo 3. Create folder C:\Tools\VidDownload\
    echo 4. Place yt-dlp.exe in this folder
    echo.
)
echo.

:: Creating folder on D: drive
echo Creating folder D:\materials...
if not exist "D:\materials" (
    mkdir "D:\materials"
    echo Folder created
) else (
    echo Folder already exists
)
echo.

echo ============================================
echo Installation finished!
echo ============================================
echo.
echo To run the application, use: start.bat
echo.
pause