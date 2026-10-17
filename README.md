# Global Weather Watch

An independent, pole-to-pole dashboard of El Niño and the climate system, extreme weather and natural hazards, the poles, space weather and Earth's rotation — built from public data.

**Live site:** https://cherkasovakatie-ctrl.github.io/weatherwatch/

- `index.html` — the dashboard (static; charts drawn with d3 from the CSV files in `data/`)
- `data/` — the latest datasets, `data/manifest.json` lists them; `data/archive/YYYY-MM-DD/` holds dated snapshots
- `mundane.html` — Global Mundane Timeline, National Charts and market-cycle tests
- `data.html` — data archive with downloads · `about.html` — sources and method
- `tools/mundane/` — ephemeris engine that builds the mundane datasets (`python3 tools/mundane/build.py`, tests with `pytest`)
- `REFRESH.md` — the weekly Friday refresh runbook; `tools/refresh/finalize.py` stamps and archives each snapshot

Not an official forecast or warning service. Data credits are listed on each chart and in `about.html`.
