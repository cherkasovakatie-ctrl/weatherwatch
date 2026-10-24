"""Paper: Hurricane Simon (eastern Pacific, 4–16 October 2026)."""
import json

from common import METHODS, ROOT, T, dtm, env_at, facts, fig, kt2mph, mjo, pos, refs, sst_summary

N = 'SIMON'; o = T[N]
pre = sst_summary(N, until='2026-10-10 18:00'); s_all = sst_summary(N)
pk = env_at(N, o['peak_time'][:13]); ri = o['ri_episodes'][0]
F = {f[0]: f for f in o['fixes']}
m7, m10 = mjo('2026-10-07'), mjo('2026-10-10')
NHC = 'https://www.nhc.noaa.gov/archive/2026/ep20/ep202026.discus.{:03d}.shtml'
d = lambda n: f'<a href="{NHC.format(n)}">NHC discussion {n}</a>'  # noqa: E731
KEYS = ['knapp2010', 'kaplan2003', 'huang2021', 'wheeler2004', 'carrasco2014', 'price1981', 'maloney2000', 'csu', 'paper4']
EXTRA = [('nhc', 'National Hurricane Center: Hurricane Simon (EP202026) advisory archive, forecast discussions 1–38, 7–16 October 2026 (US Government, public domain). Text copies in data/tc2026/nhc/SIMON/.', 'https://www.nhc.noaa.gov/archive/2026/SIMON.shtml', 'read in full'),
         ('afp12', 'AFP (2026). Hurricane Simon leaves one dead, causes damage on Mexico\'s Pacific coast. 12 October 2026 (via Jamaica Observer).', 'https://www.jamaicaobserver.com/2026/10/12/hurricane-simon-leaves-one-dead-causes-damage-mexicos-pacific-coast/', 'read'),
         ('ap13', 'Associated Press (2026). Death toll rises to 6 as Hurricane Simon and Rachel remnants unleash floods in Mexico. 13 October 2026 (via ITV News).', 'https://www.itv.com/news/2026-10-13/hurricane-remnants-unleash-deadly-floods-in-mexico-killing-at-least-6', 'read')]
R = refs(KEYS, EXTRA); ref = {r['key']: i + 1 for i, r in enumerate(R)}
c = lambda k: f'<a href="#ref-{k}">[{ref[k]}]</a>'  # noqa: E731

S = []
S.append({'id': 'abstract', 'title': 'Abstract', 'html': (
    f"<p>Simon was a very small, very intense hurricane that spent almost a week close to the coast of west-central Mexico without making landfall. "
    f"It became a tropical depression south of Mexico on 7 October, a hurricane at {dtm(o['first_hu'])}, and then intensified by up to {ri['max24']} kt in 24 hours, reaching a provisional peak of {o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph, Category 4) and about {o['min_pres']} mb on 10–11 October, while its northern eyewall lay about 30 n mi off the coast of Jalisco. "
    "Aircraft found concentric eyewalls at the peak. Simon then weakened over two days as mid-level dry air and shear disrupted its tiny core, stalled in weak steering currents, briefly re-intensified to about 90 kt on 13–14 October, collapsed again to a tropical storm within a day, and dissipated off Baja California Sur on 16 October. "
    f"The sea along its path was warm ({pre['sst_mean']:.1f} °C before the peak, {pre['ssta_mean']:+.1f} °C against normal) and its own cold wake was small in the 0.25° analysis. "
    "One death in Guerrero was attributed to Simon. The case illustrates how small hurricanes can change intensity very fast in both directions, and how weak steering turned a forecast landfall into a long coastal brush.</p>")})
