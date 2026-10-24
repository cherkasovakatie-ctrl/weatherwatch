"""Shared helpers for the 2026 storm papers: numbers from IBTrACS (track_stats.json), the OISST environment file and the RMM index."""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T = json.loads((ROOT / 'data/tc2026/track_stats.json').read_text())
ENV = [r for r in csv.DictReader(open(ROOT / 'data/tc2026/env_2026.csv', encoding='utf-8'))]
MJO = {r['date']: r for r in csv.DictReader(open(ROOT / 'data/mjo_daily.csv', encoding='utf-8'))}
CAT = {5: 'Category 5', 4: 'Category 4', 3: 'Category 3', 2: 'Category 2', 1: 'Category 1', 'TS': 'tropical storm', 'TD': 'depression'}
MON = 'January February March April May June July August September October November December'.split()


def day(t):
    return f'{int(t[8:10])} {MON[int(t[5:7]) - 1]}'


def dtm(t):
    return f'{int(t[8:10])} {MON[int(t[5:7]) - 1][:3]} {t[11:13]}00 UTC'


def kt2mph(k):
    return round(int(k) * 1.15078 / 5) * 5


def kt2kmh(k):
    return round(int(k) * 1.852 / 5) * 5


def pos(lat, lon):
    lat, lon = float(lat), float(lon)
    return f"{abs(lat):.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°{'W' if lon < 0 else 'E'}"


def env(name):
    return [r for r in ENV if r['name'] == name]


def env_at(name, t):
    return next(r for r in ENV if r['name'] == name and r['time'].startswith(t))


def sst_summary(name, until=None):
    L = [r for r in env(name) if r['sst_pre_c'] not in ('nan', '') and (until is None or r['time'] <= until)]
    s = [float(r['sst_pre_c']) for r in L]; a = [float(r['ssta_pre_c']) for r in L]; w = [float(r['sst_wake_c']) for r in L if r['sst_wake_c'] not in ('nan', '')]
    return dict(n=len(L), sst_mean=statistics.mean(s), sst_max=max(s), sst_min=min(s), ssta_mean=statistics.mean(a), ssta_max=max(a), ssta_min=min(a), wake_min=min(w) if w else None)


def mjo(d):
    r = MJO.get(d)
    return (int(r['phase']), float(r['amplitude'])) if r else None


def facts(name, extra=()):
    o = T[name]
    rows = [['Source of winds and pressures', 'JTWC 1-minute values (IBTrACS USA fields); JMA is the WMO centre' if o['basin'] == 'WP' else 'NHC operational values'],
            ['First and last fix (UTC)', f"{dtm(o['first'])} – {dtm(o['last'])}"],
            ['First fix position', pos(*o['genesis'])],
            ['Peak 1-minute wind', f"{o['peak_kt']} kt ({kt2mph(o['peak_kt'])} mph, {kt2kmh(o['peak_kt'])} km/h), {CAT[o['peak_cat']]}, {dtm(o['peak_time'])} near {pos(*o['peak_pos'])}"],
            ['Lowest pressure', f"{o['min_pres']} mb" if o['min_pres'] else '—'],
            ['Largest 24-hour increase', f"{o['max_24h_change'][2]} kt ({dtm(o['max_24h_change'][0])} to {dtm(o['max_24h_change'][1])})"],
            ['Time at tropical-storm / hurricane / major strength', f"{o['hours_ts']} / {o['hours_hu']} / {o['hours_major']} hours"],
            ['Accumulated cyclone energy (ACE)', f"{o['ace']:.1f} × 10⁴ kt²"],
            ['Track length and mean speed', f"{o['track_km']:,} km at {o['mean_speed_kmh']} km/h"]]
    return rows + [list(x) for x in extra]


def fig(name, caption):
    return (f'<figure><img src="papers/img/tc2026_{name.lower()}.png" alt="{name.title()} 2026: intensity, pressure and sea-surface temperature along the track" style="max-width:100%;height:auto">'
            f'<figcaption class="note">{caption}</figcaption></figure>')


