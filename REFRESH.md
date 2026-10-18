# Weekly refresh runbook

Runs every **Friday at about 10 pm Pacific** as a scheduled task. Goal: every dataset in
`data/manifest.json` reflects the latest available official data, nothing stale or truncated
is published, and the live site is redeployed.

## 0. Setup

1. Attach and clone this repo with push access (`cherkasovakatie-ctrl/weatherwatch`, branch `main`).
2. `pip install --break-system-packages -r tools/mundane/requirements.txt pytest`

## 1. Scripted datasets (run first — no judgement needed)

```bash
python3 tools/mundane/build.py          # sky_now, mundane_*, national_*, market_*
python3 -m pytest -q tools/mundane      # must pass before anything is committed
```

`build.py` refuses to publish an S&P file whose last row is more than six months old.

## 1b. Daily scripted refresh (GitHub Actions, 9 am Pacific)

`.github/workflows/nightly.yml` runs `tools/nightly/run.mjs` every day at 9 am Los Angeles time and pushes to `main`.
It refreshes, from public APIs:

- **Daily feeds:** `earthquakes`, `local_obs`, `local_periods`, `local_hourly`, `local_tides`, `local_hilo`,
  `local_watertemp`, `volcano_alerts_us` (USGS, NWS, Open-Meteo, NOAA CO-OPS, USGS HANS); `fires_global_grid`
  (past 24 h) and `fires_socal` (past 5 days) from NASA FIRMS; `space_daily` (NOAA SWPC), `calfire_active`
  (CAL FIRE), `coral_dhw` and `coral_now` (NOAA Coral Reef Watch), `ozone_2026` (NASA Ozone Watch) and the 2026
  columns of `seaice_clim` (NSIDC); `blob_boxes` (NOAA ERSSTv5 via ERDDAP, monthly); `storm_fixes` (NOAA NCEI IBTrACS last3years file, republished every few days).
- **Monthly and weekly indices, checked daily:** `sst_weekly` and `sst_monthly` (CPC Niño SST files), `oni` (ONI and RONI), `ao_aao`, `planet_monthly` (GISTEMP, Mauna Loa CO2,
  Rutgers snow), `sunspots_monthly` (SILSO) and the heat-content column of `enso_subsurface` (CPC). A new month is
  added only when every column of that month has a value; existing months take the source's latest revision.

FIRMS needs a free MAP_KEY, stored only as the repository secret `FIRMS_MAP_KEY`; the script replaces it with
`***` in every error and log line. Merged datasets are first compared with the existing file on overlapping
dates: if values disagree beyond a small tolerance (a sign of a misread column), nothing is written.
Each file is written only if its columns match the existing file, it has enough rows and its newest row is not older
than the current one; otherwise the old file stays. Results are in `data/nightly_status.json`. In the Friday run,
check that file first: re-fetch by hand only the datasets it marks as failed, and skip the ones it refreshed.
Tests: `node --test tools/nightly/transforms.test.mjs tools/nightly/feeds.test.mjs`.

## 2. Agent-fetched datasets

Use the sources named in each dataset's `description` in `data/manifest.json`, the project
instructions ("Weather & ENSO"), and these rules:

- **Read the date on the last row of every fetched file before using it.** Web fetches cap near
  60,000 characters and silently return only the opening rows. A file whose newest row is older
  than the copy already in `data/` is a failed fetch: keep the old file and log it.
- **Every index keeps its dataset, averaging period, date and climatology base.** ONI/RONI are
  centred 3-month means lagging the ocean by ~6 weeks; weekly/daily OISST is the live state.
- CPC standardized SOI is in standard deviations; BOM scale is ×10.
- Backup: the sheet is also published as CSV (File → Publish to web); each tab is readable at
  `https://docs.google.com/spreadsheets/d/e/2PACX-1vSDsjlfm3r3JwgBbm40qXK9d5lsjAwwVjyKs_hh963NuwS3_91QCmndBdqfD7ni1hyVcuNuCgxwlRJg/pub?single=true&output=csv&gid=<tab gid>`
  (SST 824748939, RSST 1898386216, SOI 0, Winds 1686709403, PDO 350267698, MJO 334938232, WWV 1170026920).
