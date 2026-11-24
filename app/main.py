"""Web server: serves the page and streams one estimate as it is built.

Run from the repo folder:  uvicorn app.main:app --port 8050
"""

from __future__ import annotations

import json

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import card, config, pipeline, safety
from .data import load_physician_fees, load_prices, load_workups, validate_data
from .models import EstimateRequest

app = FastAPI(title="ED Cost Estimator")



class FreshStaticFiles(StaticFiles):
    """Static files the browser re-checks on every load, so an edit never leaves an old script running."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


EXAMPLES = [
    {"label": "Twisted ankle", "complaint": "I rolled my ankle playing soccer an hour ago. It's swollen and hurts to walk on.", "insurance": "Blue Cross through my job"},
    {"label": "Chest pain", "complaint": "My dad is 58 and has had chest pressure for the last 30 minutes.", "insurance": "Aetna"},
    {"label": "Belly pain", "complaint": "Sharp pain in the lower right side of my belly since last night, with nausea.", "insurance": "Cigna"},
    {"label": "Cut finger", "complaint": "I cut my finger with a kitchen knife and I think it needs stitches.", "insurance": "no insurance"},
    {"label": "Cough and fever", "complaint": "I'm 72 with a fever and a bad cough for three days, and I feel weak.", "insurance": "Medicare Advantage - UHC"},
]


@app.get("/api/meta")
def meta() -> dict:
    prices = load_prices()
    return {
        "hospital": prices.hospital, "last_updated": prices.last_updated, "payers": prices.payers,
        "services": len(prices.services), "scenarios": len(load_workups()), "model": config.MODEL_NAME,
        "api_key_found": config.has_api_key(), "saves_text": config.SAVE_TEST_RUNS,
        "examples": EXAMPLES, "max_input_chars": config.MAX_INPUT_CHARS,
        "physician_fees_loaded": bool(load_physician_fees()), "data_problems": validate_data(),
        "limits": {"requests_per_run": config.MAX_REQUESTS_PER_RUN, "tokens_per_run": config.MAX_TOKENS_PER_RUN,
                   "runs_per_minute": config.MAX_RUNS_PER_MINUTE, "tokens_per_day": config.MAX_TOKENS_PER_DAY},
    }


def visitor(request: Request) -> str:
    # Behind a tunnel or proxy every visitor arrives from the same local address, so use the
    # visitor's own address when the proxy passes it along. This only feeds the rate limit.
    forwarded = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


@app.post("/api/read-card")
async def read_card(req: card.CardRequest, request: Request) -> JSONResponse:
    """Read plan details off a photo of an insurance card. The photo is used for one model call and never stored."""
    return JSONResponse(await card.read_card(req.image, visitor(request)), headers={"Cache-Control": "no-store"})


@app.post("/api/estimate")
async def estimate(req: EstimateRequest, request: Request) -> StreamingResponse:
    client = visitor(request)

    async def stream():
        async for event in pipeline.run_estimate(req, client):
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@app.get("/api/usage")
def usage() -> JSONResponse:
    return JSONResponse({"tokens_today": safety.tokens_today(), "runs": pipeline.recent_runs()})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


app.mount("/static", FreshStaticFiles(directory=config.STATIC_DIR), name="static")
