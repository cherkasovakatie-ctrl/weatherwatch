"""Build sky-2026-11.html: research brief on November 2026 sky events and Earth activity.

Reads data/sky_cluster_tests.csv, data/sky_cluster_periods.csv, data/sky_nov2026_observed.csv
(written by tools/sky/cluster_study.py) and reuses the page style of tools/papers/build.py.
Run: python3 tools/sky/build_brief.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "papers"))
from build import NAV, STYLE, esc, ref_html, table

DATA = ROOT / "data"
DATE = "6 November 2026"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


REFS = [
    {
        "key": "jpl",
        "text": "JPL Small-Body Database, 161P/Hartley-IRAS, orbit solution K262/1 (14 Oct 2026).",
        "url": "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=161P",
    },
    {
        "key": "imo",
        "text": "International Meteor Organization, 2026 Meteor Shower Calendar (Leonids).",
        "url": "https://www.imo.net/files/meteor-shower/cal2026.pdf",
    },
    {
        "key": "usgs",
        "text": "USGS ComCat earthquake catalogue, M5.5+ 1973-01-01 to 2026-11-06, FDSN event web service (read 6 Nov 2026).",
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/",
    },
    {
        "key": "gvp",
        "text": "Smithsonian Global Volcanism Program, Volcanoes of the World, Holocene eruptions (WFS service, read 6 Nov 2026).",
        "url": "https://volcano.si.edu/",
    },
    {
        "key": "gk",
        "text": "Gardner, J. K. &amp; Knopoff, L. (1974). Is the sequence of earthquakes in Southern California, with aftershocks removed, Poissonian? <i>BSSA</i> 64, 1363–1367.",
        "doi": "10.1785/BSSA0640051363",
    },
    {
        "key": "cochran",
        "text": "Cochran, E. S., Vidale, J. E. &amp; Tanaka, S. (2004). Earth tides can trigger shallow thrust fault earthquakes. <i>Science</i> 306, 1164–1166.",
        "doi": "10.1126/science.1103961",
        "check": "abstract read",
    },
    {
        "key": "ide",
        "text": "Ide, S., Yabe, S. &amp; Tanaka, Y. (2016). Earthquake potential revealed by tidal influence on earthquake size–frequency statistics. <i>Nature Geoscience</i> 9, 834–837.",
        "doi": "10.1038/ngeo2796",
        "check": "abstract read",
    },
    {
        "key": "hough",
        "text": "Hough, S. E. (2018). Do large (magnitude ≥8) global earthquakes occur on preferred days of the calendar year or lunar cycle? <i>Seismological Research Letters</i> 89(2A), 577–581.",
        "doi": "10.1785/0220170154",
        "check": "abstract read",
    },
    {
        "key": "usgsfaq",
        "text": "USGS. Can you predict earthquakes?",
        "url": "https://www.usgs.gov/faqs/can-you-predict-earthquakes",
    },
    {
        "key": "ephem",
        "text": "PyEphem 4.2.1 (VSOP87 planets, ELP 2000-82 Moon). Computations in tools/sky/ of this site's repository.",
        "url": "https://rhodesmill.org/pyephem/",
    },
]


def main() -> None:
    tests = rows("sky_cluster_tests.csv")
    periods = rows("sky_cluster_periods.csv")
    nov = rows("sky_nov2026_observed.csv")
    prim = [t for t in tests if t["family"] == "primary"]
    min_q = min(float(t["q_fdr"]) for t in prim)

    timeline = [
        [
            "4 Nov 14:24",
            "Mercury inferior conjunction (0.67 AU)",
            "Mercury between Earth and Sun",
            "PyEphem [ephem]",
        ],
        [
            "10 Nov – 4 Dec (interval)",
            "Morning grouping: Mercury, Venus, Mars, Jupiter",
            "≥4 naked-eye planets west of the Sun, each ≥10° from it, within 90° of longitude. Best seen 13–22 Nov",
            "PyEphem [ephem]",
        ],
        [
            "13 Nov 15:55 / 14 Nov 00:32",
            "Mercury, then Venus, turn direct",
            "Apparent motion only",
            "PyEphem [ephem]",
        ],
        [
            "16 Nov 06:24",
            "Mars–Jupiter conjunction, 1.2° apart, 25.5° Leo",
            "Equal ecliptic longitude seen from Earth. The planets are about 4 AU apart in space",
            "PyEphem [ephem]",
        ],
        [
            "17 Nov 23:45 (nodal peak)",
            "Leonids, ZHR about 15; weak dust-trail encounters 17–19 Nov",
            "Meteors from comet 55P/Tempel–Tuttle debris",
            "IMO [imo]",
        ],
        [
            "24 Nov 14:53",
            "Full Moon at 360,765 km: a supermoon",
            "Full Moon ≤ 362,000 km (this study). Perigee 25 Nov 20:54 UTC at 359,347 km",
            "PyEphem [ephem]",
        ],
        [
            "25 Nov 22:24",
            "Uranus at opposition",
            "Earth between Sun and Uranus",
            "PyEphem [ephem]",
        ],
        [
            "27 Nov ≈18:17 TDB",
            "Comet 161P/Hartley–IRAS at perihelion, q = 1.28 AU",
            "Closest to Earth was about 2 Oct 2026 (≈0.52 AU, two-body estimate from the JPL orbit). Predicted magnitude about 17 in late November: a telescope object",
            "JPL SBDB [jpl]",
        ],
        [
            "30 Nov",
            "Moon passes Jupiter (08:34) and Mars (17:24) near Regulus",
            "Apparent grouping",
            "PyEphem [ephem]",
        ],
    ]

    def per(label: str, outcome: str) -> dict[str, str]:
        return next(
            p
            for p in periods
            if p["period"].startswith(label) and p["outcome"] == outcome
        )

    labels = [p["period"] for p in periods if p["outcome"] == "M6+ earthquakes, all"]
    find_rows = []
    for lab in labels:
        a = per(lab, "M6+ earthquakes, all")
        m = per(lab, "M6+ mainshocks")
        m7 = per(lab, "M7+ mainshocks")
        v = per(lab, "Eruption onsets")
        if a["observed"] == "":
            obs = "Window 13–27 Nov not yet observed"
            deg = "—"
            interp = "Prospective; see monitoring plan"
        else:
            obs = (
                f"{a['observed']} M6+ ({m['observed']} mainshocks, {m7['observed']} M7+); {v['observed']} eruption onsets"
                + (f". Largest: {esc(a['largest'])}" if a["largest"] else "")
            )
            pct = [int(float(x["percentile"])) for x in (m, m7, v)]
            deg = f"mainshocks {pct[0]}th, M7+ {pct[1]}th, eruptions {pct[2]}th percentile"
            hi = max(pct)
            interp = (
                "Within normal range"
                if hi < 95
                else "Eruption onsets in the top 5% of same-length windows: a modest anomaly, one of 24 comparisons"
            )
        base = (
            f"{m['baseline_mean']} mainshocks (95%: {m['baseline_95']}); {m7['baseline_mean']} M7+; "
            f"{v['baseline_mean']} onsets (95%: {v['baseline_95']})"
        )
        find_rows.append(
            [
                f'<b>{esc(lab)}</b><br><span class="note">{esc(a["window"])}; {esc(a["astronomy"])}</span>',
                obs,
                base,
                deg,
                "Good (global M6+ complete since 1973; GVP onsets ±3 d)",
                interp,
            ]
        )
    feat_rows = [
        [
            esc(t["feature"]),
            esc(t["outcome"]),
            t["observed"],
            t["expected"],
            t["ratio"],
            t["p_value"],
            t["q_fdr"],
            esc(t["verdict"]),
        ]
        for t in prim
    ]
    sens = [
        t for t in tests if t["family"] == "sensitivity" and float(t["p_value"]) < 0.1
    ]
    sens_txt = "; ".join(
        f"{t['feature']} {t['window']}, {t['outcome']}: {t['observed']} vs {t['expected']} (p = {t['p_value']})"
        for t in sens
    )

    obs_nov = (
        ", ".join(
            f"M{r['magnitude']} {r['place']} ({r['time_utc']} UTC, {r['mainshock']})"
            for r in nov
        )
        if nov
        else "none"
    )

    sections = [
        (
            "bottom",
            "1. Bottom line",
            f"""
