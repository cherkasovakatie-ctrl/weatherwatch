"""Paper: Hurricane Rachel (eastern Pacific, 25 September – 11 October 2026)."""
import json

from common import METHODS, ROOT, T, dtm, env, facts, fig, kt2mph, mjo, pos, refs, sst_summary

N = 'RACHEL'; o = T[N]
pre = sst_summary(N, until='2026-10-02 00:00'); s_all = sst_summary(N)
E = {r['time'][:13]: r for r in env(N)}
late = [E[k] for k in sorted(E) if '2026-10-06' <= k <= '2026-10-09 18']
late_sst = sum(float(r['sst_pre_c']) for r in late) / len(late); late_a = sum(float(r['ssta_pre_c']) for r in late) / len(late)
wk = min(env(N), key=lambda r: float(r['sst_wake_c']) if r['sst_wake_c'] not in ('nan', '') else 9)
m27, m01 = mjo('2026-09-27'), mjo('2026-10-01')
F = {f[0]: f for f in o['fixes']}
NHC = 'https://www.nhc.noaa.gov/archive/2026/ep18/ep182026.discus.{:03d}.shtml'
d = lambda n: f'<a href="{NHC.format(n)}">NHC discussion {n}</a>'  # noqa: E731
KEYS = ['knapp2010', 'kaplan2003', 'huang2021', 'wheeler2004', 'price1981', 'maloney2000', 'csu', 'paper4']
EXTRA = [('nhc', 'National Hurricane Center: Hurricane Rachel (EP182026) advisory archive, forecast discussions 1–58, 27 September – 11 October 2026 (US Government, public domain). Text copies in data/tc2026/nhc/RACHEL/.', 'https://www.nhc.noaa.gov/archive/2026/RACHEL.shtml', 'read in full'),
         ('ap13', 'Associated Press (2026). Death toll rises to 6 as Hurricane Simon and Rachel remnants unleash floods in Mexico. 13 October 2026 (via ITV News).', 'https://www.itv.com/news/2026-10-13/hurricane-remnants-unleash-deadly-floods-in-mexico-killing-at-least-6', 'read'),
         ('star16', 'Reuters/Bernama (2026). Death toll from Tropical Storm Rachel rises to 8 in northwestern Mexico. 16 October 2026 (via The Star).', 'https://www.thestar.com.my/news/world/2026/10/16/death-toll-from-tropical-storm-rachel-rises-to-8-in-northwestern-mexico', 'read'),
         ('kelvin', 'Global Weather Watch (2026). El Niño\'s coastal wave reaches California (event log; Los Angeles tide-gauge residuals, NOAA CO-OPS).', 'events.html', 'own analysis')]
R = refs(KEYS, EXTRA); ref = {r['key']: i + 1 for i, r in enumerate(R)}
c = lambda k: f'<a href="#ref-{k}">[{ref[k]}]</a>'  # noqa: E731

S = []
S.append({'id': 'abstract', 'title': 'Abstract', 'html': (
    f"<p>Rachel was a long-lived eastern Pacific hurricane whose most damaging effects came after it had stopped being a hurricane. "
    f"It formed south of Mexico on 27 September, strengthened slowly through days of 15–20 kt northeasterly shear, intensified rapidly by {o['max_24h_change'][2]} kt in 24 hours near Socorro Island and peaked at {o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph, Category 3) and {o['min_pres']} mb at {dtm(o['peak_time'])}. "
    f"It then remained a hurricane for six more days while drifting west over water that was unusually warm for the latitude (about {late_sst:.0f} °C, {late_a:+.1f} °C against normal), before a deep trough swept it northeast. "
    "As a post-tropical cyclone it crossed northern Baja California near Ensenada early on 11 October with winds near 50 kt and dissipated over the southwestern United States the same day. "
    "Flooding in the municipality of Ensenada killed eight people, and Rachel's waves, combined with a long-period swell, spring tides and sea levels already raised by El Niño, caused coastal flooding and erosion in Southern California.</p>")})
S.append({'id': 'findings', 'title': 'Main findings', 'html': (
    "<ol>"
    f"<li><b>Strengthening against shear.</b> For four days Rachel's centre lay at the northern edge of its convection under about 20 kt of northeasterly shear {d(6)}, {d(10)}, yet it became a hurricane at {dtm(o['first_hu'])} and then rapidly intensified, from {F['2026-10-01 00:00'][3]} kt to {o['peak_kt']} kt in 24 hours.</li>"
    f"<li><b>Long hurricane life.</b> Rachel spent {o['hours_hu']} hours as a hurricane and produced {o['ace']:.1f} × 10⁴ kt² of ACE, as much as Simon. Repeated dry-air intrusions caused fluctuations but not collapse {d(32)}, {d(38)}.</li>"
    f"<li><b>A strong cold wake.</b> Moving slowly, Rachel cooled the sea under its track by up to {abs(s_all['wake_min']):.1f} °C in the analysis, near {pos(wk['lat'], float(wk['lon']) - 360)} on {dtm(wk['time'])}.</li>"
    "<li><b>Deadliest as a remnant.</b> All eight deaths occurred in Ensenada, Baja California, after Rachel had become post-tropical; four of the dead were children.</li>"
    "<li><b>Compound coastal hazard.</b> In Southern California, waves from Rachel met a long-period southerly swell and water levels running up to 1.5 ft above predictions.</li>"
    "</ol>")})
S.append({'id': 'intro', 'title': '1. Introduction', 'html': (
    "<p>Rachel was the eighteenth tropical cyclone of the 2026 eastern North Pacific season and the second of four major hurricanes off southwestern Mexico between 22 September and 16 October. "
    "Its track, first parallel to Mexico and then west and northeast towards Baja California, linked the hyperactive tropical season to the coastal ocean off California, where El Niño had already raised sea level " + c('kelvin') + ". "
    "This paper reconstructs Rachel's life cycle and the chain of events that turned a weakening storm into a deadly one.</p>")})
S.append({'id': 'methods', 'title': '2. Data and methods', 'html': METHODS.format(agency='National Hurricane Center')})
S.append({'id': 'lifecycle', 'title': '3. Life cycle', 'html': (
    fig(N, 'Figure 1. Rachel: 1-minute maximum wind and minimum pressure (top; shading marks rapid intensification) and sea-surface temperature at each position three days before the storm arrived, with its anomaly against 1991–2020 (bottom). The final rise in wind on 10–11 October is post-tropical.')
    + f"<p><b>Genesis and a sheared start (25–30 September).</b> IBTrACS follows the precursor from {dtm(o['first'])} near {pos(*o['genesis'])}. The depression formed early on 27 September; SHIPS guidance suggested shear would limit development at first {d(1)}. For the next three days Rachel endured about 20 kt of northeasterly shear, with its low-level centre near the northern edge of the convection {d(4)}, {d(6)}, {d(10)}. It strengthened anyway, helped by bursts of very deep convection with cloud tops near −90 °C {d(10)}. On 29 September a NOAA P-3 research flight, with an uncrewed aircraft launched into the storm, measured 66 kt at 700 mb {d(11)}.</p>"
    f"<p><b>Peak near Socorro Island (30 September – 2 October).</b> Rachel became a hurricane at {dtm(o['first_hu'])}. As the shear relaxed it intensified from {F['2026-10-01 00:00'][3]} kt to {o['peak_kt']} kt between 0000 UTC on 1 and 2 October, with a ragged eye inside cloud tops near −85 °C {d(20)}, and passed closest to Socorro Island on 2 October {d(22)}. Dry air already affected a loose eyewall {d(22)}.</p>"
    f"<p><b>Six days as a weakening hurricane (2–8 October).</b> A ridge to the north steered Rachel slowly west {d(26)}, {d(30)}. Its eye cleared and filled several times as northeasterly shear brought dry air into the northern side {d(32)}, {d(34)}, {d(38)}, {d(42)}. Winds varied between 65 and 90 kt; Rachel fell below hurricane strength only on 8–9 October.</p>"
    f"<p><b>Recurvature and post-tropical transition (8–11 October).</b> A deep mid- to upper-level trough approaching the west coast of the United States slowed Rachel, then turned it northeast and accelerated it {d(44)}, {d(48)}, {d(49)}. Under 25–35 kt of southwesterly shear its convection became shallow and frontal in structure {d(54)}, and at 0300 UTC on 11 October it was declared post-tropical {d(56)}. Its winds increased again to 50–55 kt through baroclinic interaction with the trough. The centre crossed northern Baja California near {pos('31.8', '-116.3')} around 0600 UTC on 11 October and the system dissipated over the southwestern United States {d(58)}.</p>"),
    'table': {'cols': ['Quantity', 'Value'], 'rows': facts(N, [('Post-tropical crossing of northern Baja California', 'about 0600 UTC 11 Oct near 31.8°N, 116.3°W, ~50 kt (IBTrACS)')]),
              'note': 'IBTrACS v04r01, provisional (operational NHC values). ACE includes the post-tropical fixes of 10–11 October as stored in IBTrACS.'}})
S.append({'id': 'environment', 'title': '4. Environment', 'html': (
    f"<p><b>Ocean.</b> Up to the peak the sea ahead of Rachel averaged {pre['sst_mean']:.1f} °C, {pre['ssta_mean']:+.1f} °C above normal. During its long westward drift on 6–9 October the water was about {late_sst:.1f} °C, cooler but still {late_a:+.1f} °C above normal for the season and latitude, part of the warm anomaly off Baja California. "
    f"Near Baja California on 11 October the sea was {float(E['2026-10-11 00']['sst_pre_c']):.1f} °C, {float(E['2026-10-11 00']['ssta_pre_c']):+.1f} °C above normal: too cool to sustain a hurricane, but an exceptional marine heatwave. "
    f"Rachel's slow motion produced the strongest cold wake of the storms in this batch: up to {abs(s_all['wake_min']):.1f} °C {c('price1981')}. The wake it left near 14°N, 102°W on 29 September was still visible two weeks later under Trudy (see the Trudy paper).</p>"
    f"<p><b>Shear and moisture.</b> Northeasterly shear of 15–20 kt persisted from 27 September to 30 September {d(6)}, {d(14)}; dry air intruded repeatedly after the peak {d(26)}, {d(32)}, {d(34)}; strong southwesterly shear accompanied the transition {d(54)}.</p>"
    f"<p><b>MJO.</b> RMM phase {m27[0]} (amplitude {m27[1]:.1f}) at genesis and phase {m01[0]} ({m01[1]:.1f}) during rapid intensification {c('maloney2000')}; not tested further.</p>")})
S.append({'id': 'impacts', 'title': '5. Impacts', 'html': (
    f"<p><b>Baja California.</b> Heavy rain from Rachel's remnant caused flooding and landslides in the municipality of Ensenada over the weekend of 10–11 October and knocked out power; a stream in the Buena Vista community overflowed, sweeping away vehicles, animals and a cabin {c('ap13')}. "
    f"By 15 October the death toll was eight, all in Ensenada, four of them minors, with two people still missing {c('star16')}. Soldiers rescued 32 people, including 13 children, by helicopter from an orphan camp near Ensenada; a father and son fishing from San Felipe on the Gulf of California were missing {c('ap13')}.</p>"
    f"<p><b>Southern California.</b> The hurricane centre warned that waves from Rachel, combined with an incoming long-period southerly swell, would produce life-threatening surf and rip currents, and that major coastal flooding was already occurring, with water levels running up to 1.5 ft above predictions; flooding and erosion were expected to worsen as the highest waves coincided with high tides {d(54)}. "
    f"The elevated water levels reflect El Niño's coastally trapped wave and the warm ocean along the coast {c('kelvin')}. The remnant then brought a risk of flash flooding to the southwestern United States {d(58)}.</p>")})
