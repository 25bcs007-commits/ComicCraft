from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Query,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import Jinja2Templates

from .config import get_settings
from .exporters import save_pdf
from .ai.gemini_flash import generate_outline
from .ai.gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .models import (
    ComicResponse,
    PromptRequest,
)


# ================================================================
# ROUTER
# ================================================================

router = APIRouter()

settings = get_settings()

templates = Jinja2Templates(
    directory=str(settings.templates_dir)
)


# ================================================================
# GENERATE COMPLETE COMIC
# ================================================================

def _generate_comic(
    request_data: PromptRequest,
):

    # ============================================================
    # STEP 1 - Generate story outline
    # ============================================================

    outline = generate_outline(
        request_data
    )

    # ============================================================
    # STEP 2 - Generate complete story / panels
    # ============================================================

    story = generate_story(
        request_data,
        outline,
    )

    # ============================================================
    # STEP 3 - Remove OLD panel images
    #
    # This prevents old panel_6.png, panel_7.png etc.
    # from confusing the browser.
    # ============================================================

    for old_panel in settings.exports_dir.glob(
        "panel_*.png"
    ):

        try:

            old_panel.unlink()

            print(
                f"Deleted old image: {old_panel.name}"
            )

        except Exception as exc:

            print(
                f"Could not delete "
                f"{old_panel.name}: {exc}"
            )

    # ============================================================
    # STEP 4 - Generate image for EVERY panel
    #
    # IMPORTANT:
    #
    # We use enumerate() here.
    #
    # index = 0 -> panel_1.png
    # index = 1 -> panel_2.png
    # index = 2 -> panel_3.png
    # index = 3 -> panel_4.png
    # index = 4 -> panel_5.png
    #
    # Do NOT use panel.panel_number here because the panel
    # number is already 1-based.
    # ============================================================

    image_paths = []

    for index, panel in enumerate(story):

        print(
            f"Generating image for "
            f"Panel {index + 1}..."
        )

        image_path = generate_image(
            panel.image_prompt,
            index,
        )

        image_paths.append(
            image_path
        )

        print(
            f"Panel {index + 1} image: "
            f"{image_path}"
        )

    # ============================================================
    # STEP 5 - Build combined comic layout
    # ============================================================

    layout = build_comic_layout(
        story,
        image_paths,
    )

    # ============================================================
    # STEP 6 - Create comic title
    # ============================================================

    title = (
        f"{request_data.character_name}'s "
        "Comic Adventure"
    )

    # ============================================================
    # STEP 7 - Create PDF
    # ============================================================

    pdf_url = save_pdf(
        title,
        layout,
    )

    # ============================================================
    # STEP 8 - Create browser-friendly panel data
    # ============================================================

    panels = []

    for index, panel in enumerate(story):

        image_url = None

        # --------------------------------------------------------
        # Get corresponding generated image
        # --------------------------------------------------------

        if index < len(image_paths):

            image_path = image_paths[index]

            if image_path:

                filename = Path(
                    str(image_path)
                ).name

                image_file = (
                    settings.exports_dir /
                    filename
                )

                # ------------------------------------------------
                # Confirm file really exists
                # ------------------------------------------------

                if image_file.exists():

                    image_url = (
                        f"/static/{filename}"
                    )

                    print(
                        f"Panel {index + 1}: "
                        f"{image_url}"
                    )

                else:

                    print(
                        f"WARNING: Image file "
                        f"not found: {image_file}"
                    )

        # --------------------------------------------------------
        # Add panel information
        # --------------------------------------------------------

        panels.append(
            {
                "panel_number": index + 1,

                "description": (
                    panel.description
                    if panel.description
                    else ""
                ),

                "dialogue": (
                    panel.dialogue
                    if panel.dialogue
                    else ""
                ),

                "image_prompt": (
                    panel.image_prompt
                    if panel.image_prompt
                    else ""
                ),

                "image": image_url,
            }
        )

    # ============================================================
    # RETURN EVERYTHING
    # ============================================================

    return (
        title,
        story,
        layout,
        pdf_url,
        panels,
    )


# ================================================================
# HOME PAGE
# ================================================================

@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "ComicCraft",
            "error": None,
        },
    )


# ================================================================
# GENERATE COMIC FROM HTML FORM
# ================================================================

@router.post(
    "/generate",
    response_class=HTMLResponse,
)
def generate_form(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    try:

        # --------------------------------------------------------
        # Create request object
        # --------------------------------------------------------

        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        # --------------------------------------------------------
        # Generate complete comic
        # --------------------------------------------------------

        (
            title,
            story,
            layout,
            pdf_url,
            panels,
        ) = _generate_comic(
            data
        )

        # --------------------------------------------------------
        # Show comic preview page
        # --------------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": title,

                "layout": layout,

                "panels": panels,

                "story": story,

                "pdf_url": pdf_url,
            },
        )

    except Exception as exc:

        print(
            "ERROR while generating comic:"
        )

        print(exc)

        if settings.debug:

            traceback.print_exc()

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "ComicCraft",

                "error": str(exc),
            },
            status_code=500,
        )


# ================================================================
# JSON API
# ================================================================

@router.post(
    "/generate-comic/json",
    response_model=ComicResponse,
)
def generate_json(
    data: PromptRequest,
):

    try:

        (
            title,
            story,
            layout,
            pdf_url,
            panels,
        ) = _generate_comic(
            data
        )

        return ComicResponse(
            success=True,

            title=title,

            panels=story,

            pdf_url=pdf_url,
        )

    except Exception as exc:

        print(
            "ERROR in JSON comic generation:"
        )

        print(exc)

        if settings.debug:

            traceback.print_exc()

        raise HTTPException(
            status_code=500,

            detail=str(exc),
        ) from exc


# ================================================================
# TEST IMAGE GENERATION
# ================================================================

@router.get(
    "/test-image",
)
def test_image(
    prompt: str = Query(
        "a brave fox exploring "
        "an enchanted forest, "
        "colorful comic panel"
    ),
):

    try:

        path = generate_image(
            prompt,
            0,
        )

        return {
            "success": True,

            "image_path": path,
        }

    except Exception as exc:

        if settings.debug:

            traceback.print_exc()

        raise HTTPException(
            status_code=500,

            detail=str(exc),
        ) from exc


# ================================================================
# EXPORT SUCCESS PAGE
# ================================================================

@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
def export_success(
    request: Request,

    pdf_url: str = "",
):

    return templates.TemplateResponse(
        request=request,

        name="export_success.html",

        context={
            "pdf_url": pdf_url
        },
    )


# ================================================================
# DOWNLOAD PDF
# ================================================================

@router.get(
    "/download/{filename}"
)
def download_pdf(
    filename: str,
):

    # ------------------------------------------------------------
    # Prevent directory traversal
    # ------------------------------------------------------------

    safe_name = (
        filename
        .replace("/", "")
        .replace("\\", "")
    )

    file_path = (
        settings.exports_dir /
        safe_name
    )

    # ------------------------------------------------------------
    # Check PDF exists
    # ------------------------------------------------------------

    if (
        not file_path.exists()
        or file_path.suffix.lower() != ".pdf"
    ):

        raise HTTPException(
            status_code=404,

            detail="PDF not found.",
        )

    # ------------------------------------------------------------
    # Return PDF
    # ------------------------------------------------------------

    return FileResponse(
        path=file_path,

        media_type="application/pdf",

        filename=file_path.name,
    )