<p><b>No unusual earthquake or eruption activity was found around past sky clusters like November 2026.</b>
Six periods in 1973–2026 meet the rule fixed in advance: at least four planets grouped in the sky, a supermoon and a Mars–Jupiter
conjunction, all within 30 days. Five are in the past: April 2011, October 2015, January 2018, March 2020 and May–June 2022.
In those windows, global M6+ earthquake counts, M7+ counts and eruption onsets all stayed within the normal range for windows of the same length.
None of the 16 primary tests survives correction for multiple testing (lowest q = {min_q:.2f}).
The same holds for each feature on its own: 27 Mars–Jupiter conjunctions, 146 supermoons and 67 planet-grouping episodes.</p>
<p>One modest anomaly appears: five eruption onsets in the May–June 2022 window, against a typical 1.9 (97th percentile).
With 24 period-by-outcome comparisons, about one such result is expected by chance.
The November 2026 window (13–27 November) has not happened yet. Results to date (1–6 November) are observations only, not a test.</p>
<p class="note">Four separate statements apply. An event happening is not the same as it being statistically unusual. Being unusual is not the same as being close in time
to an astronomical event, and being close in time is not evidence that the astronomy contributed. This brief makes no earthquake or eruption forecast [usgsfaq].</p>""",
        ),
        (
            "astro",
            "2. Verified astronomical timeline (UTC)",
            """