- Kate's Google Sheet "Weather Watch_NOAA source data" (ID
  `1rlsO2k4eCqrcAJ6-264_IngDDVBwbafUJwnU3izDPx0`) is the primary source for CPC indices. Read it
  with the Google Drive connector; if the read returns only a sample, fall back to the CPC `.txt`
  files (`oni.ascii.txt`, `RONI.ascii.txt`, `soi.3m.txt`). Extensionless CPC files return binary —
  don't retry them.
- Keep each CSV's existing column layout exactly; the dashboard code reads columns by name.
- Never invent or interpolate a value. If a source can't be read, leave the file as it is.

### Every week

| Group | Datasets |
|---|---|
| ENSO and drivers | `mjo_daily`, `poles_daily`, `enso_subsurface` (WWV column only) |
| Hazards | `tropical_cyclones`, `tc_tracks`, `ace_season`, `gdacs_current`, `volcanoes_weekly`, `impacts` |
| Southern California | `coast_hourly`, `ar_watch`, `ridge_watch`, `cdec_reservoirs` |
| Poles, ocean, space | `polar_stations`, `polar_motion` |
| Blob watch | `#card-blob-watch` in index.html: re-read NOAA's California Current Marine Heatwave Tracker (update date, the southern-coast and Gulf of Alaska heatwaves), the latest PDO and the ridge watch; update the "Now" column, the verdict and the update date |
| Events | `event_analyses` and `data/events/*.json`: update status of unfolding events; add new major events |

### When a new month is out (first refresh after CPC/NOAA publish)

`atmosphere_monthly`, `drivers_monthly`, `sealevel_global` (the others are in the daily script).

### Annual or static — leave alone unless the period has closed

`annual_hazards`, `correlations`, `lag_correlations`, `phase_rates`, `eruption_epoch`,
`quake_tests`, `moon_hist`, `earth_rotation`, `antarctic_stations`, `elnino_pdo`,
`seaice_annual` (after the Arctic minimum / Antarctic maximum), `ozone_annual` (after 13 Oct),
`la_rain` (water year ends 30 Sep), `sky_cycles`, `sky_tests`, `sky_events`, `world_land`, `reports`.

Hand-curated, never auto-refreshed: `paleo_temp12k`, `paleo_pages2k`, `paleo_epica_temp`, `paleo_co2_800k`, `paleo_ch4_800k`, `paleo_sealevel_800k`, `paleo_monsoon_cheng2016`, `paleo_lr04`, `paleo_cenogrid`, `paleo_gts_epochs`, `paleo_studies` (Climate tab; published reconstructions only), `deadliest_events` and `data/history/*.json` (Deadliest events pages). Change these only on request, with sources.

After updating a dataset, set its `updated` field in `data/manifest.json` to today's date.

## 3. Finalize and publish

```bash
python3 tools/refresh/finalize.py        # validates files, stamps dates, archives data/archive/<date>/
git add -A && git commit -m "Weekly refresh YYYY-MM-DD" && git push origin main
```

Then open https://cherkasovakatie-ctrl.github.io/weatherwatch/ (allow a minute for Pages) and
confirm the footer shows the new date.

## 4. Report

End the run with a short summary: datasets refreshed, datasets skipped and why (with the exact
URL that failed, so Kate can pull it manually), and anything that moved materially. Do not email
unless something failed or the ENSO state changed materially against the baseline in the
project instructions.


Report data (`data/report1976/*.csv`, behind warming-since-1976.html) is curated, not part of the weekly refresh. Rebuild only when a source publishes a new edition: `python3 tools/report1976/build.py --igcc <forcing-timeseries clone> --owid <owid-co2-data.csv>`, then re-check every figure quoted in the report text.
