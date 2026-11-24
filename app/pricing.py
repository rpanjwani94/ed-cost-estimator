"""All the arithmetic. Agents decide what to price; this module does the pricing, so no model ever adds up dollars."""

from __future__ import annotations

import re
import statistics

from .data import Service, load_physician_fees, load_prices, load_workups
from .models import (
    AdmissionOption,
    Basis,
    Estimate,
    EstimateLine,
    EstimateRequest,
    PatientShare,
    Scenario,
    WorkupPlan,
)

SCENARIO_LABELS = {"low": "Lower end", "typical": "Most likely", "high": "Higher end"}


def make_basis(kind: str, payer: str | None) -> Basis:
    """Which price column to use. Falls back to 'unknown' if the payer is not in the hospital's file."""
    prices = load_prices()
    if kind == "self_pay":
        return Basis(kind="self_pay", label="the hospital's discounted cash price (no insurance)")
    if kind == "payer" and payer:
        match = next((p for p in prices.payers if p.lower() == payer.strip().lower()), None)
        if match:
            return Basis(kind="payer", payer=match, label=f"{match}'s negotiated rate with the hospital")
    return Basis(kind="unknown", label=f"the middle (median) of {len(prices.payers)} insurers' negotiated rates")


def rate_for(svc: Service, basis: Basis) -> float:
    if basis.kind == "self_pay":
        return svc.cash
    if basis.kind == "payer" and basis.payer in svc.rates:
        return svc.rates[basis.payer]
    return statistics.median(svc.rates.values())


def patient_share(allowed: float, req: EstimateRequest, basis: Basis) -> PatientShare | None:
    """Simplified plan math: copay, then deductible, then coinsurance, capped at the out-of-pocket maximum.

    Real plans differ (some waive the copay if admitted, some apply the copay after the deductible),
    so the result is an estimate. Returns None unless the patient gave the copay, the deductible left and
    the coinsurance: a blank is unknown, and guessing zero would understate what the patient owes.
    """
    if basis.kind == "self_pay":
        return PatientShare(amount=round(allowed, 2))
    if not req.has_full_benefits():
        return None
    copay = min(req.copay or 0, allowed)
    remaining = allowed - copay
    deductible = min(req.deductible_remaining or 0, remaining)
    remaining -= deductible
    coinsurance = remaining * (req.coinsurance_pct or 0) / 100
    total = copay + deductible + coinsurance
    capped = req.oop_max_remaining is not None and total > req.oop_max_remaining
    if capped:
        total = req.oop_max_remaining
    return PatientShare(
        amount=round(total, 2), copay=round(copay, 2), deductible=round(deductible, 2),
        coinsurance=round(coinsurance, 2), capped_by_oop_max=capped,
    )


def _line(code: str, quantity: int, likelihood: str, reason: str, basis: Basis) -> EstimateLine:
    svc = load_prices().services[code]
    return EstimateLine(
        code=code, name=svc.name, category=svc.category, hospital_description=svc.hospital_description,
        quantity=quantity, likelihood=likelihood, reason=reason,  # type: ignore[arg-type]
        list_price=svc.gross, cash_price=svc.cash, rate=round(rate_for(svc, basis), 2),
        rate_low=svc.rate_low, rate_high=svc.rate_high,
    )


def price_plan(plan: WorkupPlan, basis: Basis, req: EstimateRequest) -> Estimate:
    """Price the ED visit three ways: lower end, most likely, higher end."""
    prices = load_prices()
    lines = [_line(i.code, i.quantity, "expected", i.reason, basis) for i in plan.expected]
    lines += [_line(i.code, i.quantity, "possible", i.reason, basis) for i in plan.possible]

    def total(level: str, include_possible: bool, field: str) -> float:
        visit = prices.services[level]
        amount = {"list": visit.gross, "cash": visit.cash, "rate": rate_for(visit, basis)}[field]
        for line in lines:
            if line.likelihood == "expected" or include_possible:
                amount += line.quantity * {"list": line.list_price, "cash": line.cash_price, "rate": line.rate}[field]
        return round(amount, 2)

    scenarios = []
    for key, level, include_possible, includes in (
        ("low", plan.level_low, False, "the expected tests only, at the lower visit level"),
        ("typical", plan.level_typical, False, "the expected tests, at the most likely visit level"),
        ("high", plan.level_high, True, "the expected and the possible tests, at the higher visit level"),
    ):
        allowed = total(level, include_possible, "rate")
        scenarios.append(Scenario(
            key=key, label=SCENARIO_LABELS[key], visit_level=level, visit_level_name=prices.services[level].name,  # type: ignore[arg-type]
            includes=includes, list_total=total(level, include_possible, "list"),
            cash_total=total(level, include_possible, "cash"), allowed_total=allowed,
            patient_share=patient_share(allowed, req, basis),
        ))

    visit_lines = [_line(lv, 1, "visit", "", basis) for lv in dict.fromkeys((plan.level_low, plan.level_typical, plan.level_high))]
    fees = load_physician_fees()
    if fees:
        lo, hi = fees.get(plan.level_low), fees.get(plan.level_high)
        note = (
            f"The emergency physician bills separately. Medicare pays the physician about ${lo:,.0f} to ${hi:,.0f} for these "
            "visit levels; private insurers usually pay more. That bill is not included in the totals."
            if lo is not None and hi is not None else
            "The emergency physician bills separately. That bill is not included in the totals."
        )
    else:
        note = "The emergency physician bills separately from the hospital. That bill is not included in the totals."
    return Estimate(basis=basis, lines=visit_lines + lines, scenarios=scenarios, physician_fee_note=note)


