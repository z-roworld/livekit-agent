# LiveKit Multi-Agent Meeting System

A sophisticated multi-agent meeting system built with LiveKit, featuring intelligent agents that can participate in voice and video meetings with turn-taking capabilities.

## 🎯 Features

- **Multi-Agent System**: Priya (Marketing Manager) and Alex (Technical Lead) agents
- **Intelligent Turn-Taking**: Agents respond only when addressed by name
- **Voice & Chat Support**: Both voice and text-based interactions
- **Flexible Agent Selection**: Choose which agents to include in meetings
- **Auto-Cleanup**: Automatic room deletion after specified duration
- **RESTful API**: Complete API for room management and agent control

## 🏗️ Architecture

- **FastAPI Backend**: RESTful API server with WebSocket support
- **LiveKit Integration**: Real-time voice/video communication
- **Multi-Process Agents**: Each agent runs in separate processes
- **Plugin-Based**: Modular audio processing (STT, TTS, VAD)

## 📋 Prerequisites

- Python 3.11 or higher
- LiveKit Server (self-hosted or cloud)
- API keys for:
  - LiveKit
  - ElevenLabs (TTS)
  - Groq (LLM)
  - Deepgram (STT)

## 🚀 Quick Setup

### 1. Clone and Setup Environment
```bash
git clone <your-repo>
cd livekit-agent
python -m venv livekit-env
source livekit-env/bin/activate  # On Windows: .\livekit-env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file:
```env
# LiveKit Configuration
LIVEKIT_URL=your_livekit_url_here
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here

# ElevenLabs Configuration (TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Groq Configuration (LLM)
GROQ_API_KEY=your_groq_api_key_here

# Deepgram Configuration (STT)
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

### 3. Start the Server
```bash
python main.py
```

The server will start on `http://localhost:8000`

## 📚 API Reference

### Core Endpoints

#### Create Room
```http
POST /create-room?room_name=my-meeting
```

#### Join Room with Agents
```http
POST /join-room
Content-Type: application/json

{
  "room_name": "my-meeting",
  "agents": ["priya", "alex"],
  "auto_cleanup_minutes": 15
}
```

#### Generate User Token
```http
POST /generate-user-token?user_identity=john&room_name=my-meeting
```

#### Leave Room
```http
POST /leave-room?room_name=my-meeting
```

#### Health Check
```http
GET /health
```

#### List Active Rooms
```http
GET /active-rooms
```

#### Get Room Participants
```http
GET /room-participants/{room_name}
```

## 🤖 Agent Configuration

### Agent Selection Options
- `["priya"]` - Only Priya (Marketing Manager)
- `["alex"]` - Only Alex (Technical Lead)  
- `["priya", "alex"]` - Both agents (default)
- `[]` - No agents (empty meeting)

### Agent Personalities

#### Priya (Marketing Manager)
- **Role**: Senior Manager of Growth Marketing
- **Voice**: Professional, warm but authoritative
- **Behavior**: Leads meetings, responds to general questions
- **Specialty**: Marketing strategy, business analysis

#### Alex (Technical Lead)
- **Role**: Technical Lead and Software Architect
- **Voice**: Calm, methodical, slightly technical
- **Behavior**: Only responds when called by name "Alex"
- **Specialty**: Technical questions, system architecture

## 🎮 Usage Examples

### Frontend Integration

#### Start Meeting with Both Agents
```javascript
const response = await fetch('http://localhost:8000/join-room', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        room_name: "meeting-" + Date.now(),
        agents: ["priya", "alex"],
        auto_cleanup_minutes: 30
    })
});
```

#### Start Meeting with Only Priya
```javascript
const response = await fetch('http://localhost:8000/join-room', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        room_name: "marketing-meeting",
        agents: ["priya"]
    })
});
```

#### Get User Token for LiveKit Client
```javascript
const tokenResponse = await fetch(`http://localhost:8000/generate-user-token?user_identity=${userName}&room_name=${roomName}`);
const { token, url, room } = await tokenResponse.json();

// Use with LiveKit client
const room = new LiveKitClient.Room();
await room.connect(url, token);
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t livekit-agent .

# Run container
docker run -p 8000:8000 --env-file .env livekit-agent
```

### Docker Compose
```yaml
version: '3.8'
services:
  livekit-agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

## 📁 Project Structure

```
livekit-agent/
├── main.py                 # FastAPI server with all endpoints
├── agent_runner.py         # Individual agent process runner
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Development

### Running in Development Mode
```bash
# Install development dependencies
pip install -r requirements.txt

# Start with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing API Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Create a room
curl -X POST "http://localhost:8000/create-room?room_name=test-room"

# Join with agents
curl -X POST "http://localhost:8000/join-room" \
  -H "Content-Type: application/json" \
  -d '{"room_name": "test-room", "agents": ["priya"]}'
```

## 🚨 Troubleshooting

### Common Issues

1. **Python Version Error**
   - Ensure you have Python 3.11+ installed
   - Check with: `python --version`

2. **Virtual Environment Issues**
   - Make sure to activate the virtual environment before installing packages
   - On Windows: `.\livekit-env\Scripts\Activate.ps1`

3. **API Key Errors**
   - Verify all API keys are correctly set in the `.env` file
   - Ensure the services are active and have sufficient credits

4. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check that you're in the correct virtual environment

### Logs
- Server logs: Check console output from `main.py`
- Agent logs: Check console output from `agent_runner.py` processes
- LiveKit logs: Check LiveKit server logs

If you encounter issues:
1. Check the error messages carefully
2. Verify your API keys are correct
3. Ensure all dependencies are installed
4. Make sure you're using Python 3.11+

## Features

### Priya Agent
- Senior Manager of Growth Marketing persona
- Uses AssemblyAI for speech-to-text
- Uses Groq for language model
- Uses ElevenLabs for text-to-speech
- Focused on marketing and business analysis

### Zero AI Agent
- General assistant with video and audio capabilities
- Uses Google's real-time model
- Supports noise cancellation
- Handles user context from metadata

## Development

To modify the agents:
1. Edit the respective Python files (`priya.py` or `agent.py`)
2. Update the instructions in the Agent class
3. Modify the plugins as needed
4. Test with your LiveKit room 