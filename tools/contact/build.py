"""Build contact.html from contact/contact.json (same page template as the claims cards).
The only address on the page is the public support address in the JSON. There is no form and no script.
Usage: python3 tools/contact/build.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/cards"))
import build as cards  # noqa: E402  (page template, NAV, esc)

C = json.loads((ROOT / "contact/contact.json").read_text(encoding="utf-8"))


def body() -> str:
    mail = f'mailto:{C["email"]}?subject={quote(C["subject"], safe="")}'
    parts = [f'<h1>{cards.esc(C["title"])}</h1>',
             f'<div class="prose"><p>{cards.esc(C["intro"])}</p>'
             f'<p><a href="{cards.esc(mail)}">{cards.esc(C["email"])}</a></p></div>']
    for s in C["sections"]:
        parts.append(f'<h2>{cards.esc(s["heading"])}</h2><div class="prose">')
        if s.get("list"):
            parts.append("<ul>" + "".join(f"<li>{cards.esc(x)}</li>" for x in s["list"]) + "</ul>")
        parts.extend(f"<p>{p}</p>" for p in s.get("paragraphs", []))  # authored html (links)
        parts.append("</div>")
    return "\n".join(parts)


def main() -> int:
    nav = cards.NAV.replace(' aria-current="page"', "")
    text = cards.page(C["title"], C["description"], body(), "", noindex=False)
    text = text.replace(cards.NAV, nav)
    # the footer of this page has no date: 'Page content updated' needs one, so use the plain footer wording
    import re
    text = re.sub(r'Page content updated: <span data-asof>[^<]*</span>\. ', "", text)
    (ROOT / "contact.html").write_text(text, encoding="utf-8")
    print("wrote contact.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
