from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from finalize import ASOF_RE, human  # noqa: E402


def test_human_date() -> None:
    assert human(date(2026, 10, 23)) == "23 October 2026"
    assert human(date(2026, 11, 6)) == "6 November 2026"


def test_asof_replacement() -> None:
    html = "Data snapshot: <span data-asof>16 October 2026</span>."
    assert ASOF_RE.sub(r"\g<1>23 October 2026\g<2>", html) == "Data snapshot: <span data-asof>23 October 2026</span>."
