"""Probe candidate sources for seven new metrics; saves the first 3 kB and last line of each to raw/<date>-probe/."""
import datetime as dt, urllib.request
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-probe'); OUT.mkdir(parents=True, exist_ok=True)
U = {
 '1_iri_plume_page': 'https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/?enso_tab=enso-sst_table',
 '1_iri_plume_json': 'https://iri.columbia.edu/~forecast/ensofcst/Data/ensofcst_ALLto0926',
 '1_cpc_ensodisc': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml',
 '1_cpc_probs': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities.php',
 '1_bom_enso_models': 'https://www.bom.gov.au/climate/model-summary/',
 '2_tao_erddap_t': 'https://erddap.ifremer.fr/erddap/info/index.html',
 '2_pmel_erddap_tao': 'https://data.pmel.noaa.gov/pmel/erddap/griddap/index.html?page=1&itemsPerPage=1000',
 '2_psl_godas_dir': 'https://downloads.psl.noaa.gov/Datasets/godas/',
 '2_cpc_godas_weekly': 'https://www.cpc.ncep.noaa.gov/products/GODAS/',
 '3_psl_r1_uwnd_2026': 'https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/Dailies/pressure/',
 '3_openmeteo_gfs_850': 'https://api.open-meteo.com/v1/gfs?latitude=0&longitude=160&hourly=wind_speed_850hPa,wind_direction_850hPa&past_days=30&forecast_days=10',
 '4_cr_oisst_world': 'https://climatereanalyzer.org/clim/sst_daily/json/oisst2.1_world2_sst_day.json',
 '4_ncei_ohc_700': 'https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/3month/h22-w0-700m.dat',
 '5_nasa_vitalsigns_gmsl': 'https://climate.nasa.gov/system/internal_resources/details/original/121_Global_Sea_Level_Data_File.txt',
 '5_podaac_gmsl': 'https://podaac.jpl.nasa.gov/dataset/NASA_SSH_GMSL_INDICATOR',
 '5_aviso_gmsl': 'https://www.aviso.altimetry.fr/fileadmin/documents/data/products/indic/msl/MSL_Serie_MERGED_Global_AVISO_GIA_Adjust_Filter2m_NRT.txt',
 '5_csiro_cmar': 'https://www.cmar.csiro.au/sealevel/downloads/church_white_gmsl_2011_up.zip',
 '6_swpc_plasma': 'https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json',
 '6_swpc_mag': 'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json',
 '7_cpc_mjo_fcst': 'https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/whindex.shtml',
 '7_bom_rmm_fcst': 'https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt',
 '7_ecmwf_opendata': 'https://data.ecmwf.int/forecasts/',
 'x_piomas': 'https://psc.apl.uw.edu/wordpress/wp-content/uploads/schweiger/ice_volume/PIOMAS.2sst.monthly.Current.v2.1.txt',
 'x_nsidc_greenland_melt': 'https://nsidc.org/greenland-today/',
 'x_usdm': 'https://usdmdataservices.unl.edu/api/USStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=total&startdate=9/1/2026&enddate=10/23/2026&statisticsType=1',
}
log = []
for k, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=60).read()
        (OUT / (k + '.txt')).write_bytes(b[:3000] + b'\n...\n' + b[-1500:]); log.append(f'OK   {k} {len(b)} bytes')
    except Exception as e:
        log.append(f'FAIL {k} {str(e)[:120]}')
(OUT / 'probe_log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log))
