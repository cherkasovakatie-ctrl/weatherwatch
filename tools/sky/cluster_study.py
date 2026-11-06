# ruff: noqa: DTZ007  # naive UTC datetimes throughout (PyEphem convention)
"""Do earthquakes or eruption onsets differ around planet groupings, supermoons and Mars-Jupiter conjunctions?

Pre-registered design (definitions in cluster_astro.py, fixed before the catalogues were opened):
  Outcomes   Q-all : USGS ComCat M6.0+ events, all (aftershocks included), 1973-01-01 to data cutoff
             Q-main: M6.0+ mainshocks after Gardner-Knopoff declustering;  Q7: M7.0+ mainshocks
             V     : Smithsonian GVP confirmed eruption onsets dated to +-3 days or better, 1973-2025
  Windows    primary +-3 days around each event (grouping episodes: whole run +-3 d); +-1 and +-7 d as sensitivity
  Null       5,000 circular shifts of the outcome dates (keeps aftershock and seasonal clustering structure);
             one-sided p for an excess; Benjamini-Hochberg q over the primary family only.
  Periods    every cluster found 1973-2026 (cluster_astro.clusters) plus the August 2024 candidate from the brief,
             each compared with all same-length windows 1973-2025 and with the same calendar window in other years.
Inputs: USGS and GVP files fetched by tools/sky/fetch_catalogs.py (weekly-raw branch, raw/sky/).
Run: python3 tools/sky/cluster_study.py <usgs_m55_1973_now.csv> <gvp_eruptions.csv>
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cluster_astro as A

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
Q_END = dt.date(2026, 11, 6)
V_END = dt.date(2025, 12, 31)
N_SHIFT = 5000


def day(d: dt.date) -> int:
    return (d - A.T0).days


def load_quakes(path: Path) -> list[tuple[dt.datetime, float, float, float, str]]:
    out = []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["type"] != "earthquake" or not r["mag"]:
                continue
            t = dt.datetime.strptime(r["time"][:19], "%Y-%m-%dT%H:%M:%S")
            out.append(
                (
                    t,
                    float(r["latitude"]),
                    float(r["longitude"]),
                    float(r["mag"]),
                    r["place"],
                )
            )
    return sorted(out)


def decluster(q: list[tuple[dt.datetime, float, float, float, str]]) -> list[bool]:
    """Gardner-Knopoff (1974) space-time windows, forward in time only (aftershocks); True = mainshock."""

    def win(m: float) -> tuple[float, float]:
        return (
            10 ** (0.032 * m + 2.7389) if m >= 6.5 else 10 ** (0.5409 * m - 0.547)
        ), 10 ** (0.1238 * m + 0.983)

    def hav(a: float, b: float, c: float, d: float) -> float:
        a, b, c, d = map(math.radians, (a, b, c, d))
        h = (
            math.sin((c - a) / 2) ** 2
            + math.cos(a) * math.cos(c) * math.sin((d - b) / 2) ** 2
        )
        return 6371 * 2 * math.asin(math.sqrt(h))

    tdays = np.array([(x[0] - q[0][0]).total_seconds() / 86400 for x in q])
    dep = np.zeros(len(q), bool)
    for k in sorted(range(len(q)), key=lambda k: -q[k][3]):
        if dep[k]:
            continue
        tw, km = win(q[k][3])
        lo, hi = (
            np.searchsorted(tdays, tdays[k]),
            np.searchsorted(tdays, tdays[k] + tw, side="right"),
        )
        for j in range(lo, hi):
            if (
                j != k
                and not dep[j]
                and q[j][3] <= q[k][3]
                and hav(q[k][1], q[k][2], q[j][1], q[j][2]) <= km
            ):
                dep[j] = True
    return list(~dep)


def load_eruptions(path: Path) -> list[tuple[dt.date, str, str]]:
    out = []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["Activity_Type"] != "Confirmed Eruption":
                continue
            try:
                d = dt.date(
                    int(r["StartDateYear"]),
                    int(r["StartDateMonth"]),
                    int(r["StartDateDay"]),
                )
            except ValueError:
                continue
            if (r["StartDateDayUncertainty"] or "0") not in ("0", "1", "2", "3"):
                continue
            if A.T0 <= d <= V_END:
                out.append((d, r["Volcano_Name"], r["ExplosivityIndexMax"]))
    return sorted(out)


def mask(points: list[tuple[int, int]], n: int) -> np.ndarray:
    m = np.zeros(n, bool)
    for a, b in points:
        m[max(0, a) : min(n, b + 1)] = True
    return m


def shift_test(
    m: np.ndarray, s: np.ndarray, rng: np.random.Generator
) -> tuple[int, float, float]:
    n = len(m)
    obs = int(m[s].sum())
    null = np.array([m[(s + o) % n].sum() for o in rng.integers(1, n, N_SHIFT)])
    return obs, float(null.mean()), float((1 + np.sum(null >= obs)) / (N_SHIFT + 1))


def bh(p: list[float]) -> list[float]:
    pv = np.array(p)
    o = np.argsort(pv)
    q = np.empty(len(pv))
    q[o] = np.minimum.accumulate((pv[o] * len(pv) / np.arange(1, len(pv) + 1))[::-1])[
        ::-1
    ]
    return [float(min(x, 1.0)) for x in q]


BASE_END = dt.date(2025, 12, 31)


def count(s: np.ndarray, lo: int, hi: int) -> int:
    return int(((s >= lo) & (s <= hi)).sum())


def baseline(
    s: np.ndarray, n_end: int, length: int, obs: int
) -> tuple[float, float, float, float]:
    """Mean, 2.5th and 97.5th percentile of counts in every window of this length, and the mid-rank percentile of obs."""
    srt = np.sort(s)
    starts = np.arange(0, n_end - length)
    cs = np.searchsorted(srt, starts + length, side="left") - np.searchsorted(
        srt, starts, side="left"
    )
    pct = float((cs < obs).mean() * 100 + (cs == obs).mean() * 50)
    return (
        float(cs.mean()),
        float(np.percentile(cs, 2.5)),
        float(np.percentile(cs, 97.5)),
        pct,
    )


def season(s: np.ndarray, start: dt.date, length: int, last_year: int) -> float:
    """Mean count in the same calendar window in every other year 1973..last_year."""
    vals = []
    for y in range(1973, last_year + 1):
        if y == start.year:
            continue
        try:
            lo = day(start.replace(year=y))
        except ValueError:
            continue
        if lo + length - 1 <= day(dt.date(last_year, 12, 31)):
            vals.append(count(s, lo, lo + length - 1))
    return float(np.mean(vals))


def main(usgs: Path, gvp: Path) -> None:
    rng = np.random.default_rng(2026)
    eps, fms, mj = A.grouping_episodes(), A.full_moons(), A.mars_jupiter()
    sms = [t for t, km in fms if km <= A.SUPERMOON_KM]
    cl = A.clusters(eps, fms, mj)

    q = [x for x in load_quakes(usgs) if x[3] >= 6.0 and x[0].date() <= Q_END]
    main_flag = decluster(q)
    nq = day(Q_END) + 1
    outcomes = {
        "M6+ earthquakes, all": (np.array([day(x[0].date()) for x in q]), nq),
        "M6+ mainshocks": (
            np.array([day(x[0].date()) for x, f in zip(q, main_flag) if f]),
            nq,
        ),
        "M7+ mainshocks": (
            np.array(
                [day(x[0].date()) for x, f in zip(q, main_flag) if f and x[3] >= 7]
            ),
            nq,
        ),
        "Eruption onsets": (
            np.array([day(e[0]) for e in load_eruptions(gvp)]),
            day(V_END) + 1,
        ),
    }
    features = {
        "Mars–Jupiter conjunction": [(day(t.date()), day(t.date())) for t in mj],
        "Supermoon (full Moon ≤ 362,000 km)": [
            (day(t.date()), day(t.date())) for t in sms
        ],
        "Planet grouping (≥4 planets, whole run)": [
            (day(e.start), day(e.end)) for e in eps
        ],
        "All three within 30 days (cluster span)": [
            (day(c.span_start), day(c.span_end)) for c in cl
        ],
    }
    rows = []
    for fname, iv in features.items():
        for w in (3, 1, 7):
            for oname, (s, n) in outcomes.items():
                m = mask([(a - w, b + w) for a, b in iv], n)
                ss = s[s < n]
                obs, exp, p = shift_test(m, ss, rng)
                rows.append(
                    {
                        "feature": fname,
                        "window": f"±{w} d",
                        "family": "primary" if w == 3 else "sensitivity",
                        "outcome": oname,
                        "n_windows": len(iv),
                        "time_share": round(m.mean() * 100, 1),
                        "observed": obs,
                        "expected": round(exp, 1),
                        "ratio": round(obs / exp, 2) if exp else "",
                        "p_value": round(p, 3),
                    }
                )
    prim = [r for r in rows if r["family"] == "primary"]
    for r, qq in zip(prim, bh([r["p_value"] for r in prim])):
        r["q_fdr"] = round(qq, 2)
    for r in rows:
        r.setdefault("q_fdr", "")
        p = r["p_value"]
        r["verdict"] = (
            "Real finding"
            if r["q_fdr"] != "" and r["q_fdr"] < 0.1
            else "Nominal only (fails correction)"
            if p < 0.05
            else "No excess"
        )
    with (DATA / "sky_cluster_tests.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    # ---------- period-by-period comparison
    qall = outcomes["M6+ earthquakes, all"][0]
    qmain = outcomes["M6+ mainshocks"][0]
    q7 = outcomes["M7+ mainshocks"][0]
    ver = outcomes["Eruption onsets"][0]
    periods = [(f"{c.span_start:%b %Y}", c.span_start, c.span_end, c) for c in cl]
    periods.append(
        (
            "Aug 2024 (brief's candidate)",
            dt.date(2024, 8, 14),
            dt.date(2024, 8, 28),
            None,
        )
    )
    prow = []
    for label, a, b, c in periods:
        a3, b3 = a - dt.timedelta(days=3), b + dt.timedelta(days=3)
        L = (b3 - a3).days + 1
        ia, ib = day(a3), day(b3)
        future = b3 > Q_END
        sel = [x for x in q if a3 <= x[0].date() <= min(b3, Q_END)]
        maxq = max(sel, key=lambda x: x[3]) if sel else None
        for oname, s, n_end, last in (
            ("M6+ earthquakes, all", qall, nq, 2025),
            ("M6+ mainshocks", qmain, nq, 2025),
            ("M7+ mainshocks", q7, nq, 2025),
            ("Eruption onsets", ver, day(V_END) + 1, 2025),
        ):
            observed = (
                ""
                if (future and oname != "Eruption onsets")
                or (oname == "Eruption onsets" and b3 > V_END)
                else count(s, ia, ib)
            )
            mean, lo95, hi95, pct = baseline(
                s, min(n_end, day(BASE_END) + 1), L, count(s, ia, ib)
            )
            prow.append(
                {
                    "period": label,
                    "window": f"{a3:%Y-%m-%d} to {b3:%Y-%m-%d}",
                    "days": L,
                    "astronomy": (
                        f"Mars–Jupiter {c.conj:%d %b}; supermoon {c.supermoon:%d %b} ({c.moon_km:,.0f} km); "
                        f"{c.episode.side} grouping {c.episode.start:%d %b}–{c.episode.end:%d %b} ({c.episode.planets})"
                    )
                    if c
                    else "Mars–Jupiter 14 Aug; full Moon 19 Aug 361,969 km (no qualifying grouping)",
                    "outcome": oname,
                    "observed": observed,
                    "baseline_mean": round(mean, 1),
                    "baseline_95": f"{lo95:.0f}–{hi95:.0f}",
                    "same_season_mean": round(season(s, a3, L, last), 1),
                    "percentile": "" if observed == "" else round(pct),
                    "largest": f"M{maxq[3]:.1f} {maxq[4]} ({maxq[0]:%d %b})"
                    if (maxq and oname.startswith("M6+ earthquakes"))
                    else "",
                }
            )
    with (DATA / "sky_cluster_periods.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        wr = csv.DictWriter(fh, fieldnames=list(prow[0].keys()))
        wr.writeheader()
        wr.writerows(prow)

    # ---------- November 2026 so far
    nov = [x for x in q if x[0].date() >= dt.date(2026, 11, 1)]
    with (DATA / "sky_nov2026_observed.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        wr = csv.writer(fh)
        wr.writerow(["time_utc", "magnitude", "place", "mainshock"])
        for x in nov:
            wr.writerow(
                [
                    f"{x[0]:%Y-%m-%d %H:%M}",
                    x[3],
                    x[4],
                    "yes" if main_flag[q.index(x)] else "aftershock",
                ]
            )
    print(
        f"quakes {len(q)} mainshocks {sum(main_flag)} eruptions {len(ver)} clusters {len(cl)} tests {len(rows)}"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
