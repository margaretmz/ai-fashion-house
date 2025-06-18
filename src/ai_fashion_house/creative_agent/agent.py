from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import agent_tool, load_artifacts
from google.genai import types

from ai_fashion_house.creative_agent.imagen import generate_image
from ai_fashion_house.creative_agent.veo import generate_video
from ai_fashion_house.style_agent.agent import root_agent as style_agent


def get_instructions() -> str:
    """
    Returns the instructions for the root agent.

    This function defines the responsibilities and coordination logic of CreativeAgent,
    the top-level controller in the fashion prompt-to-image generation workflow.

    Returns:
        str: Instructions for the root agent.
    """
    return (
        "You are **CreativeAgent**, a fashion-savvy orchestration assistant responsible for managing the end-to-end "
        "creative workflow that transforms user concepts into high-quality fashion images.\n\n"
        "Workflow:\n"
        "1. Accept a user-provided concept — this may be abstract, casual, or loosely defined.\n"
        "2. Invoke the **style_agent_tool** to interpret the concept and generate a vivid, structured, and fashion-specific prompt.\n"
        "3. Use the refined fashion prompt to call the **image_generation_tool**, which produces visually stunning fashion images.\n\n"
        "4. Finally, create a video using the **video_generation_tool** based on the `generated_image.png` .\n\n"
    )

style_agent_tool = agent_tool.AgentTool(agent=style_agent)

root_agent = Agent(
    model="gemini-2.0-flash",
    name="creative_agent",
    instruction=get_instructions(),
    description="Coordinates the fashion creative process by running style agent and image generation agent.",
    tools=[style_agent_tool, generate_image, generate_video, load_artifacts],
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

#
# root_agent = SequentialAgent(
#     name="creative_agent",
#     description="Coordinates the fashion creative process by running the style agent, image generation agent, and video generation agent.",
#     sub_agents=[style_agent, image_generator_agent, video_generator_agent],
#     )

