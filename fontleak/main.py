from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from .schemas import LeakParams, StaticParams, settings
from .logger import logger

app = FastAPI(
    title="fontleak",
    version="0.1.0",
    description="Fontleak server: Fast exfiltration of text using CSS and Ligatures"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request, params: LeakParams = Depends()):
    logger.debug("Handling index request with params: %s", params)
    return {
        "host": settings.host,
        **params.model_dump()
    }

@app.get("/static")
async def generate_static_payload(params: StaticParams = Depends()):
    logger.debug("Generating static payload with params: %s", params)
    return {
        "host": settings.host,
        **params.model_dump()
    }