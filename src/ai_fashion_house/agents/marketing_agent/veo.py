import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Any
from urllib.parse import urlparse

import aiofiles
import httpx
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Load environment variables
load_dotenv(find_dotenv())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CAPTION_PROMPT = (
    "Craft a vivid, high-fashion caption for this image. "
    "Be imaginative and meticulously descriptive—highlight the garment’s design, including every visible detail of the dress: "
    "its color, texture, fabric, silhouette, stitching, embellishments, and movement. "
    "If the model is visible, describe their appearance, pose, expression, and how they interact with the garment. "
    "If the model is not shown, assume the dress is worn by a tall, elegant runway model "
    "with confident posture and fluid motion, captured mid-stride under soft, ambient lighting. "
    "The caption should evoke the tone of a luxury fashion film or editorial spread. "
    "Focus on conveying the atmosphere of the scene while giving special attention to the dress’s craftsmanship, "
    "visual impact, and how it flows or reacts to the model’s movement."
)

VEO2_OUTPUT_GCS_URI = os.getenv("VEO2_OUTPUT_GCS_URI")


def use_vertexai() -> bool:
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() == "1"


def resolve_client_credentials() -> genai.Client:
    if use_vertexai():
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise EnvironmentError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set.")
        return genai.Client(project=project, location=location)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY must be set.")
    return genai.Client(api_key=api_key)


def parse_gcs_uri(gcs_url: str) -> tuple[str, str]:
    if not gcs_url.startswith("gs://"):
        raise ValueError(f"Invalid GCS URL: {gcs_url}")
    parsed = urlparse(gcs_url)
    return parsed.netloc, parsed.path.lstrip("/")


def fetch_video_bytes_from_gcs_url(gcs_url: str, gcs_client: Optional[storage.Client] = None) -> bytes:
    bucket_name, blob_path = parse_gcs_uri(gcs_url)
    gcs_client = gcs_client or storage.Client()
    blob = gcs_client.bucket(bucket_name).blob(blob_path)
    if not blob.exists():
        raise FileNotFoundError(f"Blob not found at {gcs_url}")
    return blob.download_as_bytes()


async def generate_reference_image_prompt(image_artifact: types.Part) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[image_artifact, types.Part.from_text(text=CAPTION_PROMPT)],
    )
    return response.text.strip()


async def upload_video_to_server(video_bytes: bytes, filename: str, upload_url: str):
    async with httpx.AsyncClient() as http:
        response = await http.post(
            upload_url,
            files={"file": (filename, video_bytes, "video/mp4")},
        )
        response.raise_for_status()
        return response.json()


async def save_generated_videos(
    response: types.GenerateVideosResponse,
    tool_context: Optional[ToolContext] = None,
    gcs_client: Optional[storage.Client] = None,
    save_to_disk: bool = False
) -> None:

    for idx, generated_video in enumerate(response.generated_videos):
        try:
            video_uri = generated_video.video.uri
            video_bytes = (
                fetch_video_bytes_from_gcs_url(video_uri, gcs_client)
                if use_vertexai()
                else client.files.download(file=generated_video.video)
            )

            if tool_context:
                artifact_name = f"generated_video_{idx + 1}.mp4"
                part = types.Part.from_bytes(mime_type="video/mp4",data=video_bytes)
                await tool_context.save_artifact(artifact_name, part)
                logger.info(f"Saved artifact: {artifact_name}")

            if save_to_disk:
                output_folder = Path(os.getenv("OUTPUT_FOLDER", "outputs"))
                output_folder.mkdir(parents=True, exist_ok=True)
                output_path = output_folder / f"generated_video_{idx + 1}.mp4"
                async with aiofiles.open(output_path, "wb") as out_file:
                    await out_file.write(video_bytes)
                logger.info(f"Saved video to disk: {output_path}")

        except Exception as e:
            logger.exception(f"Failed to save video {idx + 1}: {e}")
            raise RuntimeError(f"Failed to save video {idx + 1}: {e}")


# === Main Video Generation Function ===

async def generate_video(
    image_path: str,
    tool_context: Optional[ToolContext] = None,
    save_to_disk: bool = True
) -> dict[str, Any]:
    try:
        if tool_context:
            image_artifact = await tool_context.load_artifact(image_path)
            if not image_artifact:
                raise ValueError(f"Artifact not found for {image_path}")
        else:
            async with aiofiles.open(image_path, "rb") as f:
                image_data = await f.read()
            image_artifact = types.Part(inline_data=types.Blob(mime_type="image/png", data=image_data))

        prompt = await generate_reference_image_prompt(image_artifact)

        operation = client.models.generate_videos(
            model=os.getenv("VEO2_MODEL_ID", "veo-3.0-generate-preview"),
            prompt=prompt,
            image=image_artifact.file_data,
            config=types.GenerateVideosConfig(
                number_of_videos=2,
                person_generation="allow_adult",
                aspect_ratio="16:9",
                duration_seconds=8,
                output_gcs_uri=VEO2_OUTPUT_GCS_URI,
            ),
        )

        while not operation.done:
            await asyncio.sleep(20)
            operation = client.operations.get(operation)
            if operation.error:
                raise RuntimeError(operation.error.get("message"))

        await save_generated_videos(
            operation.response,
            tool_context,
            gcs_client,
            save_to_disk=save_to_disk
        )

        return {"status": "success", "message": "Video generated successfully"}

    except Exception as e:
        logger.exception("Error in generate_video")
        return {"status": "error", "message": str(e)}


client = resolve_client_credentials()
gcs_client = storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT")) if use_vertexai() else None

if __name__ == "__main__":
    test_image_path = "/Users/haruiz/open-source/ai-fashion-house/outputs/generated_image_1.png"
    asyncio.run(generate_video(
        test_image_path,
        save_to_disk=True# replace with your upload URL if needed
    ))
