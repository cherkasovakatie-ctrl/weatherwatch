"""Build the ENSO development papers (one HTML page each) from papers/*.json.

Each JSON file holds one paper: metadata, status, sections (HTML strings written by hand), a timeline,
an evidence table and a reference list. Every reference carries a DOI or URL and a verification note.
Usage: python3 tools/papers/build.py
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "papers"
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
.site-foot { max-width: 1100px; margin: 24px auto; padding: 0 16px 24px; color: var(--color-fg-muted); font-size: .8rem; line-height: 1.5; }
a { color: inherit; }
main { max-width: 1100px; margin: 0 auto; padding: 16px; }
h1 { font-family: var(--font-serif); font-weight: 400; font-size: 1.9rem; margin: .3em 0 .2em; line-height: 1.2; }
h2 { font-family: var(--font-serif); font-weight: 400; font-size: 1.35rem; margin: 1.6em 0 .4em; }
h3 { font-size: 1rem; margin: 1.2em 0 .3em; }
.meta { color: var(--color-fg-muted); font-size: .88rem; line-height: 1.6; margin: 0 0 8px; }
.prose { max-width: 78ch; line-height: 1.65; font-size: .97rem; }
.prose p { margin: 0 0 .9em; }
.card { background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: 10px; padding: 14px 16px; margin: 12px 0; min-width: 0; }
.status { border-left: 4px solid var(--warn); }
.status.done { border-left-color: var(--ok); }
.tag { display: inline-block; font-size: .72rem; padding: 1px 8px; border-radius: 999px; border: 1px solid currentColor; margin-right: 6px; white-space: nowrap; }
.tag.ok { color: var(--ok); } .tag.warn { color: var(--warn); } .tag.info { color: var(--color-fg-muted); } .tag.bad { color: var(--bad); }
.wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { border-collapse: collapse; width: 100%; font-size: .84rem; line-height: 1.45; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid var(--color-border-line); }
thead th { font-weight: 600; background: var(--color-panel); position: sticky; top: 0; }
tbody tr:nth-child(even) { background: var(--zebra); }
td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
table.data td { white-space: nowrap; padding: 5px 6px; }
table.data th { white-space: normal; overflow-wrap: normal; vertical-align: bottom; padding: 5px 6px; font-size: .78rem; line-height: 1.25; min-width: 3.6em; }
.note { font-size: .82rem; color: var(--color-fg-muted); line-height: 1.5; margin: 6px 0 0; }
ol.refs { padding-left: 1.4em; font-size: .86rem; line-height: 1.55; }
ol.refs li { margin-bottom: 6px; overflow-wrap: anywhere; }
.prose, .meta, .card { overflow-wrap: anywhere; }
.toc { font-size: .9rem; line-height: 1.7; columns: 2 16rem; }
.papers { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: 10px; }
.papers a { display: block; text-decoration: none; }
"""

NAV = """<nav class="site-nav" aria-label="Site">
  <a class="brand" href="./">Global Weather Watch</a>
  <a href="./">Dashboard</a>
  <a href="./#overview">ENSO overview</a>
  <a href="./#climate">Climate</a>
  <a href="deadliest.html">Deadliest events</a>
  <a href="events.html">Event log</a>
  <a href="claims.html">Claims vs evidence</a>
  <a href="data.html">Data archive</a>
  <a href="about.html">About &amp; method</a>
</nav>"""

STATUS_TAG = {"planned": ("info", "Planned"), "in-progress": ("warn", "In progress"), "draft": ("warn", "Draft for review"), "final": ("ok", "Published")}
CONF_TAG = {"High": "ok", "Medium": "warn", "Low": "bad", "Pending": "info"}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def ref_html(r: dict) -> str:
    link = r.get("doi") and f'https://doi.org/{r["doi"]}' or (r.get("url") or "")
    shown = r.get("doi") and f'doi:{esc(r["doi"])}' or esc(r.get("url") or "")
    note = f' <span class="note">[{esc(r["check"])}]</span>' if r.get("check") else ""
    anchor = f' <a href="{esc(link)}">{shown}</a>' if link else ""
    return f'<li id="ref-{esc(r["key"])}">{r["text"]}{anchor}{note}</li>'


def table(cols: list[str], rows: list[list[str]], cls: str = "") -> str:
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="wrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def conf(c: str) -> str:
    return f'<span class="tag {CONF_TAG.get(c.split()[0], "info")}">{esc(c)}</span>'


