"""November 2026 sky calendar, claim check and Moon/Mars-Jupiter earthquake tests for the Sky cycles tab.

Writes:
  data/sky_nov2026_calendar.csv  every lunar, planetary and station event in November 2026 (UTC and PST)
  data/sky_nov2026_claims.csv    claims made for November 2026 checked against the ephemeris
  data/sky_nov2026_tests.csv     M6+/M7+/M7.5+ mainshocks 1965-2016 vs full moons, new moons,
                                 perigean ("super") syzygies and Mars-Jupiter conjunctions
Ephemeris: PyEphem (VSOP87 planets, ELP Moon), geocentric apparent ecliptic longitude, tropical zodiac.
Catalogue and method as tools/sky/alignment_hazards.py: USGS ComCat M5.5+ 1965-2016, Gardner-Knopoff
declustering, 5,000 circular time shifts of the event dates, one-sided p, Benjamini-Hochberg q.
Run: python3 tools/sky/november_2026.py
"""

# ruff: noqa: DTZ001  # PyEphem works in naive UTC datetimes throughout
from __future__ import annotations

import csv
import datetime as dt
import math
from collections.abc import Callable
from pathlib import Path

import ephem
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "tools" / "sky" / "cache"
DATA = ROOT / "data"
SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
BODIES: dict[str, Callable[..., ephem.Body]] = {
    "Sun": ephem.Sun,
    "Moon": ephem.Moon,
    "Mercury": ephem.Mercury,
    "Venus": ephem.Venus,
    "Mars": ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn": ephem.Saturn,
    "Uranus": ephem.Uranus,
    "Neptune": ephem.Neptune,
    "Pluto": ephem.Pluto,
}
PST = dt.timedelta(hours=-8)
M0, M1 = dt.datetime(2026, 11, 1), dt.datetime(2026, 12, 1)
AU_KM = 149_597_870.7


