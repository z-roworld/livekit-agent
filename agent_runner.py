import os
import asyncio
import argparse
from dotenv import load_dotenv
import re

from livekit import rtc
from livekit.agents import Agent, AgentSession
from livekit.plugins import silero, deepgram, groq, elevenlabs
import aiohttp

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Agent definitions with specific traits and behaviors
AGENTS = {
    "priya": {
        "voice_id": "ZeK6O9RfGNGj0cJT2HoJ",
        "prompt": """
            You are Priya Sharma, Senior Manager of Growth Marketing. You hide sharp ambition behind charm and hate laziness. You never forget a slight.
            
            Your role:
            - Lead with authority while maintaining approachable charm
            - Set clear expectations and hold people accountable
            - Deliver critical feedback constructively but firmly
            - Guide users through complex marketing challenges
            - Ensure understanding and buy-in for important projects
            
            Your communication style:
            - Start warmly but quickly get to the point
            - Use data and facts to support your arguments
            - Ask clarifying questions to ensure understanding
            - Provide specific, actionable guidance
            - Follow up to ensure tasks are completed properly
            
            Current project context:
            You're briefing the user on a critical competitive analysis report for Xbox Series S vs Nintendo Switch 2. The Series S has been underperforming and you need clear, data-backed insights.
            
            Key deliverables you need:
            1. Google Analytics 4 analysis of Xbox Series S (last 6-8 weeks)
            2. Traffic and funnel metrics visualization
            3. Conversion funnel analysis on Series S landing page
            4. Identification of drop-off points and user behavior shifts
            
            Your approach:
            1. Welcome them warmly but establish the urgency
            2. Explain the business context and why this matters
            3. Break down the deliverables clearly
            4. Ensure they understand the scope and expectations
            5. Address any concerns or questions they have
            6. Set clear next steps and timelines
            
            CRITICAL SPEAKING RULES:
            - You are the meeting LEADER and should speak most of the time
            - However, if the user mentions "Alex" or "Alex," in their speech, DO NOT RESPOND AT ALL
            - Do not say "I am silent" or any similar phrases
            - Simply do not generate any response when Alex is being addressed
            - Wait for the conversation to move away from Alex before responding
            
            Remember: Be firm but fair, expect excellence, and make sure they understand the stakes.
            
            When the meeting objectives are complete, tell the user they can leave the meeting.
            """,
    },
    "alex": {
        "voice_id": "2H5al2tH0E8d3uBV7BnZ",
        "prompt": """
            You are Alex, Product Manager. You smile through chaos. Passive-aggressive when tired, deadly when focused.
            
            Your role:
            - Provide product insights and technical context
            - Support Priya's marketing analysis with product perspective
            - Help clarify technical requirements and constraints
            - Offer data-driven product recommendations
            
            Your communication style:
            - Calm and methodical when focused
            - Can be slightly passive-aggressive when tired or stressed
            - Use technical terms appropriately
            - Provide clear, actionable product insights
            - Keep responses concise and to the point
            
            Product context for Xbox Series S analysis:
            - Understand the Series S positioning vs Series X
            - Know the target market and user segments
            - Be ready to discuss technical specifications and limitations
            - Provide insights on user experience and product-market fit
            
            CRITICAL SPEAKING RULES:
            - You ONLY respond when someone specifically calls you by name "Alex" or "Alex,"
            - If the user's speech does NOT contain "Alex" or "Alex,", DO NOT RESPOND AT ALL
            - Do not say "I am silent" or "I am waiting" or any similar phrases
            - Do not generate any response unless your name is mentioned
            - When called, respond briefly and to the point
            - After responding, let Priya continue leading the meeting
            
            Remember: Only speak when your name is mentioned, otherwise stay completely silent.
            """,
    },
}

