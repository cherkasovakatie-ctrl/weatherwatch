"""Assemble papers/1-enso-1982-83.json: hand-written timeline/evidence/references plus a data table built from data/*.csv."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load(f, key):
    with open(ROOT / 'data' / f, encoding='utf-8') as fh:
        return {r[key]: r for r in csv.DictReader(fh)}
sm, oni, at, sub, dr = load('sst_monthly.csv', 'month'), load('oni.csv', 'centre_month'), load('atmosphere_monthly.csv', 'month'), load('enso_subsurface.csv', 'month'), load('drivers_monthly.csv', 'month')
rows = []
for y in (1981, 1982, 1983):
    for m in range(1, 13):
        k = f'{y}-{m:02d}'
        if k > '1983-06': break
        def g(d, c, k=k):
            return d.get(k, {}).get(c) or '—'
        rows.append([k, oni.get(k, {}).get('season', '—'), g(oni, 'roni'), g(oni, 'oni'), g(sm, 'rel_ersst_nino34'), g(sm, 'ersst_nino34'), g(sm, 'nino12'), g(at, 'soi'), g(at, 'trades_west'), g(at, 'trades_central'), g(at, 'olr_central_pac'), g(sub, 'heat_180_100w'), g(sub, 'wwv_anom'), g(dr, 'dmi_cpc')])
rows = [[r[0]] + [f'<span class="num">{c}</span>' for c in r[1:]] for r in rows]

R = lambda k: f'<a href="#ref-{k}">{k.split("_")[0].capitalize()}</a>'
refs = [
 ("bandeen1982", "Bandeen, W. R., and R. S. Fraser (1982). Radiative effects of the El Chichón volcanic eruption: preliminary results concerning remote sensing. NASA Goddard Space Flight Center report (NASA Technical Reports Server 19830011101).", None, "https://ntrs.nasa.gov/citations/19830011101", "NASA record read: AVHRR SST biased up to −2.5 °C for many months"),
 ("cane1983", "Cane, M. A. (1983). Oceanographic events during El Niño. <i>Science</i> 222, 1189–1195.", "10.1126/science.222.4629.1189", None, "abstract read"),
 ("czd1986", "Cane, M. A., S. E. Zebiak and S. C. Dolan (1986). Experimental forecasts of El Niño. <i>Nature</i> 321, 827–832.", "10.1038/321827a0", None, "bibliographic record"),
 ("dee2020", "Dee, S. G., et al. (2020). No consistent ENSO response to volcanic forcing over the last millennium. <i>Science</i> 367, 1477–1481; comment by Robock (2020) doi:10.1126/science.abc0502 and reply doi:10.1126/science.abc1733.", None, "https://doi.org/10.1126/science.abc1733", "comment and reply DOIs confirmed; original article DOI to confirm"),
 ("firing1983", "Firing, E., R. Lukas, J. Sadler and K. Wyrtki (1983). Equatorial Undercurrent disappears during 1982–1983 El Niño. <i>Science</i> 222, 1121–1123.", "10.1126/science.222.4628.1121", None, "abstract read"),
 ("gill1983", "Gill, A. E., and E. M. Rasmusson (1983). The 1982–83 climate anomaly in the equatorial Pacific. <i>Nature</i> 306, 229–234.", "10.1038/306229a0", None, "bibliographic record; abstract not retrieved"),
 ("halpern1983", "Halpern, D., S. P. Hayes, A. Leetmaa, D. V. Hansen and S. G. H. Philander (1983). Oceanographic observations of the 1982 warming of the tropical eastern Pacific. <i>Science</i> 221, 1173–1175.", "10.1126/science.221.4616.1173", None, "abstract read"),
 ("harrison1984", "Harrison, D. E. (1984). The appearance of sustained equatorial surface westerlies during the 1982 Pacific warm event. <i>Science</i> 224, 1099–1102.", "10.1126/science.224.4653.1099", None, "abstract read"),
 ("harrisonschopf1984", "Harrison, D. E., and P. S. Schopf (1984). Kelvin-wave-induced anomalous advection and the onset of surface warming in El Niño events. <i>Monthly Weather Review</i> 112, 923–933.", "10.1175/1520-0493(1984)112<0923:KWIAAA>2.0.CO;2", None, "abstract read"),
 ("harrison1989", "Harrison, D. E., W. S. Kessler and B. S. Giese (1989). Ocean circulation model hindcasts of the 1982–83 El Niño: thermal variability along the ship-of-opportunity tracks. <i>Journal of Physical Oceanography</i> 19, 397–418.", "10.1175/1520-0485(1989)019<0397:OCMHOT>2.0.CO;2", None, "abstract read"),
 ("harrisonlarkin1998", "Harrison, D. E., and N. K. Larkin (1998). El Niño–Southern Oscillation sea surface temperature and wind anomalies, 1946–1993. <i>Reviews of Geophysics</i> 36, 353–399.", "10.1029/98RG00715", None, "abstract read"),
 ("keen1982", "Keen, R. A. (1982). The role of cross-equatorial tropical cyclone pairs in the Southern Oscillation. <i>Monthly Weather Review</i> 110, 1405–1416.", "10.1175/1520-0493(1982)110<1405:TROCET>2.0.CO;2", None, "abstract read (study period 1971–79)"),
 ("khodri2017", "Khodri, M., et al. (2017). Tropical explosive volcanic eruptions can trigger El Niño by cooling tropical Africa. <i>Nature Communications</i> 8.", "10.1038/s41467-017-00755-6", None, "abstract read (model study, Pinatubo-like eruptions)"),
 ("lheureux2024", "L'Heureux, M. L., et al. (2024). A relative sea surface temperature index for classifying ENSO events in a changing climate. <i>Journal of Climate</i> 37, 1197–1211.", "10.1175/JCLI-D-23-0406.1", None, "abstract read"),
 ("lukas1984", "Lukas, R., S. P. Hayes and K. Wyrtki (1984). Equatorial sea level response during the 1982–1983 El Niño. <i>Journal of Geophysical Research</i> 89(C6), 10425–10430.", "10.1029/JC089iC06p10425", None, "abstract read"),
 ("luther1983", "Luther, D. S., D. E. Harrison and R. A. Knox (1983). Zonal winds in the central equatorial Pacific and El Niño. <i>Science</i> 222, 327–330.", "10.1126/science.222.4621.327", None, "abstract read (study period 1950–78)"),
 ("meinen2000", "Meinen, C. S., and M. J. McPhaden (2000). Observations of warm water volume changes in the equatorial Pacific and their relationship to El Niño and La Niña. <i>Journal of Climate</i> 13, 3551–3559.", "10.1175/1520-0442(2000)013<3551:OOWWVC>2.0.CO;2", None, "abstract read"),
 ("noaa2026", "NOAA National Weather Service (2026). Public Information Notice 26-05: Relative Oceanic Niño Index (RONI), effective 1 February 2026.", None, "https://weather.gov/media/notification/pdf_2026/pns26-05_Relative_ONI.pdf", "read"),
 ("rc1982", "Rasmusson, E. M., and T. H. Carpenter (1982). Variations in tropical sea surface temperature and surface wind fields associated with the Southern Oscillation/El Niño. <i>Monthly Weather Review</i> 110, 354–384.", "10.1175/1520-0493(1982)110<0354:VITSST>2.0.CO;2", None, "abstract read"),
 ("rw1983", "Rasmusson, E. M., and J. M. Wallace (1983). Meteorological aspects of the El Niño/Southern Oscillation. <i>Science</i> 222, 1195–1202.", "10.1126/science.222.4629.1195", None, "abstract read"),
 ("robock2000", "Robock, A. (2000). Volcanic eruptions and climate. <i>Reviews of Geophysics</i> 38, 191–219.", "10.1029/1998RG000054", None, "bibliographic record"),
 ("wang1995", "Wang, B. (1995). Interdecadal changes in El Niño onset in the last four decades. <i>Journal of Climate</i> 8, 267–285.", "10.1175/1520-0442(1995)008<0267:ICIENO>2.0.CO;2", None, "abstract read"),
 ("wyrtki1975", "Wyrtki, K. (1975). El Niño—the dynamic response of the equatorial Pacific Ocean to atmospheric forcing. <i>Journal of Physical Oceanography</i> 5, 572–584.", "10.1175/1520-0485(1975)005<0572:ENTDRO>2.0.CO;2", None, "bibliographic record"),
 ("wyrtki1985a", "Wyrtki, K. (1985). Sea level fluctuations in the Pacific during the 1982–83 El Niño. <i>Geophysical Research Letters</i> 12, 125–128.", "10.1029/GL012i003p00125", None, "abstract read"),
 ("wyrtki1985b", "Wyrtki, K. (1985). Water displacements in the Pacific and the genesis of El Niño cycles. <i>Journal of Geophysical Research</i> 90(C4), 7129–7132.", "10.1029/JC090iC04p07129", None, "abstract read"),
 ("cpc", "NOAA Climate Prediction Center: monthly index files (RONI.ascii.txt, oni.ascii.txt, Rnino34.ascii.txt, detrend.nino34.ascii.txt, sstoi.indices, soi, wpac850, cpac850, cpolr.mth.91-20.ascii, heat_content_index.txt, IOD files); PMEL warm water volume. Site copies in the data archive.", None, "https://www.cpc.ncep.noaa.gov/data/indices/", "data read"),
]
cite = {k: f'<a href="#ref-{k}">[{i+1}]</a>' for i, (k, *_) in enumerate(refs)}
c = lambda *ks: ' '.join(cite[k] for k in ks)

timeline = [
 ["1981", "Warm water volume (WWV) positive all year, +0.6 to +2.1 × 10¹⁴ m³; upper-300 m heat content (180°–100°W) between −0.7 and +1.0 °C.", "Recharge of the equatorial warm-water reservoir, the precondition in recharge-oscillator theory.", c('cpc', 'meinen2000', 'wyrtki1985b'), "Medium (sparse 1981 subsurface data)"],
 ["DJF 1982", "RONI +0.11, ONI −0.05: ENSO-neutral start.", "—", c('cpc'), "High"],
 ["Feb–Apr 1982", "850 hPa trades weaker than normal in the western Pacific (−0.6 to −1.3 standardized); heat content rises to +0.9 °C. Niño 1+2 cold (−0.72 to −1.38 °C, OISST).", "Early westerly anomalies in the west; coastal coolness consistent with enhanced south-east Pacific trades in the post-1976 background state.", c('cpc', 'wang1995'), "Medium"],
 ["Late Mar–early Apr 1982", "El Chichón eruptions (Mexico) inject aerosol into the tropical stratosphere. Satellite (AVHRR) SST biased low by up to 2.5 °C for months.", "Candidate volcanic forcing (see evidence table); certainly an observing-system problem that hid part of the warming from satellites.", c('robock2000', 'bandeen1982'), "High (bias); Low (forcing role)"],
 ["May–Jun 1982", "ERSSTv6 relative Niño 3.4 rises from +0.76 to +1.12 °C; SOI −1.0 by June; RONI MAM +0.46 → AMJ +0.74.", "Onset of ocean–atmosphere coupling.", c('cpc'), "High"],
 ["Jun 1982", "Band of anomalous southerly winds east of Australia (150°–160°E) crosses the equator just before sustained westerlies appear on the equator west of the Date Line.", "Cross-equatorial flow feeding sustained equatorial westerlies that force downwelling Kelvin waves.", c('harrison1984'), "Medium (one study)"],
 ["Jul 1982", "Strong anomalous warming starts along the equator, before the South American coast warms.", "Kelvin-wave-induced eastward currents advect warm water while the seasonal east–west SST gradient is strong; reproduced by an advective and a full ocean model.", c('harrisonschopf1984'), "Medium–high"],
 ["Aug 1982", "Equatorial Undercurrent at 159°W decays; near-surface flow at 0°, 110°W reverses to eastward; central-Pacific OLR −21 W m⁻².", "Basin-wide adjustment of the sea-surface slope to westerly forcing; deep convection moving east.", c('firing1983', 'halpern1983', 'cpc'), "High"],
 ["Sep 1982", "Undercurrent partly reversed at 159°W; central Pacific trades −2.0 standardized; RONI JAS +1.14.", "Bjerknes feedback: warming weakens trades, which deepen the thermocline in the east.", c('firing1983', 'cpc'), "High (observation); general theory (mechanism)"],
 ["Oct 1982", "Eastern equatorial SST +5 °C above the monthly mean; Galápagos sea level +22 cm; thermocline 50–70 m deeper along the equator and the South American coast.", "Arrival of downwelling Kelvin waves and coupled growth in the east.", c('halpern1983'), "High"],
 ["Aug–Nov 1982", "Positive Indian Ocean Dipole (CPC DMI +0.53 to +0.92 °C, peak Oct).", "Not yet assessed; may be a response to the Pacific warming (reverse causality) rather than a cause.", c('cpc'), "Pending"],
 ["Dec 1982", "First Galápagos sea-level peak; warm water drains from north of the equator; by year-end the normal east–west sea-level slope is gone. WWV falls to +1.4 × 10¹⁴ m³.", "Discharge of the warm-water reservoir driven by western Pacific westerlies.", c('wyrtki1985a', 'lukas1984', 'cpc'), "High"],
 ["DJF 1983", "Peak: RONI +2.40 (ONI +2.14). January SOI −3.5; central-Pacific OLR −46 W m⁻²; WWV negative.", "Mature, fully coupled state; discharge under way.", c('cpc'), "High"],
 ["Jan 1983", "Equatorial Undercurrent at 159°W rapidly reappears.", "Recovery of the zonal pressure gradient in the central Pacific.", c('firing1983'), "High"],
 ["Feb–Jun 1983", "Niño 3.4 declines while Niño 1+2 rises to +4.0 °C in June; second Galápagos sea-level peak in May as warm water drains from south of the equator.", "A second, southern-hemisphere draining episode prolongs warmth in the far east.", c('wyrtki1985a', 'cpc'), "High"],
 ["Oct 1983", "Sea level below normal across the equatorial Pacific.", "Warm water lost to higher latitudes: the end of the cycle.", c('wyrtki1985a', 'wyrtki1985b'), "High"],
]

evidence = [
 ["Warm-water recharge", "WWV positive through 1981 and early 1982; heat content rising from Jan 1982.", "A deep, charged warm pool lets Kelvin waves raise eastern SST and sustain growth.", "Precondition", "B: observation (sparse) + theory confirmed across 1980–99", "Medium", c('cpc', 'meinen2000', 'wyrtki1985b')],
 ["Sustained equatorial westerlies west of the Date Line (from Jun 1982)", "Appear in June; later extend east and persist.", "Wind forcing of downwelling Kelvin waves and eastward currents.", "Trigger of the vigorous phase, then amplifier", "B: event-specific observation", "Medium–high", c('harrison1984', 'lukas1984', 'firing1983')],
 ["Cross-equatorial southerly jet east of Australia (Jun 1982)", "Formed just before the sustained westerlies.", "Feeds the equatorial westerlies.", "Trigger component (proposed)", "B/C: one event-specific study; similar precursors in 1957, 1965, 1972", "Medium", c('harrison1984')],
 ["Downwelling Kelvin waves and anomalous eastward advection", "Equatorial warming from July; undercurrent collapse Aug–Sep; thermocline 50–70 m deeper by Oct.", "Eastward transfer of warm water and anomalous advection.", "Core onset mechanism", "A−: event observations + advective and full ocean model experiments", "High", c('harrisonschopf1984', 'lukas1984', 'halpern1983', 'firing1983', 'harrison1989')],
 ["Seasonal timing (annual cycle of the zonal SST gradient)", "Westerly-driven currents arrived mid-year rather than in Feb–Apr.", "The same currents give equatorial-first warming when the zonal SST gradient is strong.", "Redirector of the onset pattern", "B: model experiment for this event", "Medium–high", c('harrisonschopf1984')],
 ["Post-1976 Pacific background state", "Tropical Pacific warmer after the late 1970s; south-east Pacific trades enhanced at onset; coast cold in early 1982.", "Background state alters the onset cyclone and makes coastal warming follow, not lead, central warming.", "Precondition / redirector", "B: retrospective composite (1982, 1986–87, 1991)", "Medium", c('wang1995')],
 ["Bjerknes coupled feedback", "Trades, SOI, OLR and SST strengthen together from Aug to Dec 1982.", "Warming → weaker trades → deeper eastern thermocline → more warming.", "Amplifier / feedback", "B: event observations + general theory", "High", c('cpc', 'rw1983', 'gill1983')],
 ["Recharge–discharge and the second eastern peak", "WWV discharged by Jan 1983; two draining episodes (north then south of the equator).", "Discharge ends the event; southern draining prolongs far-eastern warmth to mid-1983.", "Decay and lingering warmth", "A−: sea-level budget for this event", "High", c('wyrtki1985a', 'wyrtki1985b')],
 ["Tropical cyclone pairs", "Not yet documented for 1982 in a verified source.", "Cyclone pairs straddling the equator produce brief strong westerlies (shown for 1971–79).", "Candidate trigger", "D for 1982: general study only", "Pending", c('keen1982')],
 ["Intraseasonal variability (MJO, westerly wind bursts)", "Westerly bursts of 1–3 weeks are typical before El Niño (1950–78); 1982 bursts not yet catalogued from a verified source.", "Bursts force Kelvin waves; MJO organises bursts.", "Candidate trigger / amplifier", "C/D for 1982: general study only", "Pending", c('luther1983')],
 ["El Chichón eruption (Mar–Apr 1982)", "Erupted after recharge and the first western-Pacific trade weakening.", "Model studies (Pinatubo-like) find eruptions can favour El Niño via tropical African cooling; palaeo-records show no consistent response.", "Coincident or weak amplifier, unresolved", "C/D: model and multi-event evidence, contested", "Low", c('khodri2017', 'dee2020', 'robock2000')],
 ["Indian Ocean (positive IOD, Aug–Nov 1982)", "DMI +0.53 to +0.92 °C.", "Could reinforce western-Pacific westerlies, or be forced by the Pacific warming.", "Not yet determined (reverse causality likely)", "C: index only", "Pending", c('cpc')],
 ["Tropical North Atlantic cooling (late 1982)", "TNA −0.5 to −0.9 °C, Aug–Dec 1982.", "Usually a lagged response to El Niño.", "Probable consequence", "C: index only", "Low", c('cpc')],
]

sections = [
 {"id": "scope", "title": "Scope, index and data", "html": f"""<p>This page holds the evidence assembled so far (stages 1–3 of 5). The paper's prose will be drafted from it after review. <b>Primary index:</b> NOAA's Relative Oceanic Niño Index (RONI), official since 1 February 2026 {c('noaa2026', 'lheureux2024')}: the three-month mean of Niño 3.4 minus the 20°N–20°S tropical-mean anomaly, rescaled. On RONI the 1982–83 peak is +2.40 (DJF 1983), the strongest of the three historical events in this series; on the traditional ONI it is +2.14.</p>