<p>Every date was computed independently, not taken from headlines. Planet and Moon positions come from PyEphem.
The comet comes from the current JPL orbit and the meteor shower from the IMO calendar.
Two corrections to circulating dates follow. The Mars–Jupiter conjunction is on 16 November UTC (15 November in the Americas), not the 14th.
Comet 161P's perihelion is 27 November per JPL's October 2026 orbit; some websites still list an older 18 December date.
An apparent alignment or conjunction is a line-of-sight effect: Mars and Jupiter are about 4 AU apart in space on 16 November.</p>""",
        ),
        (
            "design",
            "3. Design, fixed before the data were examined",
            """
<ul>
<li><b>Grouping:</b> at least 4 of Mercury, Venus, Mars, Jupiter and Saturn on the same side of the Sun, each at least 10° from it, within 90° of ecliptic longitude (daily, 00 UTC).
<b>Supermoon:</b> full Moon at most 362,000 km away (about three a year). <b>Conjunction:</b> equal geocentric longitude of Mars and Jupiter.
<b>Cluster:</b> all three within one 30-day span. These definitions were fixed before the catalogues were opened.</li>
<li><b>Earthquakes:</b> USGS ComCat global M6.0+, 1973 to 6 November 2026 [usgs]. Counts are reported for all events and for independent mainshocks; aftershocks were removed with Gardner–Knopoff space–time windows [gk].
M6+ is complete globally for this period. Regional swarms were not assessed, because they need local catalogues and local baselines.</li>
<li><b>Volcanoes:</b> Smithsonian GVP confirmed eruption onsets dated to within ±3 days, 1973–2025 [gvp]; 2026 is left out because the database lags.
The record has no consistent escalation or unrest entries, so those are assessed as <i>insufficient evidence</i>, not as no effect.</li>
<li><b>Windows:</b> ±3 days around each event (primary), with ±1 and ±7 days as sensitivity checks. A grouping counts as its whole run, padded by 3 days.
Overlapping windows are merged, so no earthquake is counted twice.</li>
<li><b>Baselines:</b> (a) 5,000 circular time shifts of the event dates, which keep aftershock and seasonal clustering, giving a one-sided p and Benjamini–Hochberg q across the 16 primary tests;
(b) every same-length window in 1973–2025; (c) the same calendar window in all other years.</li>
</ul>""",
        ),
        (
            "findings",
            "4. Findings by period",
            """
<p>All historical periods that meet the rule are listed, plus the August 2024 candidate from the original brief.
August 2024 fails the grouping rule: its "six-planet alignment" was spread over more than 90° and included Uranus and Neptune, which are not visible to the naked eye.
The rule also finds three clusters the brief did not list (2011, 2018, 2020). Percentile = where the observed count sits among all same-length windows in 1973–2025.</p>""",
        ),
        (
            "tests",
            "5. Each feature tested on its own, 1973–2026",
            """
<p>Keeping the three features separate matters because they are physically different: a tidal maximum and two line-of-sight effects.
Ratios of observed to expected counts sit between 0.67 and 1.65. None is significant after correction.</p>""",
        ),
        (
            "strong",
            "6. Strongest and negative findings",
            f"""
