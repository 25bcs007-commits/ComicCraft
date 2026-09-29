from __future__ import annotations

from pathlib import Path

from PIL import Image

from .config import get_settings


settings = get_settings()


def save_pdf(
    title: str,
    layout_path: str,
) -> str:

    image_path = Path(layout_path)

    if not image_path.exists():
        raise FileNotFoundError(
            "Comic layout image was not found."
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    safe_title = "".join(
        character
        if character.isalnum()
        else "_"
        for character in title
    )

    safe_title = (
        safe_title.strip("_")
        or "comic"
    )

    pdf_path = (
        settings.exports_dir /
        f"{safe_title}.pdf"
    )

    image.save(
        pdf_path,
        "PDF",
        resolution=100.0,
    )

    return (
        f"/download/{pdf_path.name}"
    )