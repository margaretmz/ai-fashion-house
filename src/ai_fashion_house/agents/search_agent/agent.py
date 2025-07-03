from google.adk.agents import Agent
from google.adk.tools import google_search
from ai_fashion_house.agents.search_agent.prompts import get_instructions



root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='search_agent',
    description="Search the web for visual inspiration related to the user's fashion concept.",
    instruction=get_instructions(),
    output_key='search_results',
    tools=[google_search]
)

