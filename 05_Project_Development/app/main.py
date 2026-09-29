from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routes import router


settings = get_settings()


app = FastAPI(
    title="ComicCraft AI",
    description=(
        "AI-powered comic story and "
        "comic panel generation application."
    ),
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(settings.exports_dir)
    ),
    name="static",
)


app.include_router(router)


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "application": "ComicCraft AI",
    }