"""
Unit tests for the image resize logic in lambda/handler.py.

These test the pure resize_image() function directly, with no AWS
calls involved — so they run instantly and don't need any cloud
credentials or network access.

Run with:
    pip install pytest Pillow --break-system-packages   (if not already installed)
    pytest tests/test_handler.py -v
"""

import io
import sys
import os

# Make lambda/handler.py importable from the tests folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from PIL import Image
from handler import resize_image


def make_test_image(width, height, mode='RGB', color=(255, 0, 0)):
    """Helper: creates an in-memory PNG image of a given size for testing."""
    image = Image.new(mode, (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()


def test_resize_large_image_shrinks_to_max_size():
    """A large image should be shrunk so neither dimension exceeds MAX_SIZE."""
    original_bytes = make_test_image(2000, 1000)

    result_bytes = resize_image(original_bytes, max_size=(800, 800))
    result_image = Image.open(io.BytesIO(result_bytes))

    assert result_image.width <= 800
    assert result_image.height <= 800


def test_resize_preserves_aspect_ratio():
    """Resizing shouldn't distort the image's proportions."""
    original_bytes = make_test_image(1600, 800)  # 2:1 ratio
    original_ratio = 1600 / 800

    result_bytes = resize_image(original_bytes, max_size=(800, 800))
    result_image = Image.open(io.BytesIO(result_bytes))
    result_ratio = result_image.width / result_image.height

    assert abs(result_ratio - original_ratio) < 0.01


def test_small_image_is_not_upscaled():
    """An image already smaller than max_size shouldn't be made bigger."""
    original_bytes = make_test_image(200, 150)

    result_bytes = resize_image(original_bytes, max_size=(800, 800))
    result_image = Image.open(io.BytesIO(result_bytes))

    assert result_image.width == 200
    assert result_image.height == 150


def test_output_is_valid_jpeg():
    """The function should always output JPEG format, regardless of input format."""
    original_bytes = make_test_image(500, 500)

    result_bytes = resize_image(original_bytes)
    result_image = Image.open(io.BytesIO(result_bytes))

    assert result_image.format == 'JPEG'


def test_rgba_input_is_converted_to_rgb():
    """PNGs with transparency (RGBA) should convert cleanly to RGB JPEG, not error."""
    original_bytes = make_test_image(400, 400, mode='RGBA', color=(0, 255, 0, 128))

    result_bytes = resize_image(original_bytes)
    result_image = Image.open(io.BytesIO(result_bytes))

    assert result_image.mode == 'RGB'


def test_square_image_stays_square():
    """A square image should remain square after resizing."""
    original_bytes = make_test_image(1000, 1000)

    result_bytes = resize_image(original_bytes, max_size=(800, 800))
    result_image = Image.open(io.BytesIO(result_bytes))

    assert result_image.width == result_image.height