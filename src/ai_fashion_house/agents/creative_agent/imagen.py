import asyncio
import os
import logging
import typing
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
from PIL import Image
from google import genai
from google.adk.tools import ToolContext
from google.genai import types
from rich.logging import RichHandler

# --- Configure Rich Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("StyleAgent")

# --- Load environment variables ---
if not load_dotenv(find_dotenv()):
    logger.warning("[env] Could not load .env file.")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY is not set in environment variables.")

# --- Initialize GenAI client ---
client = genai.Client(api_key=api_key)


async def save_generated_images(images: List[types.GeneratedImage], tool_context: Optional[ToolContext] = None) -> None:
    """Save a list of generated images to the specified output directory."""
    if tool_context:
        image_bytes = images[0].image.image_bytes
        artifact_part = types.Part.from_bytes(mime_type="image/png", data=image_bytes)
        await tool_context.save_artifact("generated_image.png", artifact_part)

    output_folder = Path(os.getenv("OUTPUT_FOLDER", "outputs"))
    output_folder.mkdir(parents=True, exist_ok=True)
    for i, generated_image in enumerate(images):
        try:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            output_path = output_folder / f"generated_image_{i + 1}.png"
            image.save(output_path)
            logger.info(f"Image saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save image {i}: {e}")


async def generate_image(enhanced_prompt: str, tool_context: Optional[ToolContext] = None) -> typing.Dict[str, str]:
    """
    Generate an image using a text prompt. Optionally save the result via a ToolContext.

    Args:
        enhanced_prompt (str): A descriptive text prompt for image generation.
        tool_context (Optional[ToolContext]): Optional context to save the artifact remotely.

    Returns:
        dict[str, str]: A dictionary containing the status and message of the operation.
    """
    try:
        if not enhanced_prompt.strip():
            raise ValueError("Prompt must not be empty.")
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )

        if not response.generated_images:
            raise RuntimeError("No images were generated. Check the prompt and model configuration.")

        logger.info(f"Generated {len(response.generated_images)} image(s).")

        await save_generated_images(response.generated_images, tool_context)
        return {
            "status": "success",
            "message": "Image generated and saved successfully."
        }
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {
            "status": "error",
            "message": str(e)
        }



if __name__ == "__main__":
    test_prompt = "A futuristic cityscape at sunset, with flying cars and neon lights."
    asyncio.run(generate_image(test_prompt))
