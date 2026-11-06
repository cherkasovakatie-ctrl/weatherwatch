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

try:
    get("https://volcano.si.edu/news/WeeklyVolcanoRSS.xml", OUT / "gvp_weekly_rss.xml")
    # keep every week: archive under the report period named in the first item title
    import re
    import xml.etree.ElementTree as ET
    first = ET.parse(OUT / "gvp_weekly_rss.xml").getroot().find("channel/item/title").text or ""
    m = re.search(r"Report for (.+?) - ", first)
    tag = re.sub(r"[^0-9A-Za-z]+", "_", m.group(1)).strip("_") if m else today
    arch = OUT / "gvp_weekly"
    arch.mkdir(exist_ok=True)
    (arch / f"{tag}.xml").write_bytes((OUT / "gvp_weekly_rss.xml").read_bytes())
    print("archived weekly report", tag)
except Exception as e:  # noqa: BLE001
    print("GVP weekly failed", e)

for name, url in [
    ("kp_ap_sn_f107_since_1932.txt", "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt"),
    ("pb2002_boundaries.json", "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json"),
    ("pb2002_plates.json", "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_plates.json"),
]:
    try:
        get(url, OUT / name)
    except Exception as e:  # noqa: BLE001
        print("failed", name, e)
