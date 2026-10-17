"""Build the mundane-astrology datasets for the website.

Usage (from the repo root):
    python3 tools/mundane/build.py            # full build, fetches S&P history
    python3 tools/mundane/build.py --offline  # skip the market fetch (keeps existing market files)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mundane.charts import CHARTS, natal_points, positions, transits  # noqa: E402
from mundane.cycles import (  # noqa: E402
    SYNODIC_YEARS,
    aspect_hits,
    cyclic_index,
    eclipses,
    monthly_dates,
    seasonal_ingresses,
    sign_ingresses,
    stations,
)
from mundane.ephemeris import OUTER, PLANETS, fmt_lon, lon, sign_of, speed, to_ephem  # noqa: E402
from mundane.events import WORLD_EVENTS  # noqa: E402
from mundane.markets import bear_markets, episodes, fetch_sp500, run_tests  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def utc(y: int, m: int = 1, d: int = 1) -> datetime:
    return datetime(y, m, d, tzinfo=UTC)


def write_csv(name: str, header: Sequence[str], rows: Iterable[Sequence[object]]) -> int:
    path = DATA / name
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")
    return len(rows)


def ts(t: datetime) -> tuple[str, str]:
    return t.strftime("%Y-%m-%d"), t.strftime("%H:%M")


def build_cycles() -> None:
    hits = aspect_hits(utc(1900), utc(2041))
    write_csv(
        "mundane_aspects.csv",
        [
            "date",
            "time_utc",
            "pair",
            "aspect",
            "phase",
            "kind",
            "pass_no",
            "passes",
            "position_a",
            "position_b",
            "sign",
            "retro",
            "synodic_years",
        ],
        (
            [
                *ts(h.when),
                h.pair,
                h.aspect,
                h.phase,
                h.kind,
                h.pass_no,
                h.passes,
                fmt_lon(h.lon_a),
                fmt_lon(h.lon_b),
                sign_of(h.lon_a),
                "yes" if (h.retro_a or h.retro_b) else "no",
                SYNODIC_YEARS[h.pair],
            ]
            for h in hits
        ),
    )
    ing = sign_ingresses(OUTER, utc(1900), utc(2041))
    write_csv(
        "mundane_ingresses.csv",
        ["date", "time_utc", "body", "sign", "direction"],
        ([*ts(i.when), i.body, i.sign, i.direction] for i in ing),
    )
    st = stations(OUTER, utc(1990), utc(2041))
    write_csv(
        "mundane_stations.csv",
        ["date", "time_utc", "body", "turns", "position"],
        ([*ts(s.when), s.body, s.turns, fmt_lon(s.lon)] for s in st),
    )
    se = seasonal_ingresses(utc(1990), utc(2041))
    write_csv("mundane_seasonal.csv", ["date", "time_utc", "point"], ([*ts(s.when), s.point] for s in se))
    ec = eclipses(utc(1990), utc(2041))
    write_csv(
        "mundane_eclipses.csv",
        ["date", "time_utc", "kind", "position", "sign", "moon_lat"],
        ([*ts(e.when), e.kind, fmt_lon(e.lon), sign_of(e.lon), e.moon_lat] for e in ec),
    )
    write_csv(
        "mundane_cyclic_index.csv",
        ["month", "cyclic_index"],
        ((t.strftime("%Y-%m"), round(cyclic_index(to_ephem(t)), 1)) for t in monthly_dates(1900, 2040)),
    )
    write_csv(
        "mundane_world_events.csv",
        ["date", "category", "event", "region"],
        ([e.date, e.category, e.event, e.region] for e in WORLD_EVENTS),
    )


def build_sky_now(now: datetime) -> str:
    """Refresh the dashboard's 'Planet positions now' table for 12:00 UTC on the build date."""
    t = now.replace(hour=12, minute=0, second=0, microsecond=0)
    d = to_ephem(t)
    rows = []
    for body in [*PLANETS, "Node"]:
        lo = lon(body, d)
        retro = body == "Node" or speed(body, d) < 0
        rows.append(
            [
                body if body != "Node" else "North Node (mean)",
                round(lo, 2),
                sign_of(lo),
                f"{lo % 30:.1f}°",
                "℞ yes" if retro else "no",
            ]
        )
    write_csv("sky_now.csv", ["body", "lon", "sign", "degree", "retrograde"], rows)
    return t.strftime("%-d %b %Y")


