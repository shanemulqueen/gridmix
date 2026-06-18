#!/usr/bin/env python3
"""
Estimate plant-level CO2 emissions from EIA monthly fuel consumption data
and project 12 months forward using a seasonal average forecast.

IMPORTANT: EIA facility-fuel is plant x fuel type level, not unit level.
This cannot replicate CEMS unit-level granularity but is suitable for the
plant-level covered/not-covered analysis.

Method:
  estimated_co2_tons = consumption-for-eg-btu (MMBtu)
                       x CO2_factor (lb CO2/MMBtu, EPA 40 CFR Part 98 Table C-1)
                       / 2000

Validation: EIA-estimated CO2 is compared to CEMS actual CO2 for the
2020Q1-2025Q4 overlap period to quantify method bias (see validation output).

Forecast: for each plant x fuel x month-of-year, the mean of 2023/2024/2025
EIA consumption is used as the seasonal baseline. Trend is not applied;
consumption is held at the 3-year seasonal average.

Inputs:
  data/eia_facility_fuel_monthly_all.csv
  data/cems_quarterly_clean_2020_2025.csv   (validation only)

Outputs:
  data/eia_emissions_estimated.csv          -- plant x fuel x month, 2020-2027-03
  data/eia_vs_cems_co2_validation.csv       -- plant-quarter comparison for 2020-2025
"""

import pandas as pd
import numpy as np

EIA_PATH = "data/eia_facility_fuel_monthly_all.csv"
CEMS_PATH = "data/cems_quarterly_clean_2020_2025.csv"
OUT_EST = "data/eia_emissions_estimated.csv"
OUT_VAL = "data/eia_vs_cems_co2_validation.csv"

# EPA 40 CFR Part 98 Table C-1 default CO2 emission factors (lb CO2 / MMBtu)
# Source: https://www.ecfr.gov/current/title-40/part-98/appendix-Table_C-1
CO2_LB_PER_MMBTU = {
    # Fossil gas
    "NG":  117.0,   # Natural Gas
    "OG":  117.0,   # Other Gas (assume NG-equivalent)
    "BFG": 274.3,   # Blast Furnace Gas
    "PG":  140.0,   # Petroleum Gas
    # Fossil liquid
    "DFO": 163.1,   # Distillate Fuel Oil No. 2
    "RFO": 173.7,   # Residual Fuel Oil
    "KER": 159.3,   # Kerosene
    "JF":  156.3,   # Jet Fuel / Waste Oils
    "WO":  161.3,   # Waste Oil
    # Fossil solid
    "BIT": 205.7,   # Bituminous Coal
    "SUB": 213.0,   # Subbituminous Coal
    "RC":  205.7,   # Refined Coal (treat as bituminous)
    "WC":  205.7,   # Waste Coal
    "PC":  225.1,   # Petroleum Coke
    "ANT": 228.6,   # Anthracite
    "LIG": 215.4,   # Lignite
    "SC":  205.7,   # Synthetic Coal
    # Other combustible (non-biogenic)
    "TDF": 189.5,   # Tire-Derived Fuel
    "MSN": 200.0,   # Municipal Solid Waste — Non-biogenic (estimated)
    "SLW":  11.0,   # Sewage Sludge (low fossil carbon fraction)
    # Biogenic / carbon-neutral under RGGI accounting -> 0
    "WDS":   0.0,   # Wood Waste Solids
    "BLQ":   0.0,   # Black Liquor
    "OBS":   0.0,   # Other Biomass Solids
    "OBL":   0.0,   # Other Biomass Liquids
    "OBG":   0.0,   # Other Biomass Gas
    "LFG":   0.0,   # Landfill Gas
    "MSB":   0.0,   # Municipal Solid Waste — Biogenic
    # Non-combustion (no CO2 from generation itself)
    "WAT":   0.0,   # Hydro
    "SUN":   0.0,   # Solar
    "WND":   0.0,   # Wind
    "NUC":   0.0,   # Nuclear
    "MWH":   0.0,   # Storage (battery)
}
UNKNOWN_FACTOR = None  # OTH and any missing codes → NaN


def apply_factors(df):
    df = df.copy()
    df["co2_factor_lb_per_mmbtu"] = df["fuel2002"].map(CO2_LB_PER_MMBTU)
    df["estimated_co2_tons"] = (
        df["consumption-for-eg-btu"] * df["co2_factor_lb_per_mmbtu"] / 2000
    )
    return df


def build_forecast(eia_actual, forecast_start="2026-04", n_months=12):
    """
    Seasonal average forecast: mean of last 3 years (2023/2024/2025) by
    plant x fuel x month-of-year, projected forward n_months from
    forecast_start. Returns rows in the same format as eia_actual.
    """
    base = eia_actual[eia_actual["year"].isin([2023, 2024, 2025])].copy()
    seasonal = (
        base.groupby(["plantCode", "state", "fuel2002", "primeMover", "month"],
                     as_index=False)
        .agg({
            "consumption-for-eg-btu": "mean",
            "gross-generation": "mean",
            "generation": "mean",
        })
    )

    periods = pd.date_range(forecast_start, periods=n_months, freq="MS")
    rows = []
    for period in periods:
        ym = period.strftime("%Y-%m")
        m = period.month
        slice_ = seasonal[seasonal["month"] == m].copy()
        slice_["period"] = ym
        slice_["year"] = period.year
        slice_["quarter"] = (m - 1) // 3 + 1
        slice_["source"] = "forecast"
        # Carry plantName forward
        name_map = eia_actual[["plantCode", "plantName"]].drop_duplicates("plantCode")
        slice_ = slice_.merge(name_map, on="plantCode", how="left")
        rows.append(slice_)

    return pd.concat(rows, ignore_index=True)


