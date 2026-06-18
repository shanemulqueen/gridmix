#!/usr/bin/env python3
"""
Extend CEMS unit-level quarterly emissions/generation beyond 2025Q4 by
applying plant-level year-over-year % changes derived from EIA monthly data.

Method:
  1. Filter EIA facility-fuel to fossil/thermal fuels only (excludes biomass,
     hydro, wind, solar, nuclear, storage -- fuel codes in FOSSIL_FUELS set).
  2. For each plant x calendar month compute:
       yoy_pct = (gross_mwh_this_month / gross_mwh_same_month_prior_year) - 1
     for all months where both current and prior-year EIA actuals exist.
  3. Forecast months (2026-04 onward): predict yoy_pct as the simple mean of
     the same plant x calendar-month yoy_pct over 2023, 2024, 2025.
     Fallback: state-level median yoy_pct for that calendar month if the plant
     has insufficient history.
  4. Convert monthly yoy_pct to quarterly by:
       quarterly_yoy = (sum of 3 current months) / (sum of 3 prior-year months) - 1
     rather than averaging the monthly percentages (avoids distortion when
     individual months are near zero).
  5. Apply quarterly yoy_pct to CEMS unit-level data for the prior-year quarter:
       estimated_gross_mwh = cems_gross_mwh(Q-4) * (1 + quarterly_yoy)
       estimated_co2_tons  = cems_co2_tons(Q-4)  * (1 + quarterly_yoy)
     Emission factor is implicitly held constant (same intensity assumed).

Assumptions accepted by design:
  - Unit-level generation change matches plant-level change (each unit moves
    proportionally with its plant).
  - Emission intensity (co2/MWh) is constant relative to one year prior.

Inputs:
  data/eia_facility_fuel_monthly_all.csv
  data/cems_quarterly_clean_2020_2025.csv

Outputs:
  data/plant_yoy_monthly_eia.csv     -- plant x month yoy_pct (actual + forecast)
  data/cems_extended_quarterly.csv   -- unit x quarter: cems_actual + cems_extended
"""

import pandas as pd
import numpy as np

EIA_PATH  = "data/eia_facility_fuel_monthly_all.csv"
CEMS_PATH = "data/cems_quarterly_clean_2020_2025.csv"
OUT_YOY   = "data/plant_yoy_monthly_eia.csv"
OUT_EXT   = "data/cems_extended_quarterly.csv"

FOSSIL_FUELS = {
    "NG", "OG", "BFG", "PG",
    "DFO", "RFO", "KER", "JF", "WO",
    "BIT", "SUB", "RC", "PC", "ANT", "LIG", "SC", "WC", "TDF", "MSN",
}
LAST_CEMS_YEAR, LAST_CEMS_QUARTER = 2025, 4
EXTEND_QUARTERS = [(2026, q) for q in range(1, 5)]   # 2026Q1-Q4
QUARTER_MONTHS  = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9), 4: (10, 11, 12)}

# Plants with prior-year quarterly fossil generation below this threshold are
# excluded from the plant-level YoY (their ratio is unreliable) and instead
# receive the state-level median fallback.  10 GWh/quarter ≈ ~13 MW avg load.
MIN_PRIOR_YEAR_MWH = 10_000
# After filtering low-base plants, winsorise remaining ratios.
YOY_LOWER_CLIP = -0.75   # max −75% decline
YOY_UPPER_CLIP =  1.00   # max +100% growth


# ── Step 1: EIA plant-level monthly fossil thermal generation ────────────────

def load_eia_fossil_monthly():
    eia = pd.read_csv(EIA_PATH, dtype={"plantCode": str})
    eia = eia[eia["fuel2002"].isin(FOSSIL_FUELS)].copy()
    eia["year"]  = eia["period"].str[:4].astype(int)
    eia["month"] = eia["period"].str[5:7].astype(int)
    pm = (
        eia.groupby(["plantCode", "state", "period", "year", "month"], as_index=False)
        .agg(fossil_gross_mwh=("gross-generation", "sum"),
             fossil_mmbtu=("consumption-for-eg-btu", "sum"))
    )
    return pm


# ── Step 2 & 3: Compute actual YoY and forecast ──────────────────────────────

def compute_yoy(pm):
    pm = pm.copy()
    prior = pm.rename(columns={
        "period": "prior_period",
        "year":   "prior_year",
        "fossil_gross_mwh": "fossil_gross_mwh_py",
        "fossil_mmbtu":     "fossil_mmbtu_py",
    })
    prior["year"] = prior["prior_year"] + 1  # shift up by 1 year to align

    actual = pm.merge(
        prior[["plantCode", "year", "month", "fossil_gross_mwh_py", "fossil_mmbtu_py"]],
        on=["plantCode", "year", "month"], how="left",
    )
    actual["yoy_pct"] = (
        actual["fossil_gross_mwh"] / actual["fossil_gross_mwh_py"].replace(0, np.nan) - 1
    )
    actual["source"] = "eia_actual"
    return actual


