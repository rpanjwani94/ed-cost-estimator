"""Reads a photo of an insurance card into the plan details the estimator needs.

A fifth agent, separate from the estimate pipeline: it runs only when the patient asks, sees one image, has
no tools, and can return nothing but an insurer name and four numbers. The photo is held in memory for the one
model call and is never written to disk or to a log. The member's name and ID have no field to land in.
"""

from __future__ import annotations

import base64
import binascii
import os
import re
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent, UsageLimits
from pydantic_ai.exceptions import ModelAuthenticationError, UsageLimitExceeded

from . import config, safety
from .data import load_prices

MAX_CARD_BYTES = 4_000_000
MAX_CARD_TOKENS = 20_000
_DATA_URL = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,(.+)$", re.DOTALL)
_MAGIC = {"image/jpeg": (b"\xff\xd8\xff",), "image/png": (b"\x89PNG\r\n\x1a\n",), "image/webp": (b"RIFF",)}


class CardRequest(BaseModel):
    image: str = Field(max_length=6_000_000, description="The photo as a data URL (JPEG, PNG or WebP)")


class CardDetails(BaseModel):
    """What the card reader may return. There is deliberately no field for a name or a member ID."""

    is_insurance_card: bool
    insurer: str | None = Field(default=None, max_length=80)
    matched_insurer: str | None = Field(default=None, max_length=80)
    er_copay: float | None = Field(default=None, ge=0, le=5000)
    deductible: float | None = Field(default=None, ge=0, le=50000)
    coinsurance_pct: float | None = Field(default=None, ge=0, le=100)
    oop_max: float | None = Field(default=None, ge=0, le=100000)
    not_found: list[str] = Field(default_factory=list, max_length=6)


@lru_cache(maxsize=1)
def get_reader() -> Agent[None, CardDetails]:
    return Agent(config.build_model(), name="card_reader", output_type=CardDetails, instructions=config.load_prompt("card"),
                 model_settings=config.model_settings(), retries=1)


def decode_image(data_url: str) -> tuple[bytes, str] | str:
    """Return (bytes, media type), or a message saying why the upload was refused. No model is called here."""
    match = _DATA_URL.match(data_url or "")
    if not match:
        return "Please choose a photo (JPEG, PNG or WebP)."
    media_type, payload = match.groups()
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return "That file could not be read as a photo. Please try another one."
    if len(raw) > MAX_CARD_BYTES:
        return "That photo is too large. Please use one under 4 MB."
    if not raw.startswith(_MAGIC[media_type]) or (media_type == "image/webp" and raw[8:12] != b"WEBP"):
        return "That file does not look like a photo. Please try another one."
    return raw, media_type


def clean(details: CardDetails, payers: list[str]) -> dict[str, Any]:
    """Checks in plain code on what the model returned, before anything reaches the page."""
    if not details.is_insurance_card:
        return {"ok": True, "is_insurance_card": False}
    matched = next((p for p in payers if details.matched_insurer and p.lower() == details.matched_insurer.strip().lower()), None)
    insurer = safety.scrub_data(safety.normalize(details.insurer or ""))[0][:80]
    if insurer == "[text removed]" or safety.check_input("placeholder text", insurer):  # words on a card are never trusted as text
        insurer = ""
    money = lambda v: None if v is None else round(float(v))  # noqa: E731
    return {
        "ok": True, "is_insurance_card": True, "insurer": insurer, "matched_insurer": matched,
        "er_copay": money(details.er_copay), "deductible": money(details.deductible),
        "coinsurance_pct": money(details.coinsurance_pct), "oop_max": money(details.oop_max),
        "not_found": [safety.normalize(n)[:40] for n in details.not_found if not safety.scrub_data(n)[1]][:6],
    }


async def read_card(data_url: str, client: str = "local") -> dict[str, Any]:
    """Read one card photo. Returns the cleaned details, or {"ok": False, "message": ...}."""
    from .pipeline import explain_error, log_run  # imported here: pipeline imports the agents

    decoded = decode_image(data_url)
    if isinstance(decoded, str):
        return {"ok": False, "message": decoded}
    refusal = safety.check_budget(client)
    if refusal:
        return {"ok": False, "message": refusal}
    raw, media_type = decoded
    payers = load_prices().payers
    prompt = ["Read this insurance card.\n\nINSURER LIST (copy one exactly into matched_insurer, or use null):\n" + "\n".join(payers),
              BinaryContent(data=raw, media_type=media_type)]
    started = time.monotonic()
    record: dict[str, Any] = {"run_id": f"{int(time.time()):x}-{os.urandom(2).hex()}", "model": config.MODEL_NAME,
                              "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    limits = UsageLimits(request_limit=3, total_tokens_limit=MAX_CARD_TOKENS)
    try:
        try:
            result = await get_reader().run(prompt, usage_limits=limits, timeout=config.AGENT_TIMEOUT_SECONDS)
        except ModelAuthenticationError:
            if not config.use_openai_fallback():  # Portkey rejected its key: switch to the OpenAI key once
                raise
            from .agents import get_team
            get_team.cache_clear(); get_reader.cache_clear()
            record["model"] = config.MODEL_NAME
            result = await get_reader().run(prompt, usage_limits=limits, timeout=config.AGENT_TIMEOUT_SECONDS)
    except UsageLimitExceeded:
        log_run({**record, "outcome": "card_stopped_at_limit", "seconds": round(time.monotonic() - started, 2)})
        return {"ok": False, "message": "Reading the card took more work than allowed. Please type the details in instead."}
    except Exception as e:  # noqa: BLE001 - every failure becomes a plain message; the photo is never echoed back
        log_run({**record, "outcome": "card_error", "error": type(e).__name__, "seconds": round(time.monotonic() - started, 2)})
        return {"ok": False, "message": explain_error(e).replace("building the estimate", "reading the card")}
    usage = result.usage
    tokens = {"input_tokens": usage.input_tokens or 0, "cached_input_tokens": getattr(usage, "cache_read_tokens", 0) or 0,
              "output_tokens": usage.output_tokens or 0}
    safety.add_tokens(tokens["input_tokens"] + tokens["output_tokens"])
    out = clean(result.output, payers)
    # The log keeps what was found, never the values, the insurer or the photo.
    found = [k for k in ("er_copay", "deductible", "coinsurance_pct", "oop_max") if out.get(k) is not None]
    log_run({**record, "outcome": "card_read" if out["is_insurance_card"] else "card_not_a_card", "fields_found": found,
             "totals": tokens, "seconds": round(time.monotonic() - started, 2)})
    return {**out, "tokens": tokens["input_tokens"] + tokens["output_tokens"]}
