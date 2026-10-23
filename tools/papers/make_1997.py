"""Assemble papers/2-enso-1997-98.json (Paper 2): references, monthly data table, timeline and evidence table.

Stage status is recorded in the paper's status_note. Every reference below was matched to its Crossref record
(DOI, journal, volume, pages) on 23 Oct 2026 by tools/papers/refcheck.py (weekly-raw branch, raw/papers/1997*/refs.json);
the "check" field records what was actually read. Monthly values come from the site's CPC/PMEL data files.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load(f, key):
    with open(ROOT / 'data' / f, encoding='utf-8') as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


sm, oni, at, sub, dr = (load('sst_monthly.csv', 'month'), load('oni.csv', 'centre_month'), load('atmosphere_monthly.csv', 'month'),
                        load('enso_subsurface.csv', 'month'), load('drivers_monthly.csv', 'month'))
rows = []
for y in range(1995, 1999):
    for m in range(1, 13):
        k = f'{y}-{m:02d}'
        if k < '1995-07':
            continue

        def g(d, col, k=k):
            return d.get(k, {}).get(col) or '—'
        rows.append([k, oni.get(k, {}).get('season', '—'), g(oni, 'roni'), g(oni, 'oni'), g(sm, 'rel_nino34'), g(sm, 'nino34'), g(sm, 'nino12'),
                     g(at, 'soi'), g(at, 'trades_west'), g(at, 'trades_central'), g(at, 'olr_central_pac'), g(sub, 'heat_180_100w'), g(sub, 'wwv_anom'),
                     g(dr, 'dmi_cpc'), g(dr, 'pdo')])
rows = [[r[0]] + [f'<span class="num">{x}</span>' for x in r[1:]] for r in rows]

AB = "abstract read"
refs = [
 # observing system, indices, data
 ("noaa2026", "NOAA National Weather Service (2026). Public Information Notice 26-05: Relative Oceanic Niño Index (RONI), effective 1 February 2026.", None, "https://weather.gov/media/notification/pdf_2026/pns26-05_Relative_ONI.pdf", "read"),
 ("lheureux2024", "L'Heureux, M. L., et al. (2024). A relative sea surface temperature index for classifying ENSO events in a changing climate. <i>Journal of Climate</i> 37, 1197–1211.", "10.1175/JCLI-D-23-0406.1", None, AB),
 ("mcphaden1998tao", "McPhaden, M. J., et al. (1998). The Tropical Ocean–Global Atmosphere observing system: a decade of progress. <i>Journal of Geophysical Research</i> 103(C7), 14169–14240.", "10.1029/97JC02906", None, AB),
 ("huang2017", "Huang, B., et al. (2017). Extended Reconstructed Sea Surface Temperature, version 5 (ERSSTv5): upgrades, validations, and intercomparisons. <i>Journal of Climate</i> 30, 8179–8205.", "10.1175/JCLI-D-16-0836.1", None, AB),
 ("reynolds2007", "Reynolds, R. W., et al. (2007). Daily high-resolution-blended analyses for sea surface temperature. <i>Journal of Climate</i> 20, 5473–5496.", "10.1175/2007JCLI1824.1", None, AB),
 ("wheelerhendon2004", "Wheeler, M. C., and H. H. Hendon (2004). An all-season real-time multivariate MJO index: development of an index for monitoring and prediction. <i>Monthly Weather Review</i> 132, 1917–1932.", "10.1175/1520-0493(2004)132<1917:AARMMI>2.0.CO;2", None, AB),
 ("kiladis2014", "Kiladis, G. N., et al. (2014). A comparison of OLR and circulation-based indices for tracking the MJO. <i>Monthly Weather Review</i> 142, 1697–1715.", "10.1175/MWR-D-13-00301.1", None, AB),
 ("cpc", "NOAA Climate Prediction Center: monthly index files (RONI, ONI, relative and traditional Niño indices, SOI, 850 hPa trade-wind indices, OLR, upper-300 m heat content, IOD); NOAA PMEL warm water volume; PDO (NOAA NCEI). Site copies in the data archive.", None, "https://www.cpc.ncep.noaa.gov/data/indices/", "data read"),
 # recharge and theory
 ("wyrtki1985b", "Wyrtki, K. (1985). Water displacements in the Pacific and the genesis of El Niño cycles. <i>Journal of Geophysical Research</i> 90(C4), 7129–7132.", "10.1029/JC090iC04p07129", None, AB),
 ("jin1997", "Jin, F.-F. (1997). An equatorial ocean recharge paradigm for ENSO. Part I: conceptual model. <i>Journal of the Atmospheric Sciences</i> 54, 811–829.", "10.1175/1520-0469(1997)054<0811:AEORPF>2.0.CO;2", None, AB),
 ("meinen2000", "Meinen, C. S., and M. J. McPhaden (2000). Observations of warm water volume changes in the equatorial Pacific and their relationship to El Niño and La Niña. <i>Journal of Climate</i> 13, 3551–3559.", "10.1175/1520-0442(2000)013<3551:OOWWVC>2.0.CO;2", None, AB),
 # event accounts
 ("mcphaden1999", "McPhaden, M. J. (1999). Genesis and evolution of the 1997–98 El Niño. <i>Science</i> 283, 950–954.", "10.1126/science.283.5404.950", None, AB + "; full text not accessible (paywall)"),
 ("mcphaden1999n", "McPhaden, M. J. (1999). The child prodigy of 1997–98. <i>Nature</i> 398, 559–561.", "10.1038/19193", None, "bibliographic record"),
 ("mcphadenyu1999", "McPhaden, M. J., and X. Yu (1999). Equatorial waves and the 1997–98 El Niño. <i>Geophysical Research Letters</i> 26, 2961–2964.", "10.1029/1999GL004901", None, AB),
 ("wangweisberg2000", "Wang, C., and R. H. Weisberg (2000). The 1997–98 El Niño evolution relative to previous El Niño events. <i>Journal of Climate</i> 13, 488–501.", "10.1175/1520-0442(2000)013<0488:TENOER>2.0.CO;2", None, AB),
 ("picaut2002", "Picaut, J., E. Hackert, A. J. Busalacchi, R. Murtugudde and G. S. E. Lagerloef (2002). Mechanisms of the 1997–1998 El Niño–La Niña, as inferred from space-based observations. <i>Journal of Geophysical Research</i> 107(C5), 3037.", "10.1029/2001JC000850", None, AB),
 ("delcroix2000", "Delcroix, T., B. Dewitte, Y. duPenhoat, F. Masia and J. Picaut (2000). Equatorial waves and warm pool displacements during the 1992–1998 El Niño Southern Oscillation events: observation and modeling. <i>Journal of Geophysical Research</i> 105(C11), 26045–26062.", "10.1029/2000JC900113", None, AB),
 ("kutsuwada2002", "Kutsuwada, K., and M. McPhaden (2002). Intraseasonal variations in the upper equatorial Pacific Ocean prior to and during the 1997–98 El Niño. <i>Journal of Physical Oceanography</i> 32, 1133–1149.", "10.1175/1520-0485(2002)032<1133:IVITUE>2.0.CO;2", None, AB),
 ("boulangermenkes1999", "Boulanger, J.-P., and C. Menkes (1999). Long equatorial wave reflection in the Pacific Ocean from TOPEX/POSEIDON data during the 1992–1998 period. <i>Climate Dynamics</i> 15, 205–225.", "10.1007/s003820050277", None, "bibliographic record (no abstract available)"),
 ("chavez1999", "Chavez, F. P., et al. (1999). Biological and chemical response of the equatorial Pacific Ocean to the 1997–98 El Niño. <i>Science</i> 286, 2126–2131.", "10.1126/science.286.5447.2126", None, AB),
 # westerly wind events, MJO
 ("yurienecker1998", "Yu, L., and M. M. Rienecker (1998). Evidence of an extratropical atmospheric influence during the onset of the 1997–98 El Niño. <i>Geophysical Research Letters</i> 25, 3537–3540.", "10.1029/98GL02628", None, AB),
 ("congwen2003", "Zhu, C., T. Nakazawa and J. Li (2003). Modulation of twin tropical cyclogenesis by the MJO westerly wind burst during the onset period of 1997/98 ENSO. <i>Advances in Atmospheric Sciences</i> 20, 882–898.", "10.1007/BF02915512", None, "bibliographic record (title and authors from Crossref; Crossref lists given and family names inverted)"),
 ("vanoldenborgh2000", "van Oldenborgh, G. J. (2000). What caused the onset of the 1997–98 El Niño? <i>Monthly Weather Review</i> 128, 2601–2607.", "10.1175/1520-0493(2000)128<2601:WCTOOT>2.0.CO;2", None, AB),
 ("lengaigne2002", "Lengaigne, M., J.-P. Boulanger, C. Menkes, S. Masson, G. Madec and P. Delecluse (2002). Ocean response to the March 1997 westerly wind event. <i>Journal of Geophysical Research</i> 107(C12), 8015.", "10.1029/2001JC000841", None, AB),
 ("lengaigne2003", "Lengaigne, M., J.-P. Boulanger, C. Menkes, G. Madec, P. Delecluse, E. Guilyardi and J. Slingo (2003). The March 1997 westerly wind event and the onset of the 1997/98 El Niño: understanding the role of the atmospheric response. <i>Journal of Climate</i> 16, 3330–3343.", "10.1175/1520-0442(2003)016<3330:TMWWEA>2.0.CO;2", None, AB),
 ("boulanger2001", "Boulanger, J.-P., E. Durand, J.-P. Duvel, C. Menkes, P. Delecluse, M. Imbard, M. Lengaigne, G. Madec and S. Masson (2001). Role of non-linear oceanic processes in the response to westerly wind events: new implications for the 1997 El Niño onset. <i>Geophysical Research Letters</i> 28, 1603–1606.", "10.1029/2000GL012364", None, AB),
 ("lengaigne2004", "Lengaigne, M., et al. (2004). Triggering of El Niño by westerly wind events in a coupled general circulation model. <i>Climate Dynamics</i> 23, 601–620.", "10.1007/s00382-004-0457-2", None, "bibliographic record (no abstract available)"),
 ("vialard2001", "Vialard, J., C. Menkes, J.-P. Boulanger, P. Delecluse, E. Guilyardi, M. J. McPhaden and G. Madec (2001). A model study of oceanic mechanisms affecting equatorial Pacific sea surface temperature during the 1997–98 El Niño. <i>Journal of Physical Oceanography</i> 31, 1649–1675.", "10.1175/1520-0485(2001)031<1649:AMSOOM>2.0.CO;2", None, AB),
 ("bergman2001", "Bergman, J. W., H. H. Hendon and K. M. Weickmann (2001). Intraseasonal air–sea interactions at the onset of El Niño. <i>Journal of Climate</i> 14, 1702–1719.", None, "https://journals.ametsoc.org/view/journals/clim/14/8/1520-0442_2001_014_1702_iasiat_2.0.co_2.xml", "full text read (private library copy); DOI not resolved by Crossref with the form tried"),
 ("kesslerkleeman2000", "Kessler, W. S., and R. Kleeman (2000). Rectification of the Madden–Julian oscillation into the ENSO cycle. <i>Journal of Climate</i> 13, 3560–3575.", "10.1175/1520-0442(2000)013<3560:ROTMJO>2.0.CO;2", None, AB),
 ("slingo1999", "Slingo, J. M., D. P. Rowell, K. R. Sperber and F. Nortley (1999). On the predictability of the interannual behaviour of the Madden–Julian oscillation and its relationship with El Niño. <i>Quarterly Journal of the Royal Meteorological Society</i> 125, 583–609.", "10.1256/smsqj.55410", None, "bibliographic record (no abstract available)"),
 ("kessler1995", "Kessler, W. S., M. J. McPhaden and K. M. Weickmann (1995). Forcing of intraseasonal Kelvin waves in the equatorial Pacific. <i>Journal of Geophysical Research</i> 100(C6), 10613–10631.", "10.1029/95JC00382", None, AB),
 ("zhanggottschalck2002", "Zhang, C., and J. Gottschalck (2002). SST anomalies of ENSO and the Madden–Julian oscillation in the equatorial Pacific. <i>Journal of Climate</i> 15, 2429–2445.", "10.1175/1520-0442(2002)015<2429:SAOEAT>2.0.CO;2", None, AB),
 ("hendon2007", "Hendon, H. H., M. C. Wheeler and C. Zhang (2007). Seasonal dependence of the MJO–ENSO relationship. <i>Journal of Climate</i> 20, 531–543.", "10.1175/JCLI4003.1", None, AB),
 ("vecchiharrison2000", "Vecchi, G. A., and D. E. Harrison (2000). Tropical Pacific sea surface temperature anomalies, El Niño, and equatorial westerly wind events. <i>Journal of Climate</i> 13, 1814–1830.", "10.1175/1520-0442(2000)013<1814:TPSSTA>2.0.CO;2", None, AB),
 ("chiodi2014", "Chiodi, A. M., D. E. Harrison and G. A. Vecchi (2014). Subseasonal atmospheric variability and El Niño waveguide warming: observed effects of the Madden–Julian oscillation and westerly wind events. <i>Journal of Climate</i> 27, 3619–3642.", "10.1175/JCLI-D-13-00547.1", None, AB),
 ("seikitakayabu2007", "Seiki, A., and Y. N. Takayabu (2007). Westerly wind bursts and their relationship with intraseasonal variations and ENSO. Part I: statistics. <i>Monthly Weather Review</i> 135, 3325–3345.", "10.1175/MWR3477.1", None, AB),
 ("eisenman2005", "Eisenman, I., L. Yu and E. Tziperman (2005). Westerly wind bursts: ENSO's tail rather than the dog? <i>Journal of Climate</i> 18, 5224–5238.", "10.1175/JCLI3588.1", None, AB),
 ("gebbie2007", "Gebbie, G., I. Eisenman, A. Wittenberg and E. Tziperman (2007). Modulation of westerly wind bursts by sea surface temperature: a semistochastic feedback for ENSO. <i>Journal of the Atmospheric Sciences</i> 64, 3281–3295.", "10.1175/JAS4029.1", None, AB),
 ("fedorov2002", "Fedorov, A. V. (2002). The response of the coupled tropical ocean–atmosphere to westerly wind bursts. <i>Quarterly Journal of the Royal Meteorological Society</i> 128, 1–23.", "10.1002/qj.200212857901", None, AB),
 ("fedorov2003", "Fedorov, A. V., S. L. Harper, S. G. Philander, B. Winter and A. Wittenberg (2003). How predictable is El Niño? <i>Bulletin of the American Meteorological Society</i> 84, 911–920.", "10.1175/BAMS-84-7-911", None, AB),
 ("li2023", "Li, L., et al. (2023). Comparison of Madden–Julian oscillation in three super El Niño events. <i>Frontiers in Earth Science</i> 10, 1021953.", "10.3389/feart.2022.1021953", None, "full text read (open access; private library copy)"),
 ("roundykiladis2007", "Roundy, P. E., and G. N. Kiladis (2007). Analysis of a reconstructed oceanic Kelvin wave dynamic height dataset for the period 1974–2005. <i>Journal of Climate</i> 20, 4341–4355.", "10.1175/JCLI4249.1", None, "full text read (private library copy)"),
 # extratropical / Pacific background
 ("chang2007", "Chang, P., L. Zhang, R. Saravanan, D. J. Vimont, J. C. H. Chiang, L. Ji, H. Seidel and M. K. Tippett (2007). Pacific meridional mode and El Niño–Southern Oscillation. <i>Geophysical Research Letters</i> 34, L16608.", "10.1029/2007GL030302", None, AB),
 ("vimont2003", "Vimont, D. J., J. M. Wallace and D. S. Battisti (2003). The seasonal footprinting mechanism in the Pacific: implications for ENSO. <i>Journal of Climate</i> 16, 2668–2675.", "10.1175/1520-0442(2003)016<2668:TSFMIT>2.0.CO;2", None, AB),
 ("anderson2003", "Anderson, B. T. (2003). Tropical Pacific sea-surface temperatures and preceding sea level pressure anomalies in the subtropical North Pacific. <i>Journal of Geophysical Research</i> 108(D23), 4732.", "10.1029/2003JD003805", None, AB),
 ("mcphadenzhang2002", "McPhaden, M. J., and D. Zhang (2002). Slowdown of the meridional overturning circulation in the upper Pacific Ocean. <i>Nature</i> 415, 603–608.", "10.1038/415603a", None, "bibliographic record"),
 ("mcphadenzhang2004", "McPhaden, M. J., and D. Zhang (2004). Pacific Ocean circulation rebounds. <i>Geophysical Research Letters</i> 31, L18301.", "10.1029/2004GL020727", None, AB),
 # Indian Ocean
 ("webster1999", "Webster, P. J., A. M. Moore, J. P. Loschnigg and R. R. Leben (1999). Coupled ocean–atmosphere dynamics in the Indian Ocean during 1997–98. <i>Nature</i> 401, 356–360.", "10.1038/43848", None, "bibliographic record (no abstract available)"),
 ("saji1999", "Saji, N. H., B. N. Goswami, P. N. Vinayachandran and T. Yamagata (1999). A dipole mode in the tropical Indian Ocean. <i>Nature</i> 401, 360–363.", "10.1038/43854", None, "bibliographic record (no abstract available)"),
 ("murtugudde2000", "Murtugudde, R., J. P. McCreary and A. J. Busalacchi (2000). Oceanic processes associated with anomalous events in the Indian Ocean with relevance to 1997–1998. <i>Journal of Geophysical Research</i> 105(C2), 3295–3306.", "10.1029/1999JC900294", None, AB),
 ("yurienecker1999", "Yu, L., and M. M. Rienecker (1999). Mechanisms for the Indian Ocean warming during the 1997–98 El Niño. <i>Geophysical Research Letters</i> 26, 735–738.", "10.1029/1999GL900072", None, AB),
 ("ueda2000", "Ueda, H., and J. Matsumoto (2000). A possible triggering process of east–west asymmetric anomalies over the Indian Ocean in relation to 1997/98 El Niño. <i>Journal of the Meteorological Society of Japan</i> 78, 803–818.", "10.2151/jmsj1965.78.6_803", None, "bibliographic record"),
 ("annamalai2003", "Annamalai, H., R. Murtugudde, J. Potemra, S.-P. Xie, P. Liu and B. Wang (2003). Coupled dynamics over the Indian Ocean: spring initiation of the zonal mode. <i>Deep-Sea Research II</i> 50, 2305–2330.", "10.1016/S0967-0645(03)00058-4", None, "bibliographic record"),
 ("luo2010", "Luo, J.-J., R. Zhang, S. K. Behera, Y. Masumoto, F.-F. Jin, R. Lukas and T. Yamagata (2010). Interaction between El Niño and extreme Indian Ocean dipole. <i>Journal of Climate</i> 23, 726–742.", "10.1175/2009JCLI3104.1", None, AB),
 ("izumo2010", "Izumo, T., et al. (2010). Influence of the state of the Indian Ocean Dipole on the following year's El Niño. <i>Nature Geoscience</i> 3, 168–172.", "10.1038/ngeo760", None, "bibliographic record"),
 # Atlantic
 ("ham2013", "Ham, Y.-G., J.-S. Kug, J.-Y. Park and F.-F. Jin (2013). Sea surface temperature in the north tropical Atlantic as a trigger for El Niño/Southern Oscillation events. <i>Nature Geoscience</i> 6, 112–116.", "10.1038/ngeo1686", None, "bibliographic record"),
 # heat budget, termination
 ("wangmcphaden2000", "Wang, W., and M. J. McPhaden (2000). The surface-layer heat balance in the equatorial Pacific Ocean. Part II: interannual variability. <i>Journal of Physical Oceanography</i> 30, 2989–3008.", "10.1175/1520-0485(2001)031<2989:TSLHBI>2.0.CO;2", None, AB + "; Crossref gives vol. 30 with a DOI string containing 2001/031"),
 ("harrisonvecchi1999", "Harrison, D. E., and G. A. Vecchi (1999). On the termination of El Niño. <i>Geophysical Research Letters</i> 26, 1593–1596.", "10.1029/1999GL900316", None, AB),
 ("takayabu1999", "Takayabu, Y. N., T. Iguchi, M. Kachi, A. Shibata and H. Kanzawa (1999). Abrupt termination of the 1997–98 El Niño in response to a Madden–Julian oscillation. <i>Nature</i> 402, 279–282.", "10.1038/46254", None, "bibliographic record (no abstract available)"),
 ("vecchi2006a", "Vecchi, G. A., and D. E. Harrison (2006). The termination of the 1997–98 El Niño. Part I: mechanisms of oceanic change. <i>Journal of Climate</i> 19, 2633–2646.", "10.1175/JCLI3776.1", None, AB),
 ("vecchi2006b", "Vecchi, G. A. (2006). The termination of the 1997–98 El Niño. Part II: mechanisms of atmospheric change. <i>Journal of Climate</i> 19, 2647–2664.", "10.1175/JCLI3780.1", None, AB),
 ("lengaigne2006", "Lengaigne, M., J.-P. Boulanger, C. Menkes and H. Spencer (2006). Influence of the seasonal cycle on the termination of El Niño events in a coupled general circulation model. <i>Journal of Climate</i> 19, 1850–1868.", "10.1175/JCLI3706.1", None, AB),
 # prediction
 ("barnston1999", "Barnston, A. G., M. H. Glantz and Y. He (1999). Predictive skill of statistical and dynamical climate models in SST forecasts during the 1997–98 El Niño episode and the 1998 La Niña onset. <i>Bulletin of the American Meteorological Society</i> 80, 217–243.", "10.1175/1520-0477(1999)080<0217:PSOSAD>2.0.CO;2", None, AB),
 ("barnston1999b", "Barnston, A. G., A. Leetmaa, V. E. Kousky, R. E. Livezey, E. A. O'Lenic, H. Van den Dool, A. J. Wagner and D. A. Unger (1999). NCEP forecasts of the El Niño of 1997–98 and its U.S. impacts. <i>Bulletin of the American Meteorological Society</i> 80, 1829–1852.", "10.1175/1520-0477(1999)080<1829:NFOTEN>2.0.CO;2", None, "bibliographic record"),
 ("landseaknaff2000", "Landsea, C. W., and J. A. Knaff (2000). How much skill was there in forecasting the very strong 1997–98 El Niño? <i>Bulletin of the American Meteorological Society</i> 81, 2107–2119.", "10.1175/1520-0477(2000)081<2107:HMSWTI>2.3.CO;2", None, AB),
 ("stockdale1998", "Stockdale, T. N., D. L. T. Anderson, J. O. S. Alves and M. A. Balmaseda (1998). Global seasonal rainfall forecasts using a coupled ocean–atmosphere model. <i>Nature</i> 392, 370–373.", "10.1038/32861", None, "bibliographic record"),
 ("webster1997", "Webster, P. J., and T. N. Palmer (1997). The past and the future of El Niño. <i>Nature</i> 390, 562–564.", "10.1038/37499", None, "bibliographic record"),
 # background climate
 ("trenberthhoar1997", "Trenberth, K. E., and T. J. Hoar (1997). El Niño and climate change. <i>Geophysical Research Letters</i> 24, 3057–3060.", "10.1029/97GL03092", None, AB),
 ("cai2014", "Cai, W., et al. (2014). Increasing frequency of extreme El Niño events due to greenhouse warming. <i>Nature Climate Change</i> 4, 111–116.", "10.1038/nclimate2100", None, "bibliographic record"),
 ("timmermann2018", "Timmermann, A., et al. (2018). El Niño–Southern Oscillation complexity. <i>Nature</i> 559, 535–545.", "10.1038/s41586-018-0252-6", None, "bibliographic record"),
 ("santoso2017", "Santoso, A., M. J. McPhaden and W. Cai (2017). The defining characteristics of ENSO extremes and the strong 2015/2016 El Niño. <i>Reviews of Geophysics</i> 55, 1079–1129.", "10.1002/2017RG000560", None, AB),
]
cite = {k: f'<a href="#ref-{k}">[{i + 1}]</a>' for i, (k, *_) in enumerate(refs)}


def c(*ks):
    return ' '.join(cite[k] for k in ks)


timeline = [
 ["Jul 1995 – Mar 1996", "La Niña: RONI from −0.41 (JAS 1995) to a minimum of −1.02 (OND 1995); back to −0.58 by FMA 1996.", "Strong trades pile warm water in the west.", c('cpc'), "High"],
 ["Dec 1995 – Dec 1996", "Warm water volume turns positive in December 1995 (+0.05 × 10¹⁴ m³) and stays positive all of 1996 (+0.26 to +0.85); heat content east of the Date Line near zero (−0.47 to +0.17 °C).", "Recharge of the equatorial warm-water reservoir after La Niña, the precondition in recharge-oscillator theory.", c('cpc', 'meinen2000', 'jin1997', 'wyrtki1985b'), "Medium–high (TAO-era data)"],
 ["Apr 1996 – Jan 1997", "ENSO-neutral, slightly cool: RONI −0.20 to −0.37; Niño 1+2 −0.7 to −1.6 °C (OISST).", "—", c('cpc'), "High"],
 ["SON 1996", "Warm western-Pacific SST and an eastward-extended warm pool; the same autumn pattern preceded 1989–90 (aborted event) and 1981–82.", "A warm, eastward-extended pool favours MJO convection over the western Pacific.", c('bergman2001'), "Medium (one comparative study)"],
 ["Nov 1996 – Jan 1997", "Equatorial cold SST and high SLP in the east; off-equatorial warm SST and anomalous cyclones in the far west; equatorial wind anomalies over the western Pacific switch from easterly to westerly.", "Off-equatorial cyclones feed equatorial westerlies.", c('wangweisberg2000'), "Medium (one study, FSU winds)"],
 ["Dec 1996", "First strong westerly wind event of the onset series; two exceptionally strong MJOs during winter 1996–97 (Dec 1996 and Feb 1997) cool the western Pacific through cloud shading and then evaporation.", "MJO-embedded westerly bursts begin forcing downwelling Kelvin waves; surface-flux cooling in the west.", c('vanoldenborgh2000', 'bergman2001', 'picaut2002'), "High (several studies)"],
 ["Late 1996 – early 1997", "Westerly bursts embedded in the active MJO are greatly enhanced in the western Pacific by equatorial twin cyclones, induced by northerly cold surges from East Asia and the western North Pacific.", "Extratropical cold surges → twin cyclones → amplified bursts.", c('yurienecker1998', 'congwen2003'), "Medium (one study; SSM/I winds)"],
 ["Jan – Feb 1997", "First warming near the Date Line; heat content rises to +0.56 °C (Jan) and +1.00 °C (Feb); warm water volume +1.64 and +2.14 × 10¹⁴ m³.", "Kelvin-wave deepening of the thermocline on top of the recharged state.", c('wangweisberg2000', 'cpc'), "High"],
 ["Mar 1997", "The strongest westerly wind event of the series. Model response: far-western cooling of about 0.8 °C, the eastern edge of the warm pool displaced about 2000 km in a month, warming of about 0.5 °C along the Kelvin-wave path; nonlinear surface jets near 1 m s⁻¹ at the warm-pool edge. Western-Pacific 850 hPa trade index −3.1 (standardized) for the month.", "Kelvin wave plus rapid eastward advection of the warm pool's edge; the atmospheric response to these SST changes favours further westerlies.", c('lengaigne2002', 'lengaigne2003', 'boulanger2001', 'cpc'), "High (event observations + ocean and atmosphere model experiments)"],
 ["Mar 1997", "Warming appears in the far eastern Pacific (Niño 1+2 −0.45 °C in Feb, +0.23 °C in Mar, +0.80 °C in Apr); a slower westward-spreading warm anomaly from the coast later merges with the eastward-moving one.", "Coastal arrival of the earlier Kelvin waves.", c('wangweisberg2000', 'cpc'), "Medium–high"],
 ["Late Mar – early Apr 1997", "Central-Pacific SST warms as a downwelling Kelvin wave forced by the February MJO passes; the warming is mainly zonal temperature advection by strong eastward currents, and conditions do not revert afterwards.", "Kelvin-wave-induced advection; a lasting change in winds, currents and SST gradient.", c('bergman2001'), "Medium–high (budget with model currents)"],
 ["Apr 1997", "Another westerly wind event (one of the three, with Dec 1996 and Mar 1997, that differ most from 1996). Warm water volume peaks at +3.12 × 10¹⁴ m³; heat content +2.17 °C.", "Recharged reservoir at its maximum as coupling begins.", c('vanoldenborgh2000', 'cpc'), "High"],
 ["1 Jun 1997", "In an ocean model, about 40% of the Niño 3 anomaly comes from the initial thermal state six months earlier and about 50% from wind stress, concentrated at the time and place of the Dec 1996, Mar 1997 and Apr 1997 westerly events; relative to 1996, wind stress is the main difference.", "Quantitative split between precondition and wind triggers.", c('vanoldenborgh2000'), "High for the model result; one model"],
 ["May – Jun 1997", "Coupling established: RONI AMJ +0.83, MJJ +1.20; SOI −1.3 and −1.4; central-Pacific OLR −25.7 and −26.8 W m⁻²; Niño 1+2 +1.83 and +2.79 °C.", "Bjerknes feedback takes over once the central and eastern warm regions join.", c('cpc', 'picaut2002'), "High"],
 ["Jun 1997", "End of the westerly-burst series that ran from December 1996.", "—", c('picaut2002'), "High"],
 ["Jul – Oct 1997", "Rapid growth: RONI JJA +1.50 → SON +2.22; central-Pacific trade index −4.1 and OLR −49.8 W m⁻² in October; much of the western warm water carried east by anomalous surface currents.", "Coupled growth with zonal advection important in the central Pacific.", c('cpc', 'picaut2002', 'wangmcphaden2000'), "High"],
 ["Jul 1997 – Feb 1998", "Indian Ocean: cool SST along and south of the equator in the east, from strong upwelling along the equator and Sumatra; western warm anomalies from July 1997, peaking in February 1998. CPC DMI +0.55 °C (Jul) to +1.39 °C (Nov).", "Reversed Walker circulation and displaced south-east trades over the Indian Ocean; Kelvin and Rossby waves; reduced latent heat loss later.", c('murtugudde2000', 'yurienecker1999', 'webster1999', 'saji1999', 'cpc'), "High (observation); mechanism debated"],
 ["Nov 1997", "Thermocline shoaling begins in the central Pacific and propagates east; near-Date-Line westerly anomalies shift south of the equator; warm water volume falls to +0.66 and turns negative in December (−0.77 × 10¹⁴ m³).", "Seasonal southward shift of the warmest water and its winds forces eastern thermocline shoaling; discharge begins.", c('vecchi2006a', 'vecchi2006b', 'harrisonvecchi1999', 'lengaigne2006', 'cpc'), "High"],
 ["NDJ 1997", "Peak: RONI +2.28 (ONI +2.37). Eastern SST anomalies above 4 °C; December peak in the eastern and central Pacific anomaly patterns.", "Mature coupled state; discharge under way.", c('cpc', 'vecchi2006a', 'wangweisberg2000'), "High"],
 ["Dec 1997 – Apr 1998", "Eastern SST stays warm despite strong subsurface cooling; off-equatorial SLP in the west turns high and easterly anomalies appear over the far western Pacific; easterlies vanish from the eastern equatorial Pacific in February 1998.", "Upwelling Kelvin waves from western easterlies and boundary reflection, Rossby waves from the east, and basin discharge set up the collapse.", c('vecchi2006a', 'vecchi2006b', 'wangweisberg2000', 'picaut2002', 'mcphadenyu1999', 'delcroix2000'), "High"],
 ["Early – mid May 1998", "Abrupt cooling: eastern equatorial SST falls by more than 4 °C within two weeks; about 8 °C near 0°, 130°W; cooling first centred between 125°W and 170°W. Easterlies return to the eastern Pacific.", "Thermocline surfaces once the equatorial easterlies return; an MJO is implicated in the timing.", c('vecchi2006a', 'picaut2002', 'mcphadenyu1999', 'takayabu1999'), "High"],
 ["Jun – Aug 1998", "La Niña: RONI MJJ −0.46, JJA −1.05; record equatorial phytoplankton bloom.", "Upwelling resumes over a discharged basin.", c('cpc', 'chavez1999'), "High"],
]

evidence = [
 ["Warm-water recharge after the 1995–96 La Niña", "WWV positive from Dec 1995 through 1996, peaking at +3.12 × 10¹⁴ m³ in Apr 1997; an ocean model attributes about 40% of the 1 June 1997 Niño 3 anomaly to the initial thermal state.", "A charged reservoir lets Kelvin waves raise eastern SST and sustain growth.", "Precondition", "A−: TAO-era observation + model decomposition for this event", "High", c('cpc', 'meinen2000', 'vanoldenborgh2000', 'picaut2002')],
 ["Westerly wind events, Dec 1996 – Jun 1997", "A series of strong events, notably Dec 1996, Mar 1997 and Apr 1997; wind stress ≈ 50% of the 1 June Niño 3 anomaly and the main difference from 1996.", "Downwelling Kelvin waves and eastward displacement of the warm-pool edge.", "Trigger (and early amplifier)", "A: event observations + ocean-model decomposition + targeted experiments", "High", c('vanoldenborgh2000', 'picaut2002', 'lengaigne2002', 'lengaigne2003', 'yurienecker1998')],
 ["March 1997 event: atmospheric response", "Model SST response to the March event itself generates atmospheric responses favouring growth.", "Burst-forced SST changes → more westerlies (state-dependent feedback).", "Amplifier of the trigger", "A−: ocean + atmosphere GCM experiments for this event", "Medium–high", c('lengaigne2003', 'boulanger2001')],
 ["MJO, winter 1996–97", "Two exceptionally strong MJOs (Dec 1996, Feb 1997); bursts embedded in active MJO; the February MJO's Kelvin wave warms the central Pacific in late Mar–early Apr.", "MJO organises bursts; rectified MJO stresses add warming; Kelvin waves advect warm water.", "Trigger timing / amplifier", "B: event-specific observation and budget; one intermediate-model hindcast (+50% amplitude)", "Medium–high", c('bergman2001', 'yurienecker1998', 'mcphadenyu1999', 'kesslerkleeman2000', 'kutsuwada2002')],
 ["Cold surges and twin cyclones", "Northerly cold surges from East Asia induce equatorial twin cyclones that enhance MJO bursts in late 1996 – early 1997.", "Extratropical forcing amplifies bursts.", "Amplifier of the trigger (extratropical pathway)", "B: one event-specific observational study; a second on twin cyclogenesis (title only)", "Medium", c('yurienecker1998', 'congwen2003')],
 ["Off-equatorial western-Pacific cyclones (Nov 1996 – Jan 1997)", "Off-equatorial warm SST and cyclones accompany the switch to equatorial westerlies.", "Off-equatorial circulation forces equatorial westerlies.", "Trigger component (proposed)", "B/C: one descriptive study", "Medium", c('wangweisberg2000')],
 ["Western-boundary Rossby wave reflection", "Reflection at the western boundary 'appeared favorable' before onset; minor contribution to Kelvin waves.", "Reflected Rossby waves add downwelling Kelvin energy.", "Minor precondition", "B/C: satellite-altimetry studies; magnitude small", "Low–medium", c('picaut2002', 'delcroix2000', 'boulangermenkes1999')],
 ["Bjerknes coupled feedback", "From May–June 1997 SOI, trades, OLR and SST strengthen together to an October–December peak.", "Warming → weaker trades → deeper eastern thermocline → more warming.", "Amplifier / feedback", "B: event observations + general theory; heat budgets show zonal advection important", "High", c('cpc', 'picaut2002', 'wangmcphaden2000')],
 ["State dependence of bursts", "Bursts are more likely when the warm pool extends east, which it did through spring 1997.", "Bursts partly a response to ENSO, effectively increasing coupling.", "Feedback (contested)", "C: multi-event statistics and models, not tested for 1997 alone", "Medium", c('eisenman2005', 'gebbie2007', 'seikitakayabu2007', 'vecchiharrison2000', 'chiodi2014')],
 ["Pacific meridional mode / seasonal footprinting", "Most El Niños of the past four decades preceded by spring warming and south-westerlies near the ITCZ.", "Extratropical winter variability → subtropical SST → equatorial winds.", "Possible precondition", "C: composite and model studies; 1997 not isolated in the abstracts read", "Low", c('chang2007', 'vimont2003', 'anderson2003')],
 ["Pacific decadal background", "PDO positive through 1997 (+1.6 to +2.6 in May–Jun); shallow meridional overturning at a 1992–98 low.", "Weaker overturning → warmer tropical Pacific background; background alters the response to bursts.", "Background (possible precondition)", "C: decadal observations and a simple model; not event attribution", "Low", c('cpc', 'mcphadenzhang2002', 'mcphadenzhang2004', 'fedorov2002')],
 ["Indian Ocean Dipole 1997", "Positive IOD from mid-1997, peaking in Nov (CPC DMI +1.39 °C), after Pacific coupling.", "Walker-circulation reversal → eastern upwelling; Indian Ocean coupled dynamics.", "Mainly consequence; feedback on the Pacific unresolved", "B: event-specific ocean model + observations; coupled-model feedback studies", "Medium", c('murtugudde2000', 'yurienecker1999', 'webster1999', 'saji1999', 'luo2010')],
 ["Tropical North Atlantic", "TNA near or below zero in early 1997 (−0.37 °C in Mar), warm in 1998 (+0.51 °C in May).", "Cool NTA in spring can favour El Niño; warming in 1998 is the usual lagged response.", "Untested trigger; later consequence", "C/D: index only for this event", "Low", c('cpc', 'ham2013')],
 ["Seasonal cycle in termination", "Southward shift of westerly anomalies from Nov 1997; thermocline shoaling from the central Pacific; abrupt SST drop in May 1998.", "Seasonal migration of warmest SST shifts winds south, shoaling the eastern thermocline.", "Termination mechanism", "A: event observations + AGCM and OGCM experiments", "High", c('harrisonvecchi1999', 'vecchi2006a', 'vecchi2006b', 'lengaigne2006')],
 ["MJO at termination (May 1998)", "An MJO in May 1998 implicated in the abrupt end.", "Easterly phase triggers upwelling and surfacing of the thermocline.", "Timing of termination", "B: one event-specific study (abstract not available)", "Medium", c('takayabu1999')],
 ["Volcanic forcing", "No large tropical eruption in 1995–97 (assessment pending a catalogue check).", "—", "Not applicable (to confirm)", "—", "—", "—"],
 ["Background warming", "RONI peak +2.28 vs ONI +2.37: the tropical-mean adjustment changes the peak by 0.09 °C.", "Index statement, not attribution.", "Not attributed", "D for event attribution; projections only", "—", c('lheureux2024', 'trenberthhoar1997', 'cai2014')],
]

sections = [
 {"id": "scope", "title": "Evidence base: scope, index and data", "html": f"""<p><b>Primary index:</b> NOAA's Relative Oceanic Niño Index (RONI), official since 1 February 2026 {c('noaa2026', 'lheureux2024')}. On RONI the 1997–98 peak is +2.28 (NDJ 1997); on the traditional ONI it is +2.37. The two agree within 0.1 °C for this event, unlike 1982–83 (RONI +2.40, ONI +2.14).</p>
