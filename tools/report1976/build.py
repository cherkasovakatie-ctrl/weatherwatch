"""Build the data files behind the 'Warming since 1976' report charts.

Inputs (paths are arguments so the script never fetches anything itself):
  --igcc  clone of github.com/ClimateIndicator/forcing-timeseries (IGCC 2024 ERF + CEDS v2025-03-18)
  --owid  owid-co2-data.csv from github.com/owid/co2-data (Global Carbon Budget 2025; Jones et al. 2025)

Outputs go to data/report1976/. Every series stops at the last year its source publishes;
nothing is interpolated or extrapolated.
"""

from __future__ import annotations

import argparse
import collections
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "report1976"

FORCING_COLS = [
    "CO2", "CH4", "N2O", "halogen", "O3", "H2O_stratospheric", "aerosol", "land_use",
    "BC_on_snow", "contrails", "solar", "volcanic", "anthro", "total",
]  # fmt: skip

CH4_GROUPS = {
    "Livestock (digestion and manure)": ("3E_", "3B_"),
    "Rice paddies": ("3D_",),
    "Coal mining": ("1B1",),
    "Oil and gas production and pipelines": ("1B2",),
    "Landfills and wastewater": ("5",),
}
SO2_GROUPS = {
    "Power and heat plants": ("1A1",),
    "Industry (fuel burning, metals, cement)": ("1A2", "2"),
    "International shipping": ("1A3di_International-shipping",),
    "Road, rail, aviation and other transport": ("1A3",),
    "Homes and buildings": ("1A4", "1A5"),
    "Oil, gas and coal production": ("1B",),
}


def group_of(sector: str, groups: dict[str, tuple[str, ...]]) -> str:
    # Exact sector names first (shipping), then the longest matching prefix.
    for name, prefixes in groups.items():
        if sector in prefixes:
            return name
    best, best_len = "Other", 0
    for name, prefixes in groups.items():
        for p in prefixes:
            if sector.startswith(p) and len(p) > best_len:
                best, best_len = name, len(p)
    return best


