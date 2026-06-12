#!/usr/bin/env python3
"""
Fetch EPA CAMD CEMS quarterly unit-level emissions/generation data, 2020-2025,
for the RGGI region and surrounding states.

Endpoint: https://api.epa.gov/easey/emissions-mgmt/emissions/apportioned/quarterly
Notes:
  - Multi-value params are pipe-delimited (stateCode=CT|RI). Repeated params 500.
  - perPage max tested at 500; paginate until a short page.
  - API key from env var CAMD_API_KEY (data.gov key).

Output: data/cems_quarterly_raw_2020_2025.csv
"""

import os
import sys
import time

import pandas as pd
import requests

API_KEY = os.environ.get("CAMD_API_KEY", "")
URL = "https://api.epa.gov/easey/emissions-mgmt/emissions/apportioned/quarterly"

STATES = [
    # RGGI 10
    "CT", "DE", "MA", "MD", "ME", "NH", "NJ", "NY", "RI", "VT",
    # surrounding
    "PA", "VA", "OH", "WV", "DC", "NC",
]
YEARS = range(2020, 2026)
PER_PAGE = 500
OUT_PATH = "data/cems_quarterly_raw_2020_2025.csv"


def fetch_year(year):
    rows = []
    page = 1
    while True:
        params = {
            "api_key": API_KEY,
            "stateCode": "|".join(STATES),
            "year": year,
            "quarter": "1|2|3|4",
            "page": page,
            "perPage": PER_PAGE,
        }
        for attempt in range(5):
            resp = requests.get(URL, params=params, timeout=120)
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    rate limited, sleeping {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            raise RuntimeError(f"Persistent rate limiting at year={year} page={page}")

        items = resp.json().get("items", [])
        rows.extend(items)
        print(f"  year {year} page {page}: {len(items)} rows (running total {len(rows)})")
        if len(items) < PER_PAGE:
            break
        page += 1
        time.sleep(0.2)
    return rows


def main():
    if not API_KEY:
        sys.exit("Set CAMD_API_KEY environment variable (data.gov API key).")

    all_rows = []
    for year in YEARS:
        print(f"Fetching {year}...")
        all_rows.extend(fetch_year(year))
        time.sleep(0.3)

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(df):,} rows -> {OUT_PATH}")
    print(f"States: {sorted(df['stateCode'].unique())}")
    print(f"Years: {sorted(df['year'].unique())}")
    print(f"Unique units: {df.groupby(['facilityId', 'unitId']).ngroups:,}")


if __name__ == "__main__":
    main()
