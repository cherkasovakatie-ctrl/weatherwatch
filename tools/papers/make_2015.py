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
 ("meinen2000", "Meinen, C. S., and M. J. McPhaden (2000). Observations of warm water volume changes in the equatorial Pacific and their relationship to El Niño and La Niña. <i>Journal of Climate</i> 13, 3551–3559.", "10.1175/1520-0442(2000)013<3551:OOWWVC>2.0.CO;2", None, AB),
 ("jin1997", "Jin, F.-F. (1997). An equatorial ocean recharge paradigm for ENSO. Part I: conceptual model. <i>Journal of the Atmospheric Sciences</i> 54, 811–829.", "10.1175/1520-0469(1997)054<0811:AEORPF>2.0.CO;2", None, AB),
 ("chiodi2014", "Chiodi, A. M., D. E. Harrison and G. A. Vecchi (2014). Subseasonal atmospheric variability and El Niño waveguide warming: observed effects of the Madden–Julian oscillation and westerly wind events. <i>Journal of Climate</i> 27, 3619–3642.", "10.1175/JCLI-D-13-00547.1", None, AB),
 ("eisenman2005", "Eisenman, I., L. Yu and E. Tziperman (2005). Westerly wind bursts: ENSO's tail rather than the dog? <i>Journal of Climate</i> 18, 5224–5238.", "10.1175/JCLI3588.1", None, AB),
 ("li2023", "Li, L., et al. (2023). Comparison of Madden–Julian oscillation in three super El Niño events. <i>Frontiers in Earth Science</i> 10, 1021953.", "10.3389/feart.2022.1021953", None, "full text read (open access; private library copy)"),
 ("cai2014", "Cai, W., et al. (2014). Increasing frequency of extreme El Niño events due to greenhouse warming. <i>Nature Climate Change</i> 4, 111–116.", "10.1038/nclimate2100", None, "bibliographic record"),
 cr('santoso2017', AB), cr('lheureux2017', AB), cr('xuekumar2017', AB), cr('huang2016rank', AB), cr('paek2017', AB), cr('ren2017', BIB), cr('zhai2016', BIB),
 cr('mcphaden2015', BIB), cr('menkes2014', AB), cr('hufedorov2016', AB), cr('levine2016', AB), cr('chiodiharrison2017', AB), cr('zhu2016', AB),
 cr('hu2014', AB), cr('fedorov2015', BIB), cr('chen2015', BIB), cr('lian2014', AB), cr('puy2016', BIB), cr('puy2015', BIB),
 cr('lei2021', BIB), cr('liang2021tc', BIB), cr('liang2021gl', AB), cr('liang2025', AB), cr('hong2014', AB),
 cr('bond2015', AB), cr('dilorenzo2016', BIB), cr('tseng2017', AB), cr('amaya2019', BIB),
 cr('lim2017iod', AB), cr('stuecker2017', AB), cr('stuecker2013', BIB), cr('mcgregor2012', AB),
 cr('gasparin2016', AB), cr('hufedorov2017', AB), cr('kao2009', BIB), cr('ashok2007', BIB),
 cr('tollefson2014', "news report (Nature), bibliographic record; context only"), cr('legler2014', AB), cr('smith2019', AB), cr('jacox2016', AB),
]
cite = {k: f'<a href="#ref-{k}">[{i + 1}]</a>' for i, (k, *_) in enumerate(refs)}


def c(*ks):
    return ' '.join(cite[k] for k in ks)