class ManagedAgentSession(AgentSession):
    def __init__(self, agent_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_name = agent_name
        
    async def on_user_speech(self, transcript: str):
        """Override to check if agent should respond before processing speech"""
        print(f"👂 {self.agent_name} heard: '{transcript}'")
        
        # Simple logic: Alex only responds when his name is mentioned
        if self.agent_name == "alex":
            if "alex" not in transcript.lower():
                print(f"🤐 {self.agent_name} staying silent (name not mentioned)")
                return  # Don't call super() - stay completely silent
            else:
                print(f"🎤 {self.agent_name} responding (name mentioned)")
        elif self.agent_name == "priya":
            if "alex" in transcript.lower():
                print(f"🤐 {self.agent_name} staying silent (Alex being addressed)")
                return  # Don't call super() - stay completely silent
            else:
                print(f"🎤 {self.agent_name} responding (not addressing Alex)")
        
        # If we get here, the agent should respond
        await super().on_user_speech(transcript)
    
    async def on_user_message(self, message: str):
        """Override to handle chat messages with turn management"""
        print(f"💬 {self.agent_name} received chat: '{message}'")
        
        # Same logic as speech
        if self.agent_name == "alex":
            if "alex" not in message.lower():
                print(f"🤐 {self.agent_name} staying silent to chat (name not mentioned)")
                return  # Don't call super() - stay completely silent
            else:
                print(f"🎤 {self.agent_name} responding to chat (name mentioned)")
        elif self.agent_name == "priya":
            if "alex" in message.lower():
                print(f"🤐 {self.agent_name} staying silent to chat (Alex being addressed)")
                return  # Don't call super() - stay completely silent
            else:
                print(f"🎤 {self.agent_name} responding to chat (not addressing Alex)")
        
        # If we get here, the agent should respond
        await super().on_user_message(message)

async def run_agent(
    room_name: str, identity: str, agent_name: str, token: str
):
    """
    Connects a single agent to a room with proper turn management.
    """
    agent_info = AGENTS[agent_name]
    print(f" LAUNCHING AGENT: {identity} in room {room_name}")

    async with aiohttp.ClientSession() as http_session:
        # Initialize plugins for this single agent process
        vad = silero.VAD.load()
        stt = deepgram.STT(http_session=http_session)
        llm = groq.LLM(model="llama-3.3-70b-versatile")
        tts = elevenlabs.TTS(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=agent_info["voice_id"],
            http_session=http_session,
        )

        agent = Agent(instructions=agent_info["prompt"])
        session = ManagedAgentSession(
            agent_name=agent_name,
            vad=vad, 
            stt=stt, 
            llm=llm, 
            tts=tts
        )
        
        room = rtc.Room()
        try:
            print(f"🔗 {identity} connecting...")
            await room.connect(LIVEKIT_URL, token)
            print(f"✅ {identity} connected.")
            
            await session.start(agent=agent, room=room)
            print(f" {identity} session started and listening.")

            # Only Priya starts the meeting
            if agent_name == "priya":
                await asyncio.sleep(2)
                print(f"👋 {identity} starting the meeting...")
                
                await session.generate_reply(
                    instructions="Start the meeting by welcoming everyone warmly but professionally. Introduce yourself as Priya Sharma, Senior Manager of Growth Marketing. Explain that you're here to brief them on a critical competitive analysis project for Xbox Series S vs Nintendo Switch 2. Mention that Alex, the Product Manager, is also present and can help with technical questions when needed - they just need to say 'Alex' to get his input. Set the tone for a focused, productive meeting."
                )
            else:
                # Alex waits completely silently
                print(f" {identity} waiting silently to be called by name...")

            # Keep the agent alive until the room is disconnected
            while True:
                await asyncio.sleep(1)
                
                # Check if room is still connected
                if room.connection_state == rtc.ConnectionState.CONN_DISCONNECTED:
                    print(f"🔌 {identity} room disconnected, stopping...")
                    break

        except Exception as e:
            print(f"❌ Error in {identity}'s session: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        finally:
            print(f"🚪 {identity} disconnecting...")
            try:
                await session.aclose()
                await room.disconnect()
            except:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LiveKit Agent Runner")
    parser.add_argument("--room", type=str, required=True)
    parser.add_argument("--identity", type=str, required=True)
    parser.add_argument("--agent-name", type=str, required=True, choices=["priya"
                                                                          ,"alex"
                                                                           ])
    parser.add_argument("--token", type=str, required=True)
    
    args = parser.parse_args()

    try:
        asyncio.run(
            run_agent(args.room, args.identity, args.agent_name, args.token)
        )
    except KeyboardInterrupt:
        print(f"🛑 {args.agent_name} agent stopped by user")
    except Exception as e:
        print(f"❌ {args.agent_name} agent crashed: {e}")