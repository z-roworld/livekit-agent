@echo off
REM LiveKit Agent Deployment Script for Windows
REM This script automates the deployment process

echo 🚀 Starting LiveKit Agent Deployment...

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please create a .env file with your API keys:
    echo.
    echo LIVEKIT_URL=your_livekit_url_here
    echo LIVEKIT_API_KEY=your_livekit_api_key_here
    echo LIVEKIT_API_SECRET=your_livekit_api_secret_here
    echo ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
    echo GROQ_API_KEY=your_groq_api_key_here
    echo DEEPGRAM_API_KEY=your_deepgram_api_key_here
    echo.
    pause
    exit /b 1
)

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker first: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed!
    echo Please install Docker Compose first: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo [INFO] Checking prerequisites...

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo [ERROR] main.py not found!
    pause
    exit /b 1
)

echo [INFO] All prerequisites met!

REM Stop existing containers if running
echo [INFO] Stopping existing containers...
docker-compose down >nul 2>&1

REM Build the Docker image
echo [INFO] Building Docker image...
docker-compose build --no-cache

REM Start the services
echo [INFO] Starting services...
docker-compose up -d

REM Wait for service to be ready
echo [INFO] Waiting for service to be ready...
timeout /t 10 /nobreak >nul

REM Check if service is running
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ❌ Service failed to start!
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
) else (
    echo [INFO] ✅ Deployment successful!
    echo.
    echo 🌐 Service is running at: http://localhost:8000
    echo 📚 API Documentation: http://localhost:8000/docs
    echo 🔍 Health Check: http://localhost:8000/health
    echo.
    echo 📋 Available endpoints:
    echo   POST /create-room?room_name=^<name^>
    echo   POST /join-room (with JSON body)
    echo   POST /generate-user-token?user_identity=^<name^>^&room_name=^<name^>
    echo   POST /leave-room?room_name=^<name^>
    echo   GET /active-rooms
    echo   GET /room-participants/^<room_name^>
    echo.
    echo 📝 To view logs: docker-compose logs -f
    echo 🛑 To stop: docker-compose down
    echo.
    pause
)
