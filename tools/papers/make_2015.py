"""Assemble papers/3-enso-2015-16.json (Paper 3): references, monthly data, timeline, evidence table (and prose when ready).

Journal references are formatted from their Crossref records (data/papers/2015/refs_crossref.json, retrieved 23 Oct 2026 by
tools/papers/refcheck.py), so authors, volume and pages are never typed by hand; the "check" note records what was read.
Monthly values come from the site's CPC/PMEL/NCEI data files.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
D15 = ROOT / 'data' / 'papers' / '2015'


def load(f, key):
    with open(ROOT / 'data' / f, encoding='utf-8') as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


sm, oni, at, sub, dr = (load('sst_monthly.csv', 'month'), load('oni.csv', 'centre_month'), load('atmosphere_monthly.csv', 'month'),
                        load('enso_subsurface.csv', 'month'), load('drivers_monthly.csv', 'month'))
rows = []
for y in range(2013, 2017):
    for m in range(1, 13):
        k = f'{y}-{m:02d}'
        if k < '2013-07':
            continue

        def g(d, col, k=k):
            return d.get(k, {}).get(col) or '—'
        rows.append([k, oni.get(k, {}).get('season', '—'), g(oni, 'roni'), g(oni, 'oni'), g(sm, 'rel_nino34'), g(sm, 'nino34'), g(sm, 'nino12'), g(sm, 'nino4'),
                     g(at, 'soi'), g(at, 'trades_west'), g(at, 'trades_central'), g(at, 'olr_central_pac'), g(sub, 'heat_180_100w'), g(sub, 'wwv_anom'),
                     g(dr, 'dmi_cpc'), g(dr, 'pdo')])
rows = [[r[0]] + [f'<span class="num">{x}</span>' for x in r[1:]] for r in rows]

CR = json.load(open(D15 / 'refs_crossref.json', encoding='utf-8'))


def initials(given):
    parts = given.replace('-', ' -').split()
    return ' '.join(p[0] + '.' if not p.startswith('-') else '-' + p[1] + '.' for p in parts if p.strip('-'))


def authors(lst):
    names = []
    for i, a in enumerate(lst):
        fam, _, giv = a.partition(', ')
        names.append(f'{fam}, {initials(giv)}' if i == 0 else f'{initials(giv)} {fam}')
    if len(names) > 6:
        return names[0] + ', et al.'
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def cr(key, check):
    r = CR[key]
    vol = f" {r['volume']}" if r['volume'] else ''
    pg = f", {r['page'].replace('-', '–')}" if r['page'] else ''
    jr = f" <i>{r['journal']}</i>{vol}{pg}." if r['journal'] else ''
    return (key, f"{authors(r['authors'])} ({r['year']}). {r['title']}.{jr}", r['doi'], None, check)


AB = 'abstract read'
BIB = 'bibliographic record (no abstract available)'
refs = [
 ("noaa2026", "NOAA National Weather Service (2026). Public Information Notice 26-05: Relative Oceanic Niño Index (RONI), effective 1 February 2026.", None, "https://weather.gov/media/notification/pdf_2026/pns26-05_Relative_ONI.pdf", "read"),
 ("lheureux2024", "L'Heureux, M. L., et al. (2024). A relative sea surface temperature index for classifying ENSO events in a changing climate. <i>Journal of Climate</i> 37, 1197–1211.", "10.1175/JCLI-D-23-0406.1", None, AB),
 ("cpc", "NOAA Climate Prediction Center: monthly index files (RONI, ONI, relative and traditional Niño indices, SOI, 850 hPa trade-wind indices, OLR, upper-300 m heat content, IOD); NOAA PMEL warm water volume; PDO (NOAA NCEI). Site copies in the data archive.", None, "https://www.cpc.ncep.noaa.gov/data/indices/", "data read"),
 ("gvp", "Global Volcanism Program, Smithsonian Institution: Volcanoes of the World, confirmed eruptions (snapshot of April 2020 distributed by rfordatascience/tidytuesday, 2020-05-12).", None, "https://volcano.si.edu/", "data read"),
 ("taodata", "NOAA PMEL Global Tropical Moored Buoy Array (TAO/TRITON): daily 20 °C isotherm depth and surface winds on the equator, 147°E–95°W, Jul 2013 – Dec 2016 (ERDDAP pmelTaoDyIso, pmelTaoDyW). Analysis: tools/papers/tao_2015.py; outputs in data/papers/2015/.", None, "https://www.pmel.noaa.gov/gtmba/", "data read and processed"),
 ("r1diag", "NCEP/NCAR Reanalysis 1 daily winds and NOAA interpolated OLR (via NOAA PSL THREDDS) and the NOAA PSL OLR MJO Index (OMI): westerly-burst and MJO diagnostics for Jul 2013 – Dec 2016 on the definitions of Papers 1 and 2, climatology and EOFs fixed to 1979–2000/2001 (tools/papers/event_diag.py, diag_2015.py; outputs in data/papers/2015/).", None, "https://psl.noaa.gov/mjo/mjoindex/", "data read and processed"),
 ("meinen2000", "Meinen, C. S., and M. J. McPhaden (2000). Observations of warm water volume changes in the equatorial Pacific and their relationship to El Niño and La Niña. <i>Journal of Climate</i> 13, 3551–3559.", "10.1175/1520-0442(2000)013<3551:OOWWVC>2.0.CO;2", None, AB),
 ("chiodi2014", "Chiodi, A. M., D. E. Harrison and G. A. Vecchi (2014). Subseasonal atmospheric variability and El Niño waveguide warming: observed effects of the Madden–Julian oscillation and westerly wind events. <i>Journal of Climate</i> 27, 3619–3642.", "10.1175/JCLI-D-13-00547.1", None, AB),
 ("eisenman2005", "Eisenman, I., L. Yu and E. Tziperman (2005). Westerly wind bursts: ENSO's tail rather than the dog? <i>Journal of Climate</i> 18, 5224–5238.", "10.1175/JCLI3588.1", None, AB),
 ("li2023", "Li, L., et al. (2023). Comparison of Madden–Julian oscillation in three super El Niño events. <i>Frontiers in Earth Science</i> 10, 1021953.", "10.3389/feart.2022.1021953", None, "full text read (open access; private library copy)"),
 cr('santoso2017', AB), cr('lheureux2017', AB), cr('xuekumar2017', AB), cr('huang2016rank', AB), cr('paek2017', AB), cr('menkes2014', AB), cr('hufedorov2016', AB), cr('levine2016', AB), cr('chiodiharrison2017', AB), cr('zhu2016', AB), cr('lian2014', AB), cr('liang2021gl', AB), cr('liang2025', AB), cr('hong2014', AB),
 cr('bond2015', AB), cr('dilorenzo2016', BIB), cr('tseng2017', AB),
 cr('lim2017iod', AB), cr('stuecker2017', AB), cr('stuecker2013', BIB), cr('mcgregor2012', AB),
 cr('gasparin2016', AB), cr('hufedorov2017', AB), cr('kao2009', AB), cr('legler2014', AB), cr('smith2019', AB),
]
cite = {k: f'<a href="#ref-{k}">[{i + 1}]</a>' for i, (k, *_) in enumerate(refs)}


def c(*ks):
    return ' '.join(cite[k] for k in ks)


DG = json.load(open(D15 / 'diag_2015.json'))
import datetime as _dt  # noqa: E402


def fd(x):
    return _dt.date.fromisoformat(x).strftime('%-d %b %Y')


WB = {w['start']: w for w in DG['wwb']}
KW = DG['tao_kelvin_waves_2015']
TQ = DG['tao_data_return_quarterly']
NB14 = sum(1 for w in DG['wwb'] if w['start'][:4] == '2014')
NB15 = DG['wwb_count']['2015']
BM = DG['basin_mean_min_jun_jul_2014']

timeline = [
 ["Jul 2013 – Feb 2014", "ENSO-neutral, slightly cool (RONI −0.48 in JJA 2013, then −0.22 to −0.43 through DJF 2014); warm water volume positive throughout (+0.78 to +1.25 × 10¹⁴ m³). A strong warm anomaly forms in the NE Pacific in winter 2013–14 (the 'Blob'), the largest there since at least the 1980s.", "Recharged equatorial Pacific; the Blob from reduced ocean heat loss and weak cold advection under persistent high pressure.", c('cpc', 'meinen2000', 'bond2015'), "High"],
 ["Mid-2012 – mid-2014", f"TAO reporting declines sharply. In this analysis, daily equatorial wind records exist for only {TQ['2013-07']['wind_pct']:.0f}–{TQ['2014-01']['wind_pct']:.0f}% of site-days from July 2013 to March 2014 and {TQ['2014-04']['wind_pct']:.0f}% in April–June 2014, recovering to {min(TQ[q]['wind_pct'] for q in ('2014-10','2015-01','2015-04','2015-07')):.0f}–{max(TQ[q]['wind_pct'] for q in ('2014-10','2015-01','2015-04','2015-07')):.0f}% from October 2014 to September 2015.", "Observing-system gap exactly during the 2014 onset attempt; 2014 wind-forced ocean studies must fill gaps.", c('legler2014', 'chiodiharrison2017', 'taodata'), "High"],
 ["Jan – Mar 2014", f"Two strong westerly bursts: reanalysis {fd(WB['2014-01-24']['start'])} – {fd(WB['2014-01-24']['end'])} (+{WB['2014-01-24']['peak_anom_ms']} m s⁻¹ at {WB['2014-01-24']['peak_lon_E']:g}°E) and {fd(WB['2014-02-19']['start'])} – {fd(WB['2014-02-19']['end'])} (+{WB['2014-02-19']['peak_anom_ms']} m s⁻¹ at {WB['2014-02-19']['peak_lon_E']:g}°E). Heat content east of the Date Line rises from −0.33 °C (Jan) to +1.60 °C (Mar); warm water volume peaks at +2.05 × 10¹⁴ m³ in March; until April the warm pool is displaced east as at the onset of strong events; some models point to an extreme event.", "Burst-forced downwelling Kelvin waves on a recharged basin, as in early 1997.", c('r1diag', 'hufedorov2016', 'menkes2014', 'cpc'), "High"],
 ["Apr – Jun 2014", "No westerly wind events from April to June; the warm pool retreats to its usual position by July; RONI peaks at only +0.15 (AMJ) and falls to −0.14 (JJA).", "Lack of spring bursts limits eastern growth (contrast with 1997).", c('menkes2014', 'r1diag', 'cpc'), "High"],
 ["Early 2014", "Cold SST in the south-eastern Pacific and warm SST to the north (South Pacific meridional mode pattern); in forecast experiments about 40% of the peak-phase amplitude error comes from failing to predict the south-eastern cold anomalies.", "Meridional SST gradient drives strong meridional rather than zonal winds near the equator.", c('zhu2016'), "Medium (one model)"],
 ["Jun – Jul 2014", f"An unusually strong, basin-wide easterly wind burst in June; all major Niño indices fall to near normal; two separate warm centres persist. In the reanalysis the burst is broad rather than intense: the 150°E–100°W mean 1000 hPa anomaly reaches {BM[1]} m s⁻¹ on {fd(BM[0])}, the {DG['basin_mean_rank_of_that_day']}th-lowest day of the {DG['basin_mean_days_total']} analysed, but no 5 m s⁻¹ easterly burst meets the burst definition.", "Easterly burst suppresses the Bjerknes feedback, and also prevents, then reverses, the discharge of equatorial heat content.", c('hufedorov2016', 'levine2016', 'r1diag'), "High (observation + model experiments)"],
 ["Aug – Dec 2014", "Warm water volume rebuilds to +1.49 and +1.57 × 10¹⁴ m³ (Aug–Sep); RONI rises to +0.62 (NDJ 2014–15); ONI ≥ +0.5 from SON 2014. The 2014 event 'failed to qualify as an El Niño by conventional definitions'.", "Head start of equatorial heat content for 2015.", c('cpc', 'levine2016'), "High"],
 ["2014 – 2015", "The Blob persists for multiple years; PDO positive from 2014 (up to +1.86 in Dec 2014).", "An enhanced second ocean–atmosphere coupled mode (Victoria mode, forced by a North Pacific Oscillation-like pattern) proposed as the bridge to the 2015 El Niño, triggered from the Northern Hemisphere.", c('dilorenzo2016', 'tseng2017', 'cpc'), "Medium (one statistical study)"],
 ["Mar 2015", f"The strongest early-2015 burst: reanalysis {fd(WB['2015-03-04']['start'])} – {fd(WB['2015-03-04']['end'])}, +{WB['2015-03-04']['peak_anom_ms']} m s⁻¹ at {WB['2015-03-04']['peak_lon_E']:g}°E ({WB['2015-03-04']['lon_w']:g}°–{WB['2015-03-04']['lon_e']:g}°E), during an active MJO (OMI {WB['2015-03-04']['omi_amp_at_peak']:.2f}). TAO traces the downwelling Kelvin wave from 165°E on {fd(KW[0]['start_165E'])} to 110°W on {fd(KW[0]['last'])} ({KW[0]['days']} days, about {KW[0]['speed_ms']:.1f} m s⁻¹). Western-Pacific trade index −1.8; central-Pacific OLR −18.8 W m⁻².", "Burst-forced Kelvin wave on a still-charged basin.", c('r1diag', 'taodata', 'cpc'), "High"],
 ["Apr – Nov 2015", "Four downwelling Kelvin waves; eastward current anomalies advect the warm pool east in spring and summer; a large equatorial freshwater anomaly, beyond anything in the 2004–2014 Argo record, raises steric height in the west and accelerates eastward flow at the salinity front.", "Kelvin waves and advection initiate and enhance eastern-central warming.", c('xuekumar2017', 'gasparin2016', 'taodata'), "High"],
 ["May – Jul 2015", "Coupling established: RONI AMJ +0.89, MJJ +1.02, JJA +1.27; SOI −0.6 to −1.1; Niño 1+2 +1.34, +1.91, +2.48 °C; public El Niño advisories in the first half of 2015.", "Bjerknes feedback takes over.", c('cpc', 'lheureux2017'), "High"],
 ["Jun – Oct 2015", f"Bursts keep coming during growth: {sum(1 for w in DG['wwb'] if '2015-06-01' <= w['start'] <= '2015-10-31')} reanalysis bursts from late June to October, several centred east of the Date Line; calendar 2015 has {NB15}, the most of any year in 1979–2016.", "Bursts increasingly a response to the warming (state-dependent), reinforcing growth.", c('r1diag', 'eisenman2005', 'liang2021gl'), "High (count); medium (interpretation)"],
 ["Aug – Dec 2015", "Growth to the peak: RONI SON +2.03, OND +2.18, NDJ +2.25 (ONI +2.59); Niño 4 reaches a record +1.55 °C (Nov) while Niño 1+2 stays near +2 °C; enhanced convection displaced about 20° west of 1982 and 1997; the eastern thermocline anomaly near South America only a third to a half of theirs; central-Pacific OLR −49.9 W m⁻² in December.", "Westward-centred warming: eastern-Pacific dynamics plus stronger central-Pacific (subtropically forced) dynamics.", c('cpc', 'xuekumar2017', 'lheureux2017', 'paek2017'), "High"],
 ["Nov 2015", "An upwelling Kelvin wave emerges in early November, leading to a rapid decline; warm water volume turns negative in December (−0.39 × 10¹⁴ m³).", "Discharge begins.", c('xuekumar2017', 'cpc'), "High"],
 ["Jan – May 2016", "Decay: RONI JFM +1.81 → AMJ +0.08; WWV −1.26 to −3.36 × 10¹⁴ m³; warm SST lingers near the Date Line rather than retreating to the coast; demise in May 2016.", "Discharge; stronger central-Pacific dynamics in decay.", c('cpc', 'paek2017', 'lheureux2017'), "High"],
 ["Jun – Dec 2016", "Weak La Niña (RONI −0.43 MJJ to −0.96 SON/OND) with a strong negative Indian Ocean Dipole peaking in July–September 2016 (CPC DMI −0.89 °C in July).", "Negative IOD promoted the weak La Niña.", c('cpc', 'lim2017iod'), "High (observation); one model study (mechanism)"],
]

evidence = [
 ["Recharge carried over from 2014", "WWV positive from mid-2013; partial discharge in mid-2014 reversed after the easterly burst; WWV +0.31 to +1.25 × 10¹⁴ m³ in Jan–May 2015 (against +3.12 in Apr 1997).", "Retained heat content gave 2015 a head start.", "Precondition", "A−: observation + model analysis for this event", "High", c('cpc', 'levine2016', 'meinen2000')],
 ["Easterly wind burst, June–July 2014", "Strong basin-wide easterly anomaly; Niño indices fall; discharge prevented. Broad rather than intense in the reanalysis.", "Suppressed 2014 growth while preserving heat for 2015.", "Suppressor (2014) / indirect precondition (2015)", "A: observation + model experiments", "High", c('hufedorov2016', 'levine2016', 'r1diag')],
 ["Westerly wind events, 2014 and 2015", f"{NB14} reanalysis bursts in 2014 (two in Jan–Mar, none in Apr–Jun) against {NB15} in 2015 (the most of any year 1979–2016; 1997 had 16); four downwelling Kelvin waves Apr–Nov 2015. A wind-forced ocean model reproduces 2014 and 2015 SST from bursts and easterly surges alone.", "Burst sequence decides whether onset proceeds (2014 vs 2015 contrast).", "Trigger (2015); failed trigger (2014)", "A−: event observations + ocean simulations", "High", c('r1diag', 'menkes2014', 'chiodiharrison2017', 'xuekumar2017', 'lian2014')],
 ["South Pacific meridional SST gradient (2014)", "Cold south-east / warm north pattern in early 2014.", "Meridional rather than zonal winds near the equator damp growth.", "Suppressor (2014)", "B/C: one forecast-model study", "Medium", c('zhu2016')],
 ["North Pacific (Blob, Victoria mode, meridional mode)", "NE Pacific warm anomaly from winter 2013–14, multi-year; positive PDO 2014–16.", "North Pacific atmosphere → subtropical SST and winds → equatorial westerlies; 2015 triggered from the Northern Hemisphere, unlike the Southern Hemisphere 'booster' found for earlier super events.", "Possible precondition / trigger component", "B/C: one coupled-mode statistical study for this event; general hindcast study", "Medium–low", c('tseng2017', 'bond2015', 'liang2025', 'hong2014')],
 ["MJO", f"OMI active (≥ 1) on {fd(DG['omi_episodes_2015'][0]['start'])} – {fd(DG['omi_episodes_2015'][0]['end'])} and {fd(DG['omi_episodes_2015'][1]['start'])} – {fd(DG['omi_episodes_2015'][1]['end'])} (max {DG['omi_episodes_2015'][1]['max']}), framing the March and late-June bursts; intraseasonal OLR variance at 160°E–150°W in Oct 2015 – Mar 2016 nearly twice that of Oct 1996 – Mar 1997. In a model, El Niño-like SST shifts the MJO onto the equator and strengthens it in the central Pacific, favouring bursts; March MJO alone has limited impact on ENSO in hindcasts.", "MJO organises bursts; warming feeds back on the MJO.", "Trigger timing / feedback", "B: event indices + model experiments", "Medium", c('r1diag', 'liang2021gl', 'liang2025', 'li2023', 'chiodi2014')],
 ["Bjerknes feedback and central-Pacific dynamics", "Coupled growth from May 2015; record Niño 4 and westward-shifted convection; eastern thermocline anomaly a third to a half of 1982 and 1997.", "Eastern (thermocline) and central-Pacific (subtropically forced) dynamics combined.", "Amplifier / redirector of the pattern", "B: event observations + one model comparison", "Medium–high", c('xuekumar2017', 'paek2017', 'lheureux2017', 'kao2009')],
 ["Freshwater (salinity) anomaly 2015", "Large equatorial freshwater anomaly in 2015, beyond the 2004–2014 Argo record.", "Positive steric height in the west and eastward acceleration at the salinity front.", "Amplifier (ocean dynamics)", "B: event-specific budget", "Medium", c('gasparin2016')],
 ["Seasonal cycle in termination", "Southward shift of westerly anomalies in boreal winter is a key element of the termination of strong events.", "SPCZ-related weakening of climatological winds south of the equator.", "Termination mechanism", "B/C: general model studies; 2015–16 not isolated in the sources read", "Medium", c('mcgregor2012', 'stuecker2013')],
 ["Indian Ocean", "Weak positive DMI in Aug–Oct 2015 (+0.42 to +0.47 °C); strong negative IOD in mid-2016 promoting the weak La Niña.", "IOD phase largely set by ENSO combination-mode forcing; the 2016 negative IOD developed mainly from Indian Ocean conditions.", "Consequence (2015); influence on the transition (2016)", "B: event-specific forecast experiments (2016); theory (combination mode)", "Medium", c('cpc', 'lim2017iod', 'stuecker2017')],
 ["Volcanic forcing", "Tropical VEI 4 eruptions: Sinabung (Sep 2013, 3°N), Kelud (Feb 2014, 8°S) and Wolf (May 2015, 0°); none larger.", "No event-specific study links them to the 2014–16 evolution.", "Not supported (untested)", "D", "Low", c('gvp')],
 ["Background warming", "RONI peak +2.25 vs ONI +2.59: the tropical-mean adjustment lowers the peak by 0.34 °C, the largest of the three events; the three strongest events are not separable within SST uncertainty; a review attributes the event's extremity partly to the warm 2014 conditions and long-term background warming.", "The index adjustment removes tropical-mean warming; a statement about the index, not a quantitative attribution.", "Background (amplitude partly attributed in a review)", "C: review statement; index comparison", "Medium", c('lheureux2024', 'huang2016rank', 'santoso2017', 'hufedorov2017')],
]

Q = lambda q: TQ[q]['wind_pct']  # noqa: E731
d = {
 "tao_sentence": f"In the moorings used here, daily equatorial wind records exist for {Q('2013-07'):.0f}–{Q('2014-01'):.0f}% of site-days from July 2013 to March 2014 and {Q('2014-04'):.0f}% in April–June 2014, against {min(Q(q) for q in ('2014-10','2015-01','2015-04','2015-07')):.0f}–{max(Q(q) for q in ('2014-10','2015-01','2015-04','2015-07')):.0f}% from October 2014 to September 2015 " + c('taodata') + ".",
 "bursts2014": f"The reanalysis shows two strong westerly bursts, on {fd(WB['2014-01-24']['start'])} – {fd(WB['2014-01-24']['end'])} (+{WB['2014-01-24']['peak_anom_ms']} m s⁻¹ at {WB['2014-01-24']['peak_lon_E']:g}°E) and {fd(WB['2014-02-19']['start'])} – {fd(WB['2014-02-19']['end'])} (+{WB['2014-02-19']['peak_anom_ms']} m s⁻¹ at {WB['2014-02-19']['peak_lon_E']:g}°E), and then none until a weak one in August; 2014 has {NB14} bursts in all " + c('r1diag') + ".",
 "ewb_sentence": f"In the reanalysis this easterly burst is broad rather than intense: the 150°E–100°W mean 1000 hPa anomaly reaches {BM[1]} m s⁻¹ on {fd(BM[0])}, the {DG['basin_mean_rank_of_that_day']}th-lowest of the {DG['basin_mean_days_total']} days analysed, yet no 5 m s⁻¹ easterly burst meets the burst rule " + c('r1diag') + ".",
 "march2015": f"The decisive burst came on {fd(WB['2015-03-04']['start'])} – {fd(WB['2015-03-04']['end'])}: +{WB['2015-03-04']['peak_anom_ms']} m s⁻¹ at {WB['2015-03-04']['peak_lon_E']:g}°E, spanning {WB['2015-03-04']['lon_w']:g}°–{WB['2015-03-04']['lon_e']:g}°E, during an active MJO (OMI {WB['2015-03-04']['omi_amp_at_peak']:.1f}) " + c('r1diag') + f". The restored TAO array traced its downwelling Kelvin wave from 165°E on {fd(KW[0]['start_165E'])} to 110°W on {fd(KW[0]['last'])}, {KW[0]['days']} days at about {KW[0]['speed_ms']:.1f} m s⁻¹; later waves left 165°E on {fd(KW[1]['start_165E'])} and {fd(KW[2]['start_165E'])} " + c('taodata') + ".",
 "bursts2015": f"Unlike 1997, when most bursts preceded coupling, bursts kept coming as the event grew: {sum(1 for w in DG['wwb'] if '2015-06-01' <= w['start'] <= '2015-10-31')} from late June to October, several centred east of the Date Line, and {NB15} in calendar 2015 — the most of any year in 1979–2016 (1997 had {DG['wwb_count']['1997']}, 1982 had {DG['wwb_count']['1982']}; the 1979–2001 mean is {DG['wwb_mean_1979_2001']}) " + c('r1diag') + ". A wind-forced ocean model attributes the rapid 2015 warming to this abundance of westerly events " + c('chiodiharrison2017') + ".",
 "mjo_paragraph": f"The MJO was active (OLR MJO index ≥ 1) on {fd(DG['omi_episodes_2015'][0]['start'])} – {fd(DG['omi_episodes_2015'][0]['end'])} and {fd(DG['omi_episodes_2015'][1]['start'])} – {fd(DG['omi_episodes_2015'][1]['end'])} (maximum {DG['omi_episodes_2015'][1]['max']}), framing the March and late-June bursts " + c('r1diag') + f". Intraseasonal OLR variance at 160°E–150°W in October 2015 – March 2016 was {DG['seasons']['2015-16']['olr_20_100_var_160E_150W']:.0f} W² m⁻⁴, nearly twice that of October 1996 – March 1997 ({DG['seasons']['1996-97']['olr_20_100_var_160E_150W']:.0f}), as convection shifted east with the warm water " + c('r1diag') + ". In a model, El Niño-like SST shifts the MJO onto the equator and strengthens it in the central Pacific, favouring bursts " + c('liang2021gl') + "; a comparison of the three super events finds 2015–16 alone kept a prominent eastward-propagating MJO in its mature stage " + c('li2023') + ". MJO events warm the waveguide only when they contain westerly bursts " + c('chiodi2014') + ".",
 "volcano_sentence": "The tropical eruptions of VEI 4 in the period were Sinabung (September 2013, 3°N), Kelud (February 2014, 8°S) and Wolf (May 2015, on the equator); none was larger " + c('gvp') + ". No study read here links them to the 2014–16 evolution (not a supported candidate).",
}
from prose_2015 import build as build_prose  # noqa: E402

sections = [
 {"id": "scope", "title": "Evidence base: scope, index and data", "html": f"""<p><b>Primary index:</b> NOAA's Relative Oceanic Niño Index (RONI) {c('noaa2026', 'lheureux2024')}. On RONI the 2015–16 peak is +2.25 (NDJ 2015), the weakest of the three historical events in this series (1982–83 +2.40, 1997–98 +2.28); on the traditional ONI it is +2.59, the strongest. The difference (0.34 °C) is the tropical-mean warming that RONI removes. Within SST uncertainty the three events cannot be ranked {c('huang2016rank')}.</p>
