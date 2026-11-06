# ruff: noqa: DTZ001  # PyEphem works in naive UTC datetimes throughout
"""Astronomical side of the November 2026 cluster study: fixed definitions, daily ephemeris 1973-2026.

Definitions (fixed before any geophysical data were examined):
  Planet grouping  : on a given day (00 UTC), at least 4 of the 5 naked-eye planets (Mercury, Venus, Mars,
                     Jupiter, Saturn) on the same side of the Sun (morning = west of the Sun) at elongation >= 10 deg,
                     spanning <= 90 deg of geocentric ecliptic longitude. A grouping episode is a run of such days.
  Supermoon        : a full Moon with geocentric distance <= 362,000 km at the instant of full Moon.
  Mars-Jupiter conj: instant when the geocentric ecliptic longitudes of Mars and Jupiter are equal.
  Cluster          : a Mars-Jupiter conjunction, a supermoon and a day of a grouping episode whose dates all fall
                     within one 30-day span.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

import ephem

T0 = dt.date(1973, 1, 1)
T1 = dt.date(2026, 12, 31)
NAKED = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")
SUPERMOON_KM = 362_000.0
MIN_ELONG = 10.0
MAX_SPAN = 90.0
MIN_PLANETS = 4
CLUSTER_DAYS = 30
AU_KM = 149_597_870.7


def wrap(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def ecl_lon(body: ephem.Body) -> float:
    return math.degrees(ephem.Ecliptic(body).lon)


@dataclass(frozen=True)
class Episode:
    start: dt.date
    end: dt.date
    side: str
    planets: str

    def contains(self, d: dt.date) -> bool:
        return self.start <= d <= self.end


def grouping_on(day: dt.date) -> tuple[str, list[str]] | None:
    """Return (side, planets) if a qualifying grouping exists on this day at 00 UTC."""
    d = ephem.Date(dt.datetime(day.year, day.month, day.day))
    sun = ecl_lon(ephem.Sun(d))
    for side, sign in (("morning", -1), ("evening", 1)):
        members = []
        for name in NAKED:
            el = wrap(ecl_lon(getattr(ephem, name)(d)) - sun)
            if sign * el >= MIN_ELONG:
                members.append((name, el))
        if len(members) < MIN_PLANETS:
            continue
        els = sorted(e for _, e in members)
        # best subset of >= MIN_PLANETS consecutive (in elongation) members within MAX_SPAN
        best: list[str] = []
        for i in range(len(els)):
            for j in range(len(els) - 1, i + MIN_PLANETS - 2, -1):
                if els[j] - els[i] <= MAX_SPAN and j - i + 1 > len(best):
                    best = [n for n, e in members if els[i] <= e <= els[j]]
        if len(best) >= MIN_PLANETS:
            return side, best
    return None


def grouping_episodes(t0: dt.date = T0, t1: dt.date = T1) -> list[Episode]:
    eps: list[Episode] = []
    cur: tuple[dt.date, dt.date, str, set[str]] | None = None
    day = t0
    while day <= t1:
        g = grouping_on(day)
        if g and cur and cur[2] == g[0] and (day - cur[1]).days == 1:
            cur = (cur[0], day, cur[2], cur[3] | set(g[1]))
        else:
            if cur:
                eps.append(
                    Episode(
                        cur[0],
                        cur[1],
                        cur[2],
                        ", ".join(n for n in NAKED if n in cur[3]),
                    )
                )
            cur = (day, day, g[0], set(g[1])) if g else None
        day += dt.timedelta(days=1)
    if cur:
        eps.append(
            Episode(cur[0], cur[1], cur[2], ", ".join(n for n in NAKED if n in cur[3]))
        )
    return eps


def full_moons(t0: dt.date = T0, t1: dt.date = T1) -> list[tuple[dt.datetime, float]]:
    out = []
    t = ephem.Date(dt.datetime(t0.year, t0.month, t0.day) - dt.timedelta(days=2))
    while True:
        t = ephem.next_full_moon(t)
        tt = t.datetime()
        if tt.date() > t1:
            return out
        if tt.date() >= t0:
            out.append((tt, ephem.Moon(t).earth_distance * AU_KM))
        t = ephem.Date(t + 1)


def mars_jupiter(t0: dt.date = T0, t1: dt.date = T1) -> list[dt.datetime]:
    def f(x: dt.datetime) -> float:
        d = ephem.Date(x)
        return wrap(ecl_lon(ephem.Mars(d)) - ecl_lon(ephem.Jupiter(d)))

    out, t = [], dt.datetime(t0.year, t0.month, t0.day)
    end = dt.datetime(t1.year, t1.month, t1.day)
    step = dt.timedelta(days=2)
    fa = f(t)
    while t < end:
        fb = f(t + step)
        if (fa < 0) != (fb < 0) and abs(fa - fb) < 90:
            a, b, ya = t, t + step, fa
            while b - a > dt.timedelta(minutes=1):
                m = a + (b - a) / 2
                ym = f(m)
                if (ya < 0) == (ym < 0):
                    a, ya = m, ym
                else:
                    b = m
            out.append(a)
        t, fa = t + step, fb
    return out


@dataclass(frozen=True)
class Cluster:
    conj: dt.datetime
    supermoon: dt.datetime
    moon_km: float
    episode: Episode
    span_start: dt.date
    span_end: dt.date


def clusters(
    eps: list[Episode], fms: list[tuple[dt.datetime, float]], mj: list[dt.datetime]
) -> list[Cluster]:
    sms = [(t, km) for t, km in fms if km <= SUPERMOON_KM]
    out = []
    for c in mj:
        best: Cluster | None = None
        for s, km in sms:
            if abs((s.date() - c.date()).days) > CLUSTER_DAYS:
                continue
            lo, hi = min(s.date(), c.date()), max(s.date(), c.date())
            for e in eps:
                # nearest grouping day to the [lo, hi] interval
                g = min(max(lo, e.start), e.end) if e.end >= lo else e.end
                if e.start > hi:
                    g = e.start
                a, b = min(lo, g), max(hi, g)
                if (b - a).days <= CLUSTER_DAYS and (
                    best is None or (b - a) < (best.span_end - best.span_start)
                ):
                    best = Cluster(c, s, km, e, a, b)
        if best:
            out.append(best)
    return out