def price_admission(plan: WorkupPlan, basis: Basis, req: EstimateRequest) -> tuple[list[AdmissionOption], list[EstimateLine]]:
    """Inpatient case rates for the DRGs in the plan, plus observation charges if observation is possible."""
    prices = load_prices()
    options = []
    for drg in plan.admission_drgs:
        svc = prices.drgs.get(drg)
        if not svc:
            continue
        rate = round(rate_for(svc, basis), 2)
        options.append(AdmissionOption(
            code=drg, name=svc.name, list_price=svc.gross, cash_price=svc.cash, rate=rate,
            rate_low=svc.rate_low, rate_high=svc.rate_high, patient_share=patient_share(rate, req, basis),
        ))
    options.sort(key=lambda o: o.rate)
    observation = []
    if plan.observation_possible:
        observation = [_line(c, 1, "possible", "", basis) for c in ("99222", "99223") if c in prices.services]
    return options, observation


PARTIAL_PLAN_NOTE = (" You filled in some plan details, but working out your share needs all three of copay, deductible "
                     "left and coinsurance (enter 0 for any your plan does not have), so this is not your share yet.")


def headline(estimate: Estimate, partial_plan: bool = False) -> tuple[str, str]:
    """The one line patients care about: what they might pay. Returns (headline, a short note under it).

    With plan details or no insurance the figure is the patient's own share. Without plan details the
    insurer's rate for the visit is the most the patient could owe for the hospital's bill, so it is
    shown as "up to".
    """
    typical, basis = estimate.scenarios[1], estimate.basis
    if basis.kind == "self_pay":
        return (f"Without insurance, you would pay about ${typical.allowed_total:,.0f} for the hospital's bill.",
                "This is the hospital's discounted cash price. Ask about financial assistance before you pay.")
    if typical.patient_share:
        capped = " That is the most you would owe this year under your plan." if typical.patient_share.capped_by_oop_max else ""
        return (f"You might pay about ${typical.patient_share.amount:,.0f} for the hospital's bill.",
                f"Based on the plan details you entered, at {basis.payer}'s rates." + capped if basis.payer
                else "Based on the plan details you entered, at a typical insurer's rates." + capped)
    if basis.kind == "payer":
        return (f"You might pay up to ${typical.allowed_total:,.0f} for the hospital's bill.",
                f"That is {basis.payer}'s full rate for the visit. You would pay less if you have already met part of your deductible."
                + (PARTIAL_PLAN_NOTE if partial_plan else " Add your plan details above for a closer figure."))
    return (f"You might pay up to about ${typical.allowed_total:,.0f} for the hospital's bill.",
            "That is what a typical insurer pays this hospital for the visit."
            + (PARTIAL_PLAN_NOTE if partial_plan else " Choose your insurer and add your plan details above for a closer figure."))


# ---- Look-ups the Clinical agent uses ---------------------------------------

def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def find_workups(query: str, limit: int = 3) -> list[dict]:
    """Rank the clinician-written scenarios against the patient's words. Returns compact summaries."""
    q, q_words = query.lower(), _words(query)
    scored = []
    for s in load_workups().values():
        score = sum(3 for k in s["keywords"] if k in q) + len(q_words & _words(s["title"] + " " + " ".join(s["keywords"])))
        if score:
            scored.append((score, s))
    scored.sort(key=lambda pair: -pair[0])
    return [{"id": s["id"], "title": s["title"], "match_score": score} for score, s in scored[:limit]]


def get_workup(scenario_id: str) -> dict | None:
    s = load_workups().get(scenario_id)
    if not s:
        return None
    services = load_prices().services

    def named(items: list[dict]) -> list[dict]:
        return [{"code": i["code"], "quantity": i["quantity"], "name": services[i["code"]].name,
                 **({"note": i["note"]} if i.get("note") else {})} for i in items]

    return {
        "id": s["id"], "title": s["title"], "levels": s["levels"], "expected": named(s["expected"]),
        "possible": named(s["possible"]), "admission": s["admission"], "note": s["note"],
    }


def search_services(query: str, limit: int = 8) -> list[dict]:
    """Find billable services by plain words (e.g. 'knee x-ray'). Returns code, name and list price."""
    q_words = _words(query)
    if not q_words:
        return []
    scored = []
    for svc in load_prices().services.values():
        hay = _words(svc.name + " " + svc.hospital_description + " " + svc.category)
        score = len(q_words & hay)
        if score:
            scored.append((score, svc))
    scored.sort(key=lambda pair: (-pair[0], pair[1].gross))
    return [{"code": s.code, "name": s.name, "category": s.category, "list_price": s.gross} for _, s in scored[:limit]]


def allowed_amounts(estimate: Estimate, req: EstimateRequest) -> set[int]:
    """Every dollar figure a summary is allowed to mention, rounded to whole dollars."""
    amounts: set[float] = set()
    for line in estimate.lines + estimate.observation:
        for v in (line.list_price, line.cash_price, line.rate, line.rate_low, line.rate_high):
            amounts.update((v, v * line.quantity))
    for s in estimate.scenarios:
        amounts.update((s.list_total, s.cash_total, s.allowed_total))
        if s.patient_share:
            amounts.update((s.patient_share.amount, s.patient_share.copay, s.patient_share.deductible, s.patient_share.coinsurance))
    for a in estimate.admission:
        amounts.update((a.list_price, a.cash_price, a.rate, a.rate_low, a.rate_high))
        if a.patient_share:
            amounts.update((a.patient_share.amount, a.patient_share.deductible, a.patient_share.coinsurance))
    for v in (req.copay, req.deductible_remaining, req.oop_max_remaining):
        if v is not None:
            amounts.add(v)
    amounts.update(load_physician_fees().values())
    return {round(a) for a in amounts}