timeline = [
 ["Jul 2013 – Feb 2014", "ENSO-neutral, slightly cool (RONI −0.48 in JJA 2013 to −0.22 to −0.43 through DJF 2014); warm water volume positive throughout (+0.78 to +1.25 × 10¹⁴ m³). A strong warm anomaly forms in the NE Pacific in winter 2013–14 (the 'Blob').", "Recharged equatorial Pacific; the Blob from reduced ocean heat loss and weak cold advection under persistent high pressure.", c('cpc', 'meinen2000', 'bond2015'), "High"],
 ["Mid-2012 – early 2014", "Data return from the TAO array declines sharply.", "Observing-system gap during the 2014 onset attempt.", c('legler2014', 'tollefson2014', 'chiodiharrison2017'), "High"],
 ["Jan – Mar 2014", "Two strong westerly wind bursts; heat content east of the Date Line rises from −0.33 °C (Jan) to +1.60 °C (Mar); warm water volume peaks at +2.05 × 10¹⁴ m³ in March; the warm pool displaces east; forecasts point to a moderate-to-strong, possibly extreme, El Niño.", "Burst-forced downwelling Kelvin waves on a recharged basin, as in early 1997.", c('hufedorov2016', 'menkes2014', 'cpc', 'lheureux2017'), "High"],
 ["Apr – Jun 2014", "No westerly wind events from April to June; the warm pool retreats by July; RONI peaks at only +0.15 (AMJ) and falls to −0.14 (JJA).", "Lack of spring bursts limits eastern growth (contrast with 1997).", c('menkes2014', 'chiodiharrison2017', 'cpc'), "High"],
 ["Jun – Jul 2014", "An unusually strong basin-wide easterly wind burst; all major Niño indices fall to near normal; two separate warm centres persist in the central and eastern Pacific.", "Easterly burst suppresses the Bjerknes feedback but also prevents, then reverses, the discharge of equatorial heat content.", c('hufedorov2016', 'levine2016'), "High (observation + model experiments)"],
 ["Early 2014", "Negative SST anomalies in the south-eastern Pacific and positive anomalies to the north (South Pacific meridional mode pattern); in forecast experiments about 40% of the 2014 amplitude error comes from missing the south-eastern cold anomalies.", "Off-equatorial SST gradient drives meridional rather than zonal winds near the equator.", c('zhu2016'), "Medium (one model)"],
 ["Aug – Dec 2014", "Warm water volume rebuilds to +1.49 and +1.57 × 10¹⁴ m³ (Aug–Sep); RONI rises to +0.62 (NDJ 2014–15); ONI ≥ +0.5 from SON 2014. The 2014 event 'failed to qualify as an El Niño by conventional definitions'.", "Head start of equatorial heat content for 2015.", c('cpc', 'levine2016'), "High"],
 ["2014 – 2015", "The Blob persists for multiple years; PDO positive from 2014 (up to +1.86 in Dec 2014).", "North Pacific variability (Victoria mode, NPO-like pattern) proposed as a bridge to the 2015 El Niño.", c('dilorenzo2016', 'tseng2017', 'cpc'), "Medium (precursor link disputed)"],
 ["Mar 2015", "Westerly winds return: western-Pacific trade index −1.8 and central-Pacific OLR −18.8 W m⁻²; heat content +1.52 °C.", "New burst activity on a still-charged basin.", c('cpc', 'xuekumar2017'), "High"],
 ["Apr – Nov 2015", "Four downwelling Kelvin waves; eastward current anomalies advect the warm pool east in spring and summer; a strong equatorial freshwater anomaly unprecedented in the 2004–2014 Argo record adds eastward acceleration at the salinity front.", "Kelvin waves and advection initiate and enhance eastern-central warming.", c('xuekumar2017', 'gasparin2016'), "High"],
 ["May – Jul 2015", "Coupling established: RONI AMJ +0.89, MJJ +1.02, JJA +1.27; SOI −0.6 to −1.1; Niño 1+2 +1.34, +1.91, +2.48 °C; public El Niño advisories in the first half of 2015.", "Bjerknes feedback takes over.", c('cpc', 'lheureux2017'), "High"],
 ["Aug – Dec 2015", "Growth to the peak: RONI SON +2.03, OND +2.18, NDJ +2.25 (ONI +2.59); Niño 4 reaches a record +1.55 °C (Nov) while Niño 1+2 stays near +2 °C; central-Pacific OLR −49.9 W m⁻² in December.", "Unusually westward-centred warming: convection displaced about 20° west compared with 1982 and 1997.", c('cpc', 'xuekumar2017', 'lheureux2017'), "High"],
 ["Nov 2015", "An upwelling Kelvin wave emerges, leading to a rapid decline; warm water volume turns negative in December (−0.39 × 10¹⁴ m³).", "Discharge begins.", c('xuekumar2017', 'cpc'), "High"],
 ["Jan – May 2016", "Decay: RONI JFM +1.81 → AMJ +0.08; WWV −1.26 to −3.36 × 10¹⁴ m³; warm SST lingers near the Date Line rather than retreating to the coast; demise in May 2016.", "Discharge; stronger central-Pacific dynamics in decay.", c('cpc', 'paek2017', 'lheureux2017'), "High"],
 ["Jun – Dec 2016", "Weak La Niña (RONI −0.43 MJJ to −0.96 SON/OND) with a strong negative Indian Ocean Dipole peaking in July–September 2016 (CPC DMI −0.89 °C in July).", "Negative IOD promoted the weak La Niña.", c('cpc', 'lim2017iod'), "High (observation); one model study (mechanism)"],
]

