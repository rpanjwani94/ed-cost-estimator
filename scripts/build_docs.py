"""Turn docs_src/report.src.html and docs_src/slides.src.html into single files that open with a double-click.

Every <img src="report_assets/NAME.jpg"> is replaced by the image itself (base64), resized to a
sensible width first, so report.html and slides.html need nothing else next to them.

Usage (from the repo folder):  python scripts/build_docs.py
"""

from __future__ import annotations

import base64
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_WIDTH = 1300  # pixels; plenty for print at the sizes used


def data_uri(path: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / path.name
        try:  # macOS: shrink wide images to keep the file small
            subprocess.run(["sips", "--resampleWidth", str(MAX_WIDTH), str(path), "--out", str(out)],
                           check=True, capture_output=True)
            width = subprocess.run(["sips", "-g", "pixelWidth", str(path)], capture_output=True, text=True).stdout
            data = out.read_bytes() if int(width.split()[-1]) > MAX_WIDTH else path.read_bytes()
        except (OSError, subprocess.CalledProcessError, ValueError):
            data = path.read_bytes()  # other systems: embed as is
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def build(name: str) -> None:
    src = ROOT / "docs_src" / f"{name}.src.html"
    if not src.is_file():
        return
    html = src.read_text(encoding="utf-8")
    cache: dict[str, str] = {}

    def swap(match: re.Match) -> str:
        rel = match.group(1)
        if rel not in cache:
            cache[rel] = data_uri(ROOT / rel)
        return f'src="{cache[rel]}"'

    html = re.sub(r'src="(report_assets/[^"]+)"', swap, html)
    out = ROOT / f"{name}.html"
    out.write_text(html, encoding="utf-8")
    print(f"{out.name}: {out.stat().st_size / 1_000_000:.1f} MB, {len(cache)} images embedded")


if __name__ == "__main__":
    for doc in ("report", "slides"):
        build(doc)
