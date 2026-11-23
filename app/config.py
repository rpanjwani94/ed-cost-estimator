"""Environment, paths, the model, and the limits that keep token use in check."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent

# Secrets: look for .env in this repo folder first, then in the folder one level above (where the
# teaching staff keep theirs). This folder's file wins over the one above, and both win over the
# shell, so editing .env always takes effect.
ENV_FILES_FOUND = [p for p in (ROOT / ".env", ROOT.parent / ".env") if p.is_file()]
_from_files: dict[str, str] = {}
for _env in reversed(ENV_FILES_FOUND):
    _from_files.update({k: v for k, v in dotenv_values(_env).items() if v})
os.environ.update(_from_files)
# If a .env file names an API key, it decides which service is used: a different key left in the
# shell (for example an old PORTKEY_API_KEY in ~/.zshrc) is ignored.
_KEY_NAMES = ("PORTKEY_API_KEY", "OPENAI_API_KEY")
if any(name in _from_files for name in _KEY_NAMES):
    for _name in _KEY_NAMES:
        if _name not in _from_files:
            os.environ.pop(_name, None)
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
PROMPTS_DIR = APP_DIR / "prompts"
STATIC_DIR = APP_DIR / "static"

# Data. PRICE_FILE can point at a freshly extracted file; the small test dataset ships in the repo.
PRICE_FILE = Path(os.getenv("PRICE_FILE") or DATA_DIR / "ynhh_ed_standard_charges.csv")
CATALOG_FILE = DATA_DIR / "service_catalog.csv"
WORKUPS_FILE = DATA_DIR / "workups.json"
GUIDANCE_FILE = DATA_DIR / "guidance.json"
PHYSICIAN_FEES_FILE = DATA_DIR / "physician_fees.csv"
USAGE_LOG = Path(os.getenv("USAGE_LOG") or OUTPUT_DIR / "usage_log.jsonl")
# Test mode (off unless SAVE_TEST_RUNS=1): also save what testers type and what the app decided,
# so the warning screen and scenarios can be reviewed. The page tells the user when this is on.
SAVE_TEST_RUNS = os.getenv("SAVE_TEST_RUNS", "").strip().lower() in ("1", "true", "yes", "on")
TEST_RUNS_LOG = Path(os.getenv("TEST_RUNS_LOG") or OUTPUT_DIR / "test_runs.jsonl")

# Model. The course Portkey key allows gpt-6-luna only, so that is the default and, on Portkey,
# the only model this app will use. A personal OPENAI_API_KEY may pick another with OPENAI_MODEL.
COURSE_MODEL = "gpt-6-luna"
USING_PORTKEY = bool(os.getenv("PORTKEY_API_KEY"))
MODEL_NAME = COURSE_MODEL if USING_PORTKEY else os.getenv("OPENAI_MODEL", COURSE_MODEL)
REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")

# Limits (see README "Safety"). All can be changed in .env.
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "1200"))  # patient's description
MAX_INSURANCE_CHARS = 200
MAX_REQUESTS_PER_RUN = int(os.getenv("MAX_REQUESTS_PER_RUN", "16"))  # model calls, all agents combined
MAX_TOOL_CALLS_PER_RUN = int(os.getenv("MAX_TOOL_CALLS_PER_RUN", "24"))
MAX_TOKENS_PER_RUN = int(os.getenv("MAX_TOKENS_PER_RUN", "80000"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "90"))  # one agent may not wait on the model longer than this
MAX_RUNS_PER_MINUTE = int(os.getenv("MAX_RUNS_PER_MINUTE", "6"))  # per client address
MAX_TOKENS_PER_DAY = int(os.getenv("MAX_TOKENS_PER_DAY", "2000000"))  # whole app
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "200"))  # identical questions are answered from memory

# Token prices in dollars per one million tokens, used only to show cost. Set them in .env
# to the current price of the model; left at 0 the app shows token counts without dollars.
PRICE_INPUT_PER_M = float(os.getenv("PRICE_INPUT_PER_M", "0"))
PRICE_CACHED_INPUT_PER_M = float(os.getenv("PRICE_CACHED_INPUT_PER_M", "0"))
PRICE_OUTPUT_PER_M = float(os.getenv("PRICE_OUTPUT_PER_M", "0"))


def use_openai_fallback() -> bool:
    """Portkey rejected its key. If an OpenAI key is also set, switch to it for the rest of this process.

    The teaching staff's .env holds both keys, so the app works whichever one is live.
    """
    global USING_PORTKEY, MODEL_NAME
    if USING_PORTKEY and os.getenv("OPENAI_API_KEY"):
        USING_PORTKEY = False
        MODEL_NAME = os.getenv("OPENAI_MODEL", COURSE_MODEL)
        return True
    return False


def build_model():
    """The one model every agent uses: through Portkey if PORTKEY_API_KEY is set, else direct OpenAI."""
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider

    portkey_key = os.getenv("PORTKEY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if portkey_key and USING_PORTKEY:
        client = AsyncOpenAI(
            base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            api_key="portkey",  # not a real key: Portkey reads the header below
            default_headers={
                "x-portkey-api-key": portkey_key,
                "x-portkey-provider": os.getenv("PORTKEY_PROVIDER", "openai"),
            },
        )
    elif openai_key:
        client = AsyncOpenAI(api_key=openai_key)
    else:
        raise RuntimeError(
            "No API key found. Put PORTKEY_API_KEY (or OPENAI_API_KEY) in a .env file in this folder or the folder above it."
        )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def model_settings():
    from pydantic_ai.models.openai import OpenAIResponsesModelSettings

    return OpenAIResponsesModelSettings(openai_reasoning_effort=REASONING_EFFORT)  # type: ignore[typeddict-item]


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def has_api_key() -> bool:
    return bool(os.getenv("PORTKEY_API_KEY") or os.getenv("OPENAI_API_KEY"))
