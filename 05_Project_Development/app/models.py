from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    story_prompt: str = Field(
        ...,
        min_length=1,
        description="Main story idea"
    )

    character_name: str = Field(
        ...,
        min_length=1,
        description="Main character name"
    )

    setting: str = Field(
        ...,
        min_length=1,
        description="Story setting"
    )

    tone: str = Field(
        ...,
        min_length=1,
        description="Story tone"
    )

    art_style: str = Field(
        ...,
        min_length=1,
        description="Comic art style"
    )


class ComicPanel(BaseModel):
    panel_number: int
    description: str
    dialogue: str = ""
    image_prompt: str


class ComicResponse(BaseModel):
    success: bool
    title: str
    panels: List[ComicPanel]
    pdf_url: str = ""