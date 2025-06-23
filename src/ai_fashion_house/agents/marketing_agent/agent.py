from google.adk.agents import Agent
from google.adk.tools import agent_tool, load_artifacts
from google.genai import types

from ai_fashion_house.agents.marketing_agent.imagen import generate_image
from ai_fashion_house.agents.marketing_agent.veo import generate_video
from ai_fashion_house.agents.fashion_design_agent.agent import root_agent as fashion_design_agent


def get_instructions() -> str:
    return (
        "You are **Marketing Design Agent**, a fashion-savvy orchestration assistant responsible for managing the end-to-end "
        "creative pipeline that transforms user concepts into high-quality, visually compelling fashion media.\n\n"
        "Your workflow consists of the following steps:\n"
        "1. Accept a user-provided concept — this may be abstract, loosely defined, or stylistically expressive.\n"
        "2. Invoke the **style_agent_tool** to interpret the concept and generate a vivid, structured, and fashion-specific prompt.\n"
        "3. Pass the refined prompt to the **image_generation_tool** to produce a high-quality fashion image.\n"
        "4. Use the resulting image: `generated_image.png` to create a short, cinematic fashion video targeting a fashion-forward audience.\n\n"
        "5. Write an strong social media post that captures the essence of the fashion image and video, designed to engage and inspire followers.\n\n"
        "Don't modify the enhanced prompt ; use them as-is for video generation.\n"
        "Ensure each step flows smoothly, the visual output is coherent and expressive, and the final result aligns with the user's creative intent."
    )


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


# root_agent = SequentialAgent(
#     name="creative_agent",
#     description="Coordinates the fashion creative process by running the style agent, image generation agent, and video generation agent.",
#     sub_agents=[style_agent, image_generator_agent, video_generator_agent],
#)

