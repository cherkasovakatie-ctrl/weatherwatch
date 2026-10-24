"""Paper: Hurricane Trudy (eastern Pacific, 11–20 October 2026). Numbers are read from data files via common.py."""
import json

from common import METHODS, ROOT, T, day, dtm, env_at, facts, fig, kt2mph, mjo, pos, refs, sst_summary

N = 'TRUDY'; o = T[N]
s_all = sst_summary(N)
early = sst_summary(N, until='2026-10-14 18:00')
pk = env_at(N, o['peak_time'][:13])
cross = {k: env_at(*v) for k, v in {'polo': ('POLO', '2026-09-22 00'), 'rachel': ('RACHEL', '2026-09-29 00'), 'simon': ('SIMON', '2026-10-10 06'),
                                    'trudy_p': ('TRUDY', '2026-10-17 00'), 'trudy_r': ('TRUDY', '2026-10-16 12'), 'trudy_s': ('TRUDY', '2026-10-17 18')}.items()}
m13, m16 = mjo('2026-10-13'), mjo('2026-10-16')
ri = o['ri_episodes'][0]
NHC = 'https://www.nhc.noaa.gov/archive/2026/ep21/ep212026.discus.{:03d}.shtml'
d = lambda n: f'<a href="{NHC.format(n)}">NHC discussion {n}</a>'  # noqa: E731
KEYS = ['knapp2010', 'kaplan2003', 'huang2021', 'wheeler2004', 'price1981', 'maloney2000', 'csu', 'paper4']
EXTRA = [('nhc', 'National Hurricane Center: Hurricane Trudy (EP212026) advisory archive, forecast discussions 1–27, 13–20 October 2026 (US Government, public domain). Text copies in data/tc2026/nhc/TRUDY/.', 'https://www.nhc.noaa.gov/archive/2026/TRUDY.shtml', 'read in full'),
         ('ap18', 'Associated Press (2026). Hurricane Trudy brings heavy rain and strong winds to Mexico\'s Pacific coast. 18 October 2026 (via ABC30 and KPRC).', 'https://abc30.com/story/hurricane-trudy-lashes-mexicos-pacific-coast-heavy-rain-strong-winds/19951948/', 'read'),
         ('reuters18', 'Reuters (2026). Hurricane Trudy weakens off Mexico\'s Pacific coast. 18 October 2026 (via KSL).', 'https://www.ksl.com/article/51637803/hurricane-trudy-weakens-off-mexicos-pacific-coast-as-cleanup-effort-begins', 'read'),
         ('ap19', 'Associated Press (2026). Trudy weakens to a tropical storm; Typhoon Champi a super typhoon. 18–19 October 2026 (via KPRC Click2Houston).', 'https://www.click2houston.com/news/2026/10/18/hurricane-trudy-brings-heavy-rain-and-strong-winds-to-mexicos-pacific-coast/', 'read')]
R = refs(KEYS, EXTRA); ref = {r['key']: i + 1 for i, r in enumerate(R)}
c = lambda k: f'<a href="#ref-{k}">[{ref[k]}]</a>'  # noqa: E731

S = []
S.append({'id': 'abstract', 'title': 'Abstract', 'html': (
    f"<p>Trudy was the twenty-first tropical cyclone of the 2026 eastern North Pacific season and the fourth major hurricane in four weeks in the waters off southwestern Mexico. "
    f"It formed south of southern Mexico on 13 October, intensified rapidly by {ri['max24']} kt in 24 hours on 15–16 October, and reached a provisional peak of {o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph, Category 3) and {o['min_pres']} mb near {pos(*o['peak_pos'])}. "
    f"It then weakened abruptly over water that earlier hurricanes had cooled, recovered to 85–90 kt on 17–18 October while moving northwestward roughly 160 km off the coast of Colima and Jalisco, and decayed over open water from 19 October under southwesterly shear and dry air. "
    f"The sea under Trudy's peak position was {float(pk['sst_pre_c']):.1f} °C three days before it arrived, {abs(float(pk['ssta_pre_c'])):.1f} °C below the 1991–2020 normal, whereas the same water had been {float(cross['polo']['sst_pre_c']):.1f} °C before Hurricane Polo passed over it in September. "
    "This supports the hurricane centre's suggestion that Trudy's interrupted intensification was partly caused by cool water left by Polo, Rachel and Simon. No deaths or major damage had been reported from Trudy by 19 October. The analysis uses provisional track data and should be revised against the official Tropical Cyclone Report.</p>")})
