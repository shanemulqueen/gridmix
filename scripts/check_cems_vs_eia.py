#!/usr/bin/env python3
"""
Cross-check EPA CAMD CEMS quarterly gross generation against EIA monthly
facility-fuel data aggregated to quarterly, for the subset of plants
present in both datasets.

Comparison basis: gross generation (MWh)
  - CEMS:  grossLoad summed to plant-quarter
  - EIA:   gross-generation summed across fuel-type x prime-mover rows to
           plant-quarter (ALL-rollup rows already excluded in the source file)

Metric hierarchy:
  1. Plant-quarter pct difference distribution (p5/p25/median/p75/p95)
  2. Aggregate annual totals by state (absolute and pct delta)
  3. Largest absolute outliers (plants where CEMS and EIA diverge most)
  4. Plants with data in one source but not the other

Output: printed report + data/cems_eia_generation_check.csv (plant-quarter
detail with both values and pct diff, for further inspection)
"""

import pandas as pd
import numpy as np

CEMS_PATH = "data/cems_quarterly_clean_2020_2025.csv"
EIA_PATH = "data/eia_facility_fuel_monthly_all.csv"
OUT_PATH = "data/cems_eia_generation_check.csv"


def eia_to_quarterly(eia):
    eia = eia.copy()
    eia["year"] = eia["period"].str[:4].astype(int)
    eia["month"] = eia["period"].str[5:7].astype(int)
    eia["quarter"] = (eia["month"] - 1) // 3 + 1
    q = (
        eia.groupby(["plantCode", "state", "year", "quarter"], as_index=False)
        .agg(eia_gross_mwh=("gross-generation", "sum"),
             eia_net_mwh=("generation", "sum"),
             eia_mmbtu=("consumption-for-eg-btu", "sum"))
    )
    return q


def main():
    cems = pd.read_csv(CEMS_PATH, dtype={"unitId": str})
    cems_plant = (
        cems.groupby(["facilityId", "stateCode", "year", "quarter"], as_index=False)
        .agg(cems_gross_mwh=("grossLoad", "sum"),
             cems_co2_tons=("co2Mass", "sum"))
    )
    cems_plant["oris"] = cems_plant["facilityId"].astype(str)

    eia = pd.read_csv(EIA_PATH, dtype={"plantCode": str})
    eia_q = eia_to_quarterly(eia)
    eia_q = eia_q.rename(columns={"plantCode": "oris"})

    # Only plants present in CEMS
    shared = set(cems_plant["oris"]) & set(eia_q["oris"])
    cems_only = set(cems_plant["oris"]) - set(eia_q["oris"])
    eia_only = set(eia_q["oris"]) - set(cems_plant["oris"])

    print(f"CEMS plants:        {cems_plant['oris'].nunique()}")
    print(f"EIA plants:         {eia_q['oris'].nunique()}")
    print(f"Shared:             {len(shared)}")
    print(f"CEMS only (no EIA): {len(cems_only)}")
    print(f"EIA only (no CEMS): {len(eia_only)}")

    merged = cems_plant.merge(
        eia_q, on=["oris", "year", "quarter"], how="inner"
    )
    merged["pct_diff"] = (
        (merged["eia_gross_mwh"] - merged["cems_gross_mwh"])
        / merged["cems_gross_mwh"].replace(0, np.nan)
        * 100
    )
    merged["abs_diff_mwh"] = merged["eia_gross_mwh"] - merged["cems_gross_mwh"]

    print(f"\nMatched plant-quarters: {len(merged):,}")

    # Filter to quarters where CEMS shows real generation to avoid noise from
    # zero-gen plant-quarters
    active = merged[merged["cems_gross_mwh"] > 0].copy()
    print(f"Active (CEMS > 0 MWh):  {len(active):,}")

    print("\n--- Pct difference distribution (EIA vs CEMS gross MWh) ---")
    desc = active["pct_diff"].describe(percentiles=[.05, .25, .5, .75, .95])
    print(desc.round(2).to_string())

    print("\n--- Annual aggregate by state (active plant-quarters) ---")
    annual = (
        active.groupby(["stateCode", "year"])
        .agg(cems_total=("cems_gross_mwh", "sum"),
             eia_total=("eia_gross_mwh", "sum"))
        .reset_index()
    )
    annual["pct_diff"] = (annual["eia_total"] - annual["cems_total"]) / annual["cems_total"] * 100
    print(annual.to_string(index=False))

    print("\n--- Aggregate across all states and years ---")
    cems_tot = active["cems_gross_mwh"].sum()
    eia_tot = active["eia_gross_mwh"].sum()
    print(f"  CEMS total gross MWh:  {cems_tot:>18,.1f}")
    print(f"  EIA  total gross MWh:  {eia_tot:>18,.1f}")
    print(f"  Difference:            {eia_tot - cems_tot:>18,.1f}  ({(eia_tot-cems_tot)/cems_tot*100:.3f}%)")

    print("\n--- Largest absolute divergences (plant-quarters, |diff| > 50k MWh) ---")
    big = active[active["abs_diff_mwh"].abs() > 50_000].sort_values("abs_diff_mwh")
    if len(big):
        name_map = cems[["facilityId","facilityName"]].drop_duplicates()
        name_map["oris"] = name_map["facilityId"].astype(str)
        big = big.merge(name_map[["oris","facilityName"]], on="oris", how="left")
        print(big[["oris","facilityName","stateCode","year","quarter",
                   "cems_gross_mwh","eia_gross_mwh","pct_diff"]].to_string(index=False))
    else:
        print("  None.")

    print("\n--- EIA gross vs net spread (active rows, median pct) ---")
    spread = active.merge(
        eia_q[["oris","year","quarter","eia_net_mwh"]].rename(columns={"oris":"oris"}),
        on=["oris","year","quarter"], how="left"
    )
    spread["gross_net_pct"] = (
        (spread["eia_gross_mwh"] - spread["eia_net_mwh"])
        / spread["eia_gross_mwh"].replace(0, np.nan) * 100
    )
    print(f"  Median station-service share: {spread['gross_net_pct'].median():.2f}%")
    print(f"  Mean:                         {spread['gross_net_pct'].mean():.2f}%")

    # Save plant-quarter detail
    save_cols = ["oris","stateCode","year","quarter",
                 "cems_gross_mwh","eia_gross_mwh","eia_net_mwh",
                 "abs_diff_mwh","pct_diff","cems_co2_tons","eia_mmbtu"]
    available = [c for c in save_cols if c in merged.columns]
    merged[available].sort_values(["stateCode","oris","year","quarter"]).to_csv(OUT_PATH, index=False)
    print(f"\nDetail saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
