#!/bin/bash

# LiveKit Agent Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🚀 Starting LiveKit Agent Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "LIVEKIT_URL=your_livekit_url_here"
    echo "LIVEKIT_API_KEY=your_livekit_api_key_here"
    echo "LIVEKIT_API_SECRET=your_livekit_api_secret_here"
    echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here"
    echo "GROQ_API_KEY=your_groq_api_key_here"
    echo "DEEPGRAM_API_KEY=your_deepgram_api_key_here"
    echo ""
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

print_status "Checking prerequisites..."

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    print_error "main.py not found!"
    exit 1
fi

print_status "All prerequisites met!"

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build the Docker image
print_status "Building Docker image..."
docker-compose build --no-cache

# Start the services
print_status "Starting services..."
docker-compose up -d

# Wait for service to be ready
print_status "Waiting for service to be ready..."
sleep 10

# Check if service is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Deployment successful!"
    echo ""
    echo "🌐 Service is running at: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo "📋 Available endpoints:"
    echo "  POST /create-room?room_name=<name>"
    echo "  POST /join-room (with JSON body)"
    echo "  POST /generate-user-token?user_identity=<name>&room_name=<name>"
    echo "  POST /leave-room?room_name=<name>"
    echo "  GET /active-rooms"
    echo "  GET /room-participants/<room_name>"
    echo ""
    echo "📝 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
else
    print_error "❌ Service failed to start!"
    echo "Check logs with: docker-compose logs"
    exit 1
fi
