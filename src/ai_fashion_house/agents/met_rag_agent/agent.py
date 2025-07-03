from google.adk.agents import Agent

from ai_fashion_house.agents.met_rag_agent.tools import retrieve_met_images
from ai_fashion_house.agents.met_rag_agent.prompts import get_instructions



root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='met_rag_agent',
    description="Search The Met's public collection for historical fashion images and artifacts.",
    instruction=get_instructions(),
    output_key="met_rag_results",
    tools=[retrieve_met_images]
)