<p><b>Observing system in 1997.</b> The first strong El Niño observed by the completed TAO/TRITON mooring array (finished in December 1994), TOPEX/Poseidon altimetry (from 1992), satellite microwave winds and drifting buoys {c('mcphaden1998tao', 'mcphaden1999')}. Onset, growth and termination are therefore documented daily along the equator, which allows heat-budget and wave analyses that were impossible for 1982. Argo did not yet exist; the subsurface off the equator and outside the array remains less certain.</p>"""},
 {"id": "data", "title": "Monthly indices, Jul 1995 – Dec 1998", "html": "<p>Values from NOAA CPC, PMEL and NCEI files as held in the site's data archive; read from the source files, not retyped.</p>",
  "table": {"cols": ["Month", "Season", "RONI", "ONI", "rel. Niño 3.4 (OISST)", "Niño 3.4 (OISST)", "Niño 1+2 (OISST)", "SOI", "W Pac trades", "C Pac trades", "C Pac OLR", "Heat content 180–100°W", "WWV", "DMI (CPC)", "PDO"], "rows": rows, "cls": "data",
            "note": "RONI and ONI are three-month means centred on the month. SOI and trade-wind indices are standardized (negative = El Niño-like). OLR in W m⁻² (negative = more convection). Heat content in °C vs 1981–2010; WWV in 10¹⁴ m³; DMI in °C; PDO standardized."}},
]

status_note = ("Stages 1–3 of 5 (23 Oct 2026): 93 Crossref queries; the 72 references cited are each matched to their Crossref record (one, Bergman et al. 2001, read in full from a private copy) and every available abstract was read; monthly data "
               "Jul 1995 – Dec 1998 assembled; timeline (22 rows) and evidence table (17 factors) drafted from abstracts, one full text "
               "(Bergman et al. 2001) and CPC/PMEL data. In progress: reanalysis MJO and westerly-burst diagnostics, TAO moorings and island sea "
               "level (running in GitHub Actions); full texts requested. Not yet written: the prose sections (stage 4) and verification (stage 5).")

paper = {"number": 2, "file": "enso-1997-98.html", "short": "1997–98 El Niño", "title": "How the 1997–98 El Niño developed",
         "description": "Evidence-based reconstruction of the 1997–98 El Niño (in progress): preconditions, westerly wind events, the MJO, the Indian Ocean and termination, with timeline, evidence table and verified references.",
         "status": "in-progress", "research_date": "23 October 2026", "obs_cutoff": "historical event (Jul 1995 – Dec 1998 analysed)",
         "lit_cutoff": "open, updated as new studies appear", "status_note": status_note,
         "toc": [("scope", "Evidence: scope and data"), ("data", "Monthly indices"), ("timeline", "Timeline"), ("evidence", "Evidence table"), ("references", "References")],
         "sections": sections, "timeline": timeline, "evidence": evidence,
         "references": [{"key": k, "text": t, "doi": d, "url": u, "check": ch} for k, t, d, u, ch in refs]}
with open(ROOT / 'papers' / '2-enso-1997-98.json', 'w', encoding='utf-8') as fh:
    json.dump(paper, fh, ensure_ascii=False, indent=1)
print('ok', len(timeline), len(evidence), len(refs))
