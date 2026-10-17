from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mundane.charts import CHARTS, natal_points, positions  # noqa: E402
from mundane.cycles import aspect_hits, cyclic_index, eclipses, seasonal_ingresses, sign_ingresses  # noqa: E402
from mundane.ephemeris import angles, fmt_lon, to_ephem, wrap180  # noqa: E402
from mundane.markets import Month, bear_markets, bh_fdr, parse_sp500  # noqa: E402


def utc(*a: int) -> datetime:
    return datetime(*a, tzinfo=UTC)


def test_wrap_and_format() -> None:
    assert wrap180(190) == -170
    assert wrap180(-180) == -180
    assert fmt_lon(300.5) == "0°30′ Aquarius"
    assert fmt_lon(29.9999) == "0°00′ Taurus"


def test_great_conjunction_2020() -> None:
    hits = [h for h in aspect_hits(utc(2020, 11, 1), utc(2021, 2, 1)) if h.pair == "Jupiter–Saturn"]
    conj = [h for h in hits if h.aspect == "conjunction"]
    assert len(conj) == 1
    assert abs((conj[0].when - utc(2020, 12, 21, 18, 20)).total_seconds()) < 3600
    assert fmt_lon(conj[0].lon_a).endswith("Aquarius")


def test_saturn_neptune_2026() -> None:
    hits = [h for h in aspect_hits(utc(2026, 1, 1), utc(2026, 4, 1)) if h.pair == "Saturn–Neptune"]
    assert [h.when.date().isoformat() for h in hits if h.aspect == "conjunction"] == ["2026-02-20"]


def test_pluto_aquarius_ingresses() -> None:
    ing = sign_ingresses(("Pluto",), utc(2023, 1, 1), utc(2025, 1, 1))
    got = [(i.when.date().isoformat(), i.sign, i.direction) for i in ing]
    assert got[0] == ("2023-03-23", "Aquarius", "direct")
    assert ("2023-06-11", "Capricorn", "retrograde") in got
    assert got[-1][1:] == ("Aquarius", "direct")


def test_equinox_2024_to_the_minute() -> None:
    aries = [s for s in seasonal_ingresses(utc(2024, 1, 1), utc(2024, 12, 31)) if s.point == "Aries"]
    assert abs((aries[0].when - utc(2024, 3, 20, 3, 6)).total_seconds()) < 180


def test_eclipses_2024_2027_match_nasa_dates() -> None:
    expected = {
        "solar": [
            "2024-04-08",
            "2024-10-02",
            "2025-03-29",
            "2025-09-21",
            "2026-02-17",
            "2026-08-12",
            "2027-02-06",
            "2027-08-02",
        ],
        "lunar": [
            "2024-03-25",
            "2024-09-18",
            "2025-03-14",
            "2025-09-07",
            "2026-03-03",
            "2026-08-28",
            "2027-02-20",
            "2027-07-18",
            "2027-08-17",
        ],
    }
    got = eclipses(utc(2024, 1, 1), utc(2027, 12, 31))
    for kind, dates in expected.items():
        assert [e.when.date().isoformat() for e in got if e.kind == kind] == dates


def test_ascendant_at_equator_ramc_zero_is_cancer() -> None:
    # Find a moment when local sidereal time ~0h at Greenwich on the equator: Asc must be ~0° Cancer.
    a = angles(utc(2024, 9, 22, 0, 0), 0.0, 0.0)
    assert abs(wrap180(a.asc - (a.mc + 90))) < 3


def test_india_chart_rising_degree() -> None:
    india = next(c for c in CHARTS if c.id == "india-1947")
    asc = next(p for p in positions(india) if p.point == "Ascendant")
    # Tropical ~0°51' Gemini (the classic sidereal 7°46' Taurus plus Lahiri ayanamsa).
    assert abs(asc.lon - 60.85) < 0.5


def test_untimed_charts_exclude_moon_and_angles() -> None:
    for c in CHARTS:
        names = {p.point for p in natal_points(c)}
        if c.timed:
            assert {"Moon", "Ascendant", "Midheaven"} <= names
        else:
            assert names.isdisjoint({"Moon", "Ascendant", "Midheaven"})


def test_cyclic_index_bounds() -> None:
    v = cyclic_index(to_ephem(utc(2026, 10, 15)))
    assert 0 <= v <= 1800


def test_bear_markets_synthetic() -> None:
    prices = [100, 110, 120, 90, 80, 100, 125, 130]
    months = [Month(f"2000-{i + 1:02d}", p, p) for i, p in enumerate(prices)]
    bears = bear_markets(months)
    assert len(bears) == 1
    assert (bears[0].peak, bears[0].trough, bears[0].recovered) == ("2000-03", "2000-05", "2000-07")
    assert bears[0].depth_pct == pytest.approx(33.3)


def test_bh_fdr() -> None:
    q = bh_fdr([0.01, 0.04, 0.03, 0.5])
    assert q == pytest.approx([0.04, 0.0533333, 0.0533333, 0.5], rel=1e-4)


def test_parse_sp500_marks_missing_cpi() -> None:
    text = (
        "Date,SP500,Dividend,Earnings,Consumer Price Index,Long Interest Rate,Real Price,Real Dividend,"
        "Real Earnings,PE10\n2023-09-01,4400,0,0,307.0,4.4,4400,0,0,0\n2023-10-01,4269,0,0,0.0,0,0,0,0,0\n"
    )
    rows = parse_sp500(text)
    assert rows[0].real == 4400 and rows[1].real is None
