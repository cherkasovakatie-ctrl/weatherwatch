"""Close a weekly refresh: stamp the snapshot date, archive the data and validate files.

Usage (from the repo root):  python3 tools/refresh/finalize.py [--date YYYY-MM-DD]

- Fails (exit 1) if any dataset listed in data/manifest.json is missing or empty.
- Copies every listed data file into data/archive/<date>/ and records the date in
  data/archive/index.json.
- Sets manifest "updated"/"updated_iso" and the "Data snapshot" date on every page.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PAGES = (
    "index.html",
    "enso-1982-83.html",
    "enso-1997-98.html",
    "enso-2015-16.html",
    "enso-2026.html",
    "events.html",
    "event.html",
    "data.html",
    "about.html",
    "mundane.html",
    "deadliest.html",
    "installations.html",
    "warming-since-1976.html",
)
ASOF_RE = re.compile(r"(<span data-asof>)[^<]*(</span>)")


def human(d: date) -> str:
    return f"{d.day} {d.strftime('%B %Y')}"


def validate(manifest: dict) -> list[str]:
    problems = []
    for ds in manifest["datasets"]:
        f = DATA / ds["file"]
        if not f.exists():
            problems.append(f"missing: {ds['file']}")
        elif f.stat().st_size == 0:
            problems.append(f"empty: {ds['file']}")
        else:
            ds["bytes"] = f.stat().st_size
    return problems


def stamp_pages(label: str) -> None:
    for name in PAGES:
        p = ROOT / name
        if p.exists():
            p.write_text(ASOF_RE.sub(rf"\g<1>{label}\g<2>", p.read_text(encoding="utf-8")), encoding="utf-8")


def archive(manifest: dict, iso: str) -> Path:
    dest = DATA / "archive" / iso
    dest.mkdir(parents=True, exist_ok=True)
    for ds in manifest["datasets"]:
        shutil.copy2(DATA / ds["file"], dest / ds["file"])
    ix_path = DATA / "archive" / "index.json"
    ix = json.loads(ix_path.read_text(encoding="utf-8")) if ix_path.exists() else {"snapshots": []}
    ix["snapshots"] = sorted(set(ix["snapshots"]) | {iso}, reverse=True)
    ix_path.write_text(json.dumps(ix) + "\n", encoding="utf-8")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    ap.add_argument("--no-archive", action="store_true", help="validate and stamp only (daily review); archive weekly")
    args = ap.parse_args()
    d = date.fromisoformat(args.date)
    mpath = DATA / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    problems = validate(manifest)
    if problems:
        print("Refusing to finalize:\n  " + "\n  ".join(problems))
        return 1
    manifest["updated"], manifest["updated_iso"] = human(d), d.isoformat()
    mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    stamp_pages(human(d))
    if args.no_archive:
        print(f"Stamped {d.isoformat()}: {len(manifest['datasets'])} datasets validated (no archive)")
        return 0
    dest = archive(manifest, d.isoformat())
    print(f"Snapshot {d.isoformat()}: {len(manifest['datasets'])} datasets archived to {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
