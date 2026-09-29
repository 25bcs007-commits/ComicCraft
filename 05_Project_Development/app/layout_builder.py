from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont

from .config import get_settings
from .models import ComicPanel


settings = get_settings()


def _font(size: int):

    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]

    for candidate in candidates:

        if Path(candidate).exists():

            try:
                return ImageFont.truetype(
                    candidate,
                    size,
                )
            except Exception:
                pass

    return ImageFont.load_default()


def build_comic_layout(
    story: List[ComicPanel],
    image_paths: List[str],
) -> str:

    panel_width = 512
    panel_height = 420

    page_width = panel_width * 2
    page_height = panel_height * 3

    page = Image.new(
        "RGB",
        (
            page_width,
            page_height,
        ),
        "white",
    )

    draw = ImageDraw.Draw(page)

    title_font = _font(30)
    dialogue_font = _font(17)

    for index, panel in enumerate(story):

        if index >= len(image_paths):
            break

        try:

            image = Image.open(
                image_paths[index]
            ).convert("RGB")

            image.thumbnail(
                (
                    panel_width - 20,
                    320,
                )
            )

            x = (
                (index % 2) *
                panel_width
            ) + 10

            y = (
                (index // 2) *
                panel_height
            ) + 10

            page.paste(
                image,
                (
                    x,
                    y,
                ),
            )

            draw.rectangle(
                (
                    x,
                    y,
                    x + panel_width - 20,
                    y + 340,
                ),
                outline="black",
                width=3,
            )

            draw.text(
                (
                    x + 10,
                    y + 350,
                ),
                f"Panel {panel.panel_number}",
                fill="black",
                font=title_font,
            )

            dialogue = panel.dialogue[:80]

            draw.text(
                (
                    x + 10,
                    y + 385,
                ),
                dialogue,
                fill="black",
                font=dialogue_font,
            )

        except Exception:
            continue

    # Fifth panel can be centered at bottom.
    # This keeps the page layout simple.

    output = (
        settings.exports_dir /
        "comic_preview.png"
    )

    page.save(output)

    return str(output)