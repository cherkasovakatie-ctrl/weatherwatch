"""National (country-level) charts and outer-planet transits to them.

Founding dates are historical facts; founding *times* are conventions adopted by
mundane astrologers and several are disputed. Every chart carries a reliability
rating, and angles (Ascendant/MC) and the Moon are only used for timing when the
time is rated A or B.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from .ephemeris import PLANETS, angles, find_crossings, from_ephem, lon, speed, to_ephem, wrap180


@dataclass(frozen=True)
class NationalChart:
    id: str
    country: str
    label: str
    event: str
    local: str  # local date-time as documented, for display
    utc: datetime
    place: str
    lat: float
    lon_east: float
    rating: str  # A documented time · B well-attested convention · C disputed time · X no time (noon)
    source: str
    notes: str = ""
    related: list[str] = field(default_factory=list)

    @property
    def timed(self) -> bool:
        return self.rating in ("A", "B")


def _utc(y: int, mo: int, d: int, h: int, mi: int, offset_h: float) -> datetime:
    """Local clock time with a fixed UTC offset (hours east) -> aware UTC datetime."""
    return datetime(y, mo, d, h, mi, tzinfo=UTC) - timedelta(hours=offset_h)


CHARTS: list[NationalChart] = [
    NationalChart(
        "usa-sibly",
        "United States",
        "USA (Sibly)",
        "Declaration of Independence",
        "4 Jul 1776, 17:10 LMT",
        _utc(1776, 7, 4, 17, 10, -(75 + 10 / 60) / 15),
        "Philadelphia",
        39.95,
        -75.1667,
        "C",
        "Ebenezer Sibly (1787); the most used US chart, but the signing time is not documented.",
        "Competing times range from about 02:13 to 17:10 LMT; the date is secure.",
    ),
    NationalChart(
        "uk-1801",
        "United Kingdom",
        "United Kingdom",
        "Act of Union takes effect",
        "1 Jan 1801, 00:00 LMT",
        _utc(1801, 1, 1, 0, 0, -0.1275 / 15),
        "London",
        51.5074,
        -0.1275,
        "A",
        "Union with Ireland Act 1800, effective from the first moment of 1 January 1801.",
    ),
    NationalChart(
        "ukraine-1991",
        "Ukraine",
        "Ukraine",
        "Act of Declaration of Independence",
        "24 Aug 1991, 18:00 EEST",
        _utc(1991, 8, 24, 18, 0, 3.0),
        "Kyiv",
        50.45,
        30.5236,
        "C",
        "Verkhovna Rada vote on 24 Aug 1991; ~18:00 is the commonly used time (Campion).",
        "The vote time is reported variously between late afternoon and 18:00; treat angles as unreliable.",
    ),
    NationalChart(
        "russia-1990",
        "Russia",
        "Russia (1990)",
        "RSFSR Declaration of State Sovereignty",
        "12 Jun 1990 (time not established; noon chart)",
        _utc(1990, 6, 12, 12, 0, 4.0),
        "Moscow",
        55.7558,
        37.6173,
        "X",
        "Date of the sovereignty declaration, now Russia Day.",
        "An alternative chart is 25 Dec 1991, when the RSFSR became the Russian Federation.",
    ),
    NationalChart(
        "russia-1991",
        "Russia",
        "Russia (1991)",
        "RSFSR renamed Russian Federation",
        "25 Dec 1991 (time not established; noon chart)",
        _utc(1991, 12, 25, 12, 0, 2.0),
        "Moscow",
        55.7558,
        37.6173,
        "X",
        "Date of the renaming, coinciding with the end of the USSR.",
    ),
    NationalChart(
        "china-1949",
        "China",
        "People's Republic of China",
        "Proclamation of the PRC",
        "1 Oct 1949, 15:00 CST",
        _utc(1949, 10, 1, 15, 0, 8.0),
        "Beijing",
        39.9042,
        116.4074,
        "B",
        "The founding ceremony in Tiananmen Square began at 15:00 local time.",
    ),
    NationalChart(
        "india-1947",
        "India",
        "India",
        "Independence",
        "15 Aug 1947, 00:00 IST",
        _utc(1947, 8, 15, 0, 0, 5.5),
        "New Delhi",
        28.6139,
        77.209,
        "A",
        "Independence took effect at midnight, 14–15 August 1947.",
    ),
    NationalChart(
        "israel-1948",
        "Israel",
        "Israel",
        "Declaration of the Establishment of the State",
        "14 May 1948, 16:00 local (UTC+2)",
        _utc(1948, 5, 14, 16, 0, 2.0),
        "Tel Aviv",
        32.0853,
        34.7818,
        "B",
        "Ben-Gurion began reading the declaration at 16:00 local time.",
        "Some charts assume summer time (UTC+3), which moves the angles by about 15°.",
    ),
    NationalChart(
        "germany-1990",
        "Germany",
        "Germany (reunified)",
        "German reunification",
        "3 Oct 1990, 00:00 CET",
        _utc(1990, 10, 3, 0, 0, 1.0),
        "Berlin",
        52.52,
        13.405,
        "A",
        "Unification Treaty took effect at midnight; German summer time had ended on 30 Sep 1990.",
    ),
    NationalChart(
        "france-1958",
        "France",
        "France (Fifth Republic)",
        "Constitution of the Fifth Republic",
        "5 Oct 1958, 00:00 CET",
        _utc(1958, 10, 5, 0, 0, 1.0),
        "Paris",
        48.8566,
        2.3522,
        "B",
        "Constitution promulgated 4 Oct and in force on publication, 5 Oct 1958.",
    ),
    NationalChart(
        "japan-1952",
        "Japan",
        "Japan (sovereignty restored)",
        "Treaty of San Francisco in force",
        "28 Apr 1952, 22:30 JST",
        _utc(1952, 4, 28, 22, 30, 9.0),
        "Tokyo",
        35.6762,
        139.6503,
        "B",
        "The peace treaty entered into force at 22:30 Tokyo time, ending the occupation.",
    ),
]

TRANSITING: tuple[str, ...] = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
TRANSIT_ASPECTS: dict[int, str] = {
    0: "conjunction",
    90: "square",
    180: "opposition",
    270: "square",
    120: "trine",
    240: "trine",
}


@dataclass(frozen=True)
class Position:
    point: str
    lon: float
    retro: bool


def positions(c: NationalChart) -> list[Position]:
    d = to_ephem(c.utc)
    out = [Position(p, lon(p, d), speed(p, d) < 0) for p in PLANETS]
    out.append(Position("North Node (mean)", lon("Node", d), True))
    if c.timed:
        a = angles(c.utc, c.lat, c.lon_east)
        out += [Position("Ascendant", a.asc, False), Position("Midheaven", a.mc, False)]
    return out


def natal_points(c: NationalChart) -> list[Position]:
    """Points used as transit targets. Moon and angles only for timed charts."""
    keep = {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    if c.timed:
        keep |= {"Moon", "Ascendant", "Midheaven"}
    return [p for p in positions(c) if p.point in keep]


@dataclass(frozen=True)
class TransitHit:
    when: datetime
    chart_id: str
    transiting: str
    aspect: str
    natal: str
    natal_lon: float
    transit_lon: float
    retro: bool


def transits(c: NationalChart, start: datetime, end: datetime) -> list[TransitHit]:
    d0, d1 = to_ephem(start), to_ephem(end)
    hits: list[TransitHit] = []
    for p in natal_points(c):
        for t in TRANSITING:
            for angle, name in TRANSIT_ASPECTS.items():
                target = (p.lon + angle) % 360.0

                def f(d: float, t: str = t, target: float = target) -> float:
                    return wrap180(lon(t, d) - target)

                for r in find_crossings(f, d0, d1, 2.0, guard=10.0):
                    hits.append(TransitHit(from_ephem(r), c.id, t, name, p.point, p.lon, lon(t, r), speed(t, r) < 0))
    hits.sort(key=lambda h: h.when)
    return hits
