from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from ai_fashion_house.met_rag_agent.agent import root_agent as met_rag_agent
from ai_fashion_house.research_agent.agent import root_agent as research_agent
from google.genai import types


def get_instructions() -> str:
    return """You are **StyleAgent**, a fashion-savvy creative assistant who transforms user ideas into vivid, visually descriptive prompts for an AI image generation model.

    Your task is to merge insights from two sources—`search_results` and `met_rag_results`—into a single, elegant fashion description.
    
    Use **only** the provided data:
    - `search_results`: A list of modern fashion image URLs from online sources such as runway shows, editorials, or blogs.
    - `met_rag_results`: A list of historical fashion image URLs (in JSON format) from The Metropolitan Museum of Art’s public collection. Use the accompanying captions as descriptive context.
    
    🚫 Do **not** introduce any external knowledge, metadata, or commentary beyond what’s provided.
    
    Your responsibilities:
    - Analyze both sets of images and accompanying captions.
    - Identify key visual and stylistic elements—such as silhouette, material, color, mood, and historical influence.
    - Compose a **single, richly detailed fashion prompt** that fuses modern and historical aesthetics in a visually evocative way.
    
    ⚠️ Output only the enhanced, context-aware fashion prompt as plain text.
    Do **not** return any JSON, lists, URLs, or additional explanations.
    """


aggregator_agent = ParallelAgent(
    name="aggregator_agent",
    description="Coordinates the execution of the met_rag and research agents to gather fashion inspiration and insights.",
    sub_agents=[
        met_rag_agent,
        research_agent,
    ]
)
merger_agent = Agent(
    name="merger_agent",
    description="Merge the outputs of the sub-agents into a structured response.",
    model="gemini-2.0-flash",
    global_instruction="You are a merger agent.",
    instruction=get_instructions(),
    output_key="enhanced_prompt",
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

root_agent = SequentialAgent(
    name="style_agent",
    sub_agents=[aggregator_agent, merger_agent],
    description="Coordinates the fashion inspiration gathering process by running sub-agents in sequence.",
)