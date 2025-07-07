import asyncio
import logging
import mimetypes
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiofiles
from dotenv import load_dotenv, find_dotenv
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from google.genai.errors import ClientError

from ai_fashion_house.agents.marketing_agent.prompts import get_image_caption_prompt
from ai_fashion_house.utils.gcp_utils import get_authenticated_genai_client, parse_gcs_uri, upload_media_file_to_gcs, \
    download_media_file_from_gcs

# Load environment variables
load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

genai_client = get_authenticated_genai_client()
gcs_client = storage.Client()


def caption_image(image_uri: str) -> str:
    """
    Uses Gemini to generate a fashion-themed caption prompt from an image.

    Args:
        image_uri (str): The GCS URI of the image to caption.

    Returns:
        str: A descriptive prompt/caption for the image.
    """

    response = genai_client.models.generate_content(
        model="gemini-2.5-flash",
          contents=[types.Part.from_uri(
            file_uri=image_uri,
            mime_type="image/png"
        ), types.Part.from_text(text=get_image_caption_prompt())],
    )
    return response.text


async def save_generated_video(video: types.Video, output_folder: Path, tool_context: Optional[ToolContext] = None) -> None:
    """
    Save generated images to a specified output folder and optionally save as an artifact using the ToolContext.
    :param image: The generated image object containing the image bytes.
    :param output_folder: The folder where the images will be saved.
    :param tool_context:
    :return:
    """
    video_gcs_uri = video.uri
    if not video_gcs_uri:
        raise ValueError("Image GCS URI is not provided in the generated image object.")

    # Download the image bytes from GCS
    bucket_name, blob_path = parse_gcs_uri(video_gcs_uri)
    video_bytes, video_mime_type = download_media_file_from_gcs(
        bucket_name=bucket_name,
        blob_path=blob_path
    )
    logger.debug(f"Media bytes: {video_bytes}")
    logger.debug(f"Mime type: {video_mime_type}")
    if tool_context:
        await tool_context.save_artifact("generated_video.mp4", types.Part.from_bytes(
            data=video_bytes, mime_type=video_mime_type
        ))
        tool_context.state["generated_video_url"] = video_gcs_uri

    output_path = output_folder / f"generated_video.mp4"
    async with aiofiles.open(output_path, "wb") as out_file:
        await out_file.write(video_bytes)
    logger.info(f"Video saved to {output_path} successfully.")


async def generate_video(image_gcs_uri: str, tool_context: Optional[ToolContext] = None):
    """
    Main entry point to generate a fashion-themed video from a single input image.

    This function supports loading from a ToolContext or directly from local disk,
    uploading the image to GCS, and using Gemini to generate video content with a fallback
    to dynamic prompt generation if the initial request fails.

    Args:
        image_gcs_uri (str): The GCS URI of the input image to use for video generation.
        tool_context (Optional[ToolContext]): Optional context for loading artifacts.

    Returns:
        dict[str, Any]: A dictionary containing the result status and message.
    """
    try:
        media_files_bucket_gs_uri = os.getenv("MEDIA_FILES_BUCKET_GCS_URI", None)
        media_files_local_path = Path(os.getenv("OUTPUT_FOLDER", "outputs"))

        if not media_files_bucket_gs_uri:
            raise ValueError("MEDIA_FILES_BUCKET_GCS_URI environment variable is not set.")


        try:
            # attempt to generate image-to-video directly
            logger.info("Attempting to generate video from image...")
            prompt = "The fashion model in the image walks toward the camera with a smile."
            generated_video = try_generate_video(prompt, gcs_image_uri=image_gcs_uri)


        except ClientError as e:
            logger.warning(f"Initial video generation failed: {e}")
            if e.code != 400:
                raise
            # Fallback: use Gemini to generate a caption prompt from the image and retry
            logger.info("Retrying with Gemini-generated prompt...")
            prompt = caption_image(image_gcs_uri)
            generated_video =  try_generate_video(prompt, gcs_image_uri=None)

        await save_generated_video(generated_video, media_files_local_path, tool_context)
        logger.info(f"Video generation response: {generated_video.uri}")
        logger.info("Video generated successfully")
        return {
            "status": "success",
            "message": "Video generated successfully",
            "video_gcs_uri": generated_video.uri
        }
    except Exception as e:
        logger.exception("Error in generate_video")
        return {"status": "error", "message": str(e)}


def try_generate_video(
    prompt: str,
    gcs_image_uri: Optional[str] = None
) -> types.Video:
    """
    Attempts to generate a video using a given prompt and optional image URI.

    Args:
        prompt (str): The descriptive prompt for the fashion scene.
        gcs_image_uri (Optional[str]): GCS URI of the reference image (optional).

    Returns:
        types.GenerateVideosResponse: The response containing generated video(s).

    Raises:
        ClientError: If the generation fails due to API or validation errors.
    """

    media_files_bucket_gs_uri = os.getenv("MEDIA_FILES_BUCKET_GCS_URI", None)
    if not media_files_bucket_gs_uri:
        raise ValueError("MEDIA_FILES_BUCKET_GCS_URI environment variable is not set.")

    image_input = None
    if gcs_image_uri:
        image_input = types.Image(
            gcs_uri=gcs_image_uri,
            mime_type="image/png"
        )

    # Launch video generation
    video_generation_operation = genai_client.models.generate_videos(
        model=os.getenv("VEO2_MODEL_ID", "veo-3.0-generate-preview"),
        prompt=prompt,
        image=image_input,
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            person_generation="allow_adult",
            aspect_ratio="16:9",
            duration_seconds=8,
            output_gcs_uri=media_files_bucket_gs_uri,
        ),
    )
    # Wait for the operation to complete
    while not video_generation_operation.done:
        time.sleep(20)
        video_generation_operation = genai_client.operations.get(video_generation_operation)
        if video_generation_operation.error:
            raise ClientError(f"Video generation failed: {video_generation_operation.error}")

    # Check the response for generated videos
    video_generation_operation_response = video_generation_operation.response
    if not video_generation_operation_response.generated_videos:
        raise RuntimeError("No videos were generated. Check the prompt and model configuration.")

    # Log the generated video details
    logger.info(f"Generated {len(video_generation_operation_response.generated_videos)} video(s).")
    return video_generation_operation_response.generated_videos[0].video

async def main():
    """
    Main entry point for the script.
    This function can be used to run the video generation process.
    """
    media_files_bucket_gs_uri = os.getenv("MEDIA_FILES_BUCKET_GCS_URI", None)

    test_image_path = "/Users/haruiz/open-source/ai-fashion-house/outputs/generated_image_1.png"
    async with aiofiles.open(test_image_path, "rb") as f:
        image_bytes = await f.read()
    image_mimetype = mimetypes.guess_type(test_image_path)[0]
    image_gcs_path = f"{media_files_bucket_gs_uri}/{os.path.basename(test_image_path)}"
    bucket_name, blob_path = parse_gcs_uri(image_gcs_path)
    upload_media_file_to_gcs(
        bucket_name=bucket_name,
        blob_path=blob_path,
        media_bytes=image_bytes,
        mime_type=image_mimetype
    )
    output = await generate_video(image_gcs_path)
    print(output)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

