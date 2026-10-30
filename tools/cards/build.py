"""Build the 'claim vs evidence' card pages from cards/*.json.

Each JSON file is one card written by the data team (title, summary, sections, claims with verdicts, known /
forecast / unknown, how_to_check, outcome, references, data, caveats). This script only lays the content out;
it never rewrites it. Output: claim-<slug>.html per card and claims.html (the index).
Publication state is NOT taken from the card JSON (that file belongs to the data team and is replaced when they revise
a card). It lives in cards/publish.json: {"order": [...], "state": {"<slug>": "live" | "draft"}}. A card missing
from "state" is a draft. Draft cards are built only with --drafts, are never listed on claims.html and carry noindex.
Usage: python3 tools/cards/build.py [--drafts]
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cards"
PUBLISH = json.loads((SRC / "publish.json").read_text(encoding="utf-8"))
ORDER = PUBLISH["order"]  # index order; any other card follows alphabetically
STATE = PUBLISH["state"]

STYLE = """
:root { color-scheme: light dark;
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --color-bg: #f6f5f1; --color-panel: #ffffff; --color-fg: #1d1f22; --color-fg-muted: #5c6370; --color-border-line: #e2e0d8;
  --ok: #15803d; --warn: #a16207; --bad: #b91c1c; --zebra: #faf9f6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --color-bg: #141619; --color-panel: #1c1f23; --color-fg: #eceae4; --color-fg-muted: #a3a9b2; --color-border-line: #2e3238;
  --ok: #4ade80; --warn: #facc15; --bad: #f87171; --zebra: #202429; } }
:root[data-theme="dark"] { --color-bg: #141619; --color-panel: #1c1f23; --color-fg: #eceae4; --color-fg-muted: #a3a9b2; --color-border-line: #2e3238;
  --ok: #4ade80; --warn: #facc15; --bad: #f87171; --zebra: #202429; }
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); }
body { font-family: var(--font-sans); }
.site-nav { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px; padding: 10px 16px; border-bottom: 1px solid var(--color-border-line); background: var(--color-panel); }
.site-nav .brand { font-family: var(--font-serif); font-size: 1.15rem; color: var(--color-fg); text-decoration: none; margin-right: auto; }
.site-nav a { color: var(--color-fg-muted); text-decoration: none; font-size: .9rem; }
.site-nav a[aria-current="page"], .site-nav a:hover { color: var(--color-fg); }
.site-foot { max-width: 980px; margin: 24px auto; padding: 0 16px 24px; color: var(--color-fg-muted); font-size: .8rem; line-height: 1.5; }
a { color: inherit; }
a:focus-visible, [tabindex]:focus-visible { outline: 2px solid var(--color-fg); outline-offset: 2px; }
main { max-width: 980px; margin: 0 auto; padding: 16px; overflow-wrap: anywhere; }
.kicker { font-size: .8rem; letter-spacing: .06em; text-transform: uppercase; color: var(--color-fg-muted); margin: .4em 0 0; }
h1 { font-family: var(--font-serif); font-weight: 400; font-size: 1.9rem; margin: .2em 0 .2em; line-height: 1.2; }
h2 { font-family: var(--font-serif); font-weight: 400; font-size: 1.35rem; margin: 1.6em 0 .4em; }
h3 { font-size: 1rem; margin: 0 0 .3em; }
.meta { color: var(--color-fg-muted); font-size: .88rem; line-height: 1.6; margin: 0 0 8px; }
.prose { max-width: 78ch; line-height: 1.65; font-size: .97rem; }
.prose p { margin: 0 0 .9em; }
.card { background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: 10px; padding: 14px 16px; margin: 12px 0; min-width: 0; }
.summary { border-left: 4px solid var(--color-fg-muted); }
.summary p { margin: .3em 0 0; max-width: 78ch; line-height: 1.6; }
.tag { display: inline-block; font-size: .72rem; padding: 1px 8px; border-radius: 999px; border: 1px solid currentColor; margin-right: 6px; white-space: nowrap; }
.tag.ok { color: var(--ok); } .tag.warn { color: var(--warn); } .tag.bad { color: var(--bad); } .tag.info { color: var(--color-fg-muted); }
.tag.unrated { border-style: dashed; }
.trio { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr)); gap: 10px; margin: 12px 0; }
.trio .card { margin: 0; }
.trio ul { margin: .4em 0 0; padding-left: 1.2em; font-size: .9rem; line-height: 1.5; }
.trio li { margin-bottom: .5em; }
.claims { list-style: none; padding: 0; margin: 0; }
.claim { scroll-margin-top: 12px; }
.claim:target { outline: 2px solid var(--color-fg); }
.claim .head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 10px; margin-bottom: .4em; }
.claim .cid { font-variant-numeric: tabular-nums; font-weight: 600; }
.claim dl { margin: 0; display: grid; grid-template-columns: 9.5rem 1fr; gap: 4px 12px; font-size: .88rem; line-height: 1.5; }
.claim dt { color: var(--color-fg-muted); }
.claim dd { margin: 0; }
@media (max-width: 600px) { .claim dl { grid-template-columns: 1fr; gap: 0; } .claim dd { margin-bottom: .5em; } }
.wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { border-collapse: collapse; width: 100%; font-size: .86rem; line-height: 1.45; }
caption { text-align: left; color: var(--color-fg-muted); font-size: .82rem; padding: 0 0 6px; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid var(--color-border-line); }
thead th { font-weight: 600; }
tbody tr:nth-child(even) { background: var(--zebra); }
.note { font-size: .82rem; color: var(--color-fg-muted); line-height: 1.5; margin: 6px 0 0; }
ol.refs, ul.cav { padding-left: 1.4em; font-size: .88rem; line-height: 1.55; }
ol.refs li, ul.cav li { margin-bottom: 6px; }
.res { white-space: nowrap; }
td.test { min-width: 15rem; }
.pending { color: var(--color-fg-muted); font-style: italic; }
.cards-index { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr)); gap: 12px; }
.cards-index a.card { text-decoration: none; display: block; }
.cards-index a.card:hover h2 { text-decoration: underline; }
.cards-index h2 { font-size: 1.15rem; margin: .3em 0; }
"""

NAV = """<nav class="site-nav" aria-label="Site">
  <a class="brand" href="./">Global Weather Watch</a>
  <a href="./">Dashboard</a>
  <a href="./#overview">ENSO overview</a>
  <a href="./#climate">Climate</a>
  <a href="deadliest.html">Deadliest events</a>
  <a href="events.html">Event log</a>
  <a href="claims.html" aria-current="page">Claims vs evidence</a>
  <a href="data.html">Data archive</a>
  <a href="about.html">About &amp; method</a>
