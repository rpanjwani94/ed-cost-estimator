"""Loads the hospital price file, the plain-language service catalog, the clinical scenarios and the guidance notes."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache

from . import config, safety


@dataclass
class Service:
    code: str
    code_type: str  # CPT or DRG
    name: str  # plain language
    category: str
    hospital_description: str
    setting: str
    gross: float
    cash: float
    rates: dict[str, float] = field(default_factory=dict)  # payer -> negotiated dollar amount

    @property
    def rate_low(self) -> float:
        return min(self.rates.values())

    @property
    def rate_high(self) -> float:
        return max(self.rates.values())


@dataclass
class PriceData:
    hospital: str
    last_updated: str
    services: dict[str, Service]  # outpatient services by code
    drgs: dict[str, Service]  # inpatient case rates by DRG code
    payers: list[str]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Text that reads like an order to an AI is cut out of the data as it is loaded (see safety.scrub_data),
# so no agent ever sees it. What was cut is kept here and printed once, so a poisoned file is noticed.
SCRUB_LOG: list[dict[str, str]] = []


def _safe(text: str, where: str) -> str:
    cleaned, cut = safety.scrub_data(text)
    if cut:
        SCRUB_LOG.append({"where": where, "kept": cleaned, "removed": cut[:200]})
        print(f"DATA SCRUB: removed instruction-like text from {where}: {cut[:120]!r}", flush=True)
    return cleaned


def _money(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def load_prices() -> PriceData:
    with open(config.PRICE_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    meta = dict(zip(rows[0], rows[1]))
    col = {name: i for i, name in enumerate(rows[2])}

    # Group the per-payer rows into one record per (code, description, setting).
    grouped: dict[tuple[str, str, str, str], Service] = {}
    for row in rows[3:]:
        if len(row) < len(col):
            continue
        code, code_type = row[col["code|1"]].strip(), row[col["code|1|type"]].strip()
        description, setting = _safe(_clean(row[col["description"]]), "price file description"), row[col["setting"]].strip()
        gross, cash = _money(row[col["standard_charge|gross"]]), _money(row[col["standard_charge|discounted_cash"]])
        rate = _money(row[col["standard_charge|negotiated_dollar"]])
        if gross is None or cash is None or rate is None:
            continue
        key = (code_type, code, description, setting)
        svc = grouped.get(key)
        if svc is None:
            svc = grouped[key] = Service(code, code_type, description, "other", description, setting, gross, cash)
        svc.rates[_safe(_clean(row[col["payer_name"]]), "price file insurer name")] = rate

    with open(config.CATALOG_FILE, newline="", encoding="utf-8") as f:
        catalog = {r["code"]: {**r, "name": _safe(r["name"], "service catalog name"), "category": _safe(r["category"], "service catalog category")}
                   for r in csv.DictReader(f)}

    drgs: dict[str, Service] = {}
    variants: dict[str, list[Service]] = {}
    medicines: dict[str, list[Service]] = {}
    for (code_type, code, description, _setting), svc in grouped.items():
        if code_type == "DRG":
            svc.name, svc.category = description.capitalize(), "admission"
            drgs[code] = svc
        elif code_type == "CPT" and not description.startswith("HCPR"):  # HCPR rows are professional fees
            variants.setdefault(code, []).append(svc)
        elif code_type == "CDM":  # pharmacy rows: one per manufacturer package, same description
            medicines.setdefault(description, []).append(svc)

    # A code can have several hospital descriptions. Use the one the catalog names;
    # otherwise the highest-priced one, so the estimate does not come out low.
    services: dict[str, Service] = {}
    for code, options in variants.items():
        entry = catalog.get(code)
        wanted = _clean(entry["hospital_description"]) if entry else None
        svc = next((o for o in options if o.hospital_description == wanted), None) or max(options, key=lambda o: o.gross)
        if entry:
            svc.name, svc.category = entry["name"], entry["category"]
        services[code] = svc

    # Medicines get the catalog's own id (RX-...), because the file identifies them by package.
    for code, entry in catalog.items():
        options = medicines.get(_clean(entry["hospital_description"]))
        if code.startswith("RX-") and options:
            svc = sorted(options, key=lambda o: o.gross)[len(options) // 2]  # the middle-priced package
            svc.code, svc.name, svc.category = code, entry["name"], entry["category"]
            services[code] = svc

    payers = sorted({p for s in services.values() for p in s.rates})
    return PriceData(
        hospital=meta.get("hospital_name", "Yale New Haven Hospital"),
        last_updated=meta.get("last_updated_on", ""),
        services=services,
        drgs=drgs,
        payers=payers,
    )


@lru_cache(maxsize=1)
def load_workups() -> dict[str, dict]:
    with open(config.WORKUPS_FILE, encoding="utf-8") as f:
        scenarios = json.load(f)["scenarios"]
    for s in scenarios:
        s["title"], s["note"] = _safe(s["title"], "scenario title"), _safe(s.get("note", ""), "scenario note")
        s["keywords"] = [_safe(k, "scenario keyword") for k in s.get("keywords", [])]
        for item in s["expected"] + s["possible"]:
            if item.get("note"):
                item["note"] = _safe(item["note"], "scenario item note")
        for key, value in s.get("admission", {}).items():
            if isinstance(value, str):
                s["admission"][key] = _safe(value, "scenario admission note")
    return {s["id"]: s for s in scenarios}


@lru_cache(maxsize=1)
def load_guidance() -> dict[str, dict]:
    with open(config.GUIDANCE_FILE, encoding="utf-8") as f:
        topics = json.load(f)["topics"]
    for topic in topics.values():
        topic["title"], topic["text"] = _safe(topic["title"], "guidance title"), _safe(topic["text"], "guidance text")
    return topics


@lru_cache(maxsize=1)
def load_physician_fees() -> dict[str, float]:
    """Optional: Medicare physician fee for each ED visit level. Empty until data/physician_fees.csv has rows."""
    fees: dict[str, float] = {}
    if config.PHYSICIAN_FEES_FILE.is_file():
        with open(config.PHYSICIAN_FEES_FILE, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                amount = _money(r.get("medicare_amount", ""))
                if r.get("code") and amount is not None:
                    fees[r["code"].strip()] = amount
    return fees


def validate_data() -> list[str]:
    """Problems that would make estimates wrong: scenario codes missing from the price file."""
    prices, problems = load_prices(), []
    for sid, s in load_workups().items():
        for level in s["levels"].values():
            if level not in prices.services:
                problems.append(f"{sid}: visit level {level} not in price file")
        for item in s["expected"] + s["possible"]:
            if item["code"] not in prices.services:
                problems.append(f"{sid}: code {item['code']} not in price file")
        for drg in s["admission"]["drgs"]:
            if drg not in prices.drgs:
                problems.append(f"{sid}: DRG {drg} not in price file")
    return problems
