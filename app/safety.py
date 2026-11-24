"""Defenses that run in plain code, before and after the agents.

1. Input checks: length cap, prompt-injection patterns (the run is refused before any tokens are spent).
2. Red-flag screen: emergency warning signs found by keyword. A model can add red flags but can never remove these.
3. Numbers guard: every dollar amount in the written summary must be one the pricing code produced.
4. Budget guard: per-client rate limit and a daily token ceiling for the whole app.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections import defaultdict, deque

from . import config

# ---- 0. Clean the text before anything reads it -------------------------------
# Phones type curly apostrophes ("can’t"), and an attacker can hide invisible characters inside a word
# ("ig<zero-width space>nore") or use look-alike letters. Both slip past keyword checks, so every check
# below, and every agent, sees the cleaned text.

_QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201b": "'", "\u02bc": "'", "\u2032": "'", "`": "'",
                         "\u201c": '"', "\u201d": '"', "\u2033": '"'})


def normalize(text: str) -> str:
    """Fold look-alike characters to plain ones, drop invisible characters, straighten quotes, tidy spaces."""
    text = unicodedata.normalize("NFKC", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")  # zero-width spaces, soft hyphens, direction marks
    text = text.translate(_QUOTES)
    return re.sub(r"[^\S\n]+", " ", text).strip()


# ---- 1. Input checks --------------------------------------------------------

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts|rules)",
    r"disregard (all |any |the )?(previous|prior|above|earlier|your) (instructions|prompts|rules)",
    r"(reveal|show|print|repeat|output) (me )?(your|the) (system )?(prompt|instructions)",
    r"system prompt",
    r"you are now\b",
    r"\bact as\b.*\b(dan|developer mode|jailbreak)",
    r"developer mode",
    r"\bjailbreak\b",
    r"(api|secret|portkey|openai)[ _-]?key",
    r"\.env\b",
    r"</?(system|assistant|instructions)>",
]
_INJECTION = re.compile("|".join(f"(?:{p})" for p in INJECTION_PATTERNS), re.IGNORECASE)


def check_input(complaint: str, insurance: str = "") -> str | None:
    """Return a refusal message if the request should not reach the model, else None."""
    text, insurance = normalize(complaint), normalize(insurance)
    if len(text) < 3:
        return "Please describe what is going on in a few words, for example 'twisted my ankle playing soccer'."
    if len(text) > config.MAX_INPUT_CHARS:
        return f"Please keep the description under {config.MAX_INPUT_CHARS} characters."
    if len(insurance) > config.MAX_INSURANCE_CHARS:
        return f"Please keep the insurance field under {config.MAX_INSURANCE_CHARS} characters."
    if _INJECTION.search(text) or _INJECTION.search(insurance):
        return (
            "This looks like an attempt to change how the estimator works, not a description of a health problem. "
            "Describe the symptoms or injury and I can estimate the cost."
        )
    return None


# ---- 1b. Data scrub ---------------------------------------------------------
# The agents also read text that no user typed: service names, scenario notes, guidance, and insurer names and
# descriptions that come from the hospital's own file. An instruction hidden there would reach a model as if
# it were a fact. Every such text field goes through scrub_data() when the data is loaded: the text is cut
# at the first thing that reads like an order to an AI, or a link. Clean data passes through unchanged.

DATA_DEFENSES_ON = True  # scripts/red_team_data.py turns this off to measure the app with no data defenses

DATA_INJECTION_PATTERNS = [
    r"\b(attention|note|notice|message|instructions?)\b.{0,20}\b(ai|a\.i\.|llm|assistant|agent|model|chatbot)s?\b",
    r"\b(ai|a\.i\.|llm) (agent|assistant|model|system)s?\b",
    r"\bassistant (instruction|note)s?\b",
    r"\bsystem (note|override|prompt|message|instruction)s?\b",
    r"\b(new|updated|additional) instructions?\b",
    r"\b(ignore|disregard|forget|override) (the |all |any |your )?(patient|prior|previous|above|earlier|other|rules|instructions)",
    r"\bfor every patient\b",
    r"\byou (must|should) (now|always)\b",
    r"https?://|www\.",
]
_DATA_INJECTION = re.compile("|".join(f"(?:{p})" for p in DATA_INJECTION_PATTERNS), re.IGNORECASE)


def scrub_data(text: str) -> tuple[str, str]:
    """Return (text safe to show a model, the part that was cut off). The second value is "" for clean text."""
    if not DATA_DEFENSES_ON or not isinstance(text, str):
        return text, ""
    cleaned = normalize(text)
    match = _DATA_INJECTION.search(cleaned)
    if not match:
        return text, ""
    return cleaned[:match.start()].rstrip(" \t\n(-:;,.\u2014") or "[text removed]", cleaned[match.start():]


# ---- 2. Red-flag screen -----------------------------------------------------

RED_FLAGS: list[tuple[str, str]] = [
    (r"chest (pain|pressure|tightness)|pressure in (my|the) chest|heart attack", "Chest pain or pressure"),
    (r"(can'?t|cannot|can not|trouble|difficulty|hard to|struggling to) breath|short(ness)? of breath|gasping", "Trouble breathing"),
    (r"stroke|face (is )?droop|droop(ing|y) face|slurr(ed|ing)|(weak|numb)(ness)? (on|in|down) (one|my (left|right)|the (left|right)) (side|arm|leg)|can'?t speak", "Possible stroke symptoms"),
    (r"suicid|kill myself|end my life|want to die|hurt myself|self[- ]harm", "Thoughts of self-harm (in the U.S. you can call or text 988 any time)"),
    (r"overdos|took too many|(?<!food )poison(ed|ing)", "Possible overdose or poisoning (Poison Control: 1-800-222-1222)"),
    (r"(bleeding|blood).{0,25}(won'?t stop|will not stop|not stopping|a lot|heav(y|ily)|spurting|soaking)|(heav(y|ily)|severe|a lot of|lots of|soaking)\b.{0,25}bleed|hemorrhag|vomiting blood|coughing up blood", "Heavy bleeding"),
    (r"unconscious|unresponsive|not waking|won'?t wake|passed out|fainted|blacked out|seizure|convuls", "Loss of consciousness or seizure"),
    (r"throat (is )?(closing|swelling|tight)|tongue (is )?swelling|lips? (are |is )?swelling|anaphyla", "Signs of a severe allergic reaction"),
    (r"worst headache|thunderclap|sudden(ly)? severe headache", "Sudden, severe headache"),
    (r"(pregnan).{0,40}(bleed|severe pain)|(bleed|severe pain).{0,40}pregnan", "Bleeding or severe pain in pregnancy"),
    (r"(newborn|infant|baby|[0-9] ?(week|month)s?[- ]old).{0,40}fever|fever.{0,40}(newborn|infant|baby)", "Fever in a young infant"),
    (r"stiff neck.{0,40}fever|fever.{0,40}stiff neck|confus(ed|ion)|disoriented", "Confusion, or fever with a stiff neck"),
    (r"severe (burn|pain)|bone (is )?(sticking|showing)|deform|car (accident|crash)|fell (off|from) (a |the )?(roof|ladder)|gunshot|\bstabbed\b|stab wound", "Serious injury"),
]
_RED_FLAGS = [(re.compile(p, re.IGNORECASE), label) for p, label in RED_FLAGS]


def red_flags(text: str) -> list[str]:
    text = normalize(text)
    return [label for pattern, label in _RED_FLAGS if pattern.search(text)]


EMERGENCY_MESSAGE = (
    "These symptoms can be an emergency. Call 911 or go to the nearest emergency department now. "
    "By law the hospital must examine and stabilize you whether or not you can pay. Sort out the cost afterward."
)

# ---- 3. Numbers guard -------------------------------------------------------

_DOLLARS = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")


def unsupported_amounts(text: str, allowed: set[int], tolerance: int = 1) -> list[str]:
    """Dollar amounts in the text that the pricing code never produced."""
    bad = []
    for match in _DOLLARS.finditer(text):
        value = round(float(match.group(1).replace(",", "")))
        if not any(abs(value - a) <= tolerance for a in allowed):
            bad.append(match.group(0))
    return bad


# ---- 4. Budget guard --------------------------------------------------------

_recent: dict[str, deque[float]] = defaultdict(deque)
_tokens_today: dict[str, int] = defaultdict(int)


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def check_budget(client: str) -> str | None:
    """Return a refusal message if this client is going too fast or the app has used its daily tokens."""
    if _tokens_today[_today()] >= config.MAX_TOKENS_PER_DAY:
        return "The estimator has reached its daily usage limit. Please try again tomorrow."
    now, window = time.monotonic(), _recent[client]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= config.MAX_RUNS_PER_MINUTE:
        return "Too many estimates in a short time. Please wait a minute and try again."
    window.append(now)
    return None


def add_tokens(count: int) -> None:
    _tokens_today[_today()] += count


def tokens_today() -> int:
    return _tokens_today[_today()]


def reset_budget() -> None:
    """For tests."""
    _recent.clear()
    _tokens_today.clear()
