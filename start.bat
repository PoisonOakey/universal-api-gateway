@echo off
echo ==================================================
echo   Starting Universal API Gateway (Easy Mode)
echo ==================================================
echo.

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    echo.
    pause
    exit /b
)

echo [1/2] Building the container and starting the background service...
docker-compose up -d --build

echo.
echo [2/2] Success! The Gateway is now running.
echo.
echo You can access the API documentation at:
echo http://localhost:30000/docs
echo.
echo To stop the API, run this script again or close Docker Desktop.
echo ==================================================
pause