S.append({'id': 'findings', 'title': 'Main findings', 'html': (
    "<ol>"
    f"<li><b>Explosive intensification of a tiny core.</b> Winds rose from {F[ri['start']][3]} kt to {o['peak_kt']} kt between {dtm(ri['start'])} and {dtm(ri['end'])}, with a pinhole eye on 9 October {d(11)}. Forecast guidance had given about a 70% chance of 30 kt in 24 hours {d(7)}.</li>"
    f"<li><b>Eyewall replacement at the peak.</b> On 10 October the eye widened, suggesting an eyewall replacement cycle overnight {d(13)}; aircraft found concentric eyewalls of 12 and 36 n mi radius, 932 mb and 134 kt at 700 mb, and a radar satellite recorded 138 kt {d(14)}.</li>"
    "<li><b>A near miss.</b> The northern eyewall came within about 30 n mi of the coast on 10–11 October {d}; IBTrACS places the centre 45 km from land at 1800 UTC on 11 October. Simon never made landfall; weak steering then held it offshore for five days.".format(d=d(15))
    + "</li>"
    f"<li><b>Fast changes in both directions.</b> After weakening, Simon re-strengthened to about 90 kt on 13–14 October, then lost hurricane strength within about 24 hours; the forecaster noted that small cyclones 'can undergo rapid weakening as well as rapid intensification' {d(30)}.</li>"
    "<li><b>Impacts.</b> One death in Chilpancingo, Guerrero; flooding and road damage in coastal Guerrero including Acapulco; disruption at Puerto Vallarta airport.</li>"
    "</ol>")})
S.append({'id': 'intro', 'title': '1. Introduction', 'html': (
    "<p>Simon was the third of four major hurricanes in four weeks off southwestern Mexico in 2026 (Polo, Rachel, Simon, Trudy), in a season with accumulated cyclone energy 2.7 times the normal for the date by 22 October " + c('csu') + " and during a very strong, east-based El Niño " + c('paper4') + ". "
    "It is notable for its very small size, its extreme peak close to land, and the poor predictability of both its track and its intensity. This paper reconstructs its life cycle and the conditions behind its intensity changes.</p>")})
S.append({'id': 'methods', 'title': '2. Data and methods', 'html': METHODS.format(agency='National Hurricane Center')})
S.append({'id': 'lifecycle', 'title': '3. Life cycle', 'html': (
    fig(N, 'Figure 1. Simon: 1-minute maximum wind and minimum pressure (top; shading marks rapid intensification) and sea-surface temperature at each position three days before the storm arrived, with its anomaly against 1991–2020 (bottom).')
    + f"<p><b>Genesis (4–7 October).</b> IBTrACS follows the precursor disturbance from {dtm(o['first'])} near {pos(*o['genesis'])}. Tropical Depression Twenty-E formed at 1500 UTC on 7 October south of Mexico, with curved bands and a well-defined circulation, in low shear, abundant moisture and very warm water {d(1)}.</p>"
    f"<p><b>Rapid intensification (8–11 October).</b> On 8 October the SHIPS rapid-intensification index gave a 63% chance of a 55 kt rise in 48 hours {d(4)}; by evening every ocean, dynamic and thermodynamic factor favoured quick strengthening {d(7)}. Simon became a hurricane at {dtm(o['first_hu'])}. A very small central dense overcast with −83 °C cloud tops formed over the centre {d(8)}, and by 9 October a pinhole eye was visible {d(11)}. "
    f"The largest 24-hour rise, {ri['max24']} kt, came between {dtm(o['max_24h_change'][0])} and {dtm(o['max_24h_change'][1])}. Overnight on 9–10 October the eye widened, which suggests an eyewall replacement cycle {d(13)}; on the afternoon of 10 October aircraft found concentric eyewalls (inner 12 n mi, outer 36 n mi), 932 mb and 134 kt at 700 mb, and a Canadian radar satellite pass gave 138 kt {d(14)}. The provisional peak is {o['peak_kt']} kt at {dtm(o['peak_time'])}.</p>"
    f"<p><b>Coastal brush and first weakening (11–13 October).</b> On the evening of 10 October the northern eyewall was about 30 n mi off the coast {d(15)}; a landfall between Playa Perula and Cabo Corrientes remained possible until the afternoon of 11 October, when it became clear that Simon would stay offshore {d(17)}, {d(18)}. Cloud tops then warmed and mid-level dry air wrapped around the west side {d(19)}; mid-level easterly shear opened the eyewall on its northwest side on 12 October {d(21)}, {d(22)}. Winds fell to about 80 kt.</p>"
    f"<p><b>Second peak and collapse (13–16 October).</b> Late on 13 October the eye became distinct again and deep convection more symmetric; the hurricane 'remains tiny' {d(27)}. IBTrACS gives 90 kt at 0000 UTC on 14 October. By the next morning the eye had filled under northerly shear {d(28)}, and on 14 October a radar satellite measured only 65–75 kt in the eyewall and an aircraft found no hurricane-force winds at 700 mb {d(30)}. The tropical-storm-force winds reached only about 30 n mi from the centre and the pressure had risen to 991 mb {d(31)}. Southwesterly shear and dry air finished Simon on 16 October; it became a remnant low off Baja California Sur {d(37)}, {d(38)}.</p>"),
    'table': {'cols': ['Quantity', 'Value'], 'rows': facts(N, [('Closest provisional distance to land', '45 km, 1800 UTC 11 Oct (115 kt)'), ('Aircraft peak (10 Oct)', '932 mb; 134 kt at 700 mb; SAR 138 kt; concentric eyewalls 12 and 36 n mi')]),
              'note': 'IBTrACS v04r01, provisional (operational NHC values). The first fixes are the precursor disturbance.'}})
