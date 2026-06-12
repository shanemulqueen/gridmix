#!/usr/bin/env python3
"""
Fetch EIA monthly plant-level generation and thermal data for RGGI-covered facilities.

Endpoints:
  facility-fuel                -- net/gross generation + fuel consumption (MMBtu)
                                  granularity: plant + fuel_type + prime_mover, monthly
  operating-generator-capacity -- unit-level attributes (generatorid, technology, fuel, capacity)
                                  used to match EIA generator IDs to RGGI unit names

Output:
  data/eia_facility_fuel_monthly.csv  -- generation + heat input, 2009-present
  data/eia_generator_attributes.csv   -- unit-level attributes (latest snapshot per generator)
"""

import time
import requests
import pandas as pd
import os
import openpyxl

API_KEY = os.environ.get("EIA_API_KEY", "")
BASE_URL = "https://api.eia.gov/v2"
START_PERIOD = "2009-01"
BATCH_SIZE = 50
PAGE_SIZE = 5000

FUEL_COLS = [
    "generation",
    "gross-generation",
    "total-consumption-btu",
    "consumption-for-eg-btu",
    "average-heat-content",
]


def load_rggi_facilities(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=13, values_only=True):
        row = list(row)
        facility, oris, state_id = row[0], row[1], row[2]
        units = row[5] if len(row) > 5 else None
        owner = row[6] if len(row) > 6 else None
        state = row[7] if len(row) > 7 else None
        if facility is not None and oris is not None:
            records.append({
                "facility": facility,
                "oris_code": str(oris),
                "state_id": state_id,
                "rggi_units": units,
                "state": state,
                "owner": owner,
            })
    return pd.DataFrame(records)


def fetch_all_pages(path, base_params):
    results = []
    offset = 0
    while True:
        params = base_params + [("offset", offset), ("length", PAGE_SIZE)]
        resp = requests.get(f"{BASE_URL}/{path}/data", params=params, timeout=90)
        resp.raise_for_status()
        body = resp.json()
        data = body["response"]["data"]
        total = int(body["response"]["total"])
        results.extend(data)
        offset += len(data)
        if offset >= total or not data:
            break
        time.sleep(0.15)
    return results


def fetch_facility_fuel(oris_codes):
    all_rows = []
    batches = [oris_codes[i: i + BATCH_SIZE] for i in range(0, len(oris_codes), BATCH_SIZE)]
    for b_idx, batch in enumerate(batches):
        print(f"  facility-fuel batch {b_idx + 1}/{len(batches)}  ({len(batch)} plants)")
        base_params = [
            ("api_key", API_KEY),
            ("frequency", "monthly"),
            ("start", START_PERIOD),
        ]
        for col in FUEL_COLS:
            base_params.append(("data[]", col))
        for oris in batch:
            base_params.append(("facets[plantCode][]", oris))
        base_params += [("sort[0][column]", "period"), ("sort[0][direction]", "asc")]
        rows = fetch_all_pages("electricity/facility-fuel", base_params)
        all_rows.extend(rows)
        time.sleep(0.2)
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["plantCode"] = df["plantCode"].astype(str)
    return df


def fetch_generator_attributes(oris_codes):
    all_rows = []
    batches = [oris_codes[i: i + BATCH_SIZE] for i in range(0, len(oris_codes), BATCH_SIZE)]
    for b_idx, batch in enumerate(batches):
        print(f"  generator-capacity batch {b_idx + 1}/{len(batches)}  ({len(batch)} plants)")
        base_params = [("api_key", API_KEY), ("frequency", "monthly")]
        for oris in batch:
            base_params.append(("facets[plantid][]", oris))
        base_params += [("sort[0][column]", "period"), ("sort[0][direction]", "desc")]
        rows = fetch_all_pages("electricity/operating-generator-capacity", base_params)
        all_rows.extend(rows)
        time.sleep(0.2)
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["plantid"] = df["plantid"].astype(str)
    # Keep only the most recent snapshot per generator
    df = df.sort_values("period", ascending=False).drop_duplicates(subset=["plantid", "generatorid"])
    return df


def main():
    print("Loading RGGI facility list...")
    facilities = load_rggi_facilities("data/sources_raw.xlsx")
    oris_codes = facilities["oris_code"].tolist()
    print(f"  {len(oris_codes)} facilities, states: {sorted(facilities['state'].dropna().unique())}")

    print("\nFetching facility-fuel (generation + thermal)...")
    fuel_df = fetch_facility_fuel(oris_codes)
    print(f"  {len(fuel_df):,} rows")
    fuel_df.to_csv("data/eia_facility_fuel_monthly.csv", index=False)
    print("  -> data/eia_facility_fuel_monthly.csv")

    print("\nFetching operating-generator-capacity (unit attributes)...")
    gen_df = fetch_generator_attributes(oris_codes)
    print(f"  {len(gen_df):,} unique generators")
    gen_df.to_csv("data/eia_generator_attributes.csv", index=False)
    print("  -> data/eia_generator_attributes.csv")

    print("\n=== Series in facility-fuel ===")
    print("  Columns:", list(fuel_df.columns))
    print(f"  Date range: {fuel_df['period'].min()} to {fuel_df['period'].max()}")
    print(f"  Total rows: {len(fuel_df):,}")
    print("\n  Sample (non-ALL fuel rows, recent):")
    sample = fuel_df[fuel_df["fuel2002"] != "ALL"].sort_values("period", ascending=False).head(6)
    print(sample[["period","plantCode","plantName","state","fuel2002","fuelTypeDescription",
                  "primeMover","generation","gross-generation",
                  "total-consumption-btu","average-heat-content"]].to_string(index=False))

    print("\n=== Series in generator-attributes ===")
    print("  Columns:", list(gen_df.columns))
    print(f"  Total unique generators: {len(gen_df):,}")
    attr_cols = ["plantid","plantName","generatorid","technology","energy_source_code",
                 "prime_mover_code","balancing_authority_code","stateid"]
    available = [c for c in attr_cols if c in gen_df.columns]
    print("\n  Sample:")
    print(gen_df[available].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
