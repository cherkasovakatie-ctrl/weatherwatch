"""Geocentric tropical ecliptic positions (of date) via PyEphem / VSOP87."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import ephem

SIGNS: tuple[str, ...] = (
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
)

_BODIES: dict[str, Callable[[], ephem.Body]] = {
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

PLANETS: tuple[str, ...] = tuple(_BODIES)
OUTER: tuple[str, ...] = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")

_EPHEM_EPOCH = datetime(1899, 12, 31, 12, tzinfo=UTC)  # ephem day 0


def to_ephem(t: datetime) -> float:
    return (t - _EPHEM_EPOCH).total_seconds() / 86400.0


def from_ephem(d: float) -> datetime:
    return _EPHEM_EPOCH + timedelta(days=d)


def wrap180(x: float) -> float:
    """Wrap an angle to [-180, 180)."""
    return (x + 180.0) % 360.0 - 180.0


def sign_of(lon: float) -> str:
    return SIGNS[int(lon % 360.0 // 30.0)]


def fmt_lon(lon: float) -> str:
    """Format a longitude as e.g. '0°29′ Aquarius'."""
    lon %= 360.0
    within = lon % 30.0
    deg = int(within)
    minutes = int(round((within - deg) * 60))
    if minutes == 60:
        deg, minutes = deg + 1, 0
    if deg == 30:
        return fmt_lon(lon + 1e-6)
    return f"{deg}°{minutes:02d}′ {sign_of(lon)}"


@lru_cache(maxsize=200_000)
def _lon_cached(body: str, d: float) -> float:
    if body == "Node":
        return mean_node(d)
    b = _BODIES[body]()
    b.compute(d)
    # b.ra/b.dec are apparent geocentric coordinates of date (nutation + aberration).
    return math.degrees(float(ephem.Ecliptic(ephem.Equatorial(b.ra, b.dec, epoch=d), epoch=d).lon)) % 360.0


def lon(body: str, t: datetime | float) -> float:
    """Apparent geocentric ecliptic longitude, tropical, equinox of date (degrees)."""
    d = to_ephem(t) if isinstance(t, datetime) else t
    return _lon_cached(body, round(d, 7))


def ecl_lat(body: str, d: float) -> float:
    b = _BODIES[body]()
    b.compute(d)
    return math.degrees(float(ephem.Ecliptic(ephem.Equatorial(b.ra, b.dec, epoch=d), epoch=d).lat))


def mean_node(d: float) -> float:
    """Mean lunar north node (Meeus 47.7), degrees."""
    jd = d + 2415020.0
    t = (jd - 2451545.0) / 36525.0
    om = 125.0445479 - 1934.1362891 * t + 0.0020754 * t**2 + t**3 / 467441.0
    return om % 360.0


def speed(body: str, d: float, h: float = 0.5) -> float:
    """Daily motion in degrees/day (negative = retrograde)."""
    return wrap180(lon(body, d + h) - lon(body, d - h)) / (2 * h)


def bisect_root(f: Callable[[float], float], a: float, b: float, tol_days: float = 1e-4) -> float:
    fa = f(a)
    for _ in range(80):
        m = (a + b) / 2
        fm = f(m)
        if (fa <= 0) == (fm <= 0):
            a, fa = m, fm
        else:
            b = m
        if b - a < tol_days:
            break
    return (a + b) / 2


def find_crossings(
    f: Callable[[float], float], start: float, end: float, step: float, guard: float = 30.0
) -> list[float]:
    """Zero crossings of a wrapped angular function f (values in [-180, 180)).

    A sign change counts only when both samples are within `guard` degrees of zero,
    which rejects the ±180° wrap discontinuity.
    """
    roots: list[float] = []
    d0, f0 = start, f(start)
    d = start + step
    while d <= end + 1e-9:
        f1 = f(d)
        if (f0 < 0) != (f1 < 0) and abs(f0) < guard and abs(f1) < guard:
            roots.append(bisect_root(f, d0, d))
        d0, f0 = d, f1
        d += step
    return roots


@dataclass(frozen=True)
class Angles:
    asc: float
    mc: float


def obliquity(d: float) -> float:
    jd = d + 2415020.0
    t = (jd - 2451545.0) / 36525.0
    return 23.4392911 - 0.0130042 * t


def angles(t: datetime, lat_deg: float, lon_deg_east: float) -> Angles:
    """Ascendant and Midheaven (tropical, of date) for a UTC moment and place."""
    obs = ephem.Observer()
    obs.lat = str(lat_deg)
    obs.lon = str(lon_deg_east)
    obs.date = to_ephem(t)
    obs.pressure = 0
    ramc = float(obs.sidereal_time())  # apparent local sidereal time, radians
    eps = math.radians(obliquity(to_ephem(t)))
    phi = math.radians(lat_deg)
    mc = math.degrees(math.atan2(math.sin(ramc), math.cos(ramc) * math.cos(eps))) % 360.0
    asc = (
        math.degrees(math.atan2(math.cos(ramc), -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps))))
        % 360.0
    )
    return Angles(asc=asc, mc=mc)
