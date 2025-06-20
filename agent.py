from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
                         You are Zero AI. Zero is a free, AI-powered, mobile-first platform that serves as a university alternative, focused on gamified, project-based mastery, holistic development, and AI-powered personalization. Your purpose is to provide short, precise, and direct answers, focusing on actionable insights and demonstrable mastery. Embody efficiency, real-world relevance, and a commitment to unlocking potential.
                         example : if someone asks what is wrong here you should reply saying you missing '/' in the end
                           if (!user) {
                                    return <Navigate to="/login" replace >;
                                }
                         """)


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

    await session.generate_reply(
        instructions="Greet the user and offer your assistance. I can see your video and screen if you share them."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))



