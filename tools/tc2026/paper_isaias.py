"""Paper: Hurricane Isaias (Gulf of America / Mexico, 4–11 October 2026)."""
import json

from common import shear_between, METHODS, REFS, ROOT, T, dtm, facts, fig, kt2mph, mjo, pos, refs, sst_summary

N = 'ISAIAS'; o = T[N]
pre = sst_summary(N, until='2026-10-09 18:00')
m6, m8 = mjo('2026-10-06'), mjo('2026-10-08')
F = {f[0]: f for f in o['fixes']}
NHC = 'https://www.nhc.noaa.gov/archive/2026/al09/al092026.discus.{:03d}.shtml'
d = lambda n: f'<a href="{NHC.format(n)}">NHC discussion {n}</a>'  # noqa: E731
KEYS = ['knapp2010', 'kaplan2003', 'huang2021', 'wheeler2004', 'gray1984', 'klotzbach2010', 'price1981', 'csu', 'paper4', 'hersbach2020']
EXTRA = [('nhc', 'National Hurricane Center: Hurricane Isaias (AL092026) advisory archive, forecast discussions 1–20, 6–11 October 2026 (US Government, public domain). Text copies in data/tc2026/nhc/ISAIAS/.', 'https://www.nhc.noaa.gov/archive/2026/ISAIAS.shtml', 'read in full'),
         ('tae', 'NWS Tallahassee (2026). Post-Tropical Cyclone Report, Hurricane Isaias (preliminary, issued 11 October 2026).', 'https://www.weather.gov/media/tae/TropicalEventSummary/PSHTAE_2026AL09_Isaias_Summary.pdf', 'read'),
         ('npr', 'NPR / WUNC (2026). At least 4 deaths attributed to Isaias after hurricane bashes Florida and Alabama. 10–11 October 2026.', 'https://www.wunc.org/2026-10-10/at-least-4-deaths-attributed-to-isaias-after-hurricane-bashes-florida-and-alabama', 'read'),
         ('accu', 'AccuWeather (2026). Isaias made hurricane history before hitting Southeast. October 2026.', 'https://www.accuweather.com/en/hurricane/isaias-made-hurricane-history-before-hitting-southeast-with-winds-upwards-of-110-mph-tornadoes/1945554', 'read'),
         ('cc', 'Climate Central (2026). Climate change supercharged warm Gulf waters fueling Hurricane Isaias (Climate Shift Index alert, 9 October 2026).', 'https://www.climatecentral.org/climate-shift-index-alert/climate-change-supercharged-warm-Gulf-waters-fueling-hurricane-Isaias', 'read'),
         ('artemis', 'Artemis (2026). Moody\'s estimates insured losses from Hurricane Isaias in $2.5bn to $4.5bn range. 16 October 2026.', 'https://www.artemis.bm/news/moodys-estimates-insured-losses-from-hurricane-isaias-in-2-5bn-to-4-5bn-range/', 'read'),
         ('nasa', 'NASA Earth Observatory (2026). Isaias dims the Gulf Coast (Black Marble night lights).', 'https://science.nasa.gov/earth/earth-observatory/isaias-dims-the-gulf-coast/', 'cited via site event log')]
R = refs(KEYS, EXTRA); ref = {r['key']: i + 1 for i, r in enumerate(R)}
c = lambda k: f'<a href="#ref-{k}">[{ref[k]}]</a>'  # noqa: E731
_ = REFS

S = []
S.append({'id': 'abstract', 'title': 'Abstract', 'html': (
    "<p>Isaias was the first hurricane of the suppressed 2026 Atlantic season, the latest first hurricane in more than a century, and still the season's only hurricane in late October. "
    f"It formed as a depression in the southwestern Gulf on 6 October, drifted east, then accelerated northeast over water {pre['ssta_mean']:+.1f} °C warmer than the 1991–2020 normal ({pre['sst_mean']:.1f} °C on average). "
    f"Despite moderate shear it intensified by {o['max_24h_change'][2]} kt in 24 hours, became a hurricane early on 8 October and a Category 3 hurricane of {o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph) on 9 October. "
    "Deep-layer shear of 30–40 kt then tilted and weakened it, and it made landfall near Destin, Florida, at 0130 UTC on 10 October (8:30 p.m. CDT on 9 October) as a Category 2 hurricane with 90 kt (105 mph) winds. "
    "It caused at least six deaths, power cuts to as many as 930,000 customers, storm surge of 5.6 ft above high tide at Panama City Beach and up to 13 inches of rain in Alabama; insured losses were estimated at about $2–4.5 billion. "
    "A rapid attribution study estimated that climate change made the Gulf waters it crossed about 1.4 °C warmer.</p>")})
