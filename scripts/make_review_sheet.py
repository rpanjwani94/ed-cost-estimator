"""Write SCENARIOS_REVIEW.md: the clinical scenarios in data/workups.json in a form a clinician can read.

Usage (from the repo folder):  python scripts/make_review_sheet.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data import load_prices  # noqa: E402

prices = load_prices()
data = json.loads((ROOT / "data" / "workups.json").read_text(encoding="utf-8"))
out = [
    "# Clinical scenarios", "",
    "These 17 scenarios drive every estimate. They were drafted with AI help, then reviewed and corrected by the project's ED clinician on 22 November 2026.", "",
    "To change one, describe the change in plain words (for example \"chest pain: add a second ECG to possible\") and the data file `data/workups.json` is updated to match. Prices shown are the hospital's list prices, only to show scale.", "",
]
for n, s in enumerate(data["scenarios"], 1):
    lv = s["levels"]
    out += [f"## {n}. {s['title']}", "", f"**Visit level:** low {lv['low']} · typical {lv['typical']} · high {lv['high']}  ",
            f"**Matched when the patient says:** {', '.join(s['keywords'])}", ""]
    for label, key in (("Expected (most patients)", "expected"), ("Possible (some patients)", "possible")):
        out += [f"**{label}**", ""]
        if not s[key]:
            out += ["- none", ""]
            continue
        out += ["| Service | Code | Qty | List price each | Note |", "|---|---|---|---|---|"]
        for i in s[key]:
            svc = prices.services[i["code"]]
            out.append(f"| {svc.name} | {i['code']} | {i['quantity']} | ${svc.gross:,.2f} | {i.get('note', '')} |")
        out.append("")
    a = s["admission"]
    drgs = "; ".join(f"{prices.drgs[x].name} (DRG {x})" for x in a["drgs"]) or "none listed"
    out += [f"**Admission:** {a['likelihood']} · observation stay possible: {'yes' if a['observation_possible'] else 'no'}  ",
            f"**If admitted, priced as:** {drgs}  ", f"**Note shown to the planner:** {s['note']}", "", "---", ""]
(ROOT / "SCENARIOS_REVIEW.md").write_text("\n".join(out), encoding="utf-8")
print("wrote SCENARIOS_REVIEW.md")
