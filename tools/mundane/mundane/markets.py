"""S&P 500 monthly history (Shiller via datasets/s-and-p-500) and honest cycle tests."""

from __future__ import annotations

import csv
import io
import math
import random
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime

from .cycles import cyclic_index
from .ephemeris import lon, to_ephem, wrap180

SP_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"


@dataclass(frozen=True)
class Month:
    month: str  # YYYY-MM
    nominal: float
    real: float | None  # None where the source has no CPI yet


def fetch_sp500(url: str = SP_URL, timeout: float = 60.0) -> list[Month]:
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (fixed https URL)
        text = r.read().decode("utf-8")
    return parse_sp500(text)


def parse_sp500(text: str) -> list[Month]:
    out: list[Month] = []
    for row in csv.DictReader(io.StringIO(text)):
        nominal = float(row["SP500"])
        real = float(row["Real Price"]) if float(row["Consumer Price Index"]) > 0 else None
        out.append(Month(row["Date"][:7], nominal, real))
    if not out:
        raise ValueError("S&P file parsed to zero rows")
    return out


@dataclass(frozen=True)
class Bear:
    peak: str
    trough: str
    recovered: str
    depth_pct: float


def bear_markets(months: list[Month], threshold: float = 0.20) -> list[Bear]:
    """Peak-to-trough declines of at least `threshold` in monthly-average nominal prices."""
    out: list[Bear] = []
    peak_i = 0
    i = 1
    n = len(months)
    while i < n:
        if months[i].nominal >= months[peak_i].nominal:
            peak_i = i
            i += 1
            continue
        # in a drawdown from peak_i: find the trough before recovery
        j = i
        trough_i = i
        while j < n and months[j].nominal < months[peak_i].nominal:
            if months[j].nominal < months[trough_i].nominal:
                trough_i = j
            j += 1
        depth = 1 - months[trough_i].nominal / months[peak_i].nominal
        if depth >= threshold:
            rec = months[j].month if j < n else ""
            out.append(Bear(months[peak_i].month, months[trough_i].month, rec, round(depth * 100, 1)))
        peak_i = j if j < n else peak_i
        i = j + 1
    return out


def _mid(month: str) -> float:
    y, m = int(month[:4]), int(month[5:7])
    return to_ephem(datetime(y, m, 15, tzinfo=UTC))


def hard_window(a: str, b: str, d: float, orb: float = 8.0) -> bool:
    phase = (lon(a, d) - lon(b, d)) % 360.0
    return any(abs(wrap180(phase - x)) <= orb for x in (0, 90, 180, 270))


TEST_PAIRS: tuple[tuple[str, str], ...] = (
    ("Jupiter", "Saturn"),
    ("Jupiter", "Uranus"),
    ("Saturn", "Uranus"),
    ("Saturn", "Neptune"),
    ("Saturn", "Pluto"),
    ("Uranus", "Pluto"),
)


@dataclass(frozen=True)
class TestResult:
    predictor: str
    statistic: str
    value: float
    p_value: float
    q_fdr: float
    early: float
    late: float
    replicates: bool
    n_months: int
    share_in_window: float


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _corr(x: list[float], y: list[float]) -> float:
    mx, my = _mean(x), _mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


def _diff(flag: list[bool], y: list[float]) -> float:
    inside = [v for f, v in zip(flag, y, strict=True) if f]
    outside = [v for f, v in zip(flag, y, strict=True) if not f]
    return _mean(inside) - _mean(outside)


def _shift_p(stat_fn, x: list, y: list[float], observed: float, iters: int, rng: random.Random) -> float:
    """Two-sided p from circular shifts of the predictor (keeps both series' persistence)."""
    n = len(x)
    lo, hi = 60, n - 60
    hits = 0
    for _ in range(iters):
        k = rng.randint(lo, hi)
        xs = x[k:] + x[:k]
        if abs(stat_fn(xs, y)) >= abs(observed):
            hits += 1
    return (hits + 1) / (iters + 1)


