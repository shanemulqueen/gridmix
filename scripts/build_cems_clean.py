#!/usr/bin/env python3
"""
Clean the raw CAMD CEMS quarterly pull and add RGGI obligation flags.

Inputs:
  data/cems_quarterly_raw_2020_2025.csv  (from fetch_cems_quarterly.py)
  data/sources_raw.xlsx                  (RGGI COATS Sources report)

Flag columns:
  camd_rggi_program    -- 'RGGI' appears in CAMD's programCodeInfo (current
                          assignment; drops states that exited, e.g. VA)
  coats_unit_match     -- exact (ORIS, unit) match against the COATS sources list
  coats_facility_match -- ORIS-level match against the COATS sources list
  rggi_obligated       -- per-quarter obligation: unit is RGGI-linked
                          (COATS or CAMD program) AND the state participated
                          that quarter:
                            RGGI 10 states: all of 2020-2025
                            VA: 2021Q1-2023Q4, and again from 2026Q1 (rejoining)
                            PA: never (court injunction; compliance never began)
                            OH, WV, DC, NC: never

Output: data/cems_quarterly_clean_2020_2025.csv (+ .parquet if pyarrow present)
"""

import openpyxl
import pandas as pd

RAW_PATH = "data/cems_quarterly_raw_2020_2025.csv"
COATS_PATH = "data/sources_raw.xlsx"
OUT_CSV = "data/cems_quarterly_clean_2020_2025.csv"
OUT_PARQUET = "data/cems_quarterly_clean_2020_2025.parquet"

RGGI_10 = {"CT", "DE", "MA", "MD", "ME", "NH", "NJ", "NY", "RI", "VT"}

NUMERIC_COLS = [
    "countOpTime", "sumOpTime", "grossLoad", "steamLoad",
    "so2Mass", "so2Rate", "co2Mass", "co2Rate", "noxMass", "noxRate",
    "heatInput",
]


def norm_unit(u):
    return str(u).strip().upper()


def load_coats_units(xlsx_path):
    """Return (set of ORIS codes, set of (ORIS, unit) pairs) from COATS Sources."""
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    oris_set, unit_pairs = set(), set()
    for row in ws.iter_rows(min_row=13, values_only=True):
        facility, oris, _state_id = row[0], row[1], row[2]
        units = row[5]
        if facility is None or oris is None:
            continue
        oris = str(oris).strip()
        oris_set.add(oris)
        if units:
            for u in str(units).split(","):
                unit_pairs.add((oris, norm_unit(u)))
    return oris_set, unit_pairs


def state_participated(state, year, quarter):
    if state in RGGI_10:
        return True
    if state == "VA":
        return (2021, 1) <= (year, quarter) <= (2023, 4) or (year, quarter) >= (2026, 1)
    return False  # PA never commenced compliance; OH/WV/DC/NC not members


def main():
    df = pd.read_csv(RAW_PATH, dtype={"unitId": str, "unit_id": str})
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["facilityId"] = df["facilityId"].astype(int)
    df["oris"] = df["facilityId"].astype(str)
    df["unit_norm"] = df["unitId"].map(norm_unit)

    coats_oris, coats_units = load_coats_units(COATS_PATH)

    df["camd_rggi_program"] = df["programCodeInfo"].fillna("").str.split(",").map(
        lambda codes: any(c.strip() == "RGGI" for c in codes)
    )
    df["coats_unit_match"] = [
        (o, u) in coats_units for o, u in zip(df["oris"], df["unit_norm"])
    ]
    df["coats_facility_match"] = df["oris"].isin(coats_oris)

    rggi_linked = df["camd_rggi_program"] | df["coats_unit_match"] | df["coats_facility_match"]
    participated = [
        state_participated(s, y, q)
        for s, y, q in zip(df["stateCode"], df["year"], df["quarter"])
    ]
    df["rggi_obligated"] = rggi_linked & pd.Series(participated, index=df.index)

    df = df.drop(columns=["oris", "unit_norm", "unit_id"])
    df = df.sort_values(["stateCode", "facilityId", "unitId", "year", "quarter"])

    df.to_csv(OUT_CSV, index=False)
    print(f"Saved {len(df):,} rows -> {OUT_CSV}")
    try:
        df.to_parquet(OUT_PARQUET, index=False)
        print(f"Saved parquet -> {OUT_PARQUET}")
    except ImportError:
        print("pyarrow not installed; skipped parquet")

    print("\n--- Flag summary (unit-quarters) ---")
    print(df.groupby("stateCode")[["camd_rggi_program", "coats_unit_match",
                                   "coats_facility_match", "rggi_obligated"]].sum())
    print("\nObligated unit-quarters by year:")
    print(df[df["rggi_obligated"]].groupby("year").size())


if __name__ == "__main__":
    main()
