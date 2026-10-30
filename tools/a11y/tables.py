"""Add header scopes and hidden captions to the tables of the static pages (idempotent).

- Every <th> gets a scope: "col" in a header row, "colgroup" for a header cell with colspan, "row" for the first
  cell of a body row. This also covers table rows that are written as strings inside the page scripts.
- A static table without <caption> or aria-label gets a visually hidden <caption> ONLY when the nearest heading
  above it (h2-h4, no other heading or table in between, and no other table before the next heading) can be repeated
  word for word. Anything else is left alone: the caption wording is an editorial decision (see work/TASK-009/captions.md).
The caption is hidden with an inline style, so no page layout changes.
Usage (repo root): python3 tools/a11y/tables.py [--dry-run]
Run it after the page generators (tools/papers/build.py, tools/tc2026/*) because they rewrite the HTML.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIDDEN = 'style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap"'

TR = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S)
TH = re.compile(r"<th\b([^>]*)>")
SCRIPT = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.S | re.I)
TABLE = re.compile(r"<table\b[^>]*>.*?</table>", re.S | re.I)
HEADING = re.compile(r"<(h[2-4])\b[^>]*>(.*?)</\1>", re.S | re.I)


def scope_row(tr: str) -> str:
    cells = re.findall(r"<(th|td)\b", tr)
    if "th" not in cells:
        return tr
    all_th = "td" not in cells
    first = [True]

    def sub(m: re.Match) -> str:
        attrs = m.group(1)
        was_first = first[0]
        first[0] = False
        if "scope=" in attrs:
            return m.group(0)
        if all_th:
            scope = "colgroup" if re.search(r"colspan=[\"']?([2-9])", attrs) else "col"
        elif was_first:
            scope = "row"
        else:
            scope = "col"
        return f'<th{attrs} scope="{scope}">'

    # only the first <th> of a mixed row counts as a row header; later th in a mixed row are column-ish
    return TH.sub(sub, tr)


def add_scopes(text: str) -> str:
    return TR.sub(lambda m: scope_row(m.group(0)), text)


def plain(html_text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html_text)).strip()


def add_captions(page: str) -> tuple[str, list[str]]:
    """Return (new text, notes). Works only outside <script> blocks."""
    notes: list[str] = []
    out, pos = [], 0
    scripts = [(m.start(), m.end()) for m in SCRIPT.finditer(page)]
    in_script = lambda i: any(a <= i < b for a, b in scripts)
    heads = [(m.start(), m.end(), m.group(2)) for m in HEADING.finditer(page) if not in_script(m.start())]
    tables = [m for m in TABLE.finditer(page) if not in_script(m.start())]
    for m in tables:
        t = m.group(0)
        if re.search(r"<caption\b", t, re.I) or re.search(r'aria-label=', t.split(">", 1)[0], re.I):
            continue
        above = [h for h in heads if h[1] <= m.start()]
        if not above:
            continue
        h = above[-1]
        between = page[h[1]:m.start()]
        later_heads = [x for x in heads if x[0] > m.start()]
        next_head = later_heads[0][0] if later_heads else len(page)
        tables_before_next = [x for x in tables if h[1] <= x.start() < next_head]
        ok = (len(tables_before_next) == 1 and not re.search(r"<h[1-6]\b", between, re.I)
              and "<details" not in between.lower().replace("</details>", ""))
        title = plain(h[2])
        if not ok or not title:
            notes.append(f"left for the PM: table at {m.start()} (nearest heading '{title[:50]}')")
            continue
        first_tag_end = t.index(">") + 1
        cap = f"<caption {HIDDEN}>{h[2].strip()}</caption>"
        out.append((m.start() + first_tag_end, cap))
        notes.append(f"caption '{title[:60]}'")
    for at, cap in sorted(out, reverse=True):
        page = page[:at] + cap + page[at:]
    return page, notes


def process(path: Path, dry: bool) -> tuple[int, int]:
    raw = path.read_bytes().decode("utf-8")
    text = add_scopes(raw)
    text, notes = add_captions(text)
    caps = sum(1 for n in notes if n.startswith("caption"))
    scopes = len(re.findall(r'<th\b[^>]*\bscope=', text)) - len(re.findall(r'<th\b[^>]*\bscope=', raw))
    if text != raw and not dry:
        path.write_bytes(text.encode("utf-8"))
    return scopes, caps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    files = [Path(f) for f in args.files] or sorted(ROOT.glob("*.html"))
    tot_s = tot_c = 0
    for f in files:
        # the claims cards have their own visible captions and header scopes
        if f.name.startswith("claim"):
            continue
        s, c = process(f, args.dry_run)
        if s or c:
            print(f"{f.name}: +{s} scopes, +{c} captions")
        tot_s += s
        tot_c += c
    print(f"total +{tot_s} scopes, +{tot_c} captions{' (dry run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