<ul>
<li><b>Modest anomaly.</b> May–June 2022 had five eruption onsets (Dempo, Ulawun, Bulusan, Mayon, Ebeko) where 1.9 is typical. These are ordinary small eruptions (VEI 0–2) in arcs that erupt often.
Across all six cluster windows, onsets were 12 against 7.3 expected (p = 0.08, q = 0.77): suggestive, not significant.</li>
<li><b>October 2015</b> had two M7+ mainshocks in 17 days (93rd percentile), including the M7.5 Hindu Kush earthquake of 26 October.</li>
<li><b>Exploratory only.</b> Sensitivity checks with p &lt; 0.1: {esc(sens_txt)}. These were not pre-specified as primary, do not hold at the primary ±3 d window, and do not replicate this site's earlier 1965–2016 test (±7 and ±15 d: no excess).</li>
<li><b>Negative.</b> January 2018 (M6+ counts at the 7th–12th percentile) and August 2024 (mainshocks 16th, eruption onsets 9th percentile) were quieter than usual. April 2011 and March 2020 were normal.
Supermoons and planet groupings show no excess for any outcome or window.</li>
</ul>""",
        ),
        (
            "mech",
            "7. Mechanisms and alternative explanations",
            """
<p><b>Tides are the only physical link of measurable size.</b> Solid-earth and ocean tides change stress on faults by about 0.01–0.1 bar.
That is far less than the stress released in an earthquake. Studies find a small tidal influence on some shallow thrust faults [cochran],
and a higher share of large events during high tidal stress [ide]. Neither study allows a particular month or fault to be singled out.
A global study of M8+ earthquakes found no preferred lunar phase [hough]. A supermoon raises the lunar tide by about 20% over an average full Moon.
That is comparable to the ordinary perigee spring tides that come every few months.</p>
<p><b>Planets:</b> Venus, the strongest planetary tide, is about 1/20,000 of the Moon's at its closest. Jupiter is about 1/100,000 or less.
A grouping or conjunction seen from Earth does not change those values in any meaningful way. <b>Comets and meteor showers</b> have no known route of influence on the solid Earth at these distances and masses.</p>
<p><b>Alternative explanations for apparent hits:</b> aftershock sequences, which are handled by declustering and the circular-shift null; ongoing eruptions reported as new; reporting lags; and selection.
Selection is the largest: choosing which "alignment" to look at after a disaster has happened. With about 13 M7+ mainshocks a year, any 30-day window has roughly a two-in-three chance of containing one somewhere.</p>""",
        ),
        (
            "limits",
            "8. Limitations and monitoring plan for 7–30 November 2026",
            f"""
<p><b>Data cutoff:</b> USGS to 6 Nov 2026; GVP database onsets to 31 Dec 2025. <b>Observed so far in November</b> (not a test): M6+ events {esc(obs_nov)}.
Only five historical clusters exist, so the test has little power to detect a weak effect. A small effect cannot be excluded, but no large effect is present.
Gardner–Knopoff windows ignore depth and are approximate. Eruption onsets depend on reporting, and escalations and unrest could not be tested.</p>
<p><b>Monitoring plan, fixed now:</b> on 1 December 2026, rerun <code>tools/sky/cluster_study.py</code> with the same definitions on USGS data to 30 November.
Report for the 13–27 November window: M6+ counts (all, mainshocks, M7+) against three baselines.
(1) Long-term: the same-length windows above (means 5.7 / 4.2 / 0.5).
(2) Recent rate: 1 August–6 November 2026 scaled to 15 days (6.5 all, 4.5 mainshocks), to allow for 2026's own activity level.
(3) Strong El Niño months, 1973–2025 (ONI ≥ 1.5), scaled to 15 days (3.7 mainshocks).
Also report eruption onsets from the GVP Weekly Volcanic Activity Reports, dated by activity start and not by report date, against a mean of 1.2.
Any count outside the 95% range of all three baselines will be reported as unusual. It will still not count as evidence of an astronomical cause.</p>""",
        ),
        (
            "background",
            "9. Background conditions in 2026",
            """
