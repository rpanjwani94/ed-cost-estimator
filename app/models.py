"""Structured types: what the user sends, what each agent returns, and the estimate the tools compute."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VisitLevel = Literal["99281", "99282", "99283", "99284", "99285", "99291"]
Likelihood = Literal["unlikely", "possible", "likely"]
BasisKind = Literal["payer", "self_pay", "unknown"]


# ---- Request ---------------------------------------------------------------

class EstimateRequest(BaseModel):
    complaint: str = Field(description="What is going on, in the patient's own words")
    insurance: str = Field(default="", description="Free text, e.g. 'Anthem through my job' or 'no insurance'")
    copay: float | None = Field(default=None, ge=0, le=5000)
    deductible_remaining: float | None = Field(default=None, ge=0, le=50000)
    coinsurance_pct: float | None = Field(default=None, ge=0, le=100)
    oop_max_remaining: float | None = Field(default=None, ge=0, le=100000)

    def has_benefits(self) -> bool:
        return any(v is not None for v in (self.copay, self.deductible_remaining, self.coinsurance_pct, self.oop_max_remaining))


# ---- Agent outputs ---------------------------------------------------------

class TriageResult(BaseModel):
    """Safety agent: is this a question the app should answer, and how urgent does it sound?"""

    in_scope: bool = Field(description="True only if the text describes a health problem or ED visit someone wants a cost estimate for")
    urgency: Literal["emergency", "urgent", "routine"] = Field(description="emergency = call 911 or go now")
    red_flags: list[str] = Field(default_factory=list, description="Short plain-language warning signs found in the text, if any")
    enough_detail: bool = Field(default=True, description="False only when the text names a long-term condition or diagnosis with no hint of what is happening now")
    follow_up: str = Field(default="", description="When enough_detail is false: one short, friendly question asking what is happening today")
    reason: str = Field(description="One sentence explaining the decision")


class PlanItem(BaseModel):
    code: str = Field(description="Billing code exactly as returned by a tool")
    quantity: int = Field(default=1, ge=1, le=4)
    reason: str = Field(default="", description="A few words on why this is ordered")


class WorkupPlan(BaseModel):
    """Clinical agent: the likely ED workup for this problem."""

    scenario_id: str | None = Field(description="id of the clinician-written scenario used, or null if none fit")
    chief_complaint: str = Field(description="The problem in 2 to 6 plain words")
    level_low: VisitLevel
    level_typical: VisitLevel
    level_high: VisitLevel
    expected: list[PlanItem] = Field(description="Ordered for most patients with this problem")
    possible: list[PlanItem] = Field(description="Ordered for some patients; drives the high end")
    admission_likelihood: Likelihood
    admission_drgs: list[str] = Field(default_factory=list, description="DRG codes from the scenario, if admission is possible")
    observation_possible: bool = False
    assumptions: list[str] = Field(default_factory=list, description="Up to 4 short assumptions made about this patient")


class PricingNotes(BaseModel):
    """Pricing agent: how the prices were chosen. The numbers themselves come from the tools."""

    basis_explanation: str = Field(description="One or two sentences: which prices were used and why")
    caveats: list[str] = Field(default_factory=list, description="Up to 4 short caveats, no dollar amounts")


class PatientSummary(BaseModel):
    """Advocate agent: the plain-language explanation shown to the patient."""

    summary: str = Field(description="3 to 5 sentences explaining the estimate in plain language")
    cost_drivers: list[str] = Field(description="2 to 4 things that push the bill toward the low or the high end")
    if_admitted: str | None = Field(default=None, description="2 to 4 sentences on what changes if they are admitted or kept in observation; null if admission is unlikely")
    questions_for_staff: list[str] = Field(min_length=2, description="2 to 4 questions about money and paperwork, for registration, billing or financial counseling staff (or the insurer)")
    questions_for_doctor: list[str] = Field(min_length=2, description="2 to 3 questions about the care itself, for the doctor or nurse. Never about prices.")
    rights: list[str] = Field(min_length=2, description="2 to 4 patient rights or protections that apply, in plain words")


# ---- Estimate computed by tools (never typed by a model) --------------------

class Basis(BaseModel):
    kind: BasisKind
    payer: str | None = None
    label: str = ""


class EstimateLine(BaseModel):
    code: str
    name: str
    category: str
    hospital_description: str
    quantity: int
    likelihood: Literal["visit", "expected", "possible"]
    reason: str = ""
    list_price: float  # hospital gross charge, per unit
    cash_price: float  # discounted cash price, per unit
    rate: float  # price on the chosen basis, per unit
    rate_low: float  # lowest negotiated rate across insurers
    rate_high: float  # highest negotiated rate across insurers


class PatientShare(BaseModel):
    amount: float
    copay: float = 0
    deductible: float = 0
    coinsurance: float = 0
    capped_by_oop_max: bool = False


class Scenario(BaseModel):
    key: Literal["low", "typical", "high"]
    label: str
    visit_level: str
    visit_level_name: str
    includes: str
    list_total: float
    cash_total: float
    allowed_total: float  # on the chosen basis
    patient_share: PatientShare | None = None


class AdmissionOption(BaseModel):
    code: str
    name: str
    list_price: float
    cash_price: float
    rate: float
    rate_low: float
    rate_high: float
    patient_share: PatientShare | None = None


class Estimate(BaseModel):
    basis: Basis
    lines: list[EstimateLine]
    scenarios: list[Scenario]
    admission: list[AdmissionOption] = Field(default_factory=list)
    observation: list[EstimateLine] = Field(default_factory=list)
    physician_fee_note: str = ""


class AgentUsage(BaseModel):
    agent: str
    requests: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0
