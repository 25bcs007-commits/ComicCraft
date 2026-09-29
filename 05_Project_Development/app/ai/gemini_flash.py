from __future__ import annotations

import json
import re
from typing import List

from ..config import get_settings
from ..models import ComicPanel, PromptRequest


settings = get_settings()


def _extract_json(text: str):

    text = text.strip()

    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```",
        "",
        text,
    )

    text = re.sub(
        r"```$",
        "",
        text,
    )

    text = text.strip()

    return json.loads(text)


def _fallback_outline(
    request: PromptRequest,
) -> List[ComicPanel]:

    character = request.character_name
    setting = request.setting
    idea = request.story_prompt

    return [
        ComicPanel(
            panel_number=1,
            description=(
                f"{character} begins the adventure in "
                f"{setting}. The story starts with "
                f"{idea}."
            ),
            dialogue=f"Today, something amazing is going to happen!",
            image_prompt=(
                f"{character} in {setting}, "
                f"opening scene of a colorful comic, "
                f"{request.art_style}"
            ),
        ),

        ComicPanel(
            panel_number=2,
            description=(
                f"{character} discovers an unexpected "
                f"problem related to the adventure."
            ),
            dialogue="Wait... what is happening?",
            image_prompt=(
                f"{character} discovering a mysterious "
                f"problem in {setting}, "
                f"comic panel, {request.art_style}"
            ),
        ),

        ComicPanel(
            panel_number=3,
            description=(
                f"{character} faces the main challenge "
                f"and decides to be brave."
            ),
            dialogue="I won't give up!",
            image_prompt=(
                f"{character} facing a dramatic challenge "
                f"in {setting}, heroic comic scene, "
                f"{request.art_style}"
            ),
        ),

        ComicPanel(
            panel_number=4,
            description=(
                f"{character} finds a clever solution "
                f"and overcomes the challenge."
            ),
            dialogue="I've got an idea!",
            image_prompt=(
                f"{character} solving the problem "
                f"in {setting}, exciting comic panel, "
                f"{request.art_style}"
            ),
        ),

        ComicPanel(
            panel_number=5,
            description=(
                f"{character} successfully completes "
                f"the adventure and returns safely."
            ),
            dialogue="What an adventure!",
            image_prompt=(
                f"{character} celebrating after the adventure "
                f"in {setting}, happy ending comic panel, "
                f"{request.art_style}"
            ),
        ),
    ]


def generate_outline(
    request: PromptRequest,
) -> List[ComicPanel]:

    if not settings.gemini_api_key:
        return _fallback_outline(request)

    try:

        from google import genai

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        prompt = f"""
Create a five-panel comic outline.

Main story idea:
{request.story_prompt}

Character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Return ONLY valid JSON.

Format:

[
  {{
    "panel_number": 1,
    "description": "...",
    "dialogue": "...",
    "image_prompt": "..."
  }}
]

Create exactly 5 panels.
"""

        response = client.models.generate_content(
            model=settings.gemini_flash_model,
            contents=prompt,
        )

        raw_text = response.text or ""

        data = _extract_json(raw_text)

        panels = []

        for item in data[:5]:

            panels.append(
                ComicPanel(
                    panel_number=int(
                        item.get(
                            "panel_number",
                            len(panels) + 1,
                        )
                    ),
                    description=str(
                        item.get(
                            "description",
                            "",
                        )
                    ),
                    dialogue=str(
                        item.get(
                            "dialogue",
                            "",
                        )
                    ),
                    image_prompt=str(
                        item.get(
                            "image_prompt",
                            "",
                        )
                    ),
                )
            )

        if len(panels) == 5:
            return panels

    except Exception:
        if settings.debug:
            import traceback

            traceback.print_exc()

    return _fallback_outline(request)