S.append({'id': 'environment', 'title': '4. Environment', 'html': (
    f"<p><b>Ocean.</b> Before the peak the sea along Simon's path averaged {pre['sst_mean']:.1f} °C, {pre['ssta_mean']:+.1f} °C above the 1991–2020 normal, and nowhere below {pre['sst_min']:.1f} °C. At the peak position it was {float(pk['sst_pre_c']):.1f} °C ({float(pk['ssta_pre_c']):+.1f} °C). "
    f"Simon's own cold wake in the 0.25° analysis was at most {abs(s_all['wake_min']):.1f} °C; a storm this small mixes a narrow swath that the analysis smooths out, so the true cooling under the core was probably larger. "
    f"On 13 October the forecaster could not tell whether warming cloud tops reflected the daily cycle or upwelled cool water under the slow-moving hurricane {d(26)}; by 16 October the remnant was still over 28–30 °C water {d(37)}, so the final decay was atmospheric.</p>"
    f"<p><b>Shear and moisture.</b> Through 10 October shear was low and the mid-troposphere moist {d(1)}, {d(9)}. The weakening of 11–12 October came with mid-level dry air on the west side and mid-level easterly shear 'undercutting the outflow layer' {d(19)}, {d(21)}; the collapse of 14 October followed northerly shear {d(28)}, {d(29)}; and southwesterly shear with dry mid-level air ended Simon {d(36)}.</p>"
    f"<p><b>Size.</b> Simon's very small inner core made its intensity especially volatile: forecasters called peak intensities 'virtually impossible to predict' {d(11)}. Small cyclones are more likely to undergo rapid intensification {c('carrasco2014')}, and Simon shows that the same small size allowed equally fast weakening.</p>"
    f"<p><b>MJO.</b> The RMM index was in phase {m7[0]} (amplitude {m7[1]:.1f}) at genesis and phase {m10[0]} ({m10[1]:.1f}) at the peak. The MJO modulates eastern Pacific hurricanes {c('maloney2000')}; its role here is not tested.</p>")})
S.append({'id': 'steering', 'title': '5. Track and steering', 'html': (
    f"<p>Simon first moved west-northwest along the south side of a weak mid-level ridge {d(1)}. A mid- to upper-level trough approaching Baja California was expected to turn it sharply north on 9–10 October, towards the coast; the models agreed on the pattern but not on the timing, and a small difference decided between landfall and a coastal brush {d(5)}, {d(9)}. "
    f"Simon turned north between a ridge over southern Mexico and a long-wave trough to the west {d(12)} and passed just offshore. From 12 October it lay between a ridge over the south-central United States and another building to its west and southwest, and drifted slowly northwest, then southwest {d(22)}, {d(24)}, {d(28)}. Mexico's civil protection at one point expected a landfall at Mazatlán as a Category 1 hurricane {c('afp12')}; instead the shallow remnant moved northwest, parallel to Baja California Sur {d(36)}.</p>")})