</nav>"""

# verdict -> (css class, symbol). The verdict text is always shown in full; symbol and style are extra cues.
def verdict_style(v: str) -> tuple[str, str]:
    t = v.lower()
    if t.startswith("unsupported"):
        return "bad", "✗"
    if t.startswith("unable to verify"):
        return "info", "?"
    if t.startswith("partly supported"):
        return "warn", "~"
    if t.startswith("confirmed"):
        return "ok", "✓"
    if "not rated" in t:
        return "info unrated", "•"
    return "info", "•"  # observation and anything else: neutral, text only


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


LINKABLE = re.compile(r"DOI (10\.\d{4,9}/[^\s)]+?)(?=[.,;]?(?:\s|\)|$))|(https?://[^\s)]+?)(?=[.,;]?(?:\s|\)|$))")
CLAIM_REF = re.compile(r"\[([a-z]\d+)\]")


def refs_linked(text: str) -> str:
    """Escape text and turn [f1]-style claim ids into in-page links."""
    return CLAIM_REF.sub(lambda m: f'<a href="#{m.group(1)}">[{m.group(1)}]</a>', esc(text))


def ref_line(text: str) -> str:
    """Escape a reference and link each DOI and URL once."""
    def sub(m: re.Match) -> str:
        if m.group(1):
            return f'DOI <a href="https://doi.org/{m.group(1)}">{m.group(1)}</a>'
        return f'<a href="{m.group(2)}">{m.group(2)}</a>'
    return LINKABLE.sub(sub, esc(text))


def link(url: str, label: str) -> str:
    if re.match(r"https?://", url):
        return f'<a href="{esc(url)}">{esc(label)}</a>'
    return f"{esc(label)} <span class=\"note\">(link: {esc(url)})</span>"


def dl(pairs: list[tuple[str, str]]) -> str:
    return "<dl>" + "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in pairs) + "</dl>"


def claim_html(c: dict) -> str:
    cls, sym = verdict_style(c["verdict"])
    src = link(c["url"], c["source_title"]) + f'<br><span class="note">Source date: {esc(c["source_date"])} · Retrieved: {esc(c["retrieved"])}</span>'
    return (f'<li class="card claim" id="{esc(c["id"])}"><div class="head"><span class="cid">{esc(c["id"])}</span>'
            f'<span class="tag {cls}"><span aria-hidden="true">{sym} </span><span class="vl">Verdict:</span> {esc(c["verdict"])}</span></div>'
            f'<h3>{esc(c["claim"])}</h3>'
            + dl([("Said by", esc(c["said_by"])), ("What the source says", esc(c["source_says"])), ("Source", src), ("How it was read", esc(c["read"]))])
            + "</li>")


def trio(card: dict) -> str:
    def box(label: str, tag: str, items: list[str]) -> str:
        lis = "".join(f"<li>{refs_linked(i)}</li>" for i in items) or "<li>None recorded.</li>"
        return f'<div class="card"><span class="tag {tag}">{label}</span><ul>{lis}</ul></div>'
    return ('<h2 id="status-of-knowledge">What is known, forecast and unknown</h2><div class="trio">'
            + box("Known: observation", "ok", card.get("known", []))
            + box("Forecast: not an observation", "warn", card.get("forecast", []))
            + box("Unknown", "info", card.get("unknown", [])) + "</div>")


def kv_block(d: dict) -> str:
    rows = []
    for k, v in d.items():
        v = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        val = link(v, v) if re.match(r"https?://", v) else esc(v)
        rows.append((k.replace("_", " ").capitalize(), val))
    return dl(rows)


def how_to_check(h: dict) -> str:
    parts = ['<h2 id="how-to-check">How to check</h2>']
    if "definitions" in h:
        parts.append(f'<p class="note">Tests fixed on: {esc(h["fixed_on"])}</p><div class="card"><ol>'
                     + "".join(f"<li>{esc(d)}</li>" for d in h["definitions"]) + "</ol></div>")
        if h.get("series"):
            rows = "".join(
                f'<tr><td>{link(s["url"], s["name"])}</td><td>{esc(s["delay"])}</td><td>{esc({True: "Yes", False: "No"}.get(s["tested"], s["tested"]))}</td></tr>'
                for s in h["series"])
            parts.append('<div class="wrap" tabindex="0" role="region" aria-label="Data series for the tests"><table><caption>Data series used by the tests</caption>'
                         '<thead><tr><th scope="col">Series</th><th scope="col">Delay</th><th scope="col">Access tested</th></tr></thead>'
                         f"<tbody>{rows}</tbody></table></div>")
    else:
        for name, sub in h.items():
            parts.append('<div class="card">' + (kv_block(sub) if isinstance(sub, dict) else esc(sub)) + "</div>")
    return "".join(parts)


def nice_dates(keys: list[str]) -> str:
    """'2026-11-05', '2026-11-15' -> '5 and 15 November 2026' (same month) or '5 November and 3 December 2026'."""
    import datetime as dt
    ds = [dt.date.fromisoformat(k) for k in keys]
    if len({(d.year, d.month) for d in ds}) == 1:
        return f"{' and '.join(str(d.day) for d in ds)} {ds[0].strftime('%B %Y')}"
    return " and ".join(f"{d.day} {d.strftime('%B %Y')}" for d in ds)


def outcome_html(card: dict) -> str:
    o = card.get("outcome") or {}
    checks = o.get("checks")
    if not checks:
        return ""  # e.g. "not applicable": no section
    keys = sorted(checks)
    defs = (card.get("how_to_check") or {}).get("definitions", [])
    import datetime as dt
    short = lambda k: (lambda d: f"{d.day} {d.strftime('%b %Y')}")(dt.date.fromisoformat(k))
    head = "".join(f'<th scope="col" class="res">Result {esc(short(k))}</th>' for k in keys)
    rows = ""
    for d in defs:
        cells = "".join(
            f'<td class="res">{esc(checks[k]) if checks[k] else "<span class=\"pending\">Not yet checked</span>"}</td>' for k in keys)
        rows += f'<tr><td class="test">{esc(d)}</td>{cells}</tr>'
    return (f'<h2 id="outcome">Outcome</h2><p class="prose">Checks on {nice_dates(keys)}. The tests below were fixed before the outcome. '
            'A cell that says &ldquo;Not yet checked&rdquo; means no check has been made yet; nothing has been filled in ahead of time.</p>'
            '<div class="wrap" tabindex="0" role="region" aria-label="Outcome of the tests"><table><caption>Outcome of each test</caption>'
            f'<thead><tr><th scope="col">Test</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>')


COLS = {"date": "Date", "kind": "Type", "value_ms": "Value (m/s)"}


def data_html(card: dict) -> str:
    d = card.get("data") or {}
    rows = d.get("rows") or []
    if not rows:
        return f'<h2 id="data">Data</h2><p class="prose">{esc(d.get("label", "No data."))}.</p>'
    keys = list(rows[0])
    head = "".join(f'<th scope="col">{esc(COLS.get(k, k))}</th>' for k in keys)
    body = "".join("<tr>" + "".join(f"<td>{esc(r.get(k, ''))}</td>" for k in keys) + "</tr>" for r in rows)
    return (f'<h2 id="data">Data</h2><div class="wrap" tabindex="0" role="region" aria-label="Data behind the card"><table><caption>{esc(d["label"])}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def page(title: str, desc: str, body: str, foot_date: str, noindex: bool = False) -> str:
    robots = '\n<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Global Weather Watch</title>
<meta name="description" content="{esc(desc)}">{robots}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%232b6cb0'/%3E%3C/svg%3E">
<style>{STYLE}</style>
</head><body>
{NAV}
<main id="main">
{body}
</main>
<footer class="site-foot">Page content updated: <span data-asof>{esc(foot_date)}</span>. Independent, non-commercial analysis built from public sources (see <a href="about.html">About &amp; method</a>). Analysis prepared with Claude (Anthropic). <a href="contact.html">Contact</a></footer>
</body></html>
"""


