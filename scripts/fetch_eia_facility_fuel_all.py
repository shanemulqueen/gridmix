#!/usr/bin/env python3
"""
Fetch EIA monthly facility-fuel data for ALL plants in the CEMS quarterly
dataset (16 states), broken out by fuel type and prime mover.

The earlier pull in fetch_eia_generation.py was scoped to the 266 COATS
RGGI facilities only, missing OH, WV, NC, DC entirely.

This pull:
  - Sources plant IDs from cems_quarterly_raw_2020_2025.csv (445 plants,
    16 states: the full RGGI + surrounding-states footprint)
  - Requests fuel-type × prime-mover granularity (excludes fuel2002='ALL'
    and primeMover='ALL' rollup rows -- those can be reconstructed by
    summing the fuel-level rows)
  - Fetches 2020-01 onward to align with the CEMS quarterly window
  - API key from env var EIA_API_KEY (never committed)

Outputs:
  data/eia_facility_fuel_monthly_all.csv

Fields:
  period, plantCode, plantName, state, fuel2002, fuelTypeDescription,
  primeMover, generation (net MWh), gross-generation (MWh),
  total-consumption-btu (MMBtu), consumption-for-eg-btu (MMBtu),
  average-heat-content, average-heat-content-units
"""

import os
import sys
import time

import pandas as pd
import requests

API_KEY = os.environ.get("EIA_API_KEY", "")
BASE_URL = "https://api.eia.gov/v2"
CEMS_PATH = "data/cems_quarterly_raw_2020_2025.csv"
OUT_PATH = "data/eia_facility_fuel_monthly_all.csv"
START_PERIOD = "2020-01"
BATCH_SIZE = 50
PAGE_SIZE = 5000

DATA_COLS = [
    "generation",
    "gross-generation",
    "total-consumption-btu",
    "consumption-for-eg-btu",
    "average-heat-content",
]


def fetch_all_pages(base_params):
    results = []
    offset = 0
    while True:
        params = base_params + [("offset", offset), ("length", PAGE_SIZE)]
        resp = requests.get(
            f"{BASE_URL}/electricity/facility-fuel/data",
            params=params,
            timeout=120,
        )
        resp.raise_for_status()
        body = resp.json()["response"]
        data = body["data"]
        results.extend(data)
        offset += len(data)
        if offset >= int(body["total"]) or not data:
            break
        time.sleep(0.15)
    return results


def main():
    if not API_KEY:
        sys.exit("Set EIA_API_KEY environment variable.")

    plant_ids = sorted(
        pd.read_csv(CEMS_PATH, usecols=["facilityId"])["facilityId"]
        .dropna()
        .astype(int)
        .unique()
    )
    print(f"{len(plant_ids)} CEMS plants across 16 states")

    all_rows = []
    batches = [plant_ids[i: i + BATCH_SIZE] for i in range(0, len(plant_ids), BATCH_SIZE)]
    for b_idx, batch in enumerate(batches):
        print(f"  batch {b_idx + 1}/{len(batches)} ({len(batch)} plants)")
        base_params = [
            ("api_key", API_KEY),
            ("frequency", "monthly"),
            ("start", START_PERIOD),
        ]
        for col in DATA_COLS:
            base_params.append(("data[]", col))
        for pid in batch:
            base_params.append(("facets[plantCode][]", str(pid)))
        base_params += [
            ("sort[0][column]", "period"),
            ("sort[0][direction]", "asc"),
        ]
        rows = fetch_all_pages(base_params)
        all_rows.extend(rows)
        print(f"    -> {len(rows)} rows (running total {len(all_rows):,})")
        time.sleep(0.2)

    df = pd.DataFrame(all_rows)
    print(f"\nRaw rows fetched: {len(df):,}")

    # Drop ALL-rollup rows; keep fuel × prime-mover detail only
    df = df[(df["fuel2002"] != "ALL") & (df["primeMover"] != "ALL")]
    print(f"After dropping ALL rollups: {len(df):,} rows")

    for col in DATA_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["plantCode"] = df["plantCode"].astype(str)

    keep = [
        "period", "plantCode", "plantName", "state",
        "fuel2002", "fuelTypeDescription", "primeMover",
        "generation", "gross-generation",
        "total-consumption-btu", "consumption-for-eg-btu",
        "average-heat-content", "average-heat-content-units",
        "generation-units", "gross-generation-units",
    ]
    df = df[[c for c in keep if c in df.columns]]
    df = df.sort_values(["period", "state", "plantCode", "fuel2002", "primeMover"])

    df.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(df):,} rows -> {OUT_PATH}")
    print(f"Period range: {df['period'].min()} to {df['period'].max()}")
    print(f"Unique plants: {df['plantCode'].nunique()}")
    print(f"States: {sorted(df['state'].unique())}")
    print(f"\nTop fuel types by row count:\n{df['fuel2002'].value_counts().head(10).to_string()}")
    print(f"\nTop prime movers:\n{df['primeMover'].value_counts().head(10).to_string()}")

    missing = set(map(str, plant_ids)) - set(df["plantCode"])
    print(f"\nPlants with no EIA data ({len(missing)}): {sorted(missing)[:20]}"
          + (" ..." if len(missing) > 20 else ""))


if __name__ == "__main__":
    main()
