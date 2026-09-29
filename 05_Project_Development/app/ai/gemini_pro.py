from __future__ import annotations

from typing import List

from ..config import get_settings
from ..models import ComicPanel, PromptRequest


settings = get_settings()


def generate_story(
    request: PromptRequest,
    outline: List[ComicPanel],
) -> List[ComicPanel]:

    if not settings.gemini_api_key:
        return outline

    try:

        from google import genai

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        outline_text = "\n".join(
            [
                (
                    f"Panel {panel.panel_number}: "
                    f"{panel.description} "
                    f"Dialogue: {panel.dialogue}"
                )
                for panel in outline
            ]
        )

        prompt = f"""
Expand this comic outline into polished five-panel
comic content.

Character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Original story:
{request.story_prompt}

Outline:
{outline_text}

Return exactly five panels.

For each panel provide:
- description
- dialogue
- image_prompt

Keep the same panel numbers.
"""

        response = client.models.generate_content(
            model=settings.gemini_pro_model,
            contents=prompt,
        )

        text = response.text or ""

        if text.strip():

            improved = []

            for panel in outline:

                improved.append(
                    ComicPanel(
                        panel_number=panel.panel_number,
                        description=panel.description,
                        dialogue=panel.dialogue,
                        image_prompt=panel.image_prompt,
                    )
                )

            return improved

    except Exception:

        if settings.debug:
            import traceback

            traceback.print_exc()

    return outline