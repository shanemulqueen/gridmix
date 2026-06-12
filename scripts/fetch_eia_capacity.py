#!/usr/bin/env python3
"""
Fetch EIA generator nameplate capacity for every plant in the CEMS quarterly
dataset, monthly from 2020-01, to support plant-level capacity factor.

Endpoint: electricity/operating-generator-capacity (EIA-860M inventory).
The earlier pull in fetch_eia_generation.py omitted data[] columns, so it
returned attributes only -- this pull requests the capacity values.

API key from env var EIA_API_KEY (never committed).

Outputs:
  data/eia_plant_capacity_monthly.csv   -- plant-month nameplate / net-summer
                                           MW summed over generators
  data/eia_generator_capacity_latest.csv -- latest snapshot per generator with
                                            capacity, status, technology
"""

import os
import sys
import time

import pandas as pd
import requests

API_KEY = os.environ.get("EIA_API_KEY", "")
BASE_URL = "https://api.eia.gov/v2"
CEMS_PATH = "data/cems_quarterly_clean_2020_2025.csv"
OUT_PLANT = "data/eia_plant_capacity_monthly.csv"
OUT_GEN = "data/eia_generator_capacity_latest.csv"
START_PERIOD = "2020-01"
BATCH_SIZE = 50
PAGE_SIZE = 5000

DATA_COLS = ["nameplate-capacity-mw", "net-summer-capacity-mw", "net-winter-capacity-mw"]


def fetch_all_pages(path, base_params):
    results = []
    offset = 0
    while True:
        params = base_params + [("offset", offset), ("length", PAGE_SIZE)]
        resp = requests.get(f"{BASE_URL}/{path}/data", params=params, timeout=120)
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
        pd.read_csv(CEMS_PATH, usecols=["facilityId"])["facilityId"].unique()
    )
    print(f"{len(plant_ids)} CEMS plants")

    all_rows = []
    batches = [plant_ids[i: i + BATCH_SIZE] for i in range(0, len(plant_ids), BATCH_SIZE)]
    for b_idx, batch in enumerate(batches):
        print(f"  capacity batch {b_idx + 1}/{len(batches)} ({len(batch)} plants)")
        base_params = [
            ("api_key", API_KEY),
            ("frequency", "monthly"),
            ("start", START_PERIOD),
        ]
        for col in DATA_COLS:
            base_params.append(("data[]", col))
        for pid in batch:
            base_params.append(("facets[plantid][]", str(pid)))
        base_params += [("sort[0][column]", "period"), ("sort[0][direction]", "asc")]
        all_rows.extend(fetch_all_pages("electricity/operating-generator-capacity", base_params))
        time.sleep(0.2)

    df = pd.DataFrame(all_rows)
    print(f"\n{len(df):,} generator-month rows")
    df["plantid"] = df["plantid"].astype(str)
    for col in DATA_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    plant_month = (
        df.groupby(["period", "plantid", "plantName", "stateid"], as_index=False)
        .agg(
            nameplate_mw=("nameplate-capacity-mw", "sum"),
            net_summer_mw=("net-summer-capacity-mw", "sum"),
            n_generators=("generatorid", "nunique"),
        )
    )
    plant_month.to_csv(OUT_PLANT, index=False)
    print(f"Saved {len(plant_month):,} plant-month rows -> {OUT_PLANT}")

    latest = (
        df.sort_values("period", ascending=False)
        .drop_duplicates(subset=["plantid", "generatorid"])
        .sort_values(["stateid", "plantid", "generatorid"])
    )
    keep = ["period", "plantid", "plantName", "stateid", "generatorid", "unit",
            "technology", "energy_source_code", "prime_mover_code", "status",
            "statusDescription"] + DATA_COLS
    latest = latest[[c for c in keep if c in latest.columns]]
    latest.to_csv(OUT_GEN, index=False)
    print(f"Saved {len(latest):,} generators -> {OUT_GEN}")

    print(f"\nPlants with capacity data: {plant_month['plantid'].nunique()} / {len(plant_ids)}")
    print(f"Period range: {plant_month['period'].min()} to {plant_month['period'].max()}")
    missing = set(map(str, plant_ids)) - set(plant_month["plantid"])
    if missing:
        print(f"Plants missing from EIA ({len(missing)}): {sorted(missing)[:20]}"
              + (" ..." if len(missing) > 20 else ""))


if __name__ == "__main__":
    main()