METHODS = ("<p><b>Track and intensity.</b> Six-hourly positions, 1-minute maximum sustained winds and minimum pressures from IBTrACS v04r01 <a href=\"#ref-knapp2010\">[1]</a>, "
           "downloaded on 24 October 2026. For 2026 these are <i>provisional</i> values carried over from the operational advisories ({agency}); the official best track, issued in the post-season report, can differ. "
           "Rapid intensification (RI) is an increase of at least 30 kt in 24 hours <a href=\"#ref-kaplan2003\">[2]</a>. Accumulated cyclone energy (ACE) sums the squared 6-hourly winds at tropical-storm strength or above.</p>"
           "<p><b>Ocean.</b> Sea-surface temperature (SST) and its anomaly against 1991–2020 from NOAA OISST v2.1 daily <a href=\"#ref-huang2021\">[3]</a>, sampled at each 6-hourly position three days before the storm arrived, so that the storm's own cooling is excluded; the change from three days before to three days after gives the cold wake. OISST is a 0.25° analysis and smooths very small wakes.</p>"
           "<p><b>Atmosphere.</b> Wind shear and mid-level humidity are taken from the forecasters' own analyses in the advisories and discussions (which use the SHIPS model and satellite estimates), quoted with date and time. "
           "In addition, the deep-layer (200–850 hPa) vertical wind shear was computed from ERA5 (Hersbach et al. 2020, in the references) as the difference of the winds averaged over a 200–800 km ring around each position, using daily means of 00 and 12 UTC on a 2.5° grid, with data to 18 October 2026. This coarse estimate captures the large-scale shear but not shallower or mid-level shear, which forecasters sometimes cite. The Madden–Julian oscillation (MJO) is described by the real-time RMM index <a href=\"#ref-wheeler2004\">[4]</a> (phase and amplitude; amplitude ≥ 1 means an active MJO). "
           "ENSO values are NOAA CPC indices (RONI JAS 2026 +1.69 °C; weekly relative Niño 3.4 +2.4 °C in mid-October).</p>"
           "<p><b>Impacts.</b> Deaths, damage and observations are taken from official statements where available and otherwise from wire-service reports, each cited; figures are preliminary.</p>")

