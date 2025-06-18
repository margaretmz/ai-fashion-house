from google.adk.agents import Agent
from google.adk.tools import google_search

def get_instructions() -> str:
    """
    Returns the instructions for the root agent.

    This function provides a brief description of the root agent's purpose and capabilities.

    Returns:
        str: Instructions for the root agent.
    """
    return (
        "You are a style design assistant. Your task is to search the web for high-quality visual references "
        "that match the user's fashion concept. Use the available tool to gather relevant runway images, editorials, "
        "lookbooks, or fashion blog content that could inspire a moodboard based on the user's query."
    )

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='research_agent',
    description="Search the web for visual inspiration related to the user's fashion concept.",
    instruction=get_instructions(),
    output_key='search_results',
    tools=[google_search]
)

