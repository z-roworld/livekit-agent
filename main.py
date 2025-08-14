import os
import subprocess
import sys
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from livekit.api import LiveKitAPI, CreateRoomRequest
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
)
from livekit.plugins import silero, deepgram, groq, elevenlabs
import aiohttp
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
    raise EnvironmentError(
        "LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be set in your environment."
    )

# NEW: Use FastAPI's lifespan to manage shared resources
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage shared resources for the application lifetime.
    This is the recommended approach for modern FastAPI apps.
    """
    print("🚀 Initializing shared resources...")
    app.state.http_session = aiohttp.ClientSession()
    app.state.vad = silero.VAD.load()
    app.state.stt = deepgram.STT(http_session=app.state.http_session)
    app.state.llm = groq.LLM(model="llama-3.3-70b-versatile")
    
    # Create TTS instances for each agent voice
    app.state.priya_tts = elevenlabs.TTS(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="ODq5zmih8GrVes37Dizd",  # Priya's voice
        http_session=app.state.http_session,
    )
    app.state.alex_tts = elevenlabs.TTS(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="pNInz6obpgDQGcFmaJgB",  # Alex's voice
        http_session=app.state.http_session,
    )
    print("✅ Shared resources initialized.")
    
    yield  # Application is now running

    print("🔌 Closing shared resources...")
    await app.state.http_session.close()
    print("✅ Shared resources closed.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_livekit_api():
    """Get a new LiveKitAPI instance"""
    return LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

async def run_priya_agent(room_name: str, agent_identity: str, token: str):
    """
    Priya agent with her specific voice and personality
    """
    print(f"🎯 PRIYA STARTING - Room: {room_name}, Identity: {agent_identity}")

    agent = Agent(
        instructions="""
        You are Priya, a Senior Manager of Growth Marketing...
        """
    )
    session = AgentSession(
        vad=app.state.vad,
        stt=app.state.stt,
        llm=app.state.llm,
        tts=app.state.priya_tts,
    )

    room = rtc.Room()
    try:
        print(f"🔗 Priya connecting to room...")
        await room.connect(LIVEKIT_URL, token)
        print(f"✅ Priya connected to room: {room_name}")

        await session.start(agent=agent, room=room)
        print(f"✅ Priya session started")

        await asyncio.sleep(2)
        print(f"👋 Priya sending greeting...")
        await session.generate_reply(
            instructions="Greet the user warmly as Priya, introduce yourself..."
        )
        print(f"🔄 Priya is now active and listening...")

        # FINAL FIX: A simple, universal loop to keep the task alive.
        # It doesn't depend on any specific library version attributes.
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Error in Priya's session: {e}")
        import traceback
        print(f"Priya traceback: {traceback.format_exc()}")
    finally:
        print(f"🚪 Priya disconnecting...")
        await session.aclose()
        await room.disconnect()


async def run_alex_agent(room_name: str, agent_identity: str, token: str):
    """
    Alex agent with his specific voice and personality
    """
    print(f"🔧 ALEX STARTING - Room: {room_name}, Identity: {agent_identity}")

    agent = Agent(
        instructions="""
        You are Alex, a Technical Lead and Software Architect...
        """
    )
    session = AgentSession(
        vad=app.state.vad,
        stt=app.state.stt,
        llm=app.state.llm,
        tts=app.state.alex_tts,
    )

    room = rtc.Room()
    try:
        print(f"🔗 Alex connecting to room...")
        await room.connect(LIVEKIT_URL, token)
        print(f"✅ Alex connected to room: {room_name}")

        await session.start(agent=agent, room=room)
        print(f"✅ Alex session started")
        print(f"🔄 Alex is now active and listening...")

        # FINAL FIX: A simple, universal loop to keep the task alive.
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Error in Alex's session: {e}")
        import traceback
        print(f"Alex traceback: {traceback.format_exc()}")
    finally:
        print(f"🚪 Alex disconnecting...")
        await session.aclose()
        await room.disconnect()
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/create-room")
async def create_room(room_name: str = None):
    if not room_name:
        raise HTTPException(status_code=400, detail="room_name is required")

    try:
        print(f"🏠 Creating room: {room_name}")
        api_instance = await get_livekit_api()
        request = CreateRoomRequest(name=room_name, empty_timeout=300) # Added empty_timeout
        await api_instance.room.create_room(request)
        await api_instance.aclose()
        return {"room_name": room_name}
    except Exception:
        # It's better to check if the room exists first, but this works for now.
        return {"room_name": room_name, "note": "Room might already exist"}

# Define the request model for joining agents
class JoinRoomRequest(BaseModel):
    room_name: str
    agents: List[str] = ["priya", "alex"]  # Default to both agents
    auto_cleanup_minutes: Optional[int] = 15  # Default 15 minutes

@app.post("/join-room")
async def join_room(request: JoinRoomRequest):
    """Join room with selected agents"""
    if not request.room_name:
        raise HTTPException(status_code=400, detail="room_name is required")

    # Validate agent names
    valid_agents = ["priya", "alex"]
    invalid_agents = [agent for agent in request.agents if agent not in valid_agents]
    if invalid_agents:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent names: {invalid_agents}. Valid agents: {valid_agents}"
        )

    print(f"🚀 Setting up agents for room: {request.room_name}")
    print(f"�� Selected agents: {request.agents}")

    # Define agent identities for selected agents only
    agents_to_launch = {
        agent: f"{agent}-agent-{request.room_name}"
        for agent in request.agents
    }

    launched_agents = []
    for agent_name, identity in agents_to_launch.items():
        print(f"🔑 Generating token for {agent_name}...")
        token = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(agent_name.capitalize())
            .with_grants(api.VideoGrants(
                room_join=True, 
                room=request.room_name, 
                can_publish=True,
                can_subscribe=True,
                can_publish_sources=["camera", "microphone", "screen_share_audio","screen_share",]
            ))
            .to_jwt()
        )

        print(f"🚀 Launching process for {agent_name}...")
        # Use subprocess.Popen to run agent_runner.py in a new process
        subprocess.Popen([
            sys.executable,  # Path to current python interpreter
            "agent_runner.py",
            "--room", request.room_name,
            "--identity", identity,
            "--agent-name", agent_name,
            "--token", token,
        ])
        launched_agents.append(agent_name)
    
    # Set up auto-cleanup if specified
    if request.auto_cleanup_minutes and request.auto_cleanup_minutes > 0:
        async def auto_cleanup():
            await asyncio.sleep(request.auto_cleanup_minutes * 60)
            try:
                await leave_room(request.room_name)
            except:
                pass  # Room might already be deleted
        
        asyncio.create_task(auto_cleanup())
        print(f"⏰ Auto-cleanup scheduled for {request.auto_cleanup_minutes} minutes")

    return {
        "status": "success", 
        "message": f"Agent processes launched for room '{request.room_name}'",
        "launched_agents": launched_agents,
        "total_agents": len(launched_agents),
        "auto_cleanup_minutes": request.auto_cleanup_minutes
    }


# @app.post("/join-room")
# async def join_room(room_name: str):
#     if not room_name:
#         raise HTTPException(status_code=400, detail="room_name is required")

#     print(f"🚀 Setting up agents for room: {room_name}")

#     # Define agent identities
#     agents_to_launch = {
#         "priya": f"priya-agent-{room_name}",
#         "alex": f"alex-agent-{room_name}",
#     }

#     for agent_name, identity in agents_to_launch.items():
#         print(f"🔑 Generating token for {agent_name}...")
#         token = (
#             api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
#             .with_identity(identity)
#             .with_name(agent_name.capitalize())
#             .with_grants(api.VideoGrants(room_join=True, room=room_name, can_publish=True,can_subscribe=True,can_publish_sources=["camera", "microphone", "screen_share_audio","screen_share",],))
#             .to_jwt()
#         )

#         print(f"🚀 Launching process for {agent_name}...")
#         # Use subprocess.Popen to run agent_runner.py in a new process
#         subprocess.Popen([
#             sys.executable,  # Path to current python interpreter
#             "agent_runner.py",
#             "--room", room_name,
#             "--identity", identity,
#             "--agent-name", agent_name,
#             "--token", token,
#         ])
    
#     async def auto_cleanup():
#         await asyncio.sleep(15 * 60)  # 15 minutes
#         try:
#             await leave_room(room_name)
#         except:
#             pass  # Room might already be deleted
    
#     asyncio.create_task(auto_cleanup())

#     return {"status": "success", "message": "Agent processes launched."}

# Add this new endpoint to your main.py
@app.post("/leave-room")
async def leave_room(room_name: str):
    """Leave the room and delete it, stopping all agents"""
    if not room_name:
        raise HTTPException(status_code=400, detail="room_name is required")

    print(f"🚪 Leaving and deleting room: {room_name}")

    try:
        # 1. Get LiveKit API instance
        api_instance = await get_livekit_api()
        
        # 2. Delete the room (this will disconnect all participants including agents)
        from livekit.api import DeleteRoomRequest
        delete_request = DeleteRoomRequest(room=room_name)
        await api_instance.room.delete_room(delete_request)
        print(f"✅ Room '{room_name}' deleted successfully")
        
        # 3. Close the API instance
        await api_instance.aclose()
        
        # 4. Kill any running agent processes for this room
        import psutil
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if (cmdline and 
                    'agent_runner.py' in cmdline and 
                    '--room' in cmdline and 
                    room_name in cmdline):
                    
                    print(f"🔄 Terminating agent process: {proc.info['pid']}")
                    proc.terminate()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print(f"✅ Terminated {killed_count} agent processes for room '{room_name}'")
        
        return {
            "status": "success",
            "message": f"Room '{room_name}' deleted and all agents stopped",
            "agents_terminated": killed_count
        }
        
    except Exception as e:
        print(f"❌ Error leaving room: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to leave room: {str(e)}")

# Also add a helper endpoint to list active rooms
@app.get("/active-rooms")
async def list_active_rooms():
    """List all active rooms"""
    try:
        api_instance = await get_livekit_api()
        rooms = await api_instance.room.list_rooms()
        await api_instance.aclose()
        
        return {
            "status": "success",
            "rooms": [
                {
                    "name": room.name,
                    "participant_count": len(room.participants),
                    "creation_time": room.creation_time,
                    "metadata": room.metadata
                } for room in rooms.rooms
            ]
        }
    except Exception as e:
        print(f"❌ Error listing rooms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list rooms: {str(e)}")

@app.post("/generate-user-token")
async def generate_user_token(user_identity: str, room_name: str):
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(user_identity) \
        .with_name(user_identity) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        )) \
        .to_jwt()
    
    return {
        "token": token,
        "url": LIVEKIT_URL,
        "room": room_name
    }

# Additional endpoint to check room participants
@app.get("/room-participants/{room_name}")
async def get_room_participants(room_name: str):
    """Check who's currently in the room"""
    try:
        api_instance = await get_livekit_api()
        participants = await api_instance.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )
        await api_instance.aclose()
        
        return {
            "room": room_name,
            "participant_count": len(participants.participants),
            "participants": [
                {
                    "identity": p.identity,
                    "name": p.name,
                    "kind": p.kind,
                    "state": p.state
                } for p in participants.participants
            ]
        }
    except Exception as e:
        print(f"❌ Error fetching participants: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
