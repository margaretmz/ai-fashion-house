import asyncio
import os
import uuid

from google.adk import Runner
from google.adk.agents import Agent, BaseAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search
import logging
from dotenv import load_dotenv
from style_agent.prompt import get_prompt

load_dotenv()

logging.basicConfig(level=logging.INFO)
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
        # print(f"Session state: {state.keys()}")
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text
            logger.info(f"Final response from {event.author}")
            print(response_text)



root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    description='A helpful fashion designer assistant',
    instruction=get_prompt(),
    tools=[google_search]
)

# Main async function to run the examples
async def main():

    prompts = [
        "Design an elaborate fantasy gown for a queen in a medieval-inspired world. It should be regal, flowing, and detailed with embroidery and symbols of power. Can you find references and write an image prompt for a sketch?",
        "I’m looking for inspiration for a gender-neutral uniform from the year 2100. It should be sleek, functional, and modular—maybe something people would wear in a Mars colony. Please gather visual references and produce a generation-ready prompt."
    ]

    for prompt in prompts:
        print(f"\nProcessing prompt: {prompt}")
        await call_agent_async(root_agent, prompt)
        print("\n---\n")


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
        raise e  # Re-raise other runtime errors