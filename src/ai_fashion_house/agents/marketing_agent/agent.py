from google.adk.agents import Agent
from google.adk.tools import agent_tool, load_artifacts
from google.genai import types

from ai_fashion_house.agents.marketing_agent.imagen import generate_image
from ai_fashion_house.agents.marketing_agent.veo import generate_video
from ai_fashion_house.agents.fashion_design_agent.agent import root_agent as fashion_design_agent
from ai_fashion_house.agents.marketing_agent.prompts import get_instructions



fashion_design_agent_tool = agent_tool.AgentTool(agent=fashion_design_agent)

root_agent = Agent(
    model="gemini-2.0-flash",
    name="marketing_agent",
    instruction=get_instructions(),
    description="Coordinates the fashion creative process by running style agent and generating fashion media.",
    tools=[fashion_design_agent_tool, generate_image, generate_video, load_artifacts],
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
    output_key="social_media_post",
)