<p><b>Observing system in 1982.</b> No TAO mooring array (completed in 1994), no satellite altimetry (from 1992) and no Argo floats. The evidence rests on ship and XBT tracks, island tide gauges, a few moorings (e.g. 0°, 110°W) and later reanalyses. Satellite SST from April 1982 was biased low by up to 2.5 °C by El Chichón aerosol {c('bandeen1982')}. Subsurface indices for 1981–82 are reconstructions from sparse data.</p>"""},
 {"id": "data", "title": "Monthly indices, Jan 1981 – Jun 1983", "html": "<p>Values from NOAA CPC and PMEL files as held in the site's data archive; read from the source files, not retyped.</p>",
  "table": {"cols": ["Month", "Season", "RONI", "ONI", "rel. Niño 3.4 (ERSSTv6)", "Niño 3.4 (ERSSTv6)", "Niño 1+2 (OISST)", "SOI", "W Pac trades", "C Pac trades", "C Pac OLR", "Heat content 180–100°W", "WWV", "DMI (CPC)"], "rows": rows, "cls": "data",
            "note": "RONI and ONI are three-month means centred on the month. SOI and trade-wind indices are standardized (negative SOI and negative trade anomalies are El Niño-like). OLR in W m⁻² (negative = more convection). Heat content in °C vs 1981–2010; WWV in 10¹⁴ m³; DMI in °C. OISST begins Sep 1981 and its 1982 values may carry residual El Chichón bias."}},
 {"id": "status-notes", "title": "What is not yet established", "html": f"""<ul>
