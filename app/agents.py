"""The four agents and their tools.

Triage (safety screen, no tools) -> Clinical (plans the workup) -> Pricing (chooses the price basis, runs the
pricing tools) -> Advocate (explains the result). The hand-offs are fixed in pipeline.py. Every tool call is
logged on the run so the web page can show exactly what each agent did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal

from pydantic_ai import Agent, ModelRetry, RunContext

from . import config, pricing, safety
from .data import load_guidance, load_prices
from .models import Estimate, EstimateRequest, PatientSummary, PricingNotes, TriageResult, WorkupPlan

VISIT_LEVELS = ["99281", "99282", "99283", "99284", "99285", "99291"]
GuidanceTopic = Literal[
    "emergency_care_first", "two_bills", "visit_level", "no_surprises_act", "observation_vs_inpatient",
    "admission_cost_share", "financial_assistance", "itemized_bill", "self_pay", "lower_cost_settings",
]


@dataclass
class RunDeps:
    """Shared state for one estimate. Tools read and write it; models never see it directly."""

    req: EstimateRequest
    agent: str = ""
    plan: WorkupPlan | None = None
    estimate: Estimate | None = None
    admission_priced: bool = False
    tool_log: list[dict[str, Any]] = field(default_factory=list)
    # Billing codes a tool handed to the clinical agent in this run, with the most of each it may order.
    # A code that only appears inside a piece of text (a name, a note) is not here, so it cannot enter the plan.
    offered: dict[str, int] = field(default_factory=dict)

    def offer(self, code: str, quantity: int = 1) -> None:
        self.offered[code] = max(self.offered.get(code, 0), quantity, 2)

    def log(self, tool: str, args: dict[str, Any], result: Any) -> None:
        text = str(result)
        self.tool_log.append({"agent": self.agent, "tool": tool, "args": args, "result": text if len(text) <= 400 else text[:399] + "…"})


# ---- Clinical agent tools ---------------------------------------------------

def find_scenarios(ctx: RunContext[RunDeps], problem: str) -> list[dict]:
    """Find clinician-written ED scenarios that match the patient's problem.

    Args:
        problem: The problem in a few plain words, e.g. "twisted ankle" or "chest pain".
    """
    result = pricing.find_workups(problem)
    ctx.deps.log("find_scenarios", {"problem": problem}, result)
    return result


def get_scenario(ctx: RunContext[RunDeps], scenario_id: str) -> dict:
    """Get one scenario in full: visit levels, expected and possible items with billing codes, admission details.

    Args:
        scenario_id: An id returned by find_scenarios.
    """
    result = pricing.get_workup(scenario_id) or {"error": f"No scenario with id {scenario_id!r}. Use an id from find_scenarios."}
    for item in result.get("expected", []) + result.get("possible", []):
        ctx.deps.offer(item["code"], item["quantity"])
    ctx.deps.log("get_scenario", {"scenario_id": scenario_id}, result.get("title", result))
    return result


def search_services(ctx: RunContext[RunDeps], words: str) -> list[dict]:
    """Search the hospital's price list for a test, scan, treatment or procedure by plain words.

    Args:
        words: What to look for, e.g. "knee x-ray" or "tetanus".
    """
    result = pricing.search_services(words)
    for found in result:
        ctx.deps.offer(found["code"])
    ctx.deps.log("search_services", {"words": words}, [f"{r['code']} {r['name']}" for r in result])
    return result


# ---- Pricing agent tools ----------------------------------------------------

def list_insurers(ctx: RunContext[RunDeps]) -> list[str]:
    """List the insurers that have negotiated rates in the hospital's price file."""
    result = load_prices().payers
    ctx.deps.log("list_insurers", {}, f"{len(result)} insurers")
    return result


def price_ed_visit(ctx: RunContext[RunDeps], basis: Literal["payer", "self_pay", "unknown"], insurer: str | None = None) -> dict:
    """Price the stored clinical plan (lower end, most likely, higher end) and store the estimate.

    Args:
        basis: "payer" to use one insurer's negotiated rates, "self_pay" for the cash price, "unknown" for the median insurer rate.
        insurer: Exact name from list_insurers. Required when basis is "payer".
    """
    deps = ctx.deps
    if deps.plan is None:
        raise ModelRetry("There is no clinical plan to price.")
    if basis == "payer" and not insurer:
        raise ModelRetry('basis "payer" needs an insurer name from list_insurers.')
    chosen = pricing.make_basis(basis, insurer)
    if basis == "payer" and chosen.kind != "payer":
        raise ModelRetry(f"{insurer!r} is not in the hospital's list. Call list_insurers and use an exact name, or use basis \"unknown\".")
    deps.estimate = pricing.price_plan(deps.plan, chosen, deps.req)
    needs_admission = bool(deps.plan.admission_drgs) or deps.plan.observation_possible
    result = {
        "priced_on": chosen.label,
        "scenarios": {s.key: f"{s.label}: stored" for s in deps.estimate.scenarios},
        "patient_share_calculated": deps.estimate.scenarios[0].patient_share is not None,
        "admission_pricing_needed": needs_admission,
    }
    deps.log("price_ed_visit", {"basis": basis, "insurer": insurer}, {
        "priced_on": chosen.label,
        "totals": {s.key: s.allowed_total for s in deps.estimate.scenarios},
        "admission_pricing_needed": needs_admission,
    })
    return result


