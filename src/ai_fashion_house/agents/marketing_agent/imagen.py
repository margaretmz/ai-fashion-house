import asyncio
import logging
import os
import typing
from io import BytesIO
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from PIL import Image
from ai_fashion_house.utils.gcp_utils import (
    get_authenticated_genai_client,
    parse_gcs_uri, download_media_file_from_gcs
)

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())


genai_client = get_authenticated_genai_client()
gcs_client = storage.Client()


async def save_generated_image(image: types.Image, output_folder: Path, tool_context: Optional[ToolContext] = None) -> None:
    """
    Save generated images to a specified output folder and optionally save as an artifact using the ToolContext.
    :param image: The generated image object containing the image bytes.
    :param output_folder: The folder where the images will be saved.
    :param tool_context:
    :return:
    """
    image_gcs_uri = image.gcs_uri
    if not image_gcs_uri:
        raise ValueError("Image GCS URI is not provided in the generated image object.")

    # Download the image bytes from GCS
    bucket_name, blob_path = parse_gcs_uri(image_gcs_uri)
    image_bytes, image_mime_type = download_media_file_from_gcs(
        bucket_name=bucket_name,
        blob_path=blob_path
    )
    logger.debug(f"Media bytes: {image_bytes}")
    logger.debug(f"Mime type: {image_mime_type}")
    if tool_context:
        await tool_context.save_artifact("generated_image.png", types.Part.from_bytes(
            data=image_bytes, mime_type=image_mime_type
        ))

    image = Image.open(BytesIO(image_bytes))
    output_path = output_folder / f"generated_image.png"
    image.save(output_path)
    logger.info(f"Image saved to {output_path} successfully.")


async def generate_image(enhanced_prompt: str, tool_context: Optional[ToolContext] = None) -> typing.Dict[str, str]:
    """
    Generate an image using a text prompt. Optionally save the result via a ToolContext.

    Args:
        enhanced_prompt (str): A descriptive text prompt for image generation.
        tool_context (Optional[ToolContext]): Optional context to save the artifact remotely.

    Returns:
        dict[str, str]: A dictionary containing the status and message of the operation.
    """
    media_files_bucket_gs_uri = os.getenv("MEDIA_FILES_BUCKET_GCS_URI", None)
    media_files_local_path = Path(os.getenv("OUTPUT_FOLDER", "outputs"))
    media_files_local_path.mkdir(parents=True, exist_ok=True)


    if not media_files_bucket_gs_uri:
        raise ValueError("MEDIA_FILES_BUCKET_GS_URI environment variable is not set.")
    try:
        if not enhanced_prompt.strip():
            raise ValueError("Prompt must not be empty.")
        response = genai_client.models.generate_images(
            model=os.getenv("IMAGEN_MODEL_ID","imagen-4.0-generate-preview-06-06"),
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_gcs_uri=media_files_bucket_gs_uri,
            ),
        )
        if not response.generated_images:
            raise RuntimeError("No images were generated. Check the prompt and model configuration.")

        logger.info(f"Generated {len(response.generated_images)} image(s).")
        logger.info(response.generated_images)
        generated_image = response.generated_images[0].image
        await save_generated_image(generated_image, media_files_local_path,  tool_context)

        if tool_context:
            tool_context.state["generated_image_url"] = generated_image.gcs_uri

        return {
            "status": "success",
            "message": "Image generated and saved successfully.",
            "image_gcs_uri": generated_image.gcs_uri
        }
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {
            "status": "error",
            "message": str(e),
            "image_gcs_uri": None
        }

if __name__ == "__main__":
    test_prompt = "A futuristic cityscape at sunset, with flying cars and neon lights."
    output = asyncio.run(generate_image(test_prompt))
    print(output)