<li><b>Tropical cyclone pairs and westerly wind bursts in 1982.</b> Their role is plausible in general {c('keen1982', 'luther1983')} but I have not yet found a verified 1982-specific catalogue. Next step: daily ship-wind and reanalysis evidence (ERA5, JRA-55) and the 1982 best-track record.</li>
<li><b>MJO.</b> Not yet assessed; real-time indices exist from 1979 but are themselves contaminated by ENSO signals in strong events.</li>
<li><b>El Chichón as a forcing.</b> Contested in the literature {c('khodri2017', 'dee2020')}; no study isolating its effect on the 1982 onset has been found yet.</li>
<li><b>Gill &amp; Rasmusson (1983)</b> and the full texts of the 1983 <i>Science</i> papers were not accessible; only abstracts were read.</li>
<li><b>What was knowable at the time.</b> The 1982 event departed from the Rasmusson–Carpenter composite {c('rc1982', 'cane1983')}; coupled-model forecasts began only with the 1986 event {c('czd1986')}.</li></ul>"""},
]

paper = {"number": 1, "file": "enso-1982-83.html", "short": "1982–83 El Niño", "title": "How the 1982–83 El Niño developed",
 "description": "Evidence-based reconstruction of the 1982–83 El Niño: preconditions, triggers, amplifiers and the broader climate system, with timeline, evidence table and verified references.",
 "status": "draft", "research_date": "18 October 2026", "obs_cutoff": "historical event (Jan 1981 – Oct 1983 analysed)", "lit_cutoff": "open, updated as new studies appear",
 "status_note": "Stages 1–3 of 5 complete: sources verified (DOIs checked against Crossref; abstracts read where available), monthly data assembled, timeline and evidence table drafted. <b>Prose sections are not written yet</b>; they follow your review of this evidence. Items marked Pending still need event-specific evidence.",
 "toc": [("scope", "Scope, index and data"), ("data", "Monthly indices"), ("timeline", "Timeline"), ("evidence", "Evidence table"), ("status-notes", "Not yet established"), ("references", "References")],
 "sections": sections[:2], "timeline": timeline, "evidence": evidence, "references": [{"key": k, "text": t, "doi": d, "url": u, "check": ch} for k, t, d, u, ch in refs]}
paper["sections"] = sections[:2]
paper["after"] = sections[2]
with open(ROOT / 'papers' / '1-enso-1982-83.json', 'w', encoding='utf-8') as fh:
    json.dump(paper, fh, ensure_ascii=False, indent=1)
print('ok', len(timeline), len(evidence), len(refs))