<p>November 2026 is not a quiet background. Three conditions are tested here: a record El Niño (ONI 2.46 in ASO 2026), a northeast Pacific marine heatwave, and an active earthquake year.</p>
<ul>
<li><b>Earthquake activity in 2026 is elevated but within past range.</b> To 6 November there were 124 M6+ events (90 mainshocks), against a 1973–2025 mean of 117 (85) for the same part of the year; 20 earlier years had as many or more.
M7+ mainshocks number 13 against a mean of 10.3; 10 of 53 years had as many or more. October 2026 was busy, with 21 M6+ events, many of them in the Vanuatu sequence.</li>
<li><b>El Niño:</b> months with ONI ≥ 1.5 in 1973–2025 (31 months; the 1982–83, 1997–98 and 2015–16 events) averaged 7.6 M6+ mainshocks a month, against 8.3 overall. The difference is not significant (p = 0.91, circular shifts of the ONI series).
The correlation between monthly ONI and mainshock counts is r = 0.03. No ENSO effect on global M6+ seismicity is detected, and no mechanism of the needed size is known.
El Niño does matter for coastal hazards: sea level, storm surge, landslides from heavy rain and coastal erosion. Those are tracked on the dashboard, not here.</li>
<li><b>Marine heatwave:</b> ocean warmth changes stress in the crust by far less than the ordinary tide. There is no known pathway to earthquakes or eruptions, and no data to test one, so it is listed as context only.</li>
</ul>
<p class="note">These background checks are separate from the astronomical test. They set the expected rate for November, so that a busy El Niño year is not mistaken for an astronomical effect.</p>""",
        ),
    ]

    parts = [
        "<h1>November 2026 sky events and Earth activity: a test against past clusters</h1>",
        f'<p class="meta"><span class="tag warn">Research brief</span> Research date: {DATE} · Earthquake data to 6 Nov 2026 · Eruption data to 31 Dec 2025 · Method and code: tools/sky/ in this site\'s repository</p>',
        '<div class="card status"><b>Status.</b> Historical comparison complete. The November 2026 window is prospective; results will be added after 1 December 2026.</div>',
    ]
    for sid, title, body in sections:
        parts.append(f'<h2 id="{sid}">{esc(title)}</h2><div class="prose">{body}</div>')
        if sid == "astro":
            parts.append(
                table(["Date (UTC)", "Event", "Definition / note", "Source"], timeline)
            )
        if sid == "findings":
            parts.append(
                table(
                    [
                        "Astronomical event / window",
                        "Terrestrial observation",
                        "Expected baseline (mean, 95% range)",
                        "Degree of anomaly",
                        "Data quality",
                        "Interpretation",
                    ],
                    find_rows,
                )
            )
        if sid == "tests":
            parts.append(
                table(
                    [
                        "Feature (±3 d)",
                        "Outcome",
                        "Observed",
                        "Expected",
                        "Ratio",
                        "p",
                        "q",
                        "Verdict",
                    ],
                    feat_rows,
                )
            )
            parts.append(
                '<p class="note">Full results, including ±1 and ±7 day sensitivity checks: <a href="data/sky_cluster_tests.csv">sky_cluster_tests.csv</a>; periods: <a href="data/sky_cluster_periods.csv">sky_cluster_periods.csv</a>.</p>'
            )
    parts.append(
        '<h2 id="references">Sources</h2><ol class="refs">'
        + "".join(ref_html(r) for r in REFS)
        + "</ol>"
    )
    body = "\n".join(parts)
    for r in REFS:
        body = body.replace(
            f"[{r['key']}]", f'<a href="#ref-{r["key"]}">[{REFS.index(r) + 1}]</a>'
        )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>November 2026 sky events · Global Weather Watch</title>
<meta name="description" content="Do planet groupings, supermoons and Mars–Jupiter conjunctions coincide with unusual earthquakes or eruptions? A pre-registered test of 1973–2026 clusters like November 2026.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%232b6cb0'/%3E%3C/svg%3E">
<style>{STYLE}</style>
</head><body>
{NAV}
<main>
{body}
</main>
<footer class="site-foot">Data snapshot: <span data-asof>{DATE}</span>. Independent, non-commercial analysis built from public sources (see <a href="about.html">About &amp; method</a>). Analysis prepared with Claude (Anthropic). <a href="contact.html">Contact</a></footer>
</body></html>
"""
    (ROOT / "sky-2026-11.html").write_text(page, encoding="utf-8")
    print("wrote sky-2026-11.html")


if __name__ == "__main__":
    main()
