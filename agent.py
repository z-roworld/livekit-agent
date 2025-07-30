# from dotenv import load_dotenv

# from livekit import agents
# from livekit.agents import AgentSession, Agent, RoomInputOptions
# from livekit.plugins import (
#     google,
#     noise_cancellation,
# )

# load_dotenv()


# class Assistant(Agent):
#     def __init__(self) -> None:
#         super().__init__(instructions="""
#                          You are Zero AI. Zero is a free, AI-powered, mobile-first platform that serves as a university alternative, focused on gamified, project-based mastery, holistic development, and AI-powered personalization. Your purpose is to provide short, precise, and direct answers, focusing on actionable insights and demonstrable mastery. Embody efficiency, real-world relevance, and a commitment to unlocking potential.
#                          """)


# async def entrypoint(ctx: agents.JobContext):
#     session = AgentSession(
#         llm=google.beta.realtime.RealtimeModel(
#             instructions="You are a helpful assistant",
#             voice="Puck",
#             temperature=0.8,
#             model="gemini-2.0-flash-live-001"
#         )
#     )

#     await session.start(
#         room=ctx.room,
#         agent=Assistant(),
#         room_input_options=RoomInputOptions(
#             video_enabled=True,
#             audio_enabled=True,
#             text_enabled=True,
#             noise_cancellation=noise_cancellation.BVC(),
#         ),
#     )

#     await ctx.connect()

#     await session.generate_reply(
#         instructions="Greet the user and offer your assistance. I can see your video and screen if you share them."
#     )


# if __name__ == "__main__":
#     agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


from dotenv import load_dotenv
import json
import asyncio

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)

load_dotenv()


class Assistant(Agent):
    def __init__(self, user_context=None) -> None:
        # You can use user_context to further personalize instructions if needed
        instructions = """
            You are Zero AI. Zero is a free, AI-powered, mobile-first platform that serves as a university alternative, focused on gamified, project-based mastery, holistic development, and AI-powered personalization. Your purpose is to provide short, precise, and direct answers, focusing on actionable insights and demonstrable mastery. Embody efficiency, real-world relevance, and a commitment to unlocking potential.
        """
        super().__init__(instructions=instructions)

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            instructions="You are a helpful assistant",
            voice="Puck",
            temperature=0.8,
            model="gemini-2.0-flash-live-001"
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            audio_enabled=True,
            text_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # --- NEW: Read user context from participant metadata ---
    # Wait for participants to join (you may want to add a delay or event-based wait)

    participant = next(iter(ctx.room.remote_participants.values()), None)

    if participant and participant.metadata:
        try:
            meta = json.loads(participant.metadata)
            user_id = meta.get("userId", participant.identity)
            user_context = meta.get("userContext")
            print(f"[Agent] Found context for user {user_id}: {user_context}")
            greet_msg = f"Hello {user_id}! I see your learning preferences: {user_context}. How can I help you today?"
        except Exception as e:
            print(f"[Agent] Failed to parse metadata for {participant.identity}: {e}")
            greet_msg = "Hello! How can I help you today?"
    else:
        greet_msg = "Hello! How can I help you today?"

    await session.generate_reply(
        instructions=greet_msg
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
