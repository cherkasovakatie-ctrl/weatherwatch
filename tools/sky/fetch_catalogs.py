"""Fetch USGS ComCat M5.5+ 1973-now and Smithsonian GVP Holocene eruptions into raw/sky/ (run in GitHub Actions)."""
import datetime as dt
import urllib.request
from pathlib import Path

OUT = Path("raw/sky")
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "weatherwatch-research/1.0 (github.com/cherkasovakatie-ctrl/weatherwatch)"}


def get(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    path.write_bytes(data)
    print(path.name, len(data), "bytes")


today = dt.date.today().isoformat()
parts = []
for y0 in range(1973, 2027, 5):
    y1 = min(y0 + 5, 2027)
    end = f"{y1}-01-01" if y1 < 2027 else today
    p = OUT / f"usgs_{y0}.csv"
    get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&minmagnitude=5.5&orderby=time-asc"
        f"&starttime={y0}-01-01&endtime={end}", p)
    parts.append(p)
with open(OUT / "usgs_m55_1973_now.csv", "w", encoding="utf-8") as fh:
    for i, p in enumerate(parts):
        lines = p.read_text(encoding="utf-8").splitlines()
        fh.write("\n".join(lines if i == 0 else lines[1:]) + "\n")
        p.unlink()
for name, layer in [("gvp_eruptions.csv", "Smithsonian_VOTW_Holocene_Eruptions"),
                    ("gvp_volcanoes.csv", "Smithsonian_VOTW_Holocene_Volcanoes")]:
    try:
        get("https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wfs?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName=GVP-VOTW:{layer}&outputFormat=csv", OUT / name)
    except Exception as e:  # noqa: BLE001
        print("GVP failed", layer, e)

for name, url in [("gvp_weekly_rss.xml", "https://volcano.si.edu/news/WeeklyVolcanoRSS.xml"),
                  ("gvp_weekly_page.html", "https://volcano.si.edu/reports_weekly.cfm")]:
    try:
        get(url, OUT / name)
    except Exception as e:  # noqa: BLE001
        print("GVP weekly failed", name, e)