def main():
    eia = pd.read_csv(EIA_PATH, dtype={"plantCode": str})
    eia["year"]    = eia["period"].str[:4].astype(int)
    eia["month"]   = eia["period"].str[5:7].astype(int)
    eia["quarter"] = (eia["month"] - 1) // 3 + 1
    eia["source"]  = "eia_actual"

    # Split: EIA periods already in CEMS window vs. gap (2026+)
    last_cems_period = "2025-12"
    eia_actual = eia[eia["period"] <= last_cems_period].copy()
    eia_gap    = eia[eia["period"] >  last_cems_period].copy()

    # Apply emission factors to actuals and gap
    eia_actual = apply_factors(eia_actual)
    eia_gap    = apply_factors(eia_gap)
    eia_gap["source"] = "eia_gap_fill"

    # Build 12-month forecast from 2026-04
    forecast = build_forecast(eia_actual, forecast_start="2026-04", n_months=12)
    forecast  = apply_factors(forecast)

    all_cols = [
        "period", "plantCode", "plantName", "state",
        "fuel2002", "primeMover", "year", "quarter",
        "consumption-for-eg-btu", "gross-generation", "generation",
        "co2_factor_lb_per_mmbtu", "estimated_co2_tons", "source",
    ]
    combined = pd.concat(
        [eia_actual[all_cols], eia_gap[all_cols], forecast[all_cols]],
        ignore_index=True,
    )
    combined = combined.sort_values(
        ["plantCode", "fuel2002", "primeMover", "period"]
    )
    combined.to_csv(OUT_EST, index=False)
    print(f"Saved {len(combined):,} rows -> {OUT_EST}")
    print(f"  Period range: {combined['period'].min()} to {combined['period'].max()}")
    print(f"  Sources: {combined['source'].value_counts().to_dict()}")

    # --- Validation: EIA-estimated vs CEMS actual CO2 ---
    cems = pd.read_csv(CEMS_PATH, dtype={"unitId": str})
    cems_plant_q = (
        cems.groupby(["facilityId", "stateCode", "year", "quarter"], as_index=False)
        .agg(cems_co2_tons=("co2Mass", "sum"), cems_gross_mwh=("grossLoad", "sum"))
    )
    cems_plant_q["oris"] = cems_plant_q["facilityId"].astype(str)

    eia_est_q = (
        eia_actual.groupby(["plantCode", "year", "quarter"], as_index=False)
        .agg(
            eia_co2_tons=("estimated_co2_tons", "sum"),
            eia_gross_mwh=("gross-generation", "sum"),
            eia_mmbtu=("consumption-for-eg-btu", "sum"),
        )
    )

    val = cems_plant_q.merge(
        eia_est_q, left_on=["oris", "year", "quarter"],
        right_on=["plantCode", "year", "quarter"], how="inner",
    )
    active = val[val["cems_co2_tons"] > 0].copy()
    active["pct_diff"] = (
        (active["eia_co2_tons"] - active["cems_co2_tons"])
        / active["cems_co2_tons"] * 100
    )
    active["abs_diff_tons"] = active["eia_co2_tons"] - active["cems_co2_tons"]
    active.to_csv(OUT_VAL, index=False)
    print(f"\nSaved {len(active):,} validation rows -> {OUT_VAL}")

    print("\n--- Validation: EIA-estimated vs CEMS CO2 (plant-quarters, CEMS > 0) ---")
    desc = active["pct_diff"].describe(percentiles=[.05, .25, .5, .75, .95])
    print(desc.round(2).to_string())

    print("\n--- Aggregate validation ---")
    cems_tot = active["cems_co2_tons"].sum()
    eia_tot  = active["eia_co2_tons"].sum()
    print(f"  CEMS actual CO2:     {cems_tot:>16,.0f} short tons")
    print(f"  EIA estimated CO2:   {eia_tot:>16,.0f} short tons")
    delta = eia_tot - cems_tot
    print(f"  Delta:               {delta:>16,.0f} short tons  ({delta/cems_tot*100:.2f}%)")

    print("\n--- Annual aggregate delta by state ---")
    ann = (
        active.groupby(["stateCode", "year"])
        .agg(cems=("cems_co2_tons", "sum"), eia=("eia_co2_tons", "sum"))
        .reset_index()
    )
    ann["pct_diff"] = (ann["eia"] - ann["cems"]) / ann["cems"] * 100
    print(ann.to_string(index=False))

    print("\n--- Forecast summary: estimated annual CO2 by state (2026-04 to 2027-03) ---")
    fc_ann = (
        forecast.groupby("state")
        .agg(forecast_co2_tons=("estimated_co2_tons", "sum"),
             forecast_gross_mwh=("gross-generation", "sum"))
        .reset_index()
    )
    print(fc_ann.sort_values("state").to_string(index=False))


if __name__ == "__main__":
    main()