REFS = {
    'knapp2010': ("Knapp, K. R., M. C. Kruk, D. H. Levinson, H. J. Diamond and C. J. Neumann (2010). The International Best Track Archive for Climate Stewardship (IBTrACS). <i>Bulletin of the American Meteorological Society</i> 91, 363–376. Data: IBTrACS v04r01, NOAA NCEI (2026 positions provisional).", '10.1175/2009BAMS2755.1', None, 'bibliographic record; data read'),
    'kaplan2003': ("Kaplan, J., and M. DeMaria (2003). Large-scale characteristics of rapidly intensifying tropical cyclones in the North Atlantic basin. <i>Weather and Forecasting</i> 18, 1093–1108.", '10.1175/1520-0434(2003)018<1093:LCORIT>2.0.CO;2', None, 'abstract read'),
    'huang2021': ("Huang, B., et al. (2021). Improvements of the Daily Optimum Interpolation Sea Surface Temperature (DOISST) Version 2.1. <i>Journal of Climate</i> 34, 2923–2939. Data via NOAA PSL.", '10.1175/JCLI-D-20-0166.1', None, 'abstract read; data read'),
    'wheeler2004': ("Wheeler, M. C., and H. H. Hendon (2004). An all-season real-time multivariate MJO index: development of an index for monitoring and prediction. <i>Monthly Weather Review</i> 132, 1917–1932.", '10.1175/1520-0493(2004)132<1917:AARMMI>2.0.CO;2', None, 'abstract read'),
    'price1981': ("Price, J. F. (1981). Upper ocean response to a hurricane. <i>Journal of Physical Oceanography</i> 11, 153–175.", '10.1175/1520-0485(1981)011<0153:UORTAH>2.0.CO;2', None, 'abstract read'),
    'maloney2000': ("Maloney, E. D., and D. L. Hartmann (2000). Modulation of eastern North Pacific hurricanes by the Madden–Julian oscillation. <i>Journal of Climate</i> 13, 1451–1460.", '10.1175/1520-0442(2000)013<1451:MOENPH>2.0.CO;2', None, 'abstract read'),
    'carrasco2014': ("Carrasco, C. A., C. W. Landsea and Y.-L. Lin (2014). The influence of tropical cyclone size on its intensification. <i>Weather and Forecasting</i> 29, 582–590.", '10.1175/WAF-D-13-00092.1', None, 'abstract read'),
    'klotzbach2010': ("Klotzbach, P. J. (2010). On the Madden–Julian oscillation–Atlantic hurricane relationship. <i>Journal of Climate</i> 23, 282–293.", '10.1175/2009JCLI2978.1', None, 'abstract read'),
    'gray1984': ("Gray, W. M. (1984). Atlantic seasonal hurricane frequency. Part I: El Niño and 30 mb quasi-biennial oscillation influences. <i>Monthly Weather Review</i> 112, 1649–1668.", '10.1175/1520-0493(1984)112<1649:ASHFPI>2.0.CO;2', None, 'abstract read'),
    'wang2002': ("Wang, B., and J. C. L. Chan (2002). How strong ENSO events affect tropical storm activity over the western North Pacific. <i>Journal of Climate</i> 15, 1643–1658.", '10.1175/1520-0442(2002)015<1643:HSEEAT>2.0.CO;2', None, 'abstract read'),
    'camargo2005': ("Camargo, S. J., and A. H. Sobel (2005). Western North Pacific tropical cyclone intensity and ENSO. <i>Journal of Climate</i> 18, 2996–3006.", '10.1175/JCLI3457.1', None, 'abstract read'),
    'csu': ("Colorado State University, Department of Atmospheric Science: real-time tropical cyclone season statistics (ACE and storm counts to date by basin), read 22–23 October 2026; site copy data/ace_season.csv.", None, 'https://tropical.atmos.colostate.edu/Realtime/', 'data read'),
    'hersbach2020': ("Hersbach, H., et al. (2020). The ERA5 global reanalysis. <i>Quarterly Journal of the Royal Meteorological Society</i> 146, 1999–2049. 2026 data: Copernicus Climate Change Service Climate Data Store (u, v at 850 and 200 hPa, to 18 October 2026).", '10.1002/qj.3803', None, 'full text read (open access); data processed'),
    'paper4': ("Global Weather Watch (2026). The 2026 El Niño against 1982–83, 1997–98 and 2015–16: a preliminary comparison (Paper 4).", None, 'enso-2026.html', 'own analysis'),
}


def refs(keys, extra=()):
    out = [{'key': k, 'text': REFS[k][0], 'doi': REFS[k][1], 'url': REFS[k][2], 'check': REFS[k][3]} for k in keys]
    for k, t, u, c in extra:
        out.append({'key': k, 'text': t, 'doi': None, 'url': u, 'check': c})
    return out


def num(keys):
    """Map reference keys to their numbers in the final list."""
    return {k: i + 1 for i, k in enumerate(keys)}


SH = [r for r in csv.DictReader(open(ROOT / 'data/tc2026/era5_shear.csv', encoding='utf-8'))]


def shear(name):
    """List of (time, shear_kt) where ERA5 is available."""
    return [(r['time'], float(r['shear_kt'])) for r in SH if r['name'] == name and r['shear_kt'] != '']


def shear_between(name, a, b):
    v = [x for t, x in shear(name) if a <= t <= b]
    return (min(v), max(v), sum(v) / len(v)) if v else None