def write(name: str, header: list[str], rows: list[list]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows, last {rows[-1][0] if rows else '-'}")


def r3(v: float | None) -> str:
    return "" if v is None else f"{v:.4f}"


def forcing(igcc: Path) -> None:
    rows = []
    with open(
        igcc / "output" / "ERF_best_aggregates_1750-2024.csv", encoding="utf-8"
    ) as fh:
        recs = list(csv.DictReader(fh))
    for r in recs:
        y = int(float(r[""]))
        if y >= 1850:
            rows.append([y] + [r3(float(r[c])) for c in FORCING_COLS])
    write("forcing_by_agent.csv", ["year"] + FORCING_COLS, rows)


def ceds(igcc: Path, gas: str, groups: dict[str, tuple[str, ...]], start: int) -> None:
    fn = (
        igcc
        / "data"
        / "slcf_emissions"
        / "ceds"
        / "v20250318"
        / f"{gas}_CEDS_global_emissions_by_sector_v_2025_03_18.csv"
    )
    with open(fn, encoding="utf-8") as fh:
        recs = list(csv.DictReader(fh))
    years = sorted(
        int(k[1:]) for k in recs[0] if k.startswith("X") and int(k[1:]) >= start
    )
    names = list(groups) + ["Other"]
    tot = {y: collections.Counter() for y in years}
    for r in recs:
        g = group_of(r["sector"], groups)
        for y in years:
            tot[y][g] += float(r[f"X{y}"] or 0) / 1000  # kt -> Mt
    rows = [[y] + [f"{tot[y][n]:.3f}" for n in names] for y in years]
    write(f"{gas.lower()}_by_sector.csv", ["year"] + names, rows)


def owid(path: Path) -> None:
    by: dict[str, dict[int, dict]] = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by[r["country"]][int(r["year"])] = r

    def g(c: str, y: int, k: str) -> float | None:
        v = by[c].get(y, {}).get(k)
        return float(v) if v else None

    fuels = [
        "coal_co2",
        "oil_co2",
        "gas_co2",
        "cement_co2",
        "flaring_co2",
        "other_industry_co2",
        "land_use_change_co2",
    ]
    rows = []
    for y in range(1950, 2100):
        if y not in by["World"]:
            break
        rows.append([y] + [f"{(g('World', y, k) or 0) / 1000:.4f}" for k in fuels])
    write(
        "co2_by_fuel_world.csv", ["year"] + [k.replace("_co2", "") for k in fuels], rows
    )

    rows = []
    for y in range(1851, 2100):
        if y not in by["World"] or g("World", y, "temperature_change_from_ghg") is None:
            break
        rows.append(
            [y]
            + [
                r3(g("World", y, k))
                for k in (
                    "temperature_change_from_co2",
                    "temperature_change_from_ch4",
                    "temperature_change_from_n2o",
                )
            ]
        )
    write("ghg_warming_world.csv", ["year", "co2", "ch4", "n2o"], rows)

    def z(v: float | None) -> float:
        return v or 0.0

    iso = {c: by[c][max(by[c])]["iso_code"] for c in by}
    world = g("World", 2024, "temperature_change_from_ghg") - g(
        "World", 1976, "temperature_change_from_ghg"
    )
    res = []
    for c in by:
        if (
            not iso[c]
            or iso[c].startswith("OWID")
            or g(c, 2024, "temperature_change_from_ghg") is None
        ):
            continue

        def d(k: str, c: str = c) -> float:
            return z(g(c, 2024, k)) - z(g(c, 1976, k))

        cum = lambda k, c=c: sum(z(g(c, y, k)) for y in range(1976, 2025)) / 1000
        res.append([c, d("temperature_change_from_ghg"), d("temperature_change_from_co2"), d("temperature_change_from_ch4"),
                    d("temperature_change_from_n2o"), cum("co2"), cum("land_use_change_co2"), z(g(c, 2024, "co2_per_capita")),
                    z(g(c, 2024, "population")) / 1e6])  # fmt: skip
    # Top 20, extended to keep countries tied at the cut-off together (the source resolves 0.001 C).
    res.sort(key=lambda r: (-round(r[1], 3), r[0]))
    cut = round(res[19][1], 3)
    top = [r for r in res if round(r[1], 3) >= cut]
    rest = [r for r in res if round(r[1], 3) < cut]
    out = [
        [r[0]]
        + [f"{v:.4f}" for v in r[1:5]]
        + [f"{r[5]:.1f}", f"{r[6]:.1f}", f"{r[7]:.2f}", f"{r[8]:.0f}"]
        for r in top
    ]
    out.append([f"All other countries ({len(rest)})", f"{sum(r[1] for r in rest):.4f}", f"{sum(r[2] for r in rest):.4f}",
                f"{sum(r[3] for r in rest):.4f}", f"{sum(r[4] for r in rest):.4f}", f"{sum(r[5] for r in rest):.1f}",
                f"{sum(r[6] for r in rest):.1f}", "", f"{sum(r[8] for r in rest):.0f}"])  # fmt: skip
    write("country_ghg_warming_1976_2024.csv",
          ["country", "dT_ghg", "dT_co2", "dT_ch4", "dT_n2o", "fossil_co2_gt_1976_2024", "landuse_co2_gt_1976_2024",
           "co2_per_capita_t_2024", "population_m_2024"], out)  # fmt: skip
    print(
        f"world GHG warming 1976->2024: {world:.3f} C; countries sum {sum(r[1] for r in res):.3f}"
    )

    groups = [
        "High-income countries",
        "Upper-middle-income countries",
        "Lower-middle-income countries",
        "Low-income countries",
    ]
    rows = [[c, f"{z(g(c, 2024, 'temperature_change_from_ghg')) - z(g(c, 1976, 'temperature_change_from_ghg')):.4f}",
             f"{z(g(c, 2024, 'population')) / 1e6:.0f}"] for c in groups]  # fmt: skip
    write(
        "income_group_ghg_warming_1976_2024.csv",
        ["group", "dT_ghg", "population_m_2024"],
        rows,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--igcc", type=Path, required=True)
    ap.add_argument("--owid", type=Path, required=True)
    a = ap.parse_args()
    forcing(a.igcc)
    ceds(a.igcc, "CH4", CH4_GROUPS, 1970)
    ceds(a.igcc, "SO2", SO2_GROUPS, 1950)
    owid(a.owid)


if __name__ == "__main__":
    main()