S.append({'id': 'findings', 'title': 'Main findings', 'html': (
    "<ol>"
    f"<li><b>Exceptionally warm Gulf.</b> Ahead of Isaias the sea averaged {pre['sst_mean']:.1f} °C and reached {pre['sst_max']:.1f} °C, {pre['ssta_mean']:+.1f} °C against normal on average.</li>"
    f"<li><b>Rapid intensification under moderate shear.</b> Winds rose from {F['2026-10-07 00:00'][3]} kt to {o['peak_kt']} kt between 7 and 9 October, with the vortex tilted by westerly to southwesterly shear throughout {d(7)}, {d(10)}.</li>"
    f"<li><b>Shear before landfall.</b> On 9 October deep-layer shear rose to 30–40 kt; dropsondes showed winds dropping sharply near the surface, and Isaias came ashore at 90 kt rather than its 105 kt peak {d(13)}, {d(14)}.</li>"
    "<li><b>Impacts.</b> Wind damage across the Florida Panhandle and southern Alabama; storm surge 5.59 ft above MHHW at Panama City Beach Pier; 12.97 inches of rain at Bellwood, Alabama; at least six deaths; tornadoes in Georgia and the Carolinas.</li>"
    f"<li><b>El Niño season.</b> Atlantic ACE was only 18% of normal for the date {c('csu')}, as expected when El Niño raises shear over the Atlantic {c('gray1984')}; the Gulf was the exception.</li>"
    "</ol>")})
S.append({'id': 'intro', 'title': '1. Introduction', 'html': (
    f"<p>El Niño tends to suppress Atlantic hurricanes by increasing vertical wind shear over the tropical Atlantic and Caribbean {c('gray1984')}. In 2026, during a very strong El Niño {c('paper4')}, the season produced eight named storms before its first hurricane; by 22 October its accumulated cyclone energy was 19.5 × 10⁴ kt² against a normal of 110.4 {c('csu')}. "
    f"Isaias, the ninth named storm, became the first hurricane only on 8 October, the latest date for a first Atlantic hurricane in 121 years {c('accu')}. This paper reconstructs how it intensified over the Gulf, why it weakened before landfall, and what it did on land.</p>")})
S.append({'id': 'methods', 'title': '2. Data and methods', 'html': METHODS.format(agency='National Hurricane Center')})
S.append({'id': 'lifecycle', 'title': '3. Life cycle', 'html': (
    fig(N, 'Figure 1. Isaias: 1-minute maximum wind and minimum pressure (top; shading marks rapid intensification) and sea-surface temperature at each position three days before the storm arrived, with its anomaly against 1991–2020 (bottom).')
    + f"<p><b>Genesis (4–7 October).</b> IBTrACS follows a low that sat almost stationary near {pos(*o['genesis'])}, in the southwestern Gulf off Tamaulipas and Veracruz, from {dtm(o['first'])}. It became Tropical Depression Nine at 2100 UTC on 6 October and drifted slowly east within weak steering south of an upper trough over the southeastern United States {d(1)}, {d(2)}. Early on 7 October its circulation was still broad {d(3)}; that morning an Air Force aircraft found the centre re-forming farther north, closer to the mid-level centre, a structural change that forecasters expected could allow rapid intensification {d(4)}.</p>"
    f"<p><b>Intensification (7–9 October).</b> By the afternoon of 7 October aircraft found 61 kt at 700 mb and 994 mb {d(5)}; that evening the pressure was 988 mb and the eyewall was open to the southwest, with outflow restricted by moderate shear {d(6)}. A dropsonde with a 76 kt boundary-layer wind made Isaias a hurricane at 0330 UTC on 8 October {d(7)}; tail Doppler radar on a NOAA P-3 showed a vortex tilted northward with height {d(7)}. "
    f"Later on 8 October the first satellite-visible eye of the 2026 Atlantic season appeared {d(9)}, although microwave data still showed a tilted vortex under southwesterly shear {d(10)}. Overnight the eyewall contracted and the eye warmed; aircraft found 107 kt at flight level {d(11)}, and on the morning of 9 October 120 kt at 700 mb, making Isaias a major hurricane of 105 kt {d(12)}.</p>"
    f"<p><b>Weakening and landfall (9–10 October).</b> As Isaias accelerated north, deep-layer southwesterly shear increased to 30–40 kt; radar showed the convection confined to the northern eyewall, and dropsondes showed a sharp drop-off of wind towards the surface, supporting 90–95 kt {d(13)}. Isaias made landfall near Destin at 0130 UTC on 10 October with 90 kt winds {d(14)}; NWS Tallahassee estimated 971 mb {c('tae')}. It weakened very rapidly over Alabama and became post-tropical by the morning of 10 October {d(15)}; its remnant brought heavy rain to the southern Appalachians, the Southeast and the Mid-Atlantic until 11 October {d(19)}.</p>"),
    'table': {'cols': ['Quantity', 'Value'], 'rows': facts(N, [('Landfall', 'near Destin, Florida, 0130 UTC 10 Oct, 90 kt (NHC), about 971 mb (NWS Tallahassee estimate)')]),
              'note': 'IBTrACS v04r01, provisional (operational NHC values). IBTrACS shows 95 kt at 0000 UTC 10 Oct, the last fix before landfall.'}})
