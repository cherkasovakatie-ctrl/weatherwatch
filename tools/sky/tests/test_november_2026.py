"""Checks of the November 2026 ephemeris helpers against independently known dates."""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import november_2026 as nov


def test_wrap_keeps_angles_in_half_open_range() -> None:
    assert nov.wrap(190.0) == -170.0
    assert nov.wrap(-190.0) == 170.0
    assert nov.wrap(0.0) == 0.0


def test_fmt_gives_degree_and_sign() -> None:
    assert nov.fmt(242.0) == "2.0° Sagittarius"


def test_roots_finds_sun_ingress_to_sagittarius() -> None:
    hits = nov.roots(lambda x: nov.wrap(nov.lon("Sun", x) - 240.0), nov.M0, nov.M1, 12)
    assert len(hits) == 1
    assert hits[0].date() == dt.date(2026, 11, 22)


def test_calendar_has_one_full_moon_on_24_november() -> None:
    rows, facts = nov.calendar()
    full = facts["Full Moon"]
    assert len(full) == 1
    assert full[0].date() == dt.date(2026, 11, 24)
    assert all(r[0].startswith("2026-11") for r in rows)