def build_forecast_yoy(actual, state_map):
    """
    For each plant x calendar month, predict yoy_pct as the mean of the
    same plant x month from 2023, 2024, 2025 actual observations.
    Fallback: state-level median for that calendar month.
    """
    base = actual[actual["year"].isin([2023, 2024, 2025]) & actual["yoy_pct"].notna()]
    plant_seasonal = (
        base.groupby(["plantCode", "state", "month"])["yoy_pct"]
        .mean()
        .reset_index()
        .rename(columns={"yoy_pct": "yoy_pct_forecast"})
    )
    state_seasonal = (
        base.groupby(["state", "month"])["yoy_pct"]
        .median()
        .reset_index()
        .rename(columns={"yoy_pct": "state_yoy_median"})
    )

    # Only generate forecasts for months NOT already in EIA actuals
    actual_periods = set(actual["period"].unique())

    rows = []
    for year, quarter in EXTEND_QUARTERS:
        for month in QUARTER_MONTHS[quarter]:
            ym = f"{year:04d}-{month:02d}"
            if ym in actual_periods:
                continue   # EIA actual exists; no forecast row needed
            plants = actual[["plantCode", "state"]].drop_duplicates()
            tmp = plants.merge(plant_seasonal[plant_seasonal["month"] == month],
                               on=["plantCode", "state"], how="left")
            tmp = tmp.merge(state_seasonal[state_seasonal["month"] == month],
                            on="state", how="left")
            tmp["yoy_pct"] = tmp["yoy_pct_forecast"].combine_first(tmp["state_yoy_median"])
            tmp["period"]  = ym
            tmp["year"]    = year
            tmp["month"]   = month
            tmp["source"]  = "eia_forecast"
            tmp["fossil_gross_mwh"]    = np.nan
            tmp["fossil_gross_mwh_py"] = np.nan
            tmp["fossil_mmbtu"]        = np.nan
            rows.append(tmp[["plantCode", "state", "period", "year", "month",
                              "fossil_gross_mwh", "fossil_gross_mwh_py",
                              "fossil_mmbtu", "yoy_pct", "source"]])

    if not rows:
        return pd.DataFrame(columns=["plantCode","state","period","year","month",
                                     "fossil_gross_mwh","fossil_gross_mwh_py",
                                     "fossil_mmbtu","yoy_pct","source"])
    return pd.concat(rows, ignore_index=True)


# ── Step 4: Monthly → quarterly yoy ─────────────────────────────────────────

def monthly_to_quarterly_yoy(yoy_df):
    """
    For actual periods: sum current month gross / sum prior-year month gross - 1.
    For forecast periods: simple mean of the 3 monthly yoy_pct values.
    """
    yoy_df = yoy_df.copy()
    yoy_df["quarter"] = (yoy_df["month"] - 1) // 3 + 1

    # Actual quarters: ratio of sums; require minimum prior-year base
    act = yoy_df[yoy_df["source"] == "eia_actual"].copy()
    act_q = act.groupby(["plantCode", "state", "year", "quarter"]).apply(
        lambda g: pd.Series({
            "quarterly_yoy": (
                g["fossil_gross_mwh"].sum() / g["fossil_gross_mwh_py"].sum() - 1
                if g["fossil_gross_mwh_py"].sum() >= MIN_PRIOR_YEAR_MWH else np.nan
            ),
            "n_months": g["yoy_pct"].notna().sum(),
            "source": "eia_actual",
        }),
        include_groups=False,
    ).reset_index()
    act_q["quarterly_yoy"] = act_q["quarterly_yoy"].clip(YOY_LOWER_CLIP, YOY_UPPER_CLIP)

    # Forecast quarters: mean of monthly forecasts; clip same bounds
    fct = yoy_df[yoy_df["source"] == "eia_forecast"].copy()
    fct_q = fct.groupby(["plantCode", "state", "year", "quarter"]).agg(
        quarterly_yoy=("yoy_pct", "mean"),
        n_months=("yoy_pct", "count"),
        source=("source", "first"),
    ).reset_index()
    fct_q["quarterly_yoy"] = fct_q["quarterly_yoy"].clip(YOY_LOWER_CLIP, YOY_UPPER_CLIP)

    q = pd.concat([act_q, fct_q], ignore_index=True)

    # Fallback to state median where plant quarterly_yoy is NaN
    state_q = q[q["quarterly_yoy"].notna()].groupby(["state", "year", "quarter"])["quarterly_yoy"].median()
    def fill(row):
        if pd.notna(row["quarterly_yoy"]):
            return row["quarterly_yoy"]
        key = (row["state"], row["year"], row["quarter"])
        return state_q.get(key, np.nan)
    q["quarterly_yoy"] = q.apply(fill, axis=1)

    return q


# ── Step 5: Apply to CEMS ────────────────────────────────────────────────────