def build(p: dict, siblings: list[dict]) -> str:
    tag_cls, tag_label = STATUS_TAG[p["status"]]
    parts = [f'<h1>{esc(p["title"])}</h1>',
             (f'<p class="meta"><span class="tag {tag_cls}">{tag_label}</span> Paper {p["number"]} of 4 · Research date: {esc(p["research_date"])} · '
              f'Observational cutoff: {esc(p["obs_cutoff"])} · Literature: {esc(p["lit_cutoff"])} · Primary index: RONI (NOAA CPC)</p>')]
    parts.append(f'<div class="card status{" done" if p["status"] == "final" else ""}"><b>Status.</b> {p["status_note"]}</div>')
    if p.get("toc"):
        parts.append('<div class="card"><b>Contents</b><div class="toc">' + "".join(f'<div><a href="#{a}">{esc(t)}</a></div>' for a, t in p["toc"]) + "</div></div>")
    for s in p.get("sections", []):
        parts.append(f'<h2 id="{s["id"]}">{esc(s["title"])}</h2><div class="prose">{s["html"]}</div>')
        if s.get("table"):
            t = s["table"]
            parts.append(table(t["cols"], t["rows"], t.get("cls", "")))
            if t.get("note"):
                parts.append(f'<p class="note">{t["note"]}</p>')
    if p.get("timeline"):
        parts.append('<h2 id="timeline">Timeline</h2>')
        parts.append(table(["Date", "Observation", "Proposed mechanism", "Source", "Confidence"],
                           [[esc(t[0]), t[1], t[2], t[3], conf(t[4])] for t in p["timeline"]]))
        parts.append('<p class="note">Confidence refers to the observation and its link to the stated mechanism for this event, not to general ENSO theory.</p>')
    if p.get("evidence"):
        parts.append('<h2 id="evidence">Evidence table</h2>')
        parts.append(table(["Factor", "Observed conditions and timing", "Proposed mechanism", "Role in development", "Evidence type", "Confidence", "Key sources"],
                           [[f"<b>{esc(e[0])}</b>", e[1], e[2], e[3], e[4], conf(e[5]), e[6]] for e in p["evidence"]]))
        parts.append('<p class="note">Evidence grades: A = event-specific observation plus a model or heat-budget study isolating the effect; B = event-specific observation with a plausible mechanism and supporting studies; '
                     'C = correlation, composite or general theory only; D = speculative, disputed, or not yet tested for this event.</p>')
    for s in p.get("post_sections", []):
        parts.append(f'<h2 id="{s["id"]}">{esc(s["title"])}</h2><div class="prose">{s["html"]}</div>')
        if s.get("table"):
            t = s["table"]
            parts.append(table(t["cols"], t["rows"], t.get("cls", "")))
            if t.get("note"):
                parts.append(f'<p class="note">{t["note"]}</p>')
        if s.get("html_after"):
            parts.append(f'<div class="prose">{s["html_after"]}</div>')
    if p.get("after"):
        s = p["after"]
        parts.append(f'<h2 id="{s["id"]}">{esc(s["title"])}</h2><div class="prose">{s["html"]}</div>')
    if p.get("references"):
        parts.append('<h2 id="references">References</h2><ol class="refs">' + "".join(ref_html(r) for r in p["references"]) + "</ol>")
        parts.append('<p class="note">Every DOI was checked against the Crossref registry; summaries rely on the published abstract unless noted. Full texts behind publisher paywalls were not read and are marked.</p>')
    sib = "".join(f'<a class="card" href="{s["file"]}"{" aria-current=\"page\"" if s["file"] == p["file"] else ""}><b>{esc(s["short"])}</b><br><span class="note">{STATUS_TAG[s["status"]][1]}</span></a>' for s in siblings)
    parts.append(f'<h2>The four papers</h2><div class="papers">{sib}</div>')
    extra = "".join(p.get("head_scripts", []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(p["short"])} · Global Weather Watch</title>
<meta name="description" content="{esc(p["description"])}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%232b6cb0'/%3E%3C/svg%3E">
<style>{STYLE}</style>{extra}
</head><body>
{NAV}
<main>
{chr(10).join(parts)}
</main>
<footer class="site-foot">Data snapshot: <span data-asof>{esc(p["research_date"])}</span>. Independent, non-commercial analysis built from public sources (see <a href="about.html">About &amp; method</a>). Analysis prepared with Claude (Anthropic).</footer>
</body></html>
"""


def main() -> int:
    papers = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(SRC.glob("*.json"))]
    papers.sort(key=lambda p: p["number"])
    for p in papers:
        (ROOT / p["file"]).write_text(build(p, papers), encoding="utf-8")
        print("wrote", p["file"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
