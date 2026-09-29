from __future__ import annotations

import base64
import traceback
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from google import genai

from .config import get_settings


settings = get_settings()


# ---------------------------------------------------------
# FONT
# ---------------------------------------------------------

def _get_font(size: int):

    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]

    for font_path in candidates:

        if Path(font_path).exists():

            try:
                return ImageFont.truetype(
                    font_path,
                    size,
                )

            except Exception:
                pass

    return ImageFont.load_default()


# ---------------------------------------------------------
# PLACEHOLDER IMAGE
# ---------------------------------------------------------

def _create_placeholder_image(
    prompt: str,
    panel_number: int,
) -> str:

    width = settings.image_width
    height = settings.image_height

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    title_font = _get_font(28)
    body_font = _get_font(18)

    draw.rectangle(
        (
            10,
            10,
            width - 10,
            height - 10,
        ),
        outline="black",
        width=4,
    )

    draw.text(
        (30, 30),
        f"Comic Panel {panel_number + 1}",
        fill="black",
        font=title_font,
    )

    clean_prompt = prompt[:350]

    words = clean_prompt.split()

    lines = []
    current = ""

    for word in words:

        test = (
            current + " " + word
        ).strip()

        if len(test) > 38:

            if current:
                lines.append(current)

            current = word

        else:

            current = test

    if current:
        lines.append(current)

    y = 100

    for line in lines[:10]:

        draw.text(
            (30, y),
            line,
            fill="black",
            font=body_font,
        )

        y += 30

    filename = (
        f"panel_{panel_number + 1}.png"
    )

    path = (
        settings.exports_dir /
        filename
    )

    image.save(
        path,
        format="PNG",
    )

    return str(path)


# ---------------------------------------------------------
# GEMINI IMAGE GENERATION
# ---------------------------------------------------------

def _generate_with_gemini(
    prompt: str,
    panel_number: int,
) -> str | None:

    if not settings.gemini_api_key:

        print(
            "ERROR: Gemini API key is missing."
        )

        return None

    try:

        print(
            f"Generating Gemini image "
            f"for panel {panel_number + 1}..."
        )

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        image_prompt = f"""
Create a single high-quality comic book illustration.

Scene:
{prompt}

Visual requirements:

- colorful comic book illustration
- detailed environment
- expressive characters
- clear facial expressions
- cinematic composition
- vibrant colors
- clean comic line art
- visually attractive
- suitable for a student AI comic project
- one complete comic panel
- no text
- no speech bubbles
- no captions
- no watermark
"""

        # Gemini currently returns JPEG for this image
        # generation response format.
        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=image_prompt,
            response_format={
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "1:1",
                "image_size": "1K",
            },
        )

        output_image = getattr(
            interaction,
            "output_image",
            None,
        )

        if output_image is None:

            print(
                "ERROR: Gemini did not return an image."
            )

            return None

        image_data = getattr(
            output_image,
            "data",
            None,
        )

        if not image_data:

            print(
                "ERROR: Gemini image data is empty."
            )

            return None

        # -------------------------------------------------
        # Decode Gemini Base64 image
        # -------------------------------------------------

        image_bytes = base64.b64decode(
            image_data
        )

        # -------------------------------------------------
        # Convert Gemini JPEG → PNG
        #
        # This is important because ComicCraft uses
        # .png files for panel images.
        # -------------------------------------------------

        image = Image.open(
            BytesIO(image_bytes)
        )

        image = image.convert(
            "RGB"
        )

        filename = (
            f"panel_{panel_number + 1}.png"
        )

        path = (
            settings.exports_dir /
            filename
        )

        image.save(
            path,
            format="PNG",
        )

        print(
            f"SUCCESS: Gemini image generated: "
            f"{path}"
        )

        return str(path)

    except Exception as exc:

        print(
            "Gemini image generation failed:"
        )

        print(exc)

        if settings.debug:

            traceback.print_exc()

        return None


# ---------------------------------------------------------
# MAIN IMAGE GENERATION FUNCTION
# ---------------------------------------------------------

def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    # First try Gemini image generation.
    generated = _generate_with_gemini(
        prompt,
        panel_number,
    )

    if generated:

        return generated

    # If Gemini fails, use a placeholder
    # instead of crashing the complete comic generation.
    print(
        "Using placeholder image because "
        "Gemini image generation failed."
    )

    return _create_placeholder_image(
        prompt,
        panel_number,
    )