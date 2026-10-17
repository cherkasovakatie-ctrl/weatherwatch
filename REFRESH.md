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

## 2. Agent-fetched datasets

Use the sources named in each dataset's `description` in `data/manifest.json`, the project
instructions ("Weather & ENSO"), and these rules:

- **Read the date on the last row of every fetched file before using it.** Web fetches cap near
  60,000 characters and silently return only the opening rows. A file whose newest row is older
  than the copy already in `data/` is a failed fetch: keep the old file and log it.
- **Every index keeps its dataset, averaging period, date and climatology base.** ONI/RONI are
  centred 3-month means lagging the ocean by ~6 weeks; weekly/daily OISST is the live state.
- CPC standardized SOI is in standard deviations; BOM scale is ×10.
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
| ENSO and drivers | `sst_weekly`, `mjo_daily`, `poles_daily`, `enso_subsurface` |
| Hazards | `earthquakes`, `tropical_cyclones`, `tc_tracks`, `storm_fixes`, `ace_season`, `gdacs_current`, `fires_global_grid`, `fires_socal`, `calfire_active`, `volcanoes_weekly`, `volcano_alerts_us`, `impacts` |
| Southern California | `local_obs`, `local_periods`, `local_hourly`, `local_tides`, `local_hilo`, `local_watertemp`, `coast_hourly`, `ar_watch`, `ridge_watch`, `cdec_reservoirs` |
| Poles, ocean, space | `polar_stations`, `seaice_clim`, `coral_dhw`, `coral_now`, `space_daily`, `polar_motion` |
| Seasonal | `ozone_2026` (Aug–Dec only) |
| Events | `event_analyses` and `data/events/*.json`: update status of unfolding events; add new major events |

### When a new month is out (first refresh after CPC/NOAA publish)

`oni`, `atmosphere_monthly`, `sst_monthly`, `drivers_monthly`, `ao_aao`, `planet_monthly`,
`sunspots_monthly`, `sealevel_global`.

### Annual or static — leave alone unless the period has closed

`annual_hazards`, `correlations`, `lag_correlations`, `phase_rates`, `eruption_epoch`,
`quake_tests`, `moon_hist`, `earth_rotation`, `antarctic_stations`, `elnino_pdo`,
`seaice_annual` (after the Arctic minimum / Antarctic maximum), `ozone_annual` (after 13 Oct),
`la_rain` (water year ends 30 Sep), `sky_cycles`, `sky_tests`, `sky_events`, `world_land`, `reports`.

Hand-curated, never auto-refreshed: `paleo_temp12k`, `paleo_studies` (Climate tab; published reconstructions only), `deadliest_events` and `data/history/*.json` (Deadliest events pages). Change these only on request, with sources.

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