def state_of(slug: str) -> str:
    return STATE.get(slug, "draft")


def build_card(slug: str, c: dict) -> str:
    st = state_of(slug)
    parts = [f'<p class="kicker">{esc(c["kicker"])}</p><h1>{esc(c["title"])}</h1>',
             f'<p class="meta"><span class="tag {"ok" if st == "live" else "warn"}">{esc(st.capitalize())}</span> Updated: {esc(c["updated"])} · '
             f'<a href="claims.html">All claim-vs-evidence cards</a></p>',
             f'<div class="card summary"><b>Summary</b><p>{refs_linked(c["summary"])}</p></div>',
             trio(c)]
    for s in c.get("sections", []):
        parts.append(f'<h2>{esc(s["heading"])}</h2><div class="prose">' + "".join(f"<p>{refs_linked(p)}</p>" for p in s["paragraphs"]) + "</div>")
    parts.append('<h2 id="claims">Claims and ratings</h2><p class="note">Each statement is rated against the named source on the date it was read. '
                 'The rating describes the statement, not the person who made it. &ldquo;Forecast as issued (not rated)&rdquo; means the source is shown, with no verdict.</p>')
    parts.append('<ol class="claims">' + "".join(claim_html(x) for x in c["claims"]) + "</ol>")
    parts.append(how_to_check(c["how_to_check"]))
    parts.append(outcome_html(c))
    parts.append(data_html(c))
    parts.append('<h2 id="caveats">Caveats</h2><ul class="cav">' + "".join(f"<li>{esc(x)}</li>" for x in c["caveats"]) + "</ul>")
    parts.append('<h2 id="references">References</h2><ol class="refs">' + "".join(f"<li>{ref_line(x)}</li>" for x in c["references"]) + "</ol>")
    return page(c["title"], c["summary"][:200], "\n".join(p for p in parts if p), c["updated"], noindex=st != "live")


def build_index(cards: list[tuple[str, dict]]) -> str:
    items = "".join(
        f'<a class="card" href="claim-{esc(s)}.html"><span class="tag ok">Live</span>'
        f'<span class="note">Updated {esc(c["updated"])}</span><h2>{esc(c["title"])}</h2><p class="note">{esc(c["summary"])}</p></a>'
        for s, c in cards)
    body = ('<p class="kicker">Claim vs evidence</p><h1>Claims vs evidence</h1>'
            '<div class="prose"><p>Each card takes one claim that is circulating, splits it into single statements, and rates every statement against a named source, '
            'with the date the source was read and a link to it. Observations, forecasts as issued and what is not known are kept apart. '
            'Where a card makes a testable prediction, the tests are fixed before the outcome and the result is added afterwards. '
            'Ratings describe statements, not people.</p></div>'
            f'<h2>Cards</h2><div class="cards-index">{items}</div>')
    return page("Claims vs evidence", "Cards that rate circulating weather and climate claims against named sources.", body, max(c["updated"] for _, c in cards))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", action="store_true", help="also build draft cards (never listed on the index, noindex)")
    args = ap.parse_args()
    found = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in SRC.glob("*.json") if f.stem != "publish"}
    cards = [(s, found[s]) for s in ORDER if s in found] + [(s, found[s]) for s in sorted(found) if s not in ORDER]
    live = [(s, c) for s, c in cards if state_of(s) == "live"]
    for slug, c in cards:
        if state_of(slug) != "live" and not args.drafts:
            print("skipped draft", slug)
            continue
        (ROOT / f"claim-{slug}.html").write_text(build_card(slug, c), encoding="utf-8")
        print("wrote", f"claim-{slug}.html", f"({state_of(slug)})")
    (ROOT / "claims.html").write_text(build_index(live), encoding="utf-8")
    print("wrote claims.html with", len(live), "live card(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
