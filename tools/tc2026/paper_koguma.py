"""Paper: Typhoon Koguma (western North Pacific, 5–13 October 2026)."""
import json
import math

from common import METHODS, ROOT, T, dtm, env, facts, fig, kt2mph, mjo, pos, refs, sst_summary

N = 'KOGUMA'; o = T[N]
pre = sst_summary(N, until='2026-10-10 12:00'); s_all = sst_summary(N)
m5, m9 = mjo('2026-10-05'), mjo('2026-10-09')
F = {f[0]: f for f in o['fixes']}; NO = {f[0]: f for f in T['NOLO']['fixes']}


def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


sep = {t: round(dist(F[t], NO[t])) for t in F if t in NO}
smin = min(sep.items(), key=lambda kv: kv[1])
KEYS = ['knapp2010', 'kaplan2003', 'huang2021', 'wheeler2004', 'wang2002', 'camargo2005', 'price1981', 'csu', 'paper4']
EXTRA = [('wn', 'Weathernews (2026). Typhoon No. 29 (Koguma) (JMA observations and forecasts, 9 October 2026).', 'https://sea.weathernews.com/resources/202610/269', 'read'),
         ('nwsg', 'Pogodnik (2026). Typhoon Koguma heads north with 130 mph winds (summarising NWS Guam advisories, 11 October 2026).', 'https://pogodnik.com/en/news/typhoon-koguma-2026-130-mph-winds-forecast-track', 'read; secondary source')]
R = refs(KEYS, EXTRA); ref = {r['key']: i + 1 for i, r in enumerate(R)}
c = lambda k: f'<a href="#ref-{k}">[{ref[k]}]</a>'  # noqa: E731
METH = METHODS.format(agency='JTWC for the 1-minute winds; the Japan Meteorological Agency is the WMO centre, and its 10-minute winds are lower').replace(
    "Wind shear and mid-level humidity are taken from the forecasters' own analyses in the advisories and discussions (which use the SHIPS model and satellite estimates), quoted with date and time.",
    "No forecast-discussion archive comparable to NHC's was available for this typhoon, so wind shear and humidity could not be documented from operational analyses; the atmospheric discussion is limited accordingly.")

S = []
S.append({'id': 'abstract', 'title': 'Abstract', 'html': (
    f"<p>Koguma (Typhoon No. 29 in the JMA numbering) was a powerful typhoon that stayed over the open western North Pacific throughout its life. "
    f"It formed on 5 October near {pos(*o['genesis'])}, far to the east, as is typical of strong El Niño years, moved northwest across water about {pre['ssta_mean']:+.1f} °C warmer than normal, and intensified rapidly by {o['max_24h_change'][2]} kt in 24 hours on 8–9 October. "
    f"It peaked at {o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph, Category 4 equivalent) and {o['min_pres']} mb at {dtm(o['peak_time'])} over the open ocean, then recurved north and northeast and weakened over cooler water, leaving the tropics by 13 October. "
    "No land was threatened; NWS Guam issued no watches or warnings. At the same time, the remnant of eastern Pacific Hurricane Nolo, which had crossed the date line, lay 700–1,300 km to the north and northwest; forecasters cited it as one influence on Koguma's turn north. "
    "Koguma contributed 22 × 10⁴ kt² of ACE to a western Pacific season running 41% above normal.</p>")})
S.append({'id': 'findings', 'title': 'Main findings', 'html': (
    "<ol>"
    f"<li><b>Southeastern genesis.</b> Koguma formed at {pos(*o['genesis'])}, in the southeastern quadrant of the basin where strong El Niño events concentrate tropical-storm formation {c('wang2002')}.</li>"
    f"<li><b>Rapid intensification over warm water.</b> Winds rose from {F['2026-10-08 00:00'][3]} kt to {F['2026-10-09 12:00'][3]} kt in 36 hours and reached {o['peak_kt']} kt a day later; the sea ahead of the storm averaged {pre['sst_mean']:.1f} °C ({pre['ssta_mean']:+.1f} °C) up to the peak.</li>"
    f"<li><b>An intense, long-lived typhoon.</b> {o['hours_hu']} hours at typhoon strength and {o['hours_major']} hours at Category 3-equivalent or above, consistent with the tendency of El Niño years to produce more intense, longer-lived typhoons {c('camargo2005')}.</li>"
    f"<li><b>A neighbour across the date line.</b> The remnant of Hurricane Nolo came within {smin[1]:,} km of Koguma on {dtm(smin[0])}; its role in Koguma's recurvature is plausible but untested.</li>"
    "<li><b>No land impacts.</b> The closest land was about 650 km away (Iwo To); the hazard was to shipping.</li>"
    "</ol>")})