S.append({'id': 'findings', 'title': 'Main findings', 'html': (
    "<ol>"
    f"<li><b>Rapid intensification, then two interruptions.</b> Winds rose from {o['fixes'][[f[0] for f in o['fixes']].index(ri['start'])][3]} kt to {o['peak_kt']} kt between {dtm(ri['start'])} and {dtm(ri['end'])}; a 37-GHz microwave ring marked a forming eyewall on 15 October {d(9)}. Strengthening paused twice: on 15 October, when dry air wrapped around the northern side {d(10)}, and on 16 October, when the eyewall opened and an aircraft found only 982 mb {d(14)}.</li>"
    f"<li><b>A track over cooled water.</b> Trudy crossed the paths of three earlier hurricanes: Polo (25 days earlier), Rachel (17 days) and Simon (7 days). Along Trudy's track before 15 October the sea averaged {early['sst_mean']:.1f} °C, {early['ssta_mean']:+.1f} °C against normal; at the peak position it was {float(pk['sst_pre_c']):.1f} °C ({float(pk['ssta_pre_c']):+.1f} °C).</li>"
    "<li><b>Peak intensity is uncertain.</b> The 105 kt in IBTrACS rests on satellite estimates at 0600 UTC on 16 October; the next aircraft, 12 hours later, found a much weaker storm. A later aircraft on 18 October measured 95 kt at flight level with a dropsonde suggesting about 85 kt at the surface.</li>"
    "<li><b>Offshore track.</b> Weak steering between a ridge over Mexico and a trough over the Gulf kept Trudy moving slowly northwestward, parallel to the coast; its closest provisional position was about 160 km from land. Hurricane conditions on the coast were forecast but not reported.</li>"
    "<li><b>Background.</b> Trudy formed in an exceptionally energetic eastern Pacific season (ACE 2.7 times the normal for the date) during a very strong, east-based El Niño.</li>"
    "</ol>")})
S.append({'id': 'intro', 'title': '1. Introduction', 'html': (
    "<p>October 2026 brought an unusual sequence of strong hurricanes to the waters off southwestern Mexico. Polo reached Category 5 strength off Guerrero on 22 September; Rachel became a major hurricane on 1–2 October; Simon reached Category 4 on 10–11 October within about 50 km of the coast of Jalisco; Trudy followed a week later along almost the same corridor. "
    f"By 22 October the season's accumulated cyclone energy east of 180° was 343.9 × 10⁴ kt², 2.7 times the climatological value for the date {c('csu')}. "
    f"The season unfolded during a very strong El Niño that is unusually concentrated in the eastern Pacific {c('paper4')}.</p>"
    "<p>This paper reconstructs Trudy's life cycle from provisional track data, the hurricane centre's analyses and sea-surface temperature, asks why its intensification stopped twice, and records its effects on Mexico. It does not assess the forecasts.</p>")})
