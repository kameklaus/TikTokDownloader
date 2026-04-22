@echo off
chcp 65001 >nul
cls
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     TikTok Downloader - System Diagnostics                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set ERROR_COUNT=0

:: Check 1: Python
echo [1/7] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     ❌ Python NOT FOUND
    echo     Install: https://www.python.org/downloads/
    set /a ERROR_COUNT+=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo     ✅ Python installed: %PYTHON_VER%
)
echo.

:: Check 2: pip
echo [2/7] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     ❌ pip NOT FOUND
    set /a ERROR_COUNT+=1
) else (
    echo     ✅ pip installed
)
echo.

:: Check 3: Virtual Environment
echo [3/7] Checking virtual environment...
if exist "venv\" (
    echo     ✅ Virtual environment exists
) else (
    echo     ❌ Virtual environment NOT CREATED
    echo     Run: install.bat
    set /a ERROR_COUNT+=1
)
echo.

:: Check 4: yt-dlp
echo [4/7] Checking yt-dlp...
if exist "C:\Tools\VidDownload\yt-dlp.exe" (
    echo     ✅ yt-dlp found
    for /f "tokens=*" %%i in ('C:\Tools\VidDownload\yt-dlp.exe --version 2^>^&1') do (
        echo     📦 Version: %%i
        goto :ytdlp_found
    )
    :ytdlp_found
) else (
    echo     ❌ yt-dlp NOT FOUND
    echo     Path: C:\Tools\VidDownload\yt-dlp.exe
    echo     Download: https://github.com/yt-dlp/yt-dlp/releases
    set /a ERROR_COUNT+=1
)
echo.

:: Check 5: Disk D
echo [5/7] Checking D: drive...
if exist "D:\" (
    echo     ✅ Drive D is accessible
    if exist "D:\materials\" (
        echo     ✅ Folder D:\materials exists
    ) else (
        echo     ⚠️  Folder D:\materials not created
        echo     Will be created automatically
    )
) else (
    echo     ❌ Drive D NOT FOUND
    echo     Change path in config.py:
    echo     MATERIALS_PATH = r"C:\materials"
    set /a ERROR_COUNT+=1
)
echo.

:: Check 6: Project Files
echo [6/7] Checking project files...
set FILE_COUNT=0

if exist "app.py" (
    set /a FILE_COUNT+=1
) else (
    echo     ❌ app.py not found
)

if exist "config.py" (
    set /a FILE_COUNT+=1
) else (
    echo     ❌ config.py not found
)

if exist "index.html" (
    set /a FILE_COUNT+=1
) else (
    echo     ❌ index.html not found
)

if exist "requirements.txt" (
    set /a FILE_COUNT+=1
) else (
    echo     ❌ requirements.txt not found
)

if %FILE_COUNT% equ 4 (
    echo     ✅ All project files are in place
) else (
    echo     ❌ Missing project files: %FILE_COUNT%/4
    set /a ERROR_COUNT+=1
)
echo.

:: Check 7: Python Dependencies
echo [7/7] Checking Python dependencies...
if exist "venv\" (
    call venv\Scripts\activate.bat >nul 2>&1
    
    pip show Flask >nul 2>&1
    if %errorlevel% equ 0 (
        echo     ✅ Flask is installed
    ) else (
        echo     ❌ Flask is NOT installed
        set /a ERROR_COUNT+=1
    )
    
    pip show Flask-CORS >nul 2>&1
    if %errorlevel% equ 0 (
        echo     ✅ Flask-CORS is installed
    ) else (
        echo     ❌ Flask-CORS is NOT installed
        set /a ERROR_COUNT+=1
    )
    
    call deactivate >nul 2>&1
) else (
    echo     ⚠️  Cannot check (no venv)
)
echo.

:: Summary
echo ══════════════════════════════════════════════════════════════
echo.
if %ERROR_COUNT% equ 0 (
    color 0A
    echo ✅✅✅ ALL CHECKS PASSED! ✅✅✅
    echo.
    echo System is ready to work!
    echo Run: start.bat
) else (
    color 0C
    echo ❌ ERRORS DETECTED: %ERROR_COUNT%
    echo.
    echo Fix the errors before starting!
    echo Read: INSTALLATION_INSTRUCTIONS.md
)
echo.
echo ══════════════════════════════════════════════════════════════
echo.

:: Additional Information
echo 📋 Additional information:
echo.
echo    Current folder: %CD%
echo    Computer name: %COMPUTERNAME%
echo    User: %USERNAME%
echo.
echo ══════════════════════════════════════════════════════════════
echo.

pause