S.append({'id': 'impacts', 'title': '6. Impacts', 'html': (
    f"<p>A 71-year-old man died when a wall collapsed in Chilpancingo, Guerrero, during Simon's rain {c('afp12')}. Heavy rain in Guerrero toppled trees and utility poles, blocked roads and flooded homes in coastal communities including Acapulco; Nayarit and Sinaloa were on alert for rising rivers; operations at Puerto Vallarta's airport were resuming on 13 October {c('ap13')}. "
    f"On 12 October waves were still crashing along the Puerto Vallarta seafront {c('afp12')}. Press tallies that combine Simon and the remnants of Rachel (six deaths by 13 October) include five deaths in Ensenada caused by Rachel {c('ap13')}. Damage estimates and rainfall totals were not available for this paper.</p>")})
S.append({'id': 'climate', 'title': '7. Climate context', 'html': (
    "<p>Simon formed over water about half a degree warmer than normal in a very active season during a strong El Niño " + c('csu') + ", " + c('paper4') + ". No attribution study exists. Its most remarkable features, the tiny core, the extreme intensity changes and the stalling track, are governed by storm-scale and synoptic processes that are not specific to El Niño.</p>")})
S.append({'id': 'uncertainty', 'title': '8. Uncertainties', 'html': (
    "<ul><li>Provisional track and intensities; the peak and the second peak may be revised in the official report. For such a small storm, satellite estimates were especially uncertain between aircraft flights.</li>"
    "<li>The 0.25° SST analysis underestimates the cold wake of a very small hurricane.</li>"
    "<li>Shear and humidity are operational estimates, not an independent reanalysis.</li>"
    "<li>Impact figures are early press reports.</li></ul>")})
S.append({'id': 'conclusion', 'title': '9. Conclusion', 'html': (
    "<p>Simon combined favourable conditions (warm water, low shear, moist air) with a very small inner core, and intensified explosively to Category 4 within 50 km of the Jalisco coast. Its weakening was as abrupt as its strengthening, driven by dry air and shifting shear, and weak, conflicting steering kept it offshore for most of a week. "
    "The coast escaped a direct hit by a narrow margin, but the repeated rain contributed to saturated ground before Trudy arrived a week later.</p>")})
EVID = [
    ['Warm ocean', f"SST {pre['sst_mean']:.1f} °C ({pre['ssta_mean']:+.1f}) before the peak", 'Supported rapid intensification', 'Observed (OISST)', 'High', c('huang2021')],
    ['Low shear, moist air', 'Through 10 Oct (NHC, SHIPS)', 'Allowed rapid intensification', 'Operational analysis', 'High', c('nhc')],
    ['Very small inner core', 'Pinhole eye 9 Oct; TS-force winds only ~30 n mi on 14 Oct', 'Made intensity changes fast in both directions', 'Observed (satellite, aircraft); literature for RI', 'High', f"{c('nhc')} {c('carrasco2014')}"],
    ['Eyewall replacement', 'Concentric eyewalls 12 and 36 n mi, 10 Oct', 'Probably ended the peak', 'Aircraft observation', 'Medium', c('nhc')],
    ['Dry air and changing shear', 'Easterly (12 Oct), northerly (14 Oct), southwesterly (15–16 Oct)', 'Caused the weakening episodes', 'Operational analysis', 'High', c('nhc')],
    ['Weak, conflicting steering', 'Between ridges and a trough off California', 'Near-miss of the coast; long stall offshore', 'Operational analysis', 'High', c('nhc')],
]
paper = dict(storm=N, order=2, file='tc-2026-simon.html', short='Hurricane Simon (2026)', card_line='E. Pacific · Cat 4 · 4–16 Oct',
             title='Hurricane Simon (October 2026): a tiny Category 4 that brushed the Jalisco coast', basin_name='Eastern North Pacific',
             description='Research paper on Hurricane Simon, eastern Pacific, October 2026.', status='draft', research_date='24 October 2026',
             obs_cutoff='IBTrACS to 16 Oct; NHC discussions 1–38; press to 13 Oct', track_source='IBTrACS v04r01 (provisional, NHC operational)',
             status_note='Draft for review (24 Oct 2026). Built from provisional data; to be checked against NHC\'s Tropical Cyclone Report when published.',
             toc=[(s['id'], s['title']) for s in S] + [('evidence', 'Evidence table'), ('references', 'References')], sections=S, evidence=EVID, references=R)
(ROOT / 'tc2026/simon.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', sum(len(s['html'].split()) for s in S), 'words')