S.append({'id': 'methods', 'title': '2. Data and methods', 'html': METHODS.format(agency='National Hurricane Center')})
S.append({'id': 'lifecycle', 'title': '3. Life cycle', 'html': (
    fig(N, 'Figure 1. Trudy: 1-minute maximum wind and minimum pressure (top; shading marks rapid intensification) and sea-surface temperature at each position three days before the storm arrived, with its anomaly against 1991–2020 (bottom).')
    + f"<p><b>Genesis (11–13 October).</b> IBTrACS follows the precursor disturbance from {dtm(o['first'])} near {pos(*o['genesis'])}. The hurricane centre classified Tropical Depression Twenty-One-E at 1500 UTC on 13 October with 30 kt winds, after scatterometer data showed a closed but still broad circulation {d(1)}, and named it Trudy within the next 12 hours.</p>"
    f"<p><b>Rapid intensification (14–16 October).</b> Trudy moved west-northwestward south of a mid-level ridge over central Mexico. Forecasters expected rapid intensification from the outset; SHIPS guidance gave a high probability {d(2)}. Trudy became a hurricane at {dtm(o['first_hu'])}. At 1500 UTC on 15 October a cyan ring on the 37-GHz microwave channel showed a developing eyewall and a 30 kt rise in 24 hours {d(9)}. "
    f"That afternoon an Air Force Reserve aircraft found 84 kt at 700 mb and 978 mb; a tongue of dry air wrapping around the north side was blamed for a pause {d(10)}. An eye then appeared and strengthening resumed, giving the provisional peak of {o['peak_kt']} kt and {o['min_pres']} mb at {dtm(o['peak_time'])}.</p>"
    f"<p><b>Collapse and recovery (16–18 October).</b> By 1500 UTC on 16 October the eye had become less distinct, cloud tops had warmed and microwave data showed the eyewall open on the south side {d(13)}. The next aircraft found 982 mb and 76 kt at 700 mb: Trudy had weakened sharply without an obvious atmospheric cause. The forecaster wrote that the reasons were 'speculative' and that one possibility was cold water upwelled under the slow-moving hurricane where it crossed the paths of Polo and Rachel {d(14)}. "
    f"From the evening of 16 October deep convection reorganised, and on 17 October an aircraft found a 38 n mi eye open to the southwest, 95 kt at 700 mb and 976 mb {d(18)}. On 18 October another aircraft found 95 kt at 700 mb in the northeast eyewall, with a dropsonde suggesting about 85 kt at the surface {d(22)}.</p>"
    f"<p><b>Decay (18–20 October).</b> As Trudy moved away from the coast, increasing southwesterly shear and drier, more stable air broke down the core from the evening of 18 October {d(23)}. Within 12 hours most deep convection had gone {d(24)}; on 19 October the shear was about 15 kt in the SHIPS analysis, then 20–30 kt aloft {d(25)}, {d(26)}. The last advisory, at 0300 UTC on 20 October, declared Trudy a remnant low {d(27)}.</p>"),
    'table': {'cols': ['Quantity', 'Value'], 'rows': facts(N), 'note': 'From IBTrACS v04r01, provisional (operational NHC values). UTC throughout. The first fixes are the precursor disturbance before NHC classification.'}})
S.append({'id': 'ocean', 'title': '4. The ocean beneath: a corridor of cold wakes', 'html': (
    f"<p>Over its first three days the water ahead of Trudy averaged {early['sst_mean']:.1f} °C with an anomaly of {early['ssta_mean']:+.1f} °C, reaching {early['ssta_max']:+.1f} °C: very warm, consistent with the El Niño background. "
    f"From 15 October, as Trudy entered the corridor that earlier hurricanes had used, the pre-storm SST fell to {float(pk['sst_pre_c']):.1f} °C ({float(pk['ssta_pre_c']):+.1f} °C) at the peak position and stayed near or below normal for two days (Figure 1).</p>"
    "<p>Three earlier hurricanes crossed Trudy's later path. The table compares the sea at the crossing points before each of them arrived with the sea three days before Trudy arrived. Hurricanes cool the ocean surface by mixing up colder water from below, and slow-moving storms cool it most <a href=\"#ref-price1981\">[" + str(ref['price1981']) + "]</a>; the cooling can last weeks.</p>"),
    'table': {'cols': ['Crossing point', 'Earlier storm (date, wind)', 'SST before earlier storm', 'SST before Trudy', 'Change'],
              'rows': [[pos(cross['polo']['lat'], float(cross['polo']['lon']) - 360), 'Polo (22 Sep, 90 kt)', f"{float(cross['polo']['sst_pre_c']):.1f} °C ({float(cross['polo']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_p']['sst_pre_c']):.1f} °C ({float(cross['trudy_p']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_p']['sst_pre_c']) - float(cross['polo']['sst_pre_c']):+.1f} °C"],
                       [pos(cross['rachel']['lat'], float(cross['rachel']['lon']) - 360), 'Rachel (29 Sep, 50 kt)', f"{float(cross['rachel']['sst_pre_c']):.1f} °C ({float(cross['rachel']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_r']['sst_pre_c']):.1f} °C ({float(cross['trudy_r']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_r']['sst_pre_c']) - float(cross['rachel']['sst_pre_c']):+.1f} °C"],
                       [pos(cross['simon']['lat'], float(cross['simon']['lon']) - 360), 'Simon (10 Oct, 120 kt)', f"{float(cross['simon']['sst_pre_c']):.1f} °C ({float(cross['simon']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_s']['sst_pre_c']):.1f} °C ({float(cross['trudy_s']['ssta_pre_c']):+.1f})", f"{float(cross['trudy_s']['sst_pre_c']) - float(cross['simon']['sst_pre_c']):+.1f} °C"]],
              'note': 'OISST v2.1 at the nearest grid point, three days before each storm reached the point; anomalies against 1991–2020 in brackets. Crossing points are where Trudy came within 25 km of the earlier track (Polo 11 km, Rachel 22 km, Simon 0 km). Part of the cooling is seasonal: the normal SST falls by a few tenths of a degree between late September and mid-October here.'},
    'html_after': (
        f"<p>The pattern is consistent: the sea was {abs(float(cross['trudy_p']['sst_pre_c']) - float(cross['polo']['sst_pre_c'])):.1f} °C cooler where Polo had passed and {abs(float(cross['trudy_r']['sst_pre_c']) - float(cross['rachel']['sst_pre_c'])):.1f} °C cooler where Rachel had passed, and the anomalies turned from strongly positive to negative. "
        "Two limits apply. SST is only the surface: the forecasters later noted that Trudy moved 'over warmer waters with increasing ocean heat content' on 16–17 October and re-strengthened, so the depth of warm water probably mattered as much as the surface value; ocean heat content was not analysed here. And the 982 mb found on 16 October may partly reflect an over-estimated satellite peak earlier that day rather than a true collapse.</p>"
        f"<p><b>Trudy's own wake</b> was modest: the largest cooling under its track was {abs(s_all['wake_min']):.1f} °C, smaller than Rachel's (more than 2 °C), because Trudy crossed water that had already been mixed.</p>")})
