@echo off
chcp 65001 >nul
cls
echo ============================================
echo TikTok Downloader
echo ============================================
echo.
echo Starting server...
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start Flask application
echo Backend started at http://localhost:5000
echo.
echo Open index.html in your browser to access the interface
echo.
echo Press Ctrl+C to stop
echo ============================================
echo.

python app.py