<p><b>Observing system.</b> Argo floats (from the 2000s) and satellite altimetry, salinity and winds were available, but TAO mooring data return had declined sharply from mid-2012 to early 2014, so the 2014 onset attempt is less well observed at the equator than 1997 {c('legler2014', 'chiodiharrison2017', 'smith2019')}.</p>"""},
 {"id": "data", "title": "Monthly indices, Jul 2013 – Dec 2016", "html": "<p>Values from NOAA CPC, PMEL and NCEI files as held in the site's data archive; read from the source files, not retyped.</p>",
  "table": {"cols": ["Month", "Season", "RONI", "ONI", "rel. Niño 3.4 (OISST)", "Niño 3.4 (OISST)", "Niño 1+2 (OISST)", "Niño 4 (OISST)", "SOI", "W Pac trades", "C Pac trades", "C Pac OLR", "Heat content 180–100°W", "WWV", "DMI (CPC)", "PDO"], "rows": rows, "cls": "data",
            "note": "RONI and ONI are three-month means centred on the month. SOI and trade-wind indices are standardized (negative = El Niño-like). OLR in W m⁻² (negative = more convection). Heat content in °C vs 1981–2010; WWV in 10¹⁴ m³; DMI in °C; PDO standardized."}},
]

status_note = ("Stage 5 of 5 (24 Oct 2026): 48 data checks recomputed from source files, all passing; literature claims checked against abstracts "
               "(no full texts held yet); see the verification log. Draft for review.")

post = [{"id": "verification", "title": "Stage 5 verification log (24 October 2026)", "html": "<p><b>Data.</b> Every number in the text taken from the monthly table, the TAO analysis or the reanalysis and MJO diagnostics was recomputed from the source files by <code>tools/papers/verify_2015.py</code>: 48 checks, all passing. Diagnostic values are inserted by the build script from <code>data/papers/2015/diag_2015.json</code>, not typed by hand; the 1997 burst count from the extended run (16) matches Paper 2.</p>"
 "<p><b>Literature.</b> No full texts are held for this paper yet; every literature claim was checked against the published abstract recorded in the reference list. Studies listed as bibliographic records only are cited for nothing beyond their titles.</p>"
 "<p><b>Corrections made while drafting.</b> TAO data return is stated as a range per period rather than a single recovery figure; the October 2015 – March 2016 intraseasonal OLR variance is 'nearly twice' (ratio 1.83) rather than 'about twice' that of 1996–97; 16 uncited candidate references were removed from the list.</p>"
 "<p><b>Open items.</b> Full texts of Xue and Kumar (2017), Tseng et al. (2017), Gasparin and Roemmich (2016) and Lim and Hendon (2017) would allow numbers beyond the abstracts to be checked; island sea-level records could not be retrieved.</p>"}]

paper = {"number": 3, "file": "enso-2015-16.html", "short": "2015–16 El Niño", "title": "How the 2015–16 El Niño developed",
         "description": "Evidence-based reconstruction of the 2015–16 El Niño (draft): the failed 2014 event, westerly and easterly wind bursts, the North Pacific, and the central-Pacific character of the peak.",
         "status": "draft", "research_date": "23 October 2026", "obs_cutoff": "historical event (Jul 2013 – Dec 2016 analysed)",
         "lit_cutoff": "open, updated as new studies appear", "status_note": status_note,
         "toc": [("abstract", "Abstract"), ("findings", "Main findings"), ("intro", "1. Introduction"), ("methods", "2. Data and methods"), ("preconditions", "3. Pre-event conditions and 2014"), ("chronology", "4. Development, 2015"), ("termination", "5. Termination"), ("interactions", "6. Interactions"), ("synthesis", "7. Causal synthesis"), ("knowable", "8. What was forecast"), ("uncertainty", "9. Uncertainties"), ("conclusion", "10. Conclusion"), ("scope", "Evidence: scope and data"), ("data", "Monthly indices"), ("timeline", "Timeline"), ("evidence", "Evidence table"), ("verification", "Verification log"), ("references", "References")],
         "sections": build_prose(c, d) + sections, "post_sections": post, "timeline": timeline, "evidence": evidence,
         "references": [{"key": k, "text": t, "doi": d, "url": u, "check": ch} for k, t, d, u, ch in refs]}
with open(ROOT / 'papers' / '3-enso-2015-16.json', 'w', encoding='utf-8') as fh:
    json.dump(paper, fh, ensure_ascii=False, indent=1)
print('ok', len(timeline), len(evidence), len(refs))
