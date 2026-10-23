"""Fetch full pages for the ENSO forecast plume (IRI model plume, IRI/CPC probabilities, CPC discussion, BoM summary)."""
import datetime as dt, urllib.request
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-plume'); OUT.mkdir(parents=True, exist_ok=True)
U = {
 'iri_sst_table': 'https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/?enso_tab=enso-sst_table',
 'iri_plume_tab': 'https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/?enso_tab=enso-iri_plume',
 'iri_cpc_probs': 'https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/?enso_tab=enso-cpc_plume',
 'iri_forecast_dir': 'https://iri.columbia.edu/~forecast/ensofcst/Data/',
 'iri_ensofcst_dir': 'https://iri.columbia.edu/~forecast/ensofcst/',
 'cpc_ensodisc': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml',
 'bom_models': 'https://www.bom.gov.au/climate/model-summary/',
}
log = []
for k, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 GlobalWeatherWatch/1.0'}), timeout=60).read()
        (OUT / (k + '.html')).write_bytes(b); log.append(f'OK   {k} {len(b)}')
    except Exception as e:
        log.append(f'FAIL {k} {str(e)[:150]}')
(OUT / 'log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log))