def build_charts() -> None:
    write_csv(
        "national_charts.csv",
        ["id", "country", "label", "event", "local_time", "utc", "place", "lat", "lon", "rating", "source", "notes"],
        (
            [
                c.id,
                c.country,
                c.label,
                c.event,
                c.local,
                c.utc.strftime("%Y-%m-%d %H:%M"),
                c.place,
                c.lat,
                c.lon_east,
                c.rating,
                c.source,
                c.notes,
            ]
            for c in CHARTS
        ),
    )
    rows: list[list[object]] = []
    for c in CHARTS:
        targets = {p.point for p in natal_points(c)}
        for p in positions(c):
            rows.append(
                [
                    c.id,
                    p.point,
                    round(p.lon, 3),
                    fmt_lon(p.lon),
                    sign_of(p.lon),
                    "yes" if p.retro and p.point != "North Node (mean)" else "no",
                    "yes" if p.point in targets else "no",
                ]
            )
    write_csv(
        "national_positions.csv", ["chart_id", "point", "lon", "position", "sign", "retro", "transit_target"], rows
    )
    trows: list[list[object]] = []
    for c in CHARTS:
        for h in transits(c, utc(2015), utc(2036)):
            trows.append(
                [
                    *ts(h.when),
                    c.id,
                    h.transiting,
                    h.aspect,
                    h.natal,
                    fmt_lon(h.natal_lon),
                    fmt_lon(h.transit_lon),
                    "yes" if h.retro else "no",
                ]
            )
    write_csv(
        "national_transits.csv",
        [
            "date",
            "time_utc",
            "chart_id",
            "transiting",
            "aspect",
            "natal",
            "natal_position",
            "transit_position",
            "retro",
        ],
        trows,
    )


def build_markets() -> None:
    months = fetch_sp500()
    last = months[-1].month
    now = datetime.now(UTC)
    age = (now.year - int(last[:4])) * 12 + now.month - int(last[5:7])
    if age > 6:  # truncated or stale fetch: never publish it
        raise RuntimeError(f"S&P source looks stale or truncated: last row {last}")
    ci = {t.strftime("%Y-%m"): round(cyclic_index(to_ephem(t)), 1) for t in monthly_dates(1900, 2040)}
    write_csv(
        "market_monthly.csv",
        ["month", "sp500", "sp500_real", "cyclic_index"],
        (
            [m.month, m.nominal, "" if m.real is None else m.real, ci.get(m.month, "")]
            for m in months
            if m.month >= "1900-01"
        ),
    )
    write_csv(
        "market_bear.csv",
        ["peak", "trough", "recovered", "depth_pct"],
        ([b.peak, b.trough, b.recovered, b.depth_pct] for b in bear_markets(months) if b.peak >= "1900-01"),
    )
    res = run_tests(months)
    write_csv(
        "market_tests.csv",
        [
            "predictor",
            "statistic",
            "value",
            "p_value",
            "q_fdr",
            "first_half",
            "second_half",
            "same_sign_both_halves",
            "n_months",
            "share_of_months_in_window",
        ],
        (
            [
                r.predictor,
                r.statistic,
                r.value,
                r.p_value,
                r.q_fdr,
                r.early,
                r.late,
                "yes" if r.replicates else "no",
                r.n_months,
                "" if r.share_in_window != r.share_in_window else r.share_in_window,
            ]
            for r in res
        ),
    )
    best = min(res, key=lambda r: r.q_fdr)
    if "hard aspect" in best.predictor:
        a, b = best.predictor.split(" ")[0].split("–")
        write_csv(
            "market_episodes.csv",
            ["predictor", "start", "end", "months", "mean_fwd_12m_real_return_pct", "gap_if_dropped"],
            (
                [best.predictor, e.start, e.end, e.months, e.mean_fwd_return, e.effect_without]
                for e in episodes(months, a, b)
            ),
        )
    print(f"  S&P source last row: {last}")


