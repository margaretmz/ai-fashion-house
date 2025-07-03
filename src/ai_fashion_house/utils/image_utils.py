import base64
import io
import math

from PIL.Image import Image as PILImage
from PIL import Image, ImageOps
from typing import  List

from google.cloud import storage

from ai_fashion_house.utils.gcp_utils import load_gcs_image

import logging

logger = logging.getLogger(__name__)


def pil_image_to_base64(image: PILImage, format: str = "PNG") -> bytes:
    """
    Converts a Pillow image to a base64-encoded string.

    Args:
        image (PIL.Image.Image): The image to encode.
        format (str): Format for encoding (e.g., "PNG", "JPEG"). Defaults to "PNG".

    Returns:
        str: Base64-encoded image string (without data URI prefix).
    """
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    encoded_bytes = base64.b64encode(img_bytes)
    return encoded_bytes

def pil_image_to_png_bytes(image: PILImage, format: str = "PNG") -> bytes:
    """
    Converts a Pillow image to raw PNG bytes in memory.

    Args:
        image (PIL.Image.Image): The image to convert.
        format (str): Format for encoding (default is "PNG").

    Returns:
        bytes: PNG-encoded image bytes.
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer.read()



def add_pill_image_border_and_shadow(image: PILImage, border_size: int = 10, shadow_offset: tuple = (10, 10), shadow_blur_radius: int = 10, shadow_color: tuple = (0, 0, 0, 128)) -> Image.Image:
    """
    Adds a border and a drop shadow to the input image.

    Args:
        image (Image.Image): The input PIL image.
        border_size (int): The width of the border to add.
        shadow_offset (tuple): The (x, y) offset of the shadow.
        shadow_blur_radius (int): How blurry the shadow should be.
        shadow_color (tuple): RGBA color for the shadow.

    Returns:
        Image.Image: A new image with border and shadow applied.
    """
    # Add border
    bordered = ImageOps.expand(image, border=border_size, fill='white')

    # Create shadow base image
    total_width = bordered.width + abs(shadow_offset[0]) + shadow_blur_radius * 2
    total_height = bordered.height + abs(shadow_offset[1]) + shadow_blur_radius * 2

    background = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

    # Create shadow image
    shadow = Image.new('RGBA', bordered.size, shadow_color)
    shadow_pos = (shadow_offset[0] + shadow_blur_radius, shadow_offset[1] + shadow_blur_radius)
    image_pos = (shadow_blur_radius, shadow_blur_radius)

    # Composite shadow and bordered image onto the background
    background.paste(shadow, shadow_pos, shadow)
    background.paste(bordered, image_pos, bordered.convert('RGBA'))

    return background.convert("RGB")

def concat_images_v(im_list: List[PILImage], resample: int = Image.Resampling.BICUBIC) -> PILImage:
    """
    Concatenate images vertically with multiple resize.

    Args:
        im_list (List[Image.Image]): List of images to concatenate.
        resample (int): Resample method.

    Returns:
        Image.Image: Concatenated image.
    """
    min_width = min(im.width for im in im_list)
    im_list_resize = [
        im.resize((min_width, int(im.height * min_width / im.width)), resample=resample)
        for im in im_list
    ]
    total_height = sum(im.height for im in im_list_resize)
    dst = Image.new("RGB", (min_width, total_height))
    pos_y = 0
    for im in im_list_resize:
        dst.paste(im, (0, pos_y))
        pos_y += im.height
    return dst

def concat_images_h(im_list: List[PILImage], resample: int = Image.Resampling.BICUBIC) -> Image.Image:
    """
    Concatenate images horizontally with multiple resize.

    Args:
        im_list (List[Image.Image]): List of images to concatenate.
        resample (int): Resample method.

    Returns:
        Image.Image: Concatenated image.
    """
    min_height = min(im.height for im in im_list)
    im_list_resize = [
        im.resize(
            (int(im.width * min_height / im.height), min_height), resample=resample
        )
        for im in im_list
    ]
    total_width = sum(im.width for im in im_list_resize)
    dst = Image.new("RGB", (total_width, min_height))
    pos_x = 0
    for im in im_list_resize:
        dst.paste(im, (pos_x, 0))
        pos_x += im.width
    return dst

def make_images_grid_from_2dlist(im_list_2d: List[List[PILImage]], resample: int = Image.Resampling.BICUBIC) -> PILImage:
    """
    Concatenate images in a 2D list/tuple of images, with multiple resize.

    Args:
        im_list_2d (List[List[Image.Image]]): 2D list of images to concatenate.
        resample (int): Resample method.

    Returns:
        Image.Image: Concatenated image.
    """
    im_list_v = [
        concat_images_h(im_list_h, resample=resample) for im_list_h in im_list_2d
    ]
    return concat_images_v(im_list_v, resample=resample)


def make_images_grid(images_list: List[PILImage], num_cols: int, resample: int = Image.Resampling.BICUBIC) ->PILImage:
    """
    Make a grid of images.

    Args:
        images_list (List[Image.Image]): List of images.
        num_cols (int): Number of columns.
        resample (int): Resample method.

    Returns:
        Image.Image: Grid of images.
    """
    num_rows = math.ceil(len(images_list) / num_cols)
    images_list_2d = [
        images_list[i * num_cols : (i + 1) * num_cols] for i in range(num_rows)
    ]
    return make_images_grid_from_2dlist(images_list_2d, resample=resample)



def create_moodboard(
    image_urls: List[str],
    columns: int = 4,
    gcs_client : storage.Client = None
) -> Image.Image:
    """
    Creates a moodboard from GCS image URLs using Pillow without cropping the images.
    Resizes each image to fit within the thumbnail box while maintaining aspect ratio.
    Images are arranged in a grid, centered in their cells, with consistent padding and outer margin.

    Args:
        image_urls (List[str]): List of GCS image URLs (gs://...).
        columns (int): Number of columns in the moodboard grid.
        gcs_client (storage.Client): Optional GCS client for loading images. If None, uses default client.

    Returns:
        PIL.Image.Image: The moodboard image assembled in memory.
    """
    if not image_urls:
        raise ValueError("No images provided for moodboard.")
    moodboard_images = []
    for i, url in enumerate(image_urls):
        img = load_gcs_image(url, gcs_client=gcs_client)
        if img:
            img = add_pill_image_border_and_shadow(img, border_size=10)
            img.thumbnail(
                (800, 600),  # Resize to fit within a 300x300 box
                resample=Image.Resampling.LANCZOS
            )
            moodboard_images.append(img)
        else:
            logger.warning(f"[⚠️] Skipping unavailable image: {url}")
    board = make_images_grid(
        moodboard_images,
        num_cols=columns,
        resample=Image.Resampling.LANCZOS
    )
    return board