evidence = [
 ["Recharge carried over from 2014", "WWV positive from mid-2013; partial discharge in mid-2014 reversed by the July 2014 easterly burst; WWV +0.31 to +1.25 × 10¹⁴ m³ in Jan–May 2015 (vs +3.12 in Apr 1997).", "Retained heat content gave 2015 a head start.", "Precondition", "A−: observation + model analysis for this event", "High", c('cpc', 'levine2016', 'meinen2000')],
 ["Easterly wind burst, June–July 2014", "Strong basin-wide EWB; Niño indices fall; discharge prevented.", "Suppressed 2014 growth (suppressor) while preserving heat for 2015.", "Suppressor (2014) / indirect precondition (2015)", "A: observation + model experiments", "High", c('hufedorov2016', 'levine2016')],
 ["Westerly wind events, 2014 and 2015", "Strong bursts Jan–Mar 2014 but none Apr–Jun 2014; renewed bursts from early 2015 with four downwelling Kelvin waves Apr–Nov 2015.", "Burst sequence decides whether onset proceeds (2014 vs 2015 contrast).", "Trigger (2015); failed trigger (2014)", "A−: event observations + ocean simulations", "High", c('menkes2014', 'chiodiharrison2017', 'xuekumar2017', 'chen2015')],
 ["South Pacific meridional SST gradient (2014)", "Cold SE Pacific / warm north pattern in early 2014.", "Meridional rather than zonal winds near the equator damp growth.", "Suppressor (2014)", "B/C: one forecast-model study", "Medium", c('zhu2016')],
 ["North Pacific (Blob, Victoria mode, meridional mode)", "NE Pacific warm anomaly from winter 2013–14, multi-year; positive PDO 2014–16.", "North Pacific atmosphere → subtropical SST/winds → equatorial westerlies (seasonal footprinting / meridional mode).", "Possible precondition / trigger component", "B/C: one coupled-mode statistical study for this event; general reviews", "Medium–low", c('tseng2017', 'bond2015', 'dilorenzo2016', 'amaya2019', 'liang2025')],
 ["MJO and twin tropical cyclones", "To be assessed with the reanalysis and index diagnostics (running).", "MJO convection and paired cyclones organise bursts.", "Pending", "Pending", "Pending", c('liang2021tc', 'liang2021gl', 'puy2015', 'lei2021')],
 ["Bjerknes feedback and central-Pacific dynamics", "Coupled growth from May 2015; record Niño 4 and westward-shifted convection; weaker eastern thermocline anomaly than 1982 and 1997.", "Eastern (thermocline) and central-Pacific (subtropically forced) dynamics combined.", "Amplifier / redirector of the pattern", "B: event observations + one model comparison", "Medium–high", c('xuekumar2017', 'paek2017', 'lheureux2017', 'kao2009')],
 ["Freshwater (salinity) anomaly 2015", "Large equatorial freshwater anomaly in 2015, unprecedented in the 2004–2014 Argo record.", "Positive steric height in the west and eastward acceleration at the salinity front.", "Amplifier (ocean dynamics)", "B: event-specific budget", "Medium", c('gasparin2016')],
 ["Seasonal cycle in termination", "Southward shift of westerly anomalies in boreal winter is a key element of the termination of strong events.", "SPCZ-related weakening of climatological winds south of the equator.", "Termination mechanism", "B/C: general model studies; 2015–16 not isolated in the sources read", "Medium", c('mcgregor2012', 'stuecker2013')],
 ["Indian Ocean", "Weak positive DMI in Aug–Oct 2015 (+0.42 to +0.47 °C); strong negative IOD in mid-2016 promoting the weak La Niña.", "IOD phase largely set by ENSO combination-mode forcing; the 2016 negative IOD developed mainly from Indian Ocean conditions.", "Consequence (2015); influence on the transition (2016)", "B: event-specific forecast experiments (2016); theory (C-mode)", "Medium", c('cpc', 'lim2017iod', 'stuecker2017')],
 ["Volcanic forcing", "Tropical VEI 4 eruptions: Sinabung (Sep 2013, 3°N), Kelud (Feb 2014, 8°S) and Wolf (May 2015, 0°); none larger.", "No event-specific study links them to the 2014–16 evolution.", "Not supported (untested)", "D", "Low", c('gvp')],
 ["Background warming", "RONI peak +2.25 vs ONI +2.59: the tropical-mean adjustment lowers the peak by 0.34 °C, the largest of the three events; the three strongest events are not separable within SST uncertainty.", "The index adjustment removes the tropical-mean warming; a statement about the index, not attribution.", "Background (amplitude partly attributed in reviews)", "C: review statement; index comparison", "Medium", c('lheureux2024', 'huang2016rank', 'santoso2017', 'hufedorov2017')],
]