S.append({'id': 'intro', 'title': '1. Introduction', 'html': (
    f"<p>The 2026 western North Pacific season had produced 25 named storms and 13 typhoons, 9 of them reaching Category 3 equivalent or stronger, by 23 October, with ACE of 337 × 10⁴ kt² against a normal of 239 for the date {c('csu')}. During strong El Niño events, typhoons tend to form farther southeast, closer to the date line, and to last longer and become more intense {c('wang2002')}, {c('camargo2005')}; 2026 is a very strong El Niño {c('paper4')}. "
    "Koguma is a clear example of this type: a typhoon born east of 165°E that never approached land. This paper documents its life cycle and the ocean beneath it.</p>")})
S.append({'id': 'methods', 'title': '2. Data and methods', 'html': METH})
S.append({'id': 'lifecycle', 'title': '3. Life cycle', 'html': (
    fig(N, 'Figure 1. Koguma: 1-minute maximum wind and minimum pressure (JTWC values in IBTrACS; top; shading marks rapid intensification) and sea-surface temperature at each position three days before the storm arrived, with its anomaly against 1991–2020 (bottom).')
    + f"<p><b>Formation and slow development (5–8 October).</b> IBTrACS begins at {dtm(o['first'])} near {pos(*o['genesis'])}, in the northern Marshall Islands, with 29 kt winds. Koguma moved north-northwest, then west-northwest, and remained a tropical storm of 45–55 kt for three days. "
    f"On 9 October JMA analysed it as a typhoon of 990 hPa with 75 kt 10-minute winds, about 650 km southwest of Minamitorishima, moving west-northwest at 11 kt, and forecast further deepening to 955 hPa {c('wn')}.</p>"
    f"<p><b>Rapid intensification (8–10 October).</b> Koguma reached typhoon strength at {dtm(o['first_hu'])} and then intensified by {o['max_24h_change'][2]} kt in the 24 hours to {dtm(o['max_24h_change'][1])}, reaching {o['peak_kt']} kt and {o['min_pres']} mb at {dtm(o['peak_time'])} near {pos(*o['peak_pos'])}. "
    f"On 11 October NWS Guam still gave about 130 mph (115 kt), with typhoon-force winds extending about 72 km and tropical-storm-force winds about 193 km from the centre {c('nwsg')}.</p>"
    f"<p><b>Recurvature and transition (11–13 October).</b> Koguma turned north on 11–12 October and accelerated north-northeast, weakening below typhoon strength by midday on 13 October as it moved over water below 26 °C near 35°N. The last IBTrACS fix is at {dtm(o['last'])} near {pos(*o['fixes'][-1][1:3])} with {o['fixes'][-1][3]} kt; Weathernews expected it to become a severe tropical storm over cooler water by 14 October {c('wn')}.</p>"),
    'table': {'cols': ['Quantity', 'Value'], 'rows': facts(N, [('JMA analysis, 9 Oct 0405 UTC', '990 hPa, 75 kt (10-minute), 18.8°N, 156.1°E'), ('Closest approach to land', 'about 650 km east of Iwo To (11 Oct, NWS Guam)')]),
              'note': 'IBTrACS v04r01, provisional JTWC values. JMA peak values were not available for this paper.'}})
S.append({'id': 'environment', 'title': '4. Environment', 'html': (
    f"<p><b>Ocean.</b> Up to the peak, the sea three days ahead of Koguma averaged {pre['sst_mean']:.1f} °C and never fell below {pre['sst_min']:.1f} °C, {pre['ssta_mean']:+.1f} °C above the 1991–2020 normal on average. North of 30°N, after recurvature, it fell to about {s_all['sst_min']:.0f} °C. "
    f"Moving at a mean {o['mean_speed_kmh']} km/h, much faster than the eastern Pacific hurricanes of the same weeks, Koguma left only a weak cold wake in the analysis (up to {abs(s_all['wake_min']):.1f} °C) {c('price1981')}.</p>"
    f"<p><b>Atmosphere.</b> Without an operational discussion archive, shear and humidity were not documented. The RMM index was in phase {m5[0]} (amplitude {m5[1]:.1f}) at formation and phase {m9[0]} ({m9[1]:.1f}) during rapid intensification, with the MJO's active convection over the Indian Ocean rather than the western Pacific; Koguma's development therefore did not depend on an active MJO overhead.</p>"
    f"<p><b>Nolo.</b> Hurricane Nolo, first tracked in the eastern Pacific on 10 September, and crossed the date line in early October, weakened as it moved west near 25–32°N. Its separation from Koguma fell from about 2,000 km on 5 October to {smin[1]:,} km on {dtm(smin[0])}. "
    f"Two cyclones within about 1,000 km can influence each other's motion; NWS Guam reportedly cited the interaction as a main factor in Koguma's northward turn {c('nwsg')}. A mid-latitude trough is the usual cause of recurvature at this latitude, and the relative roles were not analysed here.</p>")})
