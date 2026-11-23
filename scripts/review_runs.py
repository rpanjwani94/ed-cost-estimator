"""Turn the test-mode log into a spreadsheet you can review: one row per run.

Shows what each tester typed, whether the red "this may be an emergency" banner showed, why, which
scenario was used and the most-likely figure. Two empty columns are left for your own judgment.

Usage (from the repo folder):  python scripts/review_runs.py [file]
Reads output/test_runs.jsonl (written only when SAVE_TEST_RUNS=1) and writes output/test_runs_review.csv.
Give a file to read something else, such as log lines copied from a hosted copy's log
(each saved run appears there as a line containing "TEST_RUN {...}").
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else ROOT / "output" / "test_runs.jsonl"
TARGET = ROOT / "output" / "test_runs_review.csv"

if not SOURCE.is_file():
    sys.exit("No saved runs yet. Test mode writes output/test_runs.jsonl when SAVE_TEST_RUNS=1.")

rows = []
for line in SOURCE.read_text(encoding="utf-8").splitlines():
    if "TEST_RUN " in line:  # a line copied from a server log: drop whatever the host put in front
        line = line.split("TEST_RUN ", 1)[1]
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if not isinstance(r, dict) or "timestamp" not in r:
        continue
    screener = r.get("screener") or {}
    share, totals = r.get("patient_share") or [], r.get("totals") or []
    typical = (share[1] if len(share) > 1 and share[1] is not None else totals[1] if len(totals) > 1 else None)
    when = datetime.fromisoformat(r["timestamp"]).astimezone().strftime("%b %d %I:%M %p")
    rows.append({
        "When": when,
        "What they typed": r.get("complaint", ""),
        "Insurance": r.get("insurance", "") or "(not sure)",
        "Result": r.get("outcome", ""),
        "Red banner shown": "YES" if r.get("red_banner_shown") else "no",
        "Warning signs found by keyword check": "; ".join(r.get("keyword_flags") or []),
        "Screener's urgency": screener.get("urgency", ""),
        "Warning signs found by screener": "; ".join(screener.get("red_flags") or []),
        "Scenario used": r.get("scenario_id") or ("(none matched)" if r.get("plan") else ""),
        "Visit levels": " / ".join((r.get("plan") or {}).get("levels", [])),
        "Admission": (r.get("plan") or {}).get("admission", ""),
        "Most-likely figure": f"${typical:,.0f}" if typical is not None else "",
        "Should the red banner have shown? (you fill in)": "",
        "Notes (you fill in)": "",
    })

if not rows:
    sys.exit(f"No saved runs found in {SOURCE}.")

with open(TARGET, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

shown = sum(1 for r in rows if r["Red banner shown"] == "YES")
print(f"{len(rows)} runs -> {TARGET.relative_to(ROOT)}  (red banner shown on {shown})")