S.append({'id': 'environment', 'title': '4. Environment', 'html': (
    f"<p><b>Ocean.</b> The water along Isaias's track was {pre['sst_mean']:.1f} °C on average three days before it arrived and up to {pre['sst_max']:.1f} °C, with anomalies of +0.5 to {pre['ssta_max']:+.1f} °C. Climate Central's rapid analysis found waters above 31 °C over the area of rapid intensification and estimated that climate change made them 1.4 °C warmer and 4 to 600 times more likely {c('cc')}. "
    f"The cold wake was modest (up to {abs(pre['wake_min']):.1f} °C) because Isaias moved quickly over the central Gulf {c('price1981')}.</p>"
    f"<p><b>Shear.</b> Isaias intensified under moderate westerly to southwesterly shear, with a vortex tilted with height and an eyewall repeatedly open on the southwest side {d(6)}, {d(7)}, {d(10)}; the warm water appears to have outweighed the shear until 9 October. The final increase in shear, to 30–40 kt, was forecast; the hurricane centre noted that a delay of about six hours in its onset could have brought a stronger landfall {d(11)}, {d(13)}.</p>"
    f"<p><b>ERA5 shear.</b> Deep-layer shear around Isaias was {shear_between(N, '2026-10-07', '2026-10-08 18')[0]:.0f}–{shear_between(N, '2026-10-07', '2026-10-08 18')[1]:.0f} kt on 7–8 October, while it intensified rapidly, and {shear_between(N, '2026-10-09', '2026-10-09 18')[1]:.0f} kt on 9 October, rising to {shear_between(N, '2026-10-10', '2026-10-10 18')[1]:.0f} kt at landfall (Figure 1), consistent with the 30–40 kt cited by forecasters. Rapid intensification under 16–19 kt of shear is unusual and underlines how much the warm Gulf contributed.</p>"
    f"<p><b>MJO.</b> The RMM index was in phase {m6[0]} (amplitude {m6[1]:.1f}) at genesis and phase {m8[0]} ({m8[1]:.1f}) during intensification. Atlantic and Gulf activity varies strongly with MJO phase {c('klotzbach2010')}; whether this phase helped Isaias is not tested here.</p>")})
S.append({'id': 'impacts', 'title': '5. Impacts', 'html': (
    f"<p><b>Wind.</b> Hurricane-force winds damaged roofs and buildings along the coast; preliminary observations include a gust of 117 mph at Oriole Beach {c('accu')} and 79 kt (91 mph) at Choctaw Beach, with 63 kt sustained at Panama City Beach {c('tae')}. As many as 930,000 customers lost power at the peak {c('accu')}; Santa Rosa, Holmes, Washington and Walton counties each had more than 80% of residents without power {c('npr')}. NASA's night-lights imagery showed much of the Pensacola area dark on 11 October {c('nasa')}.</p>"
    f"<p><b>Water.</b> The highest gauge reading was 5.59 ft above mean higher high water at Panama City Beach Pier, with 3.58 ft at Apalachicola {c('tae')}; landfall came about two hours before high tide, which limited the surge {c('npr')}. Rain reached 12.97 inches at Bellwood, Alabama, and 12.47 inches at DeFuniak Springs, Florida, with 4–8 inches across much of the region {c('tae')}.</p>"
    f"<p><b>Tornadoes and casualties.</b> The remnant produced 23 tornado reports in Georgia and the Carolinas, with at least seven confirmed (EF0–EF1) {c('accu')}. At least four deaths were confirmed by 11 October: two in Escambia County, Florida (a falling tree; carbon-monoxide poisoning from a generator), and two in Alabama (Jefferson and Barbour counties) {c('npr')}; at least six were reported by 14 October {c('accu')}. No deaths were reported in the NWS Tallahassee area {c('tae')}.</p>"
    f"<p><b>Losses.</b> Moody's RMS estimated insured losses of $2.5–4.5 billion (best estimate $3.5 billion), mostly from wind; other modellers ranged from $1–2 billion (Verisk) to $3 billion (KCC) {c('artemis')}.</p>")})