S.append({'id': 'climate', 'title': '6. Climate context', 'html': (
    "<p>Rachel's long life at 20°N and its deadly remnant both depended on an ocean that was much warmer than usual off western Mexico and Baja California, during a very strong El Niño " + c('paper4') + " and an exceptionally active season " + c('csu') + ". "
    "The Southern California coastal flooding was a compound event: storm waves, a distant swell, spring tides and a sea level raised by El Niño. No attribution study exists.</p>")})
S.append({'id': 'uncertainty', 'title': '7. Uncertainties', 'html': (
    "<ul><li>Provisional track and intensities; the post-tropical crossing point and time are approximate.</li>"
    "<li>The deaths were caused by flash flooding from the remnant; rainfall totals were not available.</li>"
    "<li>The size of Rachel's contribution to the Southern California coastal flooding, relative to the swell, tides and El Niño sea level, was not quantified.</li></ul>")})
S.append({'id': 'conclusion', 'title': '8. Conclusion', 'html': (
    "<p>Rachel strengthened despite persistent shear, peaked briefly as a major hurricane over open water and lingered as a hurricane for almost a week over an ocean warmed by El Niño. "
    "Its greatest harm came later, as a fast-moving post-tropical cyclone whose rain flooded Ensenada and whose waves reached a Southern California coast already running high. The case shows why post-tropical remnants deserve the same attention as the hurricane itself.</p>")})
EVID = [
    ['Warm ocean', f"{pre['sst_mean']:.1f} °C ({pre['ssta_mean']:+.1f}) before the peak; {late_sst:.1f} °C ({late_a:+.1f}) on 6–9 Oct", 'Allowed strengthening and a long hurricane life', 'Observed (OISST)', 'High', c('huang2021')],
    ['Northeasterly shear', '~20 kt, 27–30 Sep', 'Slowed early development', 'Operational analysis', 'High', c('nhc')],
    ['Dry-air intrusions', 'Repeated after the peak', 'Caused fluctuations and slow weakening', 'Satellite interpretation (NHC)', 'Medium', c('nhc')],
    ['Mid-latitude trough', 'Approached the US west coast 8–10 Oct', 'Recurvature, acceleration and post-tropical transition', 'Operational analysis', 'High', c('nhc')],
    ['Marine heatwave off Baja California', f"SST anomaly {float(E['2026-10-11 00']['ssta_pre_c']):+.1f} °C on 11 Oct", 'Moisture supply to the remnant (inferred)', 'Observed SST; mechanism inferred', 'Low', c('huang2021')],
    ['Elevated sea level and swell', 'Water levels up to 1.5 ft above predictions', 'Compound coastal flooding in Southern California', 'Observed (NHC statement)', 'High', f"{c('nhc')} {c('kelvin')}"],
]
paper = dict(storm=N, order=5, file='tc-2026-rachel.html', short='Hurricane Rachel (2026)', card_line='E. Pacific · Cat 3 · 25 Sep–11 Oct',
             title='Hurricane Rachel (September–October 2026): a long-lived hurricane and a deadly remnant', basin_name='Eastern North Pacific',
             description='Research paper on Hurricane Rachel, eastern Pacific, September–October 2026.', status='draft', research_date='24 October 2026',
             obs_cutoff='IBTrACS to 11 Oct; NHC discussions 1–58; press to 16 Oct', track_source='IBTrACS v04r01 (provisional, NHC operational)',
             status_note='Draft for review (24 Oct 2026). Built from provisional data; to be checked against NHC\'s Tropical Cyclone Report when published.',
             toc=[(s['id'], s['title']) for s in S] + [('evidence', 'Evidence table'), ('references', 'References')], sections=S, evidence=EVID, references=R)
(ROOT / 'tc2026/rachel.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', sum(len(s['html'].split()) for s in S), 'words')
