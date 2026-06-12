#!/usr/bin/env python3
"""
Build a unit-level crosswalk between RGGI COATS source unit IDs and EPA CAMD
CEMS unit IDs, for all facilities that appear in both datasets.

Inputs:
  data/sources_raw.xlsx                 (RGGI COATS Sources report)
  data/cems_quarterly_raw_2020_2025.csv

Output:
  data/unit_crosswalk.csv

Columns:
  oris            -- ORIS/facility ID (string)
  facility_name   -- from CEMS facilityName
  state           -- from CEMS stateCode
  coats_unit      -- unit ID as listed in COATS (normalised: stripped + upper);
                     blank if this CEMS unit has no COATS counterpart
  cems_unit       -- unit ID as it appears in CEMS unitId (normalised);
                     blank if this COATS unit has no CEMS counterpart
  status          -- "matched"     : unit appears in both
                     "coats_only"  : in COATS but absent from CEMS
                                     (typically a retired unit)
                     "cems_only"   : in CEMS but absent from COATS
                                     (new unit, repowering, or stack-level ID)

Interpretation notes (from gap analysis):
  - 261 of 266 shared ORIS codes have full unit-level overlap.
  - 5 facilities have partial or zero overlap due to retired units (coats_only)
    or new / stack-level CEMS identifiers (cems_only), not naming differences.
  - The facility-level fallback in build_cems_clean.py correctly flags all
    units at the 5 problem facilities as obligated; this file documents the gap.
"""

import openpyxl
import pandas as pd

COATS_PATH = "data/sources_raw.xlsx"
CEMS_PATH  = "data/cems_quarterly_raw_2020_2025.csv"
OUT_PATH   = "data/unit_crosswalk.csv"


def norm_unit(u):
    return str(u).strip().upper()


def load_coats_units(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(min_row=13, values_only=True):
        facility, oris, units = row[0], row[1], row[5]
        if facility is None or oris is None:
            continue
        oris = str(oris).strip()
        if units:
            for u in str(units).split(","):
                rows.append({"oris": oris, "coats_unit": norm_unit(u)})
        else:
            rows.append({"oris": oris, "coats_unit": None})
    return pd.DataFrame(rows)


def main():
    coats_df = load_coats_units(COATS_PATH)

    cems_raw = pd.read_csv(CEMS_PATH, dtype={"unitId": str, "facilityId": str})
    cems_meta = (
        cems_raw[["facilityId", "facilityName", "stateCode"]]
        .drop_duplicates("facilityId")
        .rename(columns={"facilityId": "oris", "facilityName": "facility_name", "stateCode": "state"})
    )
    cems_units = (
        cems_raw[["facilityId", "unitId"]]
        .drop_duplicates()
        .rename(columns={"facilityId": "oris", "unitId": "cems_unit"})
    )
    cems_units["cems_unit"] = cems_units["cems_unit"].map(norm_unit)

    shared_oris = set(coats_df["oris"]) & set(cems_units["oris"])
    coats_shared = coats_df[coats_df["oris"].isin(shared_oris)].copy()
    cems_shared  = cems_units[cems_units["oris"].isin(shared_oris)].copy()

    merged = pd.merge(
        coats_shared, cems_shared,
        left_on=["oris", "coats_unit"],
        right_on=["oris", "cems_unit"],
        how="outer",
    )

    def classify(row):
        if pd.notna(row["coats_unit"]) and pd.notna(row["cems_unit"]):
            return "matched"
        if pd.notna(row["coats_unit"]):
            return "coats_only"
        return "cems_only"

    merged["status"] = merged.apply(classify, axis=1)
    merged = merged.merge(cems_meta, on="oris", how="left")
    merged = merged[["oris", "facility_name", "state", "coats_unit", "cems_unit", "status"]]
    merged = merged.sort_values(["state", "oris", "status", "coats_unit", "cems_unit"])

    merged.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(merged):,} rows -> {OUT_PATH}")

    print("\n--- Status summary ---")
    print(merged["status"].value_counts().to_string())

    print("\n--- Facilities with any mismatch ---")
    gaps = merged[merged["status"] != "matched"]["oris"].unique()
    for oris in gaps:
        sub = merged[merged["oris"] == oris]
        name  = sub["facility_name"].iloc[0]
        state = sub["state"].iloc[0]
        print(f"\n  ORIS {oris} ({state}) {name}")
        for _, r in sub.iterrows():
            coats = r["coats_unit"] if pd.notna(r["coats_unit"]) else "-"
            cems  = r["cems_unit"]  if pd.notna(r["cems_unit"])  else "-"
            print(f"    {r['status']:12s}  COATS={coats:25s}  CEMS={cems}")


if __name__ == "__main__":
    main()
