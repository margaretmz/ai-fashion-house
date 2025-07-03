from typing import Optional

import aiofiles
from google.adk.tools import ToolContext
from google.genai import types


async def load_image_artifact(image_path: str, tool_context: Optional[ToolContext]) -> types.Part:
    """
    Load image artifact either from the ToolContext or directly from disk.

    Args:
        image_path (str): Path to the image file.
        tool_context (Optional[ToolContext]): Optional tool context to resolve artifacts.

    Returns:
        types.Part: A Part object containing the inline PNG image data.

    Raises:
        ValueError: If the artifact could not be found or the file doesn't exist.
    """
    if tool_context:
        image_artifact = await tool_context.load_artifact(image_path)
        if not image_artifact:
            raise ValueError(f"Artifact not found for: {image_path}")
        return image_artifact
    else:
        async with aiofiles.open(image_path, "rb") as f:
            image_data = await f.read()
        return types.Part(
            inline_data=types.Blob(mime_type="image/png", data=image_data)
        )
