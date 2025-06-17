import os
import logging
from io import BytesIO
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
from PIL import Image
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
if not load_dotenv(find_dotenv()):
    logger.warning("Could not load .env file.")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY is not set in environment variables.")

# Initialize the GenAI client
client = genai.Client(api_key=api_key)


def build_multimodal_prompt(prompt: str, reference_images: Optional[List[str]]) -> str:
    ref_text = "\n".join(reference_images) if reference_images else "None"
    return (
        "You are an AI image generation model.\n"
        f"Your task is to generate visual outputs based on this prompt:\n\n"
        f"{prompt}\n\n"
        "If reference images are provided, use them to guide the style and content.\n"
        f"Reference images:\n{ref_text}"
    )


def save_generated_images(images: List[types.GeneratedImage], output_dir: str = "outputs") -> None:
    os.makedirs(output_dir, exist_ok=True)
    for i, generated_image in enumerate(images):
        try:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            output_path = os.path.join(output_dir, f"generated_image_{i}.png")
            image.save(output_path)
            logger.info(f"Image saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save image {i}: {e}")


def generate_images(prompt: str, reference_images: Optional[List[str]] = None, number_of_images: int = 4) -> None:
    """
    Generates images from a text prompt and optional reference images.
    """
    if not prompt:
        raise ValueError("Prompt must not be empty.")

    multimodal_prompt = build_multimodal_prompt(prompt, reference_images)

    try:
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=multimodal_prompt,
            config=types.GenerateImagesConfig(number_of_images=number_of_images),
        )
        save_generated_images(response.generated_images)
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise


if __name__ == "__main__":
    prompt = "A futuristic cityscape at sunset, with flying cars and neon lights."
    reference_images = [
        "https://dustycars.com/wp-content/uploads/2018/08/ford-model-t.jpeg"
    ]
    generate_images(prompt, reference_images)