sections = [
 {"id": "scope", "title": "Evidence base: scope, index and data", "html": f"""<p><b>Primary index:</b> NOAA's Relative Oceanic Niño Index (RONI) {c('noaa2026', 'lheureux2024')}. On RONI the 2015–16 peak is +2.25 (NDJ 2015), the weakest of the three historical events in this series (1982–83 +2.40, 1997–98 +2.28); on the traditional ONI it is +2.59, the strongest. The difference (0.34 °C) is the tropical-mean warming that RONI removes. Within SST uncertainty the three events cannot be ranked {c('huang2016rank')}.</p>
<p><b>Observing system.</b> Argo floats (from the 2000s) and satellite altimetry, salinity and winds were available, but TAO mooring data return had declined sharply from mid-2012 to early 2014, so the 2014 onset attempt is less well observed at the equator than 1997 {c('legler2014', 'chiodiharrison2017', 'smith2019')}.</p>"""},
 {"id": "data", "title": "Monthly indices, Jul 2013 – Dec 2016", "html": "<p>Values from NOAA CPC, PMEL and NCEI files as held in the site's data archive; read from the source files, not retyped.</p>",
  "table": {"cols": ["Month", "Season", "RONI", "ONI", "rel. Niño 3.4 (OISST)", "Niño 3.4 (OISST)", "Niño 1+2 (OISST)", "Niño 4 (OISST)", "SOI", "W Pac trades", "C Pac trades", "C Pac OLR", "Heat content 180–100°W", "WWV", "DMI (CPC)", "PDO"], "rows": rows, "cls": "data",
            "note": "RONI and ONI are three-month means centred on the month. SOI and trade-wind indices are standardized (negative = El Niño-like). OLR in W m⁻² (negative = more convection). Heat content in °C vs 1981–2010; WWV in 10¹⁴ m³; DMI in °C; PDO standardized."}},
]

status_note = ("Stages 1–3 of 5 (23 Oct 2026): references matched to Crossref (authors, volumes and pages taken from the records) and every "
               "available abstract read; monthly data Jul 2013 – Dec 2016 assembled; timeline and evidence table drafted from abstracts and "
               "CPC/PMEL data. In progress: reanalysis burst and MJO diagnostics and TAO moorings (GitHub Actions). Not yet written: prose (stage 4) "
               "and verification (stage 5).")

paper = {"number": 3, "file": "enso-2015-16.html", "short": "2015–16 El Niño", "title": "How the 2015–16 El Niño developed",
         "description": "Evidence-based reconstruction of the 2015–16 El Niño (in progress): the failed 2014 event, westerly and easterly wind bursts, the North Pacific, and the central-Pacific character of the peak.",
         "status": "in-progress", "research_date": "23 October 2026", "obs_cutoff": "historical event (Jul 2013 – Dec 2016 analysed)",
         "lit_cutoff": "open, updated as new studies appear", "status_note": status_note,
         "toc": [("scope", "Evidence: scope and data"), ("data", "Monthly indices"), ("timeline", "Timeline"), ("evidence", "Evidence table"), ("references", "References")],
         "sections": sections, "timeline": timeline, "evidence": evidence,
         "references": [{"key": k, "text": t, "doi": d, "url": u, "check": ch} for k, t, d, u, ch in refs]}
with open(ROOT / 'papers' / '3-enso-2015-16.json', 'w', encoding='utf-8') as fh:
    json.dump(paper, fh, ensure_ascii=False, indent=1)
print('ok', len(timeline), len(evidence), len(refs))
