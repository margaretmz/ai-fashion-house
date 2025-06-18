import asyncio
import base64
import io
import os
import time
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Any, Coroutine
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.genai import types
from PIL.Image import Image as PILImage
from PIL import Image

# Setup logging
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


def save_generated_videos(operation_response: types.GenerateVideosResponse) -> None:
    output_folder = Path(os.getenv("OUTPUT_FOLDER", "outputs"))
    output_folder.mkdir(parents=True, exist_ok=True)
    for n, generated_video in enumerate(operation_response.generated_videos):
        client.files.download(file=generated_video.video)
        filepath = output_folder / f"generated_video_{n + 1}.mp4"
        generated_video.video.save(str(filepath))  # Save the video to the output folder
        logger.info(f"Video saved to {filepath}")

async def generate_video(image_path: str, tool_context: Optional[ToolContext] = None) -> dict[str, Any]:
    """
    Create a full-body fashion video of a model wearing a dress from an image.
    Args:
        image_path (str): Path to the input image file.
        tool_context (Optional[ToolContext]): Tool context for loading artifacts.
    Returns:
        dict[str, Any]: A dictionary containing the status and message of the operation.
    """
    try:
        if tool_context:
            image_artifact = await tool_context.load_artifact("generated_image.png") if tool_context else None
            if not image_artifact:
                raise ValueError("No image artifact found. Please provide a valid image.")
        else:
            # Load the image directly if no tool context is provided
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
            image_artifact = types.Part(
                inline_data=types.Blob(
                    mime_type="image/png",
                    data=image_data
                )
            )
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=(
                "A full-body fashion video of a model wearing the dress in the image. "
                "The camera captures the model from head to toe in soft lighting, clearly showing the fabric movement and the model's full pose, including arms and hands."
            ),
            image=image_artifact.file_data,
            config=types.GenerateVideosConfig(
                person_generation="allow_adult",  # "dont_allow" or "allow_adult"
                aspect_ratio="9:16",  # "16:9" or "9:16"
                duration_seconds=8,  # Duration of the video in seconds
            ),
        )
        while not operation.done:
            time.sleep(20)
            operation = client.operations.get(operation)

        save_generated_videos(operation.response)
        return {
            "status": "success",
            "message": "Video generated and saved successfully."
        }
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == '__main__':
    asyncio.run(generate_video(image_path="/Users/haruiz/open-source/ai-fashion-house/outputs/generated_image_1.png"))
