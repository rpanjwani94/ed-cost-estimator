"""Run the 30 review cases in data/review_cases.json through the real agents and score each one.

Each case has a patient's own words and a physician's expectations. For every case the script records what
the app did (red banner or not, scenario, visit levels, expected and possible items, admission, headline)
and checks three things against the case's "checks":

  banner    did the red emergency banner show when it should, and stay off when it should?
  includes  does the plan contain the services the case calls for (in the expected or the possible list)?
  restraint is the expected list free of the services the case says should not be routine?

Calls the real model: about 11,000 tokens per case, about 330,000 for all 30.

Usage (from the repo folder):  python scripts/run_review_cases.py
Writes output/review_cases_results.json and CASE_REVIEW.md.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, pipeline, safety  # noqa: E402
from app.data import load_prices  # noqa: E402
from app.models import EstimateRequest  # noqa: E402

CASES = json.loads((ROOT / "data" / "review_cases.json").read_text(encoding="utf-8"))["cases"]
OUT_JSON = ROOT / "output" / "review_cases_results.json"
OUT_MD = ROOT / "CASE_REVIEW.md"
AT_ONCE = 6


async def run_case(case: dict, gate: asyncio.Semaphore) -> dict:
    async with gate:
        req = EstimateRequest(complaint=case["input"], insurance=case.get("insurance", ""))
        events = [e async for e in pipeline.run_estimate(req, client=f"review-{case['id']}")]
    names = {code: svc.name for code, svc in load_prices().services.items()}
    result = next((e for e in events if e["type"] == "result"), None)
    emergency = next((e for e in events if e["type"] == "emergency"), None)
    keyword_flags = safety.red_flags(safety.normalize(case["input"]))
    out = {"id": case["id"], "title": case["title"], "group": case["group"], "input": case["input"],
           "expectation": case["physician_review_expectations"], "outcome": "estimate" if result else events[-1]["type"],
           "banner": bool(emergency) or bool(result and result.get("emergency")),
           "banner_from": "keyword screen" if keyword_flags else ("AI screener" if (emergency or (result and result.get("emergency"))) else ""),
           "flags": (result or {}).get("red_flags") or (emergency or {}).get("red_flags") or []}
    if not result:
        out["message"] = events[-1].get("message", "")
        out.update(scenario=None, levels=[], expected=[], possible=[], admission="", headline="", tokens=0)
    else:
        plan = result["plan"]
        out.update(scenario=plan["scenario_id"], levels=[plan["level_low"], plan["level_typical"], plan["level_high"]],
                   expected=[i["code"] for i in plan["expected"]], possible=[i["code"] for i in plan["possible"]],
                   admission=plan["admission_likelihood"], headline=result["summary"]["headline"],
                   most_likely=result["estimate"]["scenarios"][1]["allowed_total"],
                   tokens=result["usage"]["totals"]["input_tokens"] + result["usage"]["totals"]["output_tokens"])
    checks, planned = case["checks"], set(out["expected"]) | set(out["possible"])
    want_banner = checks["emergency_banner"]
    out["banner_ok"] = None if want_banner is None else (out["banner"] == want_banner)
    missing = [group for group in checks["plan_should_include_one_of_each"] if not planned & set(group)]
    out["includes_ok"] = None if not checks["plan_should_include_one_of_each"] else (not missing and bool(result))
    out["missing"] = [" or ".join(names.get(c, c) for c in group) for group in missing]
    routine = [c for c in out["expected"] if c in checks["should_not_be_in_expected"]]
    out["restraint_ok"] = None if not checks["should_not_be_in_expected"] else (not routine and bool(result))
    out["over_ordered"] = [names.get(c, c) for c in routine]
    out["expected_names"] = [names.get(c, c) for c in out["expected"]]
    out["possible_names"] = [names.get(c, c) for c in out["possible"]]
    return out


def mark(value) -> str:
    return "n/a" if value is None else ("yes" if value else "**NO**")


async def main() -> None:
    config.SAVE_TEST_RUNS = False
    config.USAGE_LOG = ROOT / "output" / "review_cases.log.jsonl"
    config.MAX_TOKENS_PER_DAY = 10_000_000
    pipeline._cache.clear(); safety.reset_budget()
    gate = asyncio.Semaphore(AT_ONCE)
    results = sorted(await asyncio.gather(*(run_case(c, gate) for c in CASES)), key=lambda r: r["id"])
    OUT_JSON.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")

    def tally(key: str) -> str:
        judged = [r for r in results if r[key] is not None]
        return f"{sum(1 for r in judged if r[key])} of {len(judged)}"

    all_ok = sum(1 for r in results if all(r[k] is not False for k in ("banner_ok", "includes_ok", "restraint_ok")))
    lines = ["# Review of 30 test cases", "",
             "Thirty patient descriptions with a physician's expectations (`data/review_cases.json`), run through the real agents by "
             "`scripts/run_review_cases.py`. The cases came from an outside AI review of the app. The three checks are simple and "
             "mechanical: they compare billing codes and the red banner with what each case calls for.", "",
             f"- **Red banner right** (shown when the case is an emergency, not shown when it is minor): {tally('banner_ok')}",
             f"- **Plan includes what the case calls for**: {tally('includes_ok')}",
             f"- **Restraint** (nothing the case says should not be routine is in the expected list): {tally('restraint_ok')}",
             f"- **Cases with no failed check**: {all_ok} of {len(results)}", "",
             "| # | Case | Result | Red banner | Banner right | Includes | Restraint | Scenario used | Visit levels | Most likely | What was off |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        off = []
        if r["banner_ok"] is False:
            off.append("banner shown for a minor problem" + (f" ({r['banner_from']}: {'; '.join(r['flags'])})" if r["flags"] else "") if r["banner"] else "no banner for an emergency")
        if r["missing"]:
            off.append("missing: " + "; ".join(r["missing"]))
        if r["over_ordered"]:
            off.append("listed as expected: " + ", ".join(r["over_ordered"]))
        if r["outcome"] != "estimate":
            off.append(f"no estimate ({r['outcome']}: {r.get('message', '')[:90]})")
        lines.append(f"| {r['id']} | {r['title']} | {r['outcome']} | {'yes' if r['banner'] else 'no'} | {mark(r['banner_ok'])} | {mark(r['includes_ok'])} | "
                     f"{mark(r['restraint_ok'])} | {r['scenario'] or '(none)'} | {'/'.join(l[-1] if l.startswith('9928') else 'critical care' for l in r['levels'])} | "
                     f"{'$' + format(r['most_likely'], ',.0f') if r.get('most_likely') else ''} | {'; '.join(off)} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[4:8]))
    for r in results:
        print(f"{r['id']} {r['title'][:26]:26} {r['outcome'][:9]:9} banner={'Y' if r['banner'] else 'n'}({mark(r['banner_ok']).strip('*')}) inc={mark(r['includes_ok']).strip('*'):3} "
              f"restr={mark(r['restraint_ok']).strip('*'):3} {str(r['scenario'])[:20]:20} {'/'.join(l[-1] if l.startswith('9928') else 'CC' for l in r['levels'])} "
              f"| miss: {'; '.join(r['missing'])[:60]} | over: {', '.join(r['over_ordered'])[:70]}")
    print("tokens:", sum(r["tokens"] for r in results))


if __name__ == "__main__":
    asyncio.run(main())
