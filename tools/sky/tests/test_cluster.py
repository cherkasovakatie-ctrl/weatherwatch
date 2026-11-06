"""Checks of the cluster definitions and the window baseline helpers."""

import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cluster_astro as astro
import cluster_study as study


def test_november_2026_morning_grouping_has_the_four_planets() -> None:
    eps = astro.grouping_episodes(dt.date(2026, 11, 1), dt.date(2026, 12, 31))
    nov = [e for e in eps if e.contains(dt.date(2026, 11, 16))]
    assert len(nov) == 1
    assert nov[0].side == "morning"
    assert nov[0].planets == "Mercury, Venus, Mars, Jupiter"


def test_mars_jupiter_conjunction_on_16_november_2026() -> None:
    mj = astro.mars_jupiter(dt.date(2026, 10, 1), dt.date(2026, 12, 31))
    assert [t.date() for t in mj] == [dt.date(2026, 11, 16)]


def test_october_2015_is_a_cluster() -> None:
    t0, t1 = dt.date(2015, 8, 1), dt.date(2015, 12, 31)
    cl = astro.clusters(astro.grouping_episodes(t0, t1), astro.full_moons(t0, t1), astro.mars_jupiter(t0, t1))
    assert [c.conj.date() for c in cl] == [dt.date(2015, 10, 17)]


def test_count_and_baseline() -> None:
    s = np.array([0, 5, 10, 15])
    assert study.count(s, 4, 11) == 2
    mean, lo, hi, pct = study.baseline(s, 20, 5, 1)
    assert 0.9 < mean < 1.1
    assert lo in (0, 1)
    assert hi >= lo
    assert 0 <= pct <= 100