S.append({'id': 'climate', 'title': '6. Climate context', 'html': (
    f"<p>Two climate signals pulled in opposite directions. El Niño's shear suppressed the Atlantic season as a whole {c('gray1984')}, {c('csu')}, but the Gulf of Mexico was exceptionally warm, and the one storm that formed there in early October found enough heat to intensify rapidly. "
    f"Climate Central's analysis attributes about 1.4 °C of the Gulf warmth to climate change and estimates about 7 mph of additional wind, without a change of category {c('cc')}. This is a rapid, model-based estimate that has not been peer reviewed; it supports a contribution of climate change to the storm's energy supply, not a claim that climate change caused the hurricane.</p>")})
S.append({'id': 'uncertainty', 'title': '7. Uncertainties', 'html': (
    "<ul><li>Track, peak intensity and landfall values are provisional until NHC's Tropical Cyclone Report.</li>"
    "<li>Observed gusts and surge are preliminary; instruments may have failed or missed the peak.</li>"
    "<li>Death tolls differed between sources and over time; the six cited is a press tally.</li>"
    "<li>Insured-loss estimates are modelled and vary by a factor of about two.</li></ul>")})
S.append({'id': 'conclusion', 'title': '8. Conclusion', 'html': (
    "<p>Isaias shows that a suppressed season can still produce a damaging hurricane where the ocean is warm enough. Over a Gulf about 2 °C warmer than normal it intensified rapidly despite moderate shear, and only a well-timed increase in shear before landfall kept it to Category 2 at the coast. "
    "Its effects, from wind damage and outages to inland flooding and tornadoes, extended far beyond the landfall point.</p>")})
EVID = [
    ['ERA5 deep-layer shear', f"{shear_between(N, '2026-10-07', '2026-10-08 18')[0]:.0f}–{shear_between(N, '2026-10-07', '2026-10-08 18')[1]:.0f} kt during RI; {shear_between(N, '2026-10-10', '2026-10-10 18')[1]:.0f} kt at landfall", 'Moderate shear tolerated; strong shear weakened Isaias before landfall', 'Reanalysis (ERA5)', 'High', c('hersbach2020')],
    ['Very warm Gulf', f"SST {pre['sst_mean']:.1f} °C ({pre['ssta_mean']:+.1f}) along the track; >31 °C over the RI area", 'Main energy source for rapid intensification', 'Observed (OISST); attribution study', 'High', f"{c('huang2021')} {c('cc')}"],
    ['Centre re-formation', '7 Oct, closer to the mid-level centre', 'Allowed intensification to begin', 'Aircraft observation (NHC)', 'Medium', c('nhc')],
    ['Moderate shear', 'Westerly to southwesterly, tilted vortex 7–8 Oct', 'Slowed but did not stop intensification', 'Aircraft radar, microwave (NHC)', 'High', c('nhc')],
    ['Strong shear before landfall', '30–40 kt on 9 Oct', 'Weakened Isaias from 105 to 90 kt', 'Operational analysis; dropsondes', 'High', c('nhc')],
    ['El Niño shear over the Atlantic', 'Atlantic ACE 18% of normal', 'Delayed the first hurricane; not decisive in the Gulf', 'Climatological reasoning', 'Medium', f"{c('gray1984')} {c('csu')}"],
    ['Climate change', 'Gulf waters ~1.4 °C warmer (rapid estimate)', 'Added energy; ~7 mph more wind', 'Model-based rapid attribution', 'Medium', c('cc')],
]
paper = dict(storm=N, order=4, file='tc-2026-isaias.html', short='Hurricane Isaias (2026)', card_line='Atlantic · Cat 3 · 4–11 Oct',
             title='Hurricane Isaias (October 2026): the late first hurricane of a suppressed Atlantic season', basin_name='North Atlantic (Gulf)',
             description='Research paper on Hurricane Isaias, Gulf of America / Mexico and Florida Panhandle, October 2026.', status='draft', research_date='24 October 2026',
             obs_cutoff='IBTrACS to 11 Oct; NHC discussions 1–20; NWS report of 11 Oct; press to 16 Oct', track_source='IBTrACS v04r01 (provisional, NHC operational)',
             status_note='Draft for review (24 Oct 2026). Built from provisional data; to be checked against NHC\'s Tropical Cyclone Report when published.',
             toc=[(s['id'], s['title']) for s in S] + [('evidence', 'Evidence table'), ('references', 'References')], sections=S, evidence=EVID, references=R)
(ROOT / 'tc2026/isaias.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', sum(len(s['html'].split()) for s in S), 'words')
