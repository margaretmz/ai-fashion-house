import base64
import os
import time
import logging
from io import BytesIO
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from google import genai
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

def pil_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Convert a PIL Image object to a base64-encoded string.

    Args:
        image (PIL.Image.Image): The image to encode.
        format (str): The image format for encoding (e.g., "PNG", "JPEG").

    Returns:
        str: Base64-encoded image string.
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def generate_video() -> None:

    list_images = os.listdir("/Users/haruiz/open-source/ai-fashion-house/style_agent/outputs/")
    selected_image_path = list_images[0]  # Select the first image for simplicity
    input_image_path = os.path.join("/Users/haruiz/open-source/ai-fashion-house/style_agent/outputs/", selected_image_path)
    input_image = Image.open(input_image_path)
    image_bytes = pil_image_to_base64(input_image)
    image_mime_type = "image/png"  # Assuming the input image is in PNG format

    input_image = types.Image(
        image_bytes=image_bytes,
        mime_type=image_mime_type
    )
    operation = client.models.generate_videos(
        model="veo-2.0-generate-001",
        prompt=(
            "A full-body fashion video of a model wearing the dress shown in the image. "
            "The model walks confidently on a runway, swinging their arms naturally and turning to show different angles. "
            "The camera captures the model from head to toe in soft lighting, clearly showing the fabric movement and the model's full pose, including arms and hands."
        ),
        image=input_image,
        config=types.GenerateVideosConfig(
            person_generation="allow_adult",  # "dont_allow" or "allow_adult"
            aspect_ratio="9:16",  # "16:9" or "9:16"
            duration_seconds=8,  # Duration of the video in seconds
        ),
    )
    while not operation.done:
        time.sleep(20)
        operation = client.operations.get(operation)

    for n, generated_video in enumerate(operation.response.generated_videos):
        client.files.download(file=generated_video.video)
        generated_video.video.save(f"video{n}.mp4")  # save the video


if __name__ == '__main__':
    image = Image.open("/Users/haruiz/open-source/ai-fashion-house/style_agent/outputs/generated_image_0.png")  # Replace with your image path
    print(image)
    generate_video(image)