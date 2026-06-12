#!/usr/bin/env python3
"""
Covered vs non-covered emissions/generation summary for all states, by quarter.

Method:
  - CEMS gross generation and CO2 aggregated to plant level.
  - A plant is "covered" in a given quarter if ANY of its units is obligated
    under the regime in force that quarter (regime_for() from
    build_regime_flags picks the applicable flag column automatically).
  - Capacity factor is plant-level: quarterly-average EIA nameplate MW
    (eia_plant_capacity_monthly.csv) x hours in the quarter vs CEMS gross MWh.
    ~2% of gross load sits at plants with no EIA capacity match; those plants
    are excluded from BOTH numerator and denominator of the capacity factor
    (but still counted in co2/MWh totals), so CF is not overstated.

Inputs:
  data/cems_quarterly_clean_2020_2025.csv
  data/unit_regime_flags.csv
  data/eia_plant_capacity_monthly.csv

Output: data/state_quarter_covered_summary.csv (long format)
  state, year, quarter, regime, group (covered / not_covered / all),
  n_plants, co2_tons, gross_mwh, co2_lb_per_mwh,
  nameplate_mw, gross_mwh_capmatched, capacity_factor
"""

import calendar
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_regime_flags import regime_for, REGIMES  # noqa: E402

CEMS_PATH = "data/cems_quarterly_clean_2020_2025.csv"
FLAGS_PATH = "data/unit_regime_flags.csv"
CAP_PATH = "data/eia_plant_capacity_monthly.csv"
OUT_PATH = "data/state_quarter_covered_summary.csv"

QUARTER_MONTHS = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9), 4: (10, 11, 12)}


def hours_in_quarter(year, quarter):
    days = sum(calendar.monthrange(year, m)[1] for m in QUARTER_MONTHS[quarter])
    return days * 24


def main():
    cems = pd.read_csv(CEMS_PATH, dtype={"unitId": str})
    plant_q = (
        cems.groupby(["stateCode", "facilityId", "year", "quarter"], as_index=False)
        .agg(co2_tons=("co2Mass", "sum"), gross_mwh=("grossLoad", "sum"))
    )
    plant_q["oris"] = plant_q["facilityId"].astype(str)

    flags = pd.read_csv(FLAGS_PATH, dtype={"oris": str})
    plant_flags = flags.groupby("oris")[list(REGIMES)].any()

    plant_q["regime"] = [
        regime_for(y, q) for y, q in zip(plant_q["year"], plant_q["quarter"])
    ]
    flag_lookup = plant_flags.stack()
    plant_q["covered"] = [
        bool(flag_lookup.get((o, r), False))
        for o, r in zip(plant_q["oris"], plant_q["regime"])
    ]

    cap = pd.read_csv(CAP_PATH, dtype={"plantid": str})
    cap["year"] = cap["period"].str[:4].astype(int)
    cap["month"] = cap["period"].str[5:7].astype(int)
    cap["quarter"] = (cap["month"] - 1) // 3 + 1
    cap_q = (
        cap.groupby(["plantid", "year", "quarter"], as_index=False)
        .agg(nameplate_mw=("nameplate_mw", "mean"))
    )
    plant_q = plant_q.merge(
        cap_q.rename(columns={"plantid": "oris"}),
        on=["oris", "year", "quarter"], how="left",
    )

    def summarize(g):
        has_cap = g["nameplate_mw"].notna()
        return pd.Series({
            "n_plants": len(g),
            "co2_tons": g["co2_tons"].sum(),
            "gross_mwh": g["gross_mwh"].sum(),
            "nameplate_mw": g.loc[has_cap, "nameplate_mw"].sum(),
            "gross_mwh_capmatched": g.loc[has_cap, "gross_mwh"].sum(),
        })

    frames = []
    for group_name, mask in [
        ("covered", plant_q["covered"]),
        ("not_covered", ~plant_q["covered"]),
        ("all", pd.Series(True, index=plant_q.index)),
    ]:
        sub = plant_q[mask]
        agg = (
            sub.groupby(["stateCode", "year", "quarter", "regime"])
            .apply(summarize, include_groups=False)
            .reset_index()
        )
        agg["group"] = group_name
        frames.append(agg)

    out = pd.concat(frames, ignore_index=True)
    gross = out["gross_mwh"].where(out["gross_mwh"] > 0)
    out["co2_lb_per_mwh"] = out["co2_tons"] * 2000 / gross
    hours = [hours_in_quarter(y, q) for y, q in zip(out["year"], out["quarter"])]
    denom = (out["nameplate_mw"] * hours).where(out["nameplate_mw"] > 0)
    out["capacity_factor"] = out["gross_mwh_capmatched"] / denom

    out = out.rename(columns={"stateCode": "state"})
    out = out[["state", "year", "quarter", "regime", "group", "n_plants",
               "co2_tons", "gross_mwh", "co2_lb_per_mwh",
               "nameplate_mw", "gross_mwh_capmatched", "capacity_factor"]]
    out = out.sort_values(["state", "year", "quarter", "group"])
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out):,} rows -> {OUT_PATH}")

    print("\n--- Validation: VA covered CO2 by quarter (should match "
          "va_co2_by_quarter_groups.csv where regimes align) ---")
    va = out[(out["state"] == "VA") & (out["group"] == "covered")]
    print(va[["year", "quarter", "regime", "co2_tons", "co2_lb_per_mwh",
              "capacity_factor"]].to_string(index=False))

    print("\n--- 2024 annual covered CO2 by state (RGGI-10 sanity check) ---")
    cov24 = out[(out["group"] == "covered") & (out["year"] == 2024)]
    print(cov24.groupby("state")["co2_tons"].sum().round(0).to_string())


if __name__ == "__main__":
    main()