MANIFEST_ENTRIES: dict[str, tuple[str, str]] = {
    "mundane_aspects": (
        "Outer-planet cycles, 1900–2040",
        "Exact conjunctions, squares, oppositions and trines between Jupiter, Saturn, Uranus, Neptune and Pluto, with retrograde passes numbered. PyEphem (VSOP87), geocentric, tropical zodiac, apparent positions of date.",
    ),
    "mundane_ingresses": (
        "Outer-planet sign ingresses, 1900–2040",
        "Every entry of Jupiter–Pluto into a zodiac sign, including retrograde re-entries. PyEphem.",
    ),
    "mundane_stations": (
        "Outer-planet stations, 1990–2040",
        "Dates on which Jupiter–Pluto turn retrograde or direct. PyEphem.",
    ),
    "mundane_seasonal": (
        "Equinox and solstice ingress times, 1990–2040",
        "UTC times of the Sun's entry into Aries, Cancer, Libra and Capricorn, used for mundane ingress charts. PyEphem.",
    ),
    "mundane_eclipses": (
        "Solar and lunar eclipses, 1990–2040",
        "New and full moons close enough to a lunar node to produce an eclipse of any type (partial and penumbral included). Type detail (total, annular) is not computed. Validated against NASA dates for 2024–2027.",
    ),
    "mundane_cyclic_index": (
        "Cyclic index (Barbault), monthly 1900–2040",
        "Sum of the ten pairwise angular separations between Jupiter, Saturn, Uranus, Neptune and Pluto (0–1800°). Low values mean the outer planets are clustered.",
    ),
    "mundane_world_events": (
        "Reference world events, 1914–2023",
        "Hand-picked geopolitical and economic turning points for orientation on the timeline. Not a test sample.",
    ),
    "national_charts": (
        "National charts: definitions",
        "Founding moments, places and time-reliability ratings for the national charts (A documented, B well-attested, C disputed, X no time).",
    ),
    "national_positions": (
        "National charts: planet positions",
        "Planet, node and (for A/B charts) angle positions for each national chart.",
    ),
    "national_transits": (
        "National charts: outer-planet transits, 2015–2035",
        "Exact transits of Jupiter–Pluto (conjunction, square, opposition, trine) to national chart points. Moon and angles only for charts with a reliable time.",
    ),
    "market_monthly": (
        "S&P 500 monthly with cyclic index",
        "Shiller monthly-average S&P 500 (nominal; real where CPI is available, to Sep 2023), via datasets/s-and-p-500 on GitHub, with the cyclic index.",
    ),
    "market_bear": (
        "S&P 500 bear markets (monthly averages)",
        "Declines of 20% or more in monthly-average prices, peak to trough. Monthly averages understate intramonth extremes.",
    ),
    "market_episodes": (
        "Strongest market lead, episode by episode",
        "Each window of the best-scoring planetary predictor, its mean forward 12-month real return, and the in-minus-out gap if that episode is dropped.",
    ),
    "market_tests": (
        "Planetary cycles vs forward 12-month real S&P returns",
        "Correlation and in-window minus out-of-window differences, with circular-shift permutation p-values, Benjamini–Hochberg q and a split-half replication check.",
    ),
}


def update_manifest(sky_label: str) -> None:
    path = DATA / "manifest.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    by_id = {d["id"]: d for d in m["datasets"]}
    if "sky_now" in by_id:
        by_id["sky_now"].update(
            description=(
                "Geocentric ecliptic longitude, zodiac sign and degree (tropical zodiac) of the Sun, Moon and planets, "
                f"plus the mean lunar node, for {sky_label} 12:00 UTC, computed with PyEphem (VSOP87). "
                "Retrograde = longitude decreasing day to day."
            ),
            updated=today,
            bytes=(DATA / "sky_now.csv").stat().st_size,
        )
    for ds_id, (title, desc) in MANIFEST_ENTRIES.items():
        f = DATA / f"{ds_id}.csv"
        if not f.exists():
            continue
        by_id[ds_id] = {
            "id": ds_id,
            "file": f.name,
            "title": title,
            "description": desc,
            "updated": today,
            "bytes": f.stat().st_size,
        }
    m["datasets"] = sorted(by_id.values(), key=lambda d: d["id"])
    path.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip the S&P fetch")
    args = ap.parse_args()
    print("Sky now…")
    sky_label = build_sky_now(datetime.now(UTC))
    print("Cycles…")
    build_cycles()
    print("National charts…")
    build_charts()
    if not args.offline:
        print("Markets…")
        build_markets()
    update_manifest(sky_label)
    print("Done.")


if __name__ == "__main__":
    main()
