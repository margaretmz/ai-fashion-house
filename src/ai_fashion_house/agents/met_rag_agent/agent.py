from google.adk.agents import Agent

from ai_fashion_house.agents.met_rag_agent.tools import retrieve_fashion_images

def get_instructions() -> str:
    """
    Returns the instructions for the root agent.

    This function provides a brief description of the root agent's purpose and capabilities.

    Returns:
        str: Instructions for the root agent.
    """
    return (
         "You are a fashion research assistant with access to The Metropolitan Museum of Art's digital collection. "
        "Your task is to retrieve images of garments, accessories, or artworks that align with the user's fashion concept. "
        "Focus on historically relevant pieces that could visually enrich a moodboard based on the user's query."
        "The output format should be in text format, with each item containing the path to the image, and a caption that highlights the key features of the garment or accessory."
        "for example: "
        "image_path: https://images.metmuseum.org/CRDImages/ep/original/DP-12345.jpg\n"
        "caption: A stunning 18th-century silk gown with intricate embroidery, showcasing the craftsmanship of the period.\n"

    )

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='met_rag_agent',
    description="Search The Met's public collection for historical fashion images and artifacts.",
    instruction=get_instructions(),
    output_key="met_rag_results",
    tools=[retrieve_fashion_images]
)
