import io
import os
import typing
from datetime import timedelta
from urllib.parse import urlparse

import aiohttp

from google import genai
from google.cloud import storage
import mimetypes
from PIL.Image import Image as PIlImage
from PIL import Image

def use_vertexai() -> bool:
    """
    Determines whether Vertex AI is being used, based on environment configuration.

    Returns:
        bool: True if Vertex AI is enabled, False otherwise.
    """
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() == "1"

def get_authenticated_genai_client() -> genai.Client:
    """
    Resolve and return a genai.Client instance based on environment configuration.

    If GOOGLE_GENAI_USE_VERTEXAI is set to "1" (case-insensitive), the client will be initialized
    using Vertex AI with GOOGLE_PROJECT_ID and GOOGLE_LOCATION.
    Otherwise, it uses the GOOGLE_API_KEY for standard API access.
    """
    if use_vertexai():
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")

        if not project_id or not location:
            raise EnvironmentError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set for Vertex AI usage.")

        return genai.Client(project=project_id, location=location)

    # Default to using API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY must be set when not using Vertex AI.")

    return genai.Client(api_key=api_key)


def parse_gcs_uri(gcs_uri: str) -> tuple[str, str]:
    """
    Parses a GCS URI and returns the bucket name and blob path.

    Args:
        gcs_uri (str): A URI in the format gs://bucket-name/path/to/blob

    Returns:
        tuple[str, str]: A tuple containing the bucket name and the blob path.
    """
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI. Must start with 'gs://'")

    # Remove 'gs://' prefix and split once at the first '/'
    parts = gcs_uri[5:].split("/", 1)

    if len(parts) != 2:
        raise ValueError("GCS URI must contain both bucket and object path")

    bucket_name = parts[0]
    blob_path = parts[1]

    return bucket_name, blob_path

def download_media_file_from_gcs(bucket_name: str, blob_path: str) -> tuple[bytes, str]:
    """
    Downloads an image or media file from GCS and returns its bytes and MIME type.

    Args:
        bucket_name (str): Name of the GCS bucket.
        blob_path (str): Path to the blob (object) within the bucket.

    Returns:
        tuple[bytes, str]: A tuple containing the media bytes and its MIME type.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download image bytes
    media_bytes = blob.download_as_bytes()

    # Try to detect MIME type from blob name
    mime_type, _ = mimetypes.guess_type(blob_path)
    if mime_type is None:
        # Fallback to GCS metadata (if available)
        blob.reload()
        mime_type = blob.content_type or "application/octet-stream"

    return media_bytes, mime_type


async def async_download_media_file_from_gcs(bucket_name: str, blob_path: str) -> tuple[bytes, str]:
    """
    Asynchronously downloads a media file from GCS using a signed URL and returns its bytes and MIME type.

    Args:
        bucket_name (str): The GCS bucket name.
        blob_path (str): The path to the blob in the bucket.

    Returns:
        tuple[bytes, str]: The media bytes and MIME type.
    """
    # Create GCS client and generate signed URL
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=10),
        method="GET"
    )

    # Try to infer MIME type
    mime_type, _ = mimetypes.guess_type(blob_path)
    if mime_type is None:
        blob.reload()
        mime_type = blob.content_type or "application/octet-stream"

    # Use aiohttp to download the file asynchronously
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download blob: {response.status}")
            media_bytes = await response.read()

    return media_bytes, mime_type

def upload_media_file_to_gcs(
    bucket_name: str, blob_path: str, media_bytes: bytes, mime_type: str
) -> None:
    """
    Uploads media bytes to a specified GCS bucket and blob path.

    Args:
        bucket_name (str): Name of the GCS bucket.
        blob_path (str): Path to the blob (object) within the bucket.
        media_bytes (bytes): The media file bytes to upload.
        mime_type (str): The MIME type of the media file.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    blob.upload_from_string(media_bytes, content_type=mime_type)



def load_gcs_image(gs_url: str, gcs_client: storage.Client) -> typing.Optional[PIlImage]:
    """
    Downloads and loads an image stored in Google Cloud Storage.

    Args:
        gs_url (str): GCS path in the form `gs://bucket_name/path/to/image`.
        gcs_client (storage.Client): An authenticated GCS client instance.

    Returns:
        Optional[PIL.Image.Image]: The downloaded image as a PIL object, or None if loading fails.
    """
    if gcs_client:
        gcs_client = storage.Client()
    parsed = urlparse(gs_url)
    bucket = gcs_client.bucket(parsed.netloc)
    blob = bucket.blob(parsed.path.lstrip("/"))
    img_bytes = blob.download_as_bytes()
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")