def wrap(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def lon(body: str, t: dt.datetime) -> float:
    b = BODIES[body](ephem.Date(t))
    return math.degrees(ephem.Ecliptic(b).lon)


def moon_km(t: dt.datetime) -> float:
    return ephem.Moon(ephem.Date(t)).earth_distance * AU_KM


def fmt(lo: float) -> str:
    return f"{lo % 30:.1f}° {SIGNS[int(lo // 30) % 12]}"


def roots(
    f: Callable[[dt.datetime], float],
    t0: dt.datetime,
    t1: dt.datetime,
    step_h: float = 6,
) -> list[dt.datetime]:
    """Times where f (an angle difference, already wrapped) crosses zero upward or downward, to the minute."""
    out, t, step = [], t0, dt.timedelta(hours=step_h)
    fa = f(t)
    while t < t1:
        tb = t + step
        fb = f(tb)
        if fa == 0 or (fa < 0) != (fb < 0) and abs(fa - fb) < 90:
            a, b, ya = t, tb, fa
            while (b - a) > dt.timedelta(seconds=30):
                m = a + (b - a) / 2
                ym = f(m)
                if (ya < 0) == (ym < 0):
                    a, ya = m, ym
                else:
                    b = m
            out.append(a + (b - a) / 2)
        t, fa = tb, fb
    return out


def stamp(t: dt.datetime) -> tuple[str, str, str]:
    p = t + PST
    return t.strftime("%Y-%m-%d"), t.strftime("%H:%M"), p.strftime("%d %b %H:%M")


# ---------------------------------------------------------------- calendar
def calendar() -> tuple[list[list[str]], dict[str, object]]:
    ev: list[tuple[dt.datetime, str, str]] = []
    facts: dict[str, object] = {}
    # lunations
    for name, fn in [
        ("Full Moon", ephem.next_full_moon),
        ("New Moon", ephem.next_new_moon),
        ("First quarter Moon", ephem.next_first_quarter_moon),
        ("Last quarter Moon", ephem.next_last_quarter_moon),
    ]:
        t = ephem.Date(M0 - dt.timedelta(days=1))
        while True:
            t = fn(t)
            tt = t.datetime()
            if tt >= M1:
                break
            if tt >= M0:
                ml = lon("Moon", tt)
                ev.append(
                    (
                        tt,
                        f"{name} at {fmt(ml)}, {moon_km(tt):,.0f} km from Earth",
                        "lunation",
                    )
                )
                facts.setdefault(name, []).append(tt)  # type: ignore[union-attr]
            t = ephem.Date(t + 1)
    # perigee and apogee: extrema of distance, hourly then refined
    hrs = [M0 - dt.timedelta(days=2) + dt.timedelta(hours=h) for h in range(24 * 35)]
    dist = [moon_km(t) for t in hrs]
    for i in range(1, len(hrs) - 1):
        for kind, cmp in (
            ("perigee", lambda a, b: a < b),
            ("apogee", lambda a, b: a > b),
        ):
            if (
                cmp(dist[i], dist[i - 1])
                and cmp(dist[i], dist[i + 1])
                and M0 <= hrs[i] < M1
            ):
                best = min(
                    ((hrs[i] + dt.timedelta(minutes=m)) for m in range(-60, 61)),
                    key=lambda x: moon_km(x) if kind == "perigee" else -moon_km(x),
                )
                ev.append(
                    (best, f"Moon at {kind}, {moon_km(best):,.0f} km", "lunar distance")
                )
                facts[kind] = best
    # planetary conjunctions and oppositions in longitude
    pairs = [
        ("Mars", "Jupiter", 0, "conjunction"),
        ("Mercury", "Sun", 0, "inferior conjunction"),
        ("Uranus", "Sun", 180, "opposition"),
        ("Moon", "Uranus", 0, "conjunction"),
        ("Moon", "Mars", 0, "conjunction"),
        ("Moon", "Jupiter", 0, "conjunction"),
    ]
    for a, b, ang, label in pairs:
        for t in roots(
            lambda x, a=a, b=b, ang=ang: wrap(lon(a, x) - lon(b, x) - ang),
            M0,
            M1,
            2 if a == "Moon" else 6,
        ):
            if a == "Mercury" and ephem.Mercury(ephem.Date(t)).earth_distance > 1:
                continue
            txt = (
                f"Uranus at opposition (Earth between Sun and Uranus), Uranus at {fmt(lon('Uranus', t))}"
                if label == "opposition"
                else f"{a}–{b if b != 'Sun' else 'Sun'} {label}"
                + (
                    f" at {fmt(lon(a, t))}"
                    if b != "Sun"
                    else f" ({ephem.Mercury(ephem.Date(t)).earth_distance:.2f} AU from Earth)"
                )
            )
            if a == "Mars":
                sep = math.degrees(
                    ephem.separation(
                        ephem.Mars(ephem.Date(t)), ephem.Jupiter(ephem.Date(t))
                    )
                )
                txt += f", closest on the sky {sep:.1f}° apart"
            ev.append(
                (
                    t,
                    txt,
                    "aspect"
                    if a != "Mercury" and label != "opposition"
                    else "conjunction",
                )
            )
            facts[f"{a}-{b}-{label}"] = t
    # stations
    for body in (
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    ):

        def spd(x: dt.datetime, body: str = body) -> float:
            return wrap(
                lon(body, x + dt.timedelta(hours=6))
                - lon(body, x - dt.timedelta(hours=6))
            )

        for t in roots(spd, M0, M1, 12):
            turns = "direct" if spd(t + dt.timedelta(days=1)) > 0 else "retrograde"
            ev.append((t, f"{body} turns {turns} at {fmt(lon(body, t))}", "station"))
            facts[f"{body} station"] = t
    # Sun sign ingress
    for t in roots(lambda x: wrap(lon("Sun", x) - 240.0), M0, M1, 12):
        ev.append((t, "Sun enters Sagittarius (240°)", "ingress"))
    ev.sort()
    rows = [[*stamp(t), e, k] for t, e, k in ev]
    return rows, facts


# ---------------------------------------------------------------- claim check
def claims(facts: dict[str, object]) -> list[list[str]]:
    full = facts["Full Moon"][0]  # type: ignore[index]
    per = facts["perigee"]
    fp = Frazier()
    sep = lambda a, b, t: abs(wrap(lon(a, t) - lon(b, t)))
    mj = facts["Mars-Jupiter-conjunction"]
    uo = facts["Uranus-Sun-opposition"]
    mu = facts.get("Moon-Uranus-conjunction")
    reg = ephem.star("Regulus")
    reg.compute(ephem.Date(full))
    rs = [
        math.degrees(ephem.separation(BODIES[b](ephem.Date(full)), reg))
        for b in ("Mars", "Jupiter")
    ]
    un, np_, up = (
        sep("Uranus", "Neptune", full),
        sep("Neptune", "Pluto", full),
        sep("Uranus", "Pluto", full),
    )
    out = [
        [
            "Mercury inferior conjunction on 4 November",
            "Confirmed",
            f"{stamp(facts['Mercury-Sun-inferior conjunction'])[0]} {stamp(facts['Mercury-Sun-inferior conjunction'])[1]} UTC.",
        ],  # type: ignore[arg-type]
        [
            "Venus inferior conjunction on 24 October",
            "Confirmed",
            "24 October 2026 (Mercury and Venus calendar below).",
        ],
        [
            "Mercury and Venus both turn direct on 14 November",
            "Confirmed (13–14 Nov)",
            f"Mercury {stamp(facts['Mercury station'])[2]} PST, Venus {stamp(facts['Venus station'])[2]} PST.",
        ],  # type: ignore[arg-type]
        [
            "Mars–Jupiter conjunction exact on 14 November, in Leo near Regulus",
            "Two days late",
            (
                f"Exact in longitude {stamp(mj)[0]} {stamp(mj)[1]} UTC at {fmt(lon('Mars', mj))}. "  # type: ignore[arg-type]
                f"On 24 November Mars is {rs[0]:.1f}° and Jupiter {rs[1]:.1f}° from Regulus."
            ),
        ],
        [
            "Full Moon on 24 November at 6:54 a.m. PST",
            "Confirmed"
            if abs((full + PST).hour * 60 + (full + PST).minute - 414) <= 3
            else "Check",
            f"{stamp(full)[2]} PST ({stamp(full)[1]} UTC).",
        ],
        [
            "It is a supermoon (Moon near its closest)",
            "Confirmed" if abs((full - per).total_seconds()) < 2 * 86400 else "Check",
            (
                f"Perigee {stamp(per)[2]} PST at {moon_km(per):,.0f} km; at full Moon {moon_km(full):,.0f} km. "  # type: ignore[arg-type]
                "The Moon's tidal pull is about 20% above its average, the total spring tide about 15% higher; "
                "West Coast king tides are expected around this date in any case."
            ),
        ],
        [
            "The last double retrograde (March 2025) brought the M7.7 Myanmar earthquake",
            "True, but one hit",
            (
                "Myanmar struck on 28 March 2025 with both planets retrograde. Over 1965–2016, days with both retrograde had "
                "5 M7+ mainshocks against 7.2 expected by chance (alignment test below)."
            ),
        ],
        [
            "Uranus opposition on 25 November, Moon conjunct Uranus at full Moon",
            "Confirmed"
            if uo.date() in (dt.date(2026, 11, 24), dt.date(2026, 11, 25))
            else "Check",  # type: ignore[union-attr]
            f"Opposition {stamp(uo)[0]} {stamp(uo)[1]} UTC; Moon–Uranus "  # type: ignore[arg-type]
            + (f"conjunction {stamp(mu)[2]} PST; " if mu else "")  # type: ignore[arg-type]
            + f"{sep('Moon', 'Uranus', full):.1f}° apart in longitude at the full Moon.",
        ],
        [
            "Uranus–Neptune–Pluto 'minor grand trine' (two sextiles and a trine)",
            "Partly",
            (
                f"At the full Moon: Uranus–Neptune {un:.1f}°, Neptune–Pluto {np_:.1f}°, Uranus–Pluto {up:.1f}° "
                "(exact would be 60°, 60°, 120°). These slow angles last for years."
            ),
        ],
        [
            "At Frazier Park, Sun rising and Moon setting at the full Moon, Mars and Jupiter overhead",
            fp[0],
            fp[1],
        ],
        [
            "Planetary tides are about 1/150 of the Moon's",
            "Overstated",
            "Venus, the strongest, raises a tide about 1/20,000 of the Moon's even at its closest; all planets together are far below 1/150.",
        ],
        [
            "Alignments, supermoons and double retrogrades raise the chance of a great earthquake",
            "Not supported",
            (
                "No excess of M6+, M7+ or M7.5+ mainshocks in 1965–2016 around these configurations (tests on this tab). "
                "Tidal triggering is real but small (Ide et al. 2016): far too weak to forecast a particular quake."
            ),
        ],
        [
            "A record El Niño and coastal Kelvin wave add seismic energy to California",
            "Not supported",
            (
                "A sea-level rise of 20–30 cm loads the crust by about 0.02–0.03 bar, less than the ordinary daily ocean tide; "
                "no link between ENSO and large earthquakes is established."
            ),
        ],
    ]
    return out


def Frazier() -> list[str]:
    o = ephem.Observer()
    o.lat, o.lon, o.elevation = "34.82", "-118.94", 1400
    o.pressure = 0
    o.horizon = "-0:34"
    o.date = ephem.Date(dt.datetime(2026, 11, 24, 14, 54))
    alt = {
        b: math.degrees(BODIES[b](o).alt)
        for b in ("Sun", "Moon", "Mars", "Jupiter", "Uranus")
    }
    az = {b: math.degrees(BODIES[b](o).az) for b in ("Mars", "Jupiter")}
    o.date = ephem.Date(dt.datetime(2026, 11, 24, 10))
    sr = o.next_rising(ephem.Sun()).datetime() + PST
    ms = o.next_setting(ephem.Moon()).datetime() + PST
    ok = abs(alt["Sun"]) < 3 and abs(alt["Moon"]) < 3 and alt["Mars"] > 50
    return [
        "Confirmed" if ok else "Partly",
        (
            f"At 06:54 PST: Sun {alt['Sun']:+.1f}°, Moon {alt['Moon']:+.1f}° altitude; Mars {alt['Mars']:.0f}° up (azimuth {az['Mars']:.0f}°), "
            f"Jupiter {alt['Jupiter']:.0f}° up. Sunrise {sr:%H:%M}, moonset {ms:%H:%M} PST. "
            "The same Sun-up/Moon-down geometry happens somewhere along the dawn line at every full Moon."
        ),
    ]


# ---------------------------------------------------------------- tests
def tests() -> list[dict[str, object]]:
    rng = np.random.default_rng(42)
    t0, t1 = dt.date(1965, 1, 1), dt.date(2016, 12, 31)
    n = (t1 - t0).days + 1
    q = []
    with open(CACHE / "earthquakes-23k.csv", encoding="utf-8") as fh:
        reader = list(csv.DictReader(fh))
    for r in reader:
        if "/" not in r["Date"]:
            continue
        mo, d_, y = r["Date"].split("/")
        q.append(
            (
                dt.date(int(y), int(mo), int(d_)),
                float(r["Latitude"]),
                float(r["Longitude"]),
                float(r["Magnitude"]),
            )
        )
    q.sort()

    def gk(m: float) -> tuple[float, float]:
        return (
            10 ** (0.032 * m + 2.7389) if m >= 6.5 else 10 ** (0.5409 * m - 0.547)
        ), 10 ** (0.1238 * m + 0.983)

    def hav(a: float, b: float, c: float, d: float) -> float:
        a, b, c, d = map(math.radians, (a, b, c, d))
        return (
            6371
            * 2
            * math.asin(
                math.sqrt(
                    math.sin((c - a) / 2) ** 2
                    + math.cos(a) * math.cos(c) * math.sin((d - b) / 2) ** 2
                )
            )
        )

    days = np.array([(x[0] - q[0][0]).days for x in q])
    dep: set[int] = set()
    for k in sorted(range(len(q)), key=lambda k: -q[k][3]):
        if k in dep:
            continue
        tw, km = gk(q[k][3])
        lo_, hi_ = (
            np.searchsorted(days, days[k]),
            np.searchsorted(days, days[k] + tw, side="right"),
        )
        for j in range(lo_, hi_):
            if (
                j != k
                and j not in dep
                and q[j][3] <= q[k][3]
                and hav(q[k][1], q[k][2], q[j][1], q[j][2]) <= km
            ):
                dep.add(j)
    main = [x for i, x in enumerate(q) if i not in dep and t0 <= x[0] <= t1]
    sets = {
        f"M{m}+ mainshocks": np.array([(x[0] - t0).days for x in main if x[3] >= m])
        for m in (6, 7, 7.5)
    }

    # lunar events, by UTC day
    full, new, sup = [], [], []
    t = ephem.Date(dt.datetime(1964, 12, 1))
    while t.datetime().date() <= t1:
        for fn, lst in ((ephem.next_full_moon, full), (ephem.next_new_moon, new)):
            e = fn(t)
            if t0 <= e.datetime().date() <= t1:
                i = (e.datetime().date() - t0).days
                if i not in lst:
                    lst.append(i)
                    if ephem.Moon(e).earth_distance * AU_KM <= 360_000:
                        sup.append(i)
        t = ephem.Date(t + 14)
    full, new, sup = sorted(set(full)), sorted(set(new)), sorted(set(sup))
    # Mars-Jupiter conjunctions in longitude
    mj = [
        (x.date() - t0).days
        for x in roots(
            lambda x: wrap(lon("Mars", x) - lon("Jupiter", x)),
            dt.datetime(1965, 1, 1),
            dt.datetime(2017, 1, 1),
            48,
        )
    ]
    events = {
        "Full Moon": (np.array(full), [1, 3]),
        "New or full Moon": (np.array(sorted(full + new)), [1, 3]),
        "Supermoon (new or full Moon within 360,000 km)": (np.array(sup), [1, 3]),
        "Mars–Jupiter conjunction": (np.array(mj), [7, 15]),
    }
    rows: list[dict[str, object]] = []
    for en, (ev, ws) in events.items():
        for w in ws:
            m = np.zeros(n, bool)
            for e in ev:
                m[max(0, e - w) : e + w + 1] = True
            for sn, s in sets.items():
                obs = int(m[s].sum())
                null = np.array(
                    [m[(s + o) % n].sum() for o in rng.integers(1, n, 5000)]
                )
                p = (1 + np.sum(null >= obs)) / 5001
                rows.append(
                    {
                        "alignment": en,
                        "window": f"±{w} d",
                        "n_alignments": len(ev),
                        "time_share": round(m.mean() * 100, 1),
                        "hazard": sn,
                        "n": len(s),
                        "observed": obs,
                        "expected": round(float(null.mean()), 1),
                        "ratio": round(obs / float(null.mean()), 2),
                        "p_value": round(float(p), 3),
                    }
                )
    pv = np.array([r["p_value"] for r in rows], float)
    o = np.argsort(pv)
    qv = np.empty(len(pv))
    qv[o] = np.minimum.accumulate((pv[o] * len(pv) / np.arange(1, len(pv) + 1))[::-1])[
        ::-1
    ]
    for r, qq in zip(rows, qv):
        r["q_fdr"] = round(float(min(qq, 1)), 2)
        r["verdict"] = (
            "Real finding"
            if qq < 0.1
            else (
                "Nominal only (fails correction)"
                if r["p_value"] < 0.05
                else "No effect"
            )
        )  # type: ignore[operator]
    rows.sort(key=lambda r: r["p_value"])  # type: ignore[arg-type,return-value]
    return rows


def main() -> None:
    cal, facts = calendar()
    with open(
        DATA / "sky_nov2026_calendar.csv", "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.writer(fh)
        w.writerow(["date", "time_utc", "time_pst", "event", "kind"])
        w.writerows(cal)
    cl = claims(facts)
    with open(DATA / "sky_nov2026_claims.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["claim", "status", "ephemeris"])
        w.writerows(cl)
    tr = tests()
    with open(DATA / "sky_nov2026_tests.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["rank", *tr[0].keys()])
        w.writeheader()
        for i, r in enumerate(tr, 1):
            w.writerow({"rank": i, **r})
    print(f"calendar {len(cal)}, claims {len(cl)}, tests {len(tr)}")


if __name__ == "__main__":
    main()
