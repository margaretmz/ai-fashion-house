import logging
import os
import uuid
import asyncio

from dotenv import load_dotenv, find_dotenv
from google.adk import Runner
from google.adk.agents import BaseAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai_fashion_house.creative_agent.agent import root_agent

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


async def call_agent_async(agent: BaseAgent, prompt: str) -> None:
    """
    Call the root agent with a prompt and print the final output using Rich panels.

    Args:
        agent:  The agent to be called.
        prompt (str): Natural language query for database.
    """
    APP_NAME = os.getenv("APP_NAME", str(uuid.uuid4()))
    USER_ID = os.getenv("USER_ID", str(uuid.uuid4()))
    SESSION_ID = os.getenv("SESSION_ID", str(uuid.uuid4()))

    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text
            logger.info(f"Final response from {event.author}")
            print(response_text)




async def main():

    prompts = [
        "I’m looking for inspiration for a A red Victorian dress with lace and floral patterns, suitable for a royal ball in the 1800s.",
        "I need ideas for a modern streetwear outfit that combines vintage denim with futuristic accessories.",
        "I want to create a moodboard for a 1920s flapper dress with sequins and feathers, perfect for a Gatsby-themed party.",
        "I’m looking for inspiration for a 1960s mod dress with bold geometric patterns and bright colors, suitable for a retro-themed photoshoot.",
        "I need ideas for a victorian-inspired gown with intricate lace details and a corset, suitable for a historical reenactment event.",
    ]

    for i, prompt in enumerate(prompts):
        os.environ["OUTPUT_FOLDER"] = f"outputs/prompt_{i + 1}"
        print(f"\nProcessing prompt: {prompt}")
        await call_agent_async(root_agent, prompt)
        print("\n---\n")


if __name__ == '__main__':

    # Execute the main async function
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Handle specific error when running asyncio.run in an already running loop (like Jupyter/Colab)
        if "cannot be called from a running event loop" in str(e):
            print("\nRunning in an existing event loop (like Colab/Jupyter).")
            print("Please run `await main()` in a notebook cell instead.")
            # If in an interactive environment like a notebook, you might need to run:
            # await main()
        else:
            raise e  # Re-raise other runtime error