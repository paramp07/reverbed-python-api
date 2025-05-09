@echo off
echo ===== Reverbed API Server with YouTube Search =====

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.6 or higher.
    exit /b 1
)

echo Checking pip installation...
pip --version
if %ERRORLEVEL% NEQ 0 (
    echo pip is not installed or not in PATH.
    exit /b 1
)

echo Checking yt-dlp installation...
where yt-dlp
if %ERRORLEVEL% NEQ 0 (
    echo Installing yt-dlp...
    pip install -U yt-dlp
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install yt-dlp.
        exit /b 1
    )
)

echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    exit /b 1
)

echo Creating necessary directories...
mkdir "%USERPROFILE%\reverbed_app_data\uploads" 2>nul
mkdir "%USERPROFILE%\reverbed_app_data\outputs" 2>nul
mkdir "%USERPROFILE%\reverbed_app_data\temp" 2>nul

echo Starting FastAPI server...
echo Server will be available at http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
