"""Outer-planet cycles, sign ingresses, stations, seasonal ingresses, eclipses, cyclic index."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from datetime import datetime

import ephem

from .ephemeris import (
    OUTER,
    SIGNS,
    ecl_lat,
    find_crossings,
    from_ephem,
    lon,
    sign_of,
    speed,
    to_ephem,
    wrap180,
)

# Phase angle = lon(faster) - lon(slower), measured 0-360.
ASPECTS: dict[int, tuple[str, str, str]] = {
    0: ("conjunction", "", "hard"),
    90: ("square", "waxing", "hard"),
    120: ("trine", "waxing", "soft"),
    180: ("opposition", "", "hard"),
    240: ("trine", "waning", "soft"),
    270: ("square", "waning", "hard"),
}

# Mean synodic periods (years), for reference in the output.
SYNODIC_YEARS: dict[str, float] = {
    "Jupiter–Saturn": 19.86,
    "Jupiter–Uranus": 13.81,
    "Jupiter–Neptune": 12.78,
    "Jupiter–Pluto": 12.46,
    "Saturn–Uranus": 45.36,
    "Saturn–Neptune": 35.87,
    "Saturn–Pluto": 33.42,
    "Uranus–Neptune": 171.4,
    "Uranus–Pluto": 127.3,
    "Neptune–Pluto": 492.3,
}


@dataclass(frozen=True)
class AspectHit:
    when: datetime
    pair: str
    aspect: str
    phase: str
    kind: str
    lon_a: float
    lon_b: float
    retro_a: bool
    retro_b: bool
    pass_no: int = 1
    passes: int = 1


def pairs() -> list[tuple[str, str]]:
    return list(itertools.combinations(OUTER, 2))


def aspect_hits(start: datetime, end: datetime, step: float = 2.0) -> list[AspectHit]:
    d0, d1 = to_ephem(start), to_ephem(end)
    hits: list[AspectHit] = []
    for a, b in pairs():
        name = f"{a}–{b}"
        for angle, (asp, phase, kind) in ASPECTS.items():

            def f(d: float, a: str = a, b: str = b, angle: int = angle) -> float:
                return wrap180(lon(a, d) - lon(b, d) - angle)

            roots = find_crossings(f, d0, d1, step, guard=20.0)
            group: list[AspectHit] = []
            for r in roots:
                h = AspectHit(
                    when=from_ephem(r),
                    pair=name,
                    aspect=asp,
                    phase=phase,
                    kind=kind,
                    lon_a=lon(a, r),
                    lon_b=lon(b, r),
                    retro_a=speed(a, r) < 0,
                    retro_b=speed(b, r) < 0,
                )
                if group and (r - to_ephem(group[-1].when)) > 500:
                    hits.extend(_number(group))
                    group = []
                group.append(h)
            hits.extend(_number(group))
    hits.sort(key=lambda h: h.when)
    return hits


def _number(group: list[AspectHit]) -> list[AspectHit]:
    n = len(group)
    return [AspectHit(**{**h.__dict__, "pass_no": i + 1, "passes": n}) for i, h in enumerate(group)]


@dataclass(frozen=True)
class Ingress:
    when: datetime
    body: str
    sign: str
    direction: str  # "direct" | "retrograde"
    first_entry: bool


def sign_ingresses(bodies: tuple[str, ...], start: datetime, end: datetime, step: float = 1.0) -> list[Ingress]:
    d0, d1 = to_ephem(start), to_ephem(end)
    out: list[Ingress] = []
    for body in bodies:
        roots: list[tuple[float, int]] = []
        for k in range(12):

            def f(d: float, k: int = k, body: str = body) -> float:
                return wrap180(lon(body, d) - 30.0 * k)

            roots += [(r, k) for r in find_crossings(f, d0, d1, step, guard=10.0)]
        for r, k in sorted(roots):
            v = speed(body, r)
            # Moving direct across 30k enters sign k; moving retrograde enters sign k-1.
            sign = SIGNS[k] if v > 0 else SIGNS[(k - 1) % 12]
            out.append(Ingress(from_ephem(r), body, sign, "direct" if v > 0 else "retrograde", False))
    out.sort(key=lambda i: i.when)
    return _flag_reentries(out)


def _flag_reentries(items: list[Ingress]) -> list[Ingress]:
    result: list[Ingress] = []
    last_direct: dict[tuple[str, str], datetime] = {}
    for i in items:
        if i.direction == "direct":
            prev = last_direct.get((i.body, i.sign))
            first = prev is None or (i.when - prev).days > 3 * 365
            last_direct[(i.body, i.sign)] = i.when
            result.append(Ingress(i.when, i.body, i.sign, i.direction, first))
        else:
            result.append(i)
    return result


@dataclass(frozen=True)
class Station:
    when: datetime
    body: str
    turns: str  # "retrograde" | "direct"
    lon: float


def stations(bodies: tuple[str, ...], start: datetime, end: datetime) -> list[Station]:
    d0, d1 = to_ephem(start), to_ephem(end)
    out: list[Station] = []
    for body in bodies:

        def f(d: float, body: str = body) -> float:
            return speed(body, d, h=1.0)

        prev = f(d0)
        d = d0 + 1
        while d <= d1:
            cur = f(d)
            if (prev < 0) != (cur < 0):
                a, b = d - 1, d
                for _ in range(40):
                    m = (a + b) / 2
                    if (f(m) < 0) == (prev < 0):
                        a = m
                    else:
                        b = m
                r = (a + b) / 2
                out.append(Station(from_ephem(r), body, "retrograde" if cur < 0 else "direct", lon(body, r)))
            prev = cur
            d += 1
    out.sort(key=lambda s: s.when)
    return out


@dataclass(frozen=True)
class Seasonal:
    when: datetime
    point: str  # "Aries" etc.


def seasonal_ingresses(start: datetime, end: datetime) -> list[Seasonal]:
    d0, d1 = to_ephem(start), to_ephem(end)
    out: list[Seasonal] = []
    for k, name in ((0, "Aries"), (3, "Cancer"), (6, "Libra"), (9, "Capricorn")):

        def f(d: float, k: int = k) -> float:
            return wrap180(lon("Sun", d) - 30.0 * k)

        out += [Seasonal(from_ephem(r), name) for r in find_crossings(f, d0, d1, 1.0, guard=10.0)]
    out.sort(key=lambda s: s.when)
    return out


@dataclass(frozen=True)
class Eclipse:
    when: datetime
    kind: str  # "solar" | "lunar"
    lon: float
    moon_lat: float


# Ecliptic-latitude limits for the Moon at syzygy (degrees). An eclipse of some kind
# (including partial and penumbral) occurs below these; validated against 2024-2027.
SOLAR_LIMIT = 1.55
LUNAR_LIMIT = 1.60


def eclipses(start: datetime, end: datetime) -> list[Eclipse]:
    out: list[Eclipse] = []
    d = to_ephem(start)
    d1 = to_ephem(end)
    while d < d1:
        nm = float(ephem.next_new_moon(d))
        fm = float(ephem.next_full_moon(d))
        nxt = min(nm, fm)
        if nxt > d1:
            break
        is_new = nxt == nm
        b = abs(ecl_lat("Moon", nxt))
        if is_new and b < SOLAR_LIMIT:
            out.append(Eclipse(from_ephem(nxt), "solar", lon("Sun", nxt), round(b, 3)))
        if not is_new and b < LUNAR_LIMIT:
            out.append(Eclipse(from_ephem(nxt), "lunar", lon("Moon", nxt), round(b, 3)))
        d = nxt + 1
    return out


def cyclic_index(d: float) -> float:
    """Barbault cyclic index: sum of the 10 pairwise separations (0-180°) of Jupiter-Pluto."""
    total = 0.0
    for a, b in pairs():
        total += abs(wrap180(lon(a, d) - lon(b, d)))
    return total


def monthly_dates(start_year: int, end_year: int) -> list[datetime]:
    from datetime import UTC

    return [datetime(y, m, 15, tzinfo=UTC) for y in range(start_year, end_year + 1) for m in range(1, 13)]


__all__ = [
    "ASPECTS",
    "SYNODIC_YEARS",
    "AspectHit",
    "Eclipse",
    "Ingress",
    "Seasonal",
    "Station",
    "aspect_hits",
    "cyclic_index",
    "eclipses",
    "monthly_dates",
    "pairs",
    "seasonal_ingresses",
    "sign_ingresses",
    "sign_of",
    "stations",
]