WP = sorted([(v['first'], k, v) for k, v in T.items() if v['basin'] == 'WP'])
wrows = [[k.title(), v['first'][:10], pos(*v['genesis']), str(v['peak_kt']), f"{v['ace']:.1f}", str(v['hours_hu'])] for _, k, v in WP]
glon = [float(v['genesis'][1]) for _, k, v in WP]; east = sum(x >= 150 for x in glon)
S.append({'id': 'season', 'title': '5. Koguma among the 2026 typhoons', 'html': (
    f"<p>The table lists the {len(WP)} western Pacific storms of 2026 that reached typhoon strength in IBTrACS. {east} of them were first tracked east of 150°E, and the mean first-fix longitude was {sum(glon) / len(glon):.0f}°E. "
    f"Koguma's first fix ({float(o['genesis'][1]):.0f}°E) was among the farthest east, and its ACE ({o['ace']:.1f}) ranks {sorted([v['ace'] for _, k, v in WP], reverse=True).index(o['ace']) + 1} of {len(WP)}. "
    "A comparison with the 1991–2020 distribution of first-fix positions would be needed to call the eastward shift unusual; that is left for the season overview.</p>"),
    'table': {'cols': ['Typhoon', 'First fix (UTC date)', 'First-fix position', 'Peak (kt, 1-min)', 'ACE', 'Hours as typhoon'], 'rows': wrows,
              'note': 'IBTrACS v04r01, provisional JTWC values; first fix may be a precursor disturbance. Champi was still active at the data cutoff.'}})
S.append({'id': 'impacts', 'title': '6. Impacts', 'html': (
    f"<p>Koguma stayed over open ocean. NWS Guam listed no watches or warnings for Guam or the Northern Mariana Islands {c('nwsg')}, and no damage or casualties were reported. Weathernews warned of expanding storm-force winds and severe gusts on trans-Pacific shipping routes {c('wn')}. No ship incidents were found in the sources consulted.</p>")})
S.append({'id': 'climate', 'title': '7. Climate context', 'html': (
    f"<p>Koguma fits the El Niño pattern in the western North Pacific: genesis in the southeast of the basin {c('wang2002')}, a long track over warm water and high intensity {c('camargo2005')}. The western Pacific season's ACE was 41% above normal by late October {c('csu')}. No attribution study exists for Koguma.</p>")})
S.append({'id': 'uncertainty', 'title': '8. Uncertainties', 'html': (
    "<ul><li>Intensities are provisional JTWC values; JMA's 10-minute winds are lower and its peak central pressure was not available here.</li>"
    "<li>Atmospheric conditions (shear, humidity) are not documented for this storm.</li>"
    "<li>The influence of Nolo is reported second-hand and not tested.</li></ul>")})
S.append({'id': 'conclusion', 'title': '9. Conclusion', 'html': (
    "<p>Koguma was a textbook El Niño typhoon: born far to the southeast, it travelled more than 4,600 km over warm water, intensified rapidly to Category 4 strength and recurved without touching land. It shows the intensity the basin can produce in a strong El Niño year even when the outcome is harmless.</p>")})
EVID = [
    ['Southeastern genesis', f"First fix {pos(*o['genesis'])}", 'Long track over warm water', 'Observed; literature for the El Niño shift', 'High', f"{c('knapp2010')} {c('wang2002')}"],
    ['Warm ocean', f"SST {pre['sst_mean']:.1f} °C ({pre['ssta_mean']:+.1f}) up to the peak", 'Supported rapid intensification', 'Observed (OISST)', 'High', c('huang2021')],
    ['Fast motion', f"Mean {o['mean_speed_kmh']} km/h", 'Limited self-induced cooling', 'Observed; physical reasoning', 'Medium', c('price1981')],
    ['Nolo remnant', f"Within {smin[1]:,} km on {dtm(smin[0])}", 'Possible influence on recurvature', 'Reported (secondary); untested', 'Low', c('nwsg')],
    ['El Niño background', 'Very strong El Niño; basin ACE 41% above normal', 'Favours intense, long-lived typhoons', 'Climatological reasoning', 'Medium', f"{c('camargo2005')} {c('csu')}"],
]
paper = dict(storm=N, order=3, file='tc-2026-koguma.html', short='Typhoon Koguma (2026)', card_line='W. Pacific · Cat 4 equiv. · 5–13 Oct',
             title='Typhoon Koguma (October 2026): an El Niño typhoon over the open Pacific', basin_name='Western North Pacific',
             description='Research paper on Typhoon Koguma, western North Pacific, October 2026.', status='draft', research_date='24 October 2026',
             obs_cutoff='IBTrACS to 13 Oct; JMA via Weathernews (9 Oct); NWS Guam via press (11 Oct)', track_source='IBTrACS v04r01 (provisional, JTWC values)',
             status_note='Draft for review (24 Oct 2026). Built from provisional JTWC data and secondary reports of JMA and NWS Guam products; atmospheric conditions not documented.',
             toc=[(s['id'], s['title']) for s in S] + [('evidence', 'Evidence table'), ('references', 'References')], sections=S, evidence=EVID, references=R)
(ROOT / 'tc2026/koguma.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', sum(len(s['html'].split()) for s in S), 'words', smin)
