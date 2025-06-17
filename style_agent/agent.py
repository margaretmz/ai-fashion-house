import asyncio
import os
import uuid
from typing import Dict, List, Any

from google.adk import Runner
from google.adk.agents import Agent, BaseAgent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search, agent_tool
import logging
from dotenv import load_dotenv, find_dotenv

from style_agent.imagen import generate_images
from style_agent.prompt import get_prompt
from style_agent.met_rag import query_met_rag
from style_agent.veo import generate_video

load_dotenv(find_dotenv())

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


# --- Task Definitions ---
TASK_CONFIGS: List[Dict[str, Any]] = [
    {
        "name": "search_agent",
        "description": "Search the web for visual inspiration related to the user's fashion concept.",
        "instruction": (
            "You are a style design assistant. Your task is to search the web for high-quality visual references "
            "that match the user's fashion concept. Use the available tool to gather relevant runway images, editorials, "
            "lookbooks, or fashion blog content that could inspire a moodboard based on the user's query."
        ),
        "output_key": "search_results",
        "tools": [google_search],
    },
    {
        "name": "met_rag_agent",
        "description": "Search The Met's public collection for historical fashion images and artifacts.",
        "instruction": (
            "You are a fashion research assistant with access to The Metropolitan Museum of Art's digital collection. "
            "Your task is to retrieve images of garments, accessories, or artworks that align with the user's fashion concept. "
            "Focus on historically relevant pieces that could visually enrich a moodboard based on the user's query."
            "The output format should be in json format, with each item containing the path to the image, and a caption that highlights the key features of the garment or accessory."
            "for example: "
            '{"image_path": "gcs://met-rag-images/12345.jpg", "caption": "A Victorian-era gown with intricate lace details and floral embroidery."}'
        ),
        "output_key": "met_rag_results",
        "tools": [query_met_rag],
    }
]

def create_task_handler_agent(task: Dict[str, str]) -> LlmAgent:
    return LlmAgent(
        name=task["name"],
        description=task["description"],
        model="gemini-2.0-flash",
        global_instruction=f"You are a {task['description'].lower()} generator.",
        instruction=task["instruction"],
        output_key=task["output_key"],
        tools=task["tools"],
        generate_content_config=types.GenerateContentConfig(temperature=1.5)
    )

sub_agents = [create_task_handler_agent(task) for task in TASK_CONFIGS]
# --- Aggregator (Parallel Execution) ---
aggregator_agent = ParallelAgent(
    name="ParallelGenerator",
    sub_agents=sub_agents,
    description="Parallel execution agent that runs multiple sub-agents to gather fashion inspiration.",
)

# --- Merger Agent ---
merger_agent = LlmAgent(
    name="merger_agent",
    description="Merge the outputs of the sub-agents into a structured response.",
    model="gemini-2.0-flash",
    global_instruction="You are a merger agent.",
    instruction=get_prompt(),
    output_key="enhanced_prompt",
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

image_generator_agent = LlmAgent(
    name="image_generator_agent",
    description="Generates images based on the enhanced fashion prompt.",
    model="gemini-2.0-flash",
    global_instruction="You are an image generation agent.",
    instruction="Generate images based on the provided fashion prompt in `enhanced_prompt`.",
    output_key="generated_images",
    tools=[generate_images],
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

video_generator_agent = LlmAgent(
    name="video_generator_agent",
    description="Generates videos based on the provided fashion images.",
    model="gemini-2.0-flash",
    global_instruction="You are a video generation agent.",
    instruction="Generate videos based on the provided fashion images.",
    output_key="generated_videos",
    tools=[generate_video],  # Assuming you have a tool for video generation
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

# --- Root Agent (Sequential Flow) ---
root_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[aggregator_agent, merger_agent, image_generator_agent, video_generator_agent],
    description="Coordinates the fashion inspiration gathering process by running sub-agents in sequence.",
)

# Main async function to run the examples
async def main():

    prompts = [
        "I’m looking for inspiration for a A red Victorian dress with lace and floral patterns, suitable for a royal ball in the 1800s.",
        # "I need ideas for a modern streetwear outfit that combines vintage denim with futuristic accessories.",
        # "I want to create a moodboard for a 1920s flapper dress with sequins and feathers, perfect for a Gatsby-themed party.",
        # "I’m looking for inspiration for a 1960s mod dress with bold geometric patterns and bright colors, suitable for a retro-themed photoshoot.",
        #"I need ideas for a victorian-inspired gown with intricate lace details and a corset, suitable for a historical reenactment event.",
    ]

    for prompt in prompts:
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
            raise e  # Re-raise other runtime errors