def bh_fdr(ps: list[float]) -> list[float]:
    n = len(ps)
    order = sorted(range(n), key=lambda i: ps[i])
    q = [0.0] * n
    running = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        running = min(running, ps[i] * n / rank)
        q[i] = running
    return q


def run_tests(months: list[Month], start: str = "1900-01", iters: int = 5000, seed: int = 26) -> list[TestResult]:
    rng = random.Random(seed)
    idx = {m.month: i for i, m in enumerate(months)}
    usable = [m for m in months if m.month >= start and m.real is not None]
    rows: list[tuple[str, float]] = []  # (month, forward 12m log real return %)
    for m in usable:
        j = idx[m.month] + 12
        if j < len(months) and months[j].real is not None and m.real:
            rows.append((m.month, 100 * math.log(months[j].real / m.real)))  # type: ignore[operator]
    y = [r[1] for r in rows]
    ds = [_mid(r[0]) for r in rows]
    half = len(rows) // 2

    raw: list[tuple[str, str, float, float, float, float, float]] = []
    ci = [cyclic_index(d) for d in ds]
    r_ci = _corr(ci, y)
    raw.append(
        (
            "Cyclic index (level)",
            "r",
            r_ci,
            _shift_p(_corr, ci, y, r_ci, iters, rng),
            _corr(ci[:half], y[:half]),
            _corr(ci[half:], y[half:]),
            float("nan"),
        )
    )
    for a, b in TEST_PAIRS:
        flag = [hard_window(a, b, d) for d in ds]
        diff = _diff(flag, y)
        raw.append(
            (
                f"{a}–{b} hard aspect (±8°)",
                "Δ mean, % pts",
                diff,
                _shift_p(_diff, flag, y, diff, iters, rng),
                _diff(flag[:half], y[:half]),
                _diff(flag[half:], y[half:]),
                sum(flag) / len(flag),
            )
        )
    q = bh_fdr([r[3] for r in raw])
    out = []
    for (name, stat, val, p, e, late, share), qq in zip(raw, q, strict=True):
        out.append(
            TestResult(
                name,
                stat,
                round(val, 3),
                round(p, 4),
                round(qq, 4),
                round(e, 3),
                round(late, 3),
                (e > 0) == (late > 0) and (e > 0) == (val > 0),
                len(rows),
                round(share, 3) if not math.isnan(share) else float("nan"),
            )
        )
    return out


@dataclass(frozen=True)
class Episode:
    start: str
    end: str
    months: int
    mean_fwd_return: float
    effect_without: float  # in-window minus out-of-window gap if this episode is dropped


def episodes(months: list[Month], a: str, b: str, start: str = "1900-01", merge_gap: int = 18) -> list[Episode]:
    """Hard-aspect windows grouped into episodes (retrograde passes merged), with leave-one-out."""
    real = [(m.month, m.real) for m in months if m.month >= start and m.real is not None]
    fw = [(real[i][0], 100 * math.log(real[i + 12][1] / real[i][1])) for i in range(len(real) - 12)]  # type: ignore[operator]
    flags = [hard_window(a, b, _mid(k)) for k, _ in fw]
    outside = [v for (_, v), f in zip(fw, flags, strict=True) if not f]
    out_mean = _mean(outside)
    groups: list[list[tuple[int, float]]] = []
    for i, ((_, v), f) in enumerate(zip(fw, flags, strict=True)):
        if not f:
            continue
        if groups and i - groups[-1][-1][0] <= merge_gap:
            groups[-1].append((i, v))
        else:
            groups.append([(i, v)])
    res: list[Episode] = []
    for gi, g in enumerate(groups):
        rest = [v for gj, h in enumerate(groups) if gj != gi for _, v in h]
        res.append(
            Episode(
                fw[g[0][0]][0],
                fw[g[-1][0]][0],
                len(g),
                round(_mean([v for _, v in g]), 1),
                round(_mean(rest) - out_mean, 2),
            )
        )
    return res