def price_admission(ctx: RunContext[RunDeps]) -> dict:
    """Price a hospital admission (case rates for the plan's DRGs) and an observation stay, on the same basis as the ED visit."""
    deps = ctx.deps
    if deps.estimate is None or deps.plan is None:
        raise ModelRetry("Call price_ed_visit first.")
    deps.estimate.admission, deps.estimate.observation = pricing.price_admission(deps.plan, deps.estimate.basis, deps.req)
    deps.admission_priced = True
    result = {"admission_options_stored": len(deps.estimate.admission), "observation_lines_stored": len(deps.estimate.observation)}
    deps.log("price_admission", {}, {
        "drgs": {a.code: a.rate for a in deps.estimate.admission}, "observation_lines": len(deps.estimate.observation),
    })
    return result


# ---- Advocate agent tool ----------------------------------------------------

def get_guidance(ctx: RunContext[RunDeps], topic: GuidanceTopic) -> dict:
    """Get a short, reviewed explanation of a patient-rights or billing topic.

    Args:
        topic: One of the listed guidance topics.
    """
    result = load_guidance().get(topic) or {"error": "Unknown topic."}
    ctx.deps.log("get_guidance", {"topic": topic}, result.get("title", result))
    return result


# ---- Agents -----------------------------------------------------------------

@dataclass
class Team:
    triage: Agent[RunDeps, TriageResult]
    clinical: Agent[RunDeps, WorkupPlan]
    pricing: Agent[RunDeps, PricingNotes]
    advocate: Agent[RunDeps, PatientSummary]


def check_plan(plan: WorkupPlan, offered: dict[str, int] | None = None) -> list[str]:
    """Reasons a clinical plan cannot be priced. Empty means it is fine.

    `offered` is the set of codes the tools handed over in this run (see RunDeps.offered). When given, a
    code the tools never returned, or more of an item than the scenario lists, is rejected: text inside
    the data cannot add a service or multiply one.
    """
    prices, problems = load_prices(), []
    for item in plan.expected + plan.possible:
        if item.code not in prices.services:
            problems.append(f"code {item.code!r} is not in the hospital's price list")
        elif item.code in VISIT_LEVELS:
            problems.append(f"{item.code} is a visit level; put it in the level fields, not in the item lists")
        elif offered is not None and safety.DATA_DEFENSES_ON:
            if item.code not in offered:
                problems.append(f"code {item.code!r} was not returned by a tool in this run; use only codes from get_scenario or search_services results")
            elif item.quantity > offered[item.code]:
                problems.append(f"quantity {item.quantity} of {item.code} is more than the scenario lists ({offered[item.code]} at most)")
    order = [VISIT_LEVELS.index(lv) for lv in (plan.level_low, plan.level_typical, plan.level_high)]
    if order != sorted(order):
        problems.append("visit levels must go low <= typical <= high")
    for drg in plan.admission_drgs:
        if drg not in prices.drgs:
            problems.append(f"DRG {drg!r} is not in the hospital's price list")
    if len(plan.expected) > 14 or len(plan.possible) > 14:
        problems.append("too many items; keep each list to 14 or fewer")
    return problems


def summary_text(summary: PatientSummary) -> str:
    return " ".join([summary.summary, summary.if_admitted or "", *summary.cost_drivers,
                     *summary.questions_for_staff, *summary.questions_for_doctor, *summary.rights])


@lru_cache(maxsize=1)
def get_team() -> Team:
    model, settings = config.build_model(), config.model_settings()

    triage = Agent(model, name="triage", deps_type=RunDeps, output_type=TriageResult,
                   instructions=config.load_prompt("triage"), model_settings=settings, retries=1)

    clinical = Agent(model, name="clinical", deps_type=RunDeps, output_type=WorkupPlan,
                     instructions=config.load_prompt("clinical"), tools=[find_scenarios, get_scenario, search_services],
                     model_settings=settings, retries=2)

    @clinical.output_validator
    def _valid_plan(ctx: RunContext[RunDeps], plan: WorkupPlan) -> WorkupPlan:
        problems = check_plan(plan, ctx.deps.offered)
        if problems:
            ctx.deps.log("plan_check", {}, "REJECTED: " + "; ".join(problems))
            raise ModelRetry("Fix these problems, using only codes returned by the tools: " + "; ".join(problems))
        return plan

    pricer = Agent(model, name="pricing", deps_type=RunDeps, output_type=PricingNotes,
                   instructions=config.load_prompt("pricing"), tools=[list_insurers, price_ed_visit, price_admission],
                   model_settings=settings, retries=2)

    @pricer.output_validator
    def _priced(ctx: RunContext[RunDeps], notes: PricingNotes) -> PricingNotes:
        deps = ctx.deps
        if deps.estimate is None:
            raise ModelRetry("You have not called price_ed_visit yet.")
        if deps.plan and (deps.plan.admission_drgs or deps.plan.observation_possible) and not deps.admission_priced:
            raise ModelRetry("Admission pricing is needed. Call price_admission.")
        if "$" in notes.basis_explanation + " ".join(notes.caveats):
            raise ModelRetry("Remove all dollar amounts from your output. The page shows the numbers from the tools.")
        return notes

    advocate = Agent(model, name="advocate", deps_type=RunDeps, output_type=PatientSummary,
                     instructions=config.load_prompt("advocate"), tools=[get_guidance], model_settings=settings, retries=2)

    @advocate.output_validator
    def _numbers_guard(ctx: RunContext[RunDeps], summary: PatientSummary) -> PatientSummary:
        deps = ctx.deps
        if deps.estimate is None:
            return summary
        bad = safety.unsupported_amounts(summary_text(summary), pricing.allowed_amounts(deps.estimate, deps.req))
        if bad:
            deps.log("numbers_guard", {}, "REJECTED: amounts not in the estimate: " + ", ".join(bad))
            raise ModelRetry(
                "These dollar amounts are not in the estimate: " + ", ".join(bad)
                + ". Use only amounts copied exactly from the estimate, or describe them in words."
            )
        return summary

    return Team(triage=triage, clinical=clinical, pricing=pricer, advocate=advocate)