def extend_cems(cems, quarterly_yoy):
    # Base: keep all CEMS actuals
    actual_cols = ["facilityId", "unitId", "stateCode", "year", "quarter",
                   "grossLoad", "co2Mass", "rggi_obligated",
                   "camd_rggi_program", "coats_unit_match", "coats_facility_match"]
    actual = cems[actual_cols].copy()
    actual["source"] = "cems_actual"
    actual = actual.rename(columns={"grossLoad": "gross_mwh", "co2Mass": "co2_tons"})

    # Deduplicate quarterly_yoy: prefer eia_actual over eia_forecast for same key
    qyoy = (
        quarterly_yoy
        .sort_values("source", ascending=True)   # eia_actual < eia_forecast
        .drop_duplicates(subset=["plantCode", "year", "quarter"], keep="first")
    )
    state_yoy_df = (
        qyoy[qyoy["quarterly_yoy"].notna()]
        .groupby(["state", "year", "quarter"])["quarterly_yoy"]
        .median()
        .reset_index()
        .rename(columns={"quarterly_yoy": "state_quarterly_yoy"})
    )

    rows = []
    for year, quarter in EXTEND_QUARTERS:
        base_year, base_quarter = year - 1, quarter
        base = cems[(cems["year"] == base_year) & (cems["quarter"] == base_quarter)].copy()
        if base.empty:
            continue

        base = base.copy()
        base["oris"] = base["facilityId"].astype(str)

        # Plant-level YoY via merge
        yoy_slice = qyoy[(qyoy["year"] == year) & (qyoy["quarter"] == quarter)][
            ["plantCode", "quarterly_yoy"]
        ].rename(columns={"plantCode": "oris", "quarterly_yoy": "plant_yoy"})
        base = base.merge(yoy_slice, on="oris", how="left")

        # State fallback via merge
        state_slice = state_yoy_df[
            (state_yoy_df["year"] == year) & (state_yoy_df["quarter"] == quarter)
        ][["state", "state_quarterly_yoy"]].rename(columns={"state": "stateCode"})
        base = base.merge(state_slice, on="stateCode", how="left")

        applied_yoy = base["plant_yoy"].combine_first(base["state_quarterly_yoy"])

        ext = base[actual_cols].copy()
        ext["year"]            = year
        ext["quarter"]         = quarter
        ext["gross_mwh"]       = base["grossLoad"] * (1 + applied_yoy.values)
        ext["co2_tons"]        = base["co2Mass"]   * (1 + applied_yoy.values)
        ext["yoy_pct_applied"] = applied_yoy.values
        ext["source"]          = "cems_extended"
        ext = ext.drop(columns=["grossLoad", "co2Mass"], errors="ignore")
        rows.append(ext)

    actual["yoy_pct_applied"] = np.nan
    extended = pd.concat([actual] + rows, ignore_index=True)
    extended = extended.sort_values(["stateCode", "facilityId", "unitId", "year", "quarter"])
    return extended


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading EIA fossil monthly...")
    pm = load_eia_fossil_monthly()
    print(f"  {len(pm):,} plant-month rows, {pm['plantCode'].nunique()} plants")

    print("Computing YoY (actual + forecast)...")
    actual_yoy = compute_yoy(pm)
    state_map  = pm[["plantCode", "state"]].drop_duplicates()
    forecast_yoy = build_forecast_yoy(actual_yoy, state_map)

    yoy_monthly = pd.concat(
        [actual_yoy, forecast_yoy], ignore_index=True
    ).sort_values(["plantCode", "period"])
    yoy_monthly.to_csv(OUT_YOY, index=False)
    print(f"  Saved {len(yoy_monthly):,} rows -> {OUT_YOY}")

    print("Rolling to quarterly YoY...")
    quarterly_yoy = monthly_to_quarterly_yoy(yoy_monthly)
    quarterly_yoy = quarterly_yoy.rename(columns={"plantCode": "plantCode"})

    print("Loading CEMS and extending...")
    cems = pd.read_csv(CEMS_PATH, dtype={"unitId": str})
    extended = extend_cems(cems, quarterly_yoy)
    extended.to_csv(OUT_EXT, index=False)
    print(f"  Saved {len(extended):,} rows -> {OUT_EXT}")

    print("\n--- Summary ---")
    by_source = extended.groupby("source").agg(
        n_rows=("facilityId", "count"),
        n_units=("unitId", "nunique"),
        gross_mwh=("gross_mwh", "sum"),
        co2_tons=("co2_tons", "sum"),
    )
    print(by_source.to_string())

    print("\n--- 2026 extended quarters: obligated unit totals by state ---")
    ext_only = extended[extended["source"] == "cems_extended"]
    cov = ext_only[ext_only["rggi_obligated"] == True]
    print(cov.groupby(["stateCode", "year", "quarter"]).agg(
        co2_tons=("co2_tons", "sum"),
        gross_mwh=("gross_mwh", "sum"),
    ).round(0).to_string())

    print("\n--- YoY pct sanity check: median quarterly by state (actual 2025) ---")
    q2025 = quarterly_yoy[quarterly_yoy["year"] == 2025]
    print(q2025.groupby("state")["quarterly_yoy"].median().mul(100).round(1).to_string())

    print("\n--- YoY pct forecast: median quarterly by state (2026) ---")
    q2026 = quarterly_yoy[quarterly_yoy["year"] == 2026]
    print(q2026.groupby("state")["quarterly_yoy"].median().mul(100).round(1).to_string())


if __name__ == "__main__":
    main()