S.append({'id': 'atmos', 'title': '5. Atmosphere and steering', 'html': (
    f"<p><b>Shear and moisture.</b> Through 16 October the forecasters described a moist, low-shear environment over very warm water {d(12)}; the two pauses were attributed to dry air entering the core rather than to shear {d(10)}, {d(13)}. From 17 October the UW-CIMSS analysis put the shear at about 14 kt, with the vortex tilted to the northeast with height {d(16)}, {d(19)}; from the evening of 18 October southwesterly shear and drier, more stable air ended the hurricane {d(23)}.</p>"
    f"<p><b>MJO.</b> The RMM index was in phase {m13[0]} (amplitude {m13[1]:.1f}) at genesis and phase {m16[0]} ({m16[1]:.1f}) at the peak, an active MJO with enhanced convection over the Indian Ocean. The MJO modulates eastern Pacific hurricanes through low-level westerly anomalies {c('maloney2000')}; whether this phase helped or hindered Trudy is not tested here.</p>"
    f"<p><b>Steering.</b> Trudy first moved west-northwestward south of a mid-level ridge over central Mexico. The ridge weakened as a mid- to upper-level trough developed over the western Gulf, and forecasters noted that Simon, then about 700 n mi away, could interact with Trudy's steering as the two came within 500 miles {d(5)}. Trudy turned north-northwestward into the weakness, briefly drifted west and stalled on 16 October {d(12)}, then moved northwestward parallel to the coast as a weak ridge rebuilt over eastern Mexico. Once weakened and shallow, it was steered west and then northwest by the low-level flow, south of Baja California Sur {d(24)}.</p>")})
S.append({'id': 'impacts', 'title': '6. Impacts', 'html': (
    f"<p>Trudy's centre stayed offshore; its closest provisional position was about 160 km from land on 18 October. On 18 October a tropical storm warning remained from Playa Perula to San Blas and for the Islas Marías; forecasts called for 100–200 mm of rain (isolated 300 mm) in Michoacán, Colima and Jalisco, with a risk of floods and mudslides on slopes saturated by Simon {c('ap18')}. "
    f"On 18 October the government discontinued all warnings as Trudy moved away {c('reuters18')}. No deaths or significant damage attributed to Trudy had been reported by 19 October {c('reuters18')}, {c('ap19')}. Rainfall totals were not available for this paper.</p>"
    "<p>The cumulative effect of the four storms on the same coast, with saturated ground and repeated evacuations, was a recurring theme of official messages; Simon's and Rachel's impacts are described in their own papers.</p>")})
