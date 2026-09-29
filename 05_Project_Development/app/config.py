from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


@dataclass
class Settings:
    base_dir: Path
    templates_dir: Path
    exports_dir: Path

    gemini_api_key: str
    gemini_flash_model: str
    gemini_pro_model: str

    stability_api_key: str
    stability_model: str

    image_width: int
    image_height: int
    image_steps: int
    guidance_scale: float

    debug: bool


def _get_bool(value: str, default: bool = False) -> bool:
    if not value:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def get_settings() -> Settings:

    exports_dir = BASE_DIR / "exports"
    templates_dir = BASE_DIR / "templates"

    exports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return Settings(
        base_dir=BASE_DIR,

        templates_dir=templates_dir,

        exports_dir=exports_dir,

        gemini_api_key=os.getenv(
            "GEMINI_API_KEY",
            "",
        ),

        gemini_flash_model=os.getenv(
            "GEMINI_FLASH_MODEL",
            "gemini-3-flash-preview",
        ),

        gemini_pro_model=os.getenv(
            "GEMINI_PRO_MODEL",
            "gemini-3.1-pro-preview",
        ),

        stability_api_key=os.getenv(
            "STABILITY_API_KEY",
            "",
        ),

        stability_model=os.getenv(
            "STABILITY_MODEL",
            "stable-diffusion-v1-5",
        ),

        image_width=int(
            os.getenv(
                "IMAGE_WIDTH",
                "512",
            )
        ),

        image_height=int(
            os.getenv(
                "IMAGE_HEIGHT",
                "512",
            )
        ),

        image_steps=int(
            os.getenv(
                "IMAGE_STEPS",
                "30",
            )
        ),

        guidance_scale=float(
            os.getenv(
                "GUIDANCE_SCALE",
                "7.5",
            )
        ),

        debug=_get_bool(
            os.getenv(
                "DEBUG",
                "true",
            ),
            True,
        ),
    )


settings = get_settings()