S.append({'id': 'climate', 'title': '7. Climate context', 'html': (
    f"<p>The 2026 eastern Pacific season has been exceptionally active, with ACE 2.7 times the normal for the date by 22 October {c('csu')}, during a very strong El Niño with record warmth off South America {c('paper4')}. "
    "The strong eastern-Pacific warming of this El Niño probably helped keep the sea warm enough for repeated major hurricanes near Mexico. Trudy's case shows the other side: in a busy season, earlier storms can cool the very water later storms need. "
    "No attribution study of Trudy exists; we do not assess the role of climate change.</p>")})
S.append({'id': 'uncertainty', 'title': '8. Uncertainties', 'html': (
    "<ul><li>Track and intensity are provisional operational values. The peak of 105 kt rests on satellite estimates and may be revised.</li>"
    "<li>SST is a 0.25° surface analysis; ocean heat content and mixed-layer depth, which control how much a hurricane can cool the surface, were not analysed.</li>"
    "<li>Shear and humidity are the forecasters' operational estimates, not an independent reanalysis.</li>"
    "<li>Impacts are from press reports up to 19 October; official damage and rainfall reports were not yet available.</li></ul>")})
S.append({'id': 'conclusion', 'title': '9. Conclusion', 'html': (
    "<p>Trudy had every ingredient for a stronger hurricane except fresh water: it intensified rapidly over warm, moist, low-shear conditions, but its path ran through a corridor that Polo, Rachel and Simon had crossed in the previous four weeks, where the sea had cooled by up to about 2 °C. "
    "Its peak was brief and is uncertain, and it recovered only partly before shear and dry air ended it. The case is a clear example of how a hyperactive season can limit itself through the ocean.</p>")})
EVID = [
    ['Warm, moist, low-shear start', f"SST {early['sst_mean']:.1f} °C ({early['ssta_mean']:+.1f}) to 14 Oct; low shear and moist air per NHC", 'Allowed genesis and rapid intensification', 'Observed (OISST); operational analysis', 'High', f"{c('huang2021')} {c('nhc')}"],
    ['Dry-air intrusions', '15 Oct (north side) and 16 Oct (south side, eyewall open)', 'Interrupted intensification', 'Satellite and microwave interpretation (NHC)', 'Medium', c('nhc')],
    ['Cold wakes of Polo, Rachel and Simon', f"Pre-storm SST at peak position {float(pk['sst_pre_c']):.1f} °C ({float(pk['ssta_pre_c']):+.1f}); 1–3 °C cooler than before the earlier storms", 'Limited peak and contributed to the collapse on 16 Oct', 'Observed SST; mechanism by physical reasoning', 'Medium', f"{c('price1981')} {c('nhc')}"],
    ['Southwesterly shear and dry, stable air', '~14 kt on 17 Oct rising to 20–30 kt aloft by 19 Oct', 'Caused final decay', 'Operational analysis (SHIPS, UW-CIMSS)', 'High', c('nhc')],
    ['Weak steering', 'Ridge over Mexico weakened by a Gulf trough; possible interaction with Simon', 'Slow track parallel to the coast; kept centre offshore', 'Operational analysis', 'High', c('nhc')],
    ['El Niño background', 'Very strong, east-based; ACE 2.7 times normal for the date', 'Raised the season\'s activity and SST before the storms', 'Climatological reasoning', 'Medium', f"{c('paper4')} {c('csu')}"],
]
paper = dict(storm=N, order=1, file='tc-2026-trudy.html', short='Hurricane Trudy (2026)', card_line='E. Pacific · Cat 3 · 11–20 Oct',
             title='Hurricane Trudy (October 2026): rapid intensification over a corridor of cold wakes', basin_name='Eastern North Pacific',
             description='Research paper on Hurricane Trudy, eastern Pacific, October 2026.', status='draft', research_date='24 October 2026',
             obs_cutoff='IBTrACS to 20 Oct; NHC discussions 1–27; press to 19 Oct', track_source='IBTrACS v04r01 (provisional, NHC operational)',
             status_note='Draft for review (24 Oct 2026). Built from provisional data; to be checked against NHC\'s Tropical Cyclone Report when published.',
             toc=[(s['id'], s['title']) for s in S] + [('evidence', 'Evidence table'), ('references', 'References')], sections=S, evidence=EVID, references=R)
(ROOT / 'tc2026/trudy.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', sum(len(s['html'].split()) + len(s.get('html_after', '').split()) for s in S), 'words')
