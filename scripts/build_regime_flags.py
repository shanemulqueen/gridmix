#!/usr/bin/env python3
"""
Build a unit-level index of RGGI obligation flags, one column per regulatory
regime, for every unit in the CEMS quarterly dataset (all 16 states).

Inputs:
  data/cems_quarterly_clean_2020_2025.csv  (per-unit COATS/CAMD match flags)
  data/unit_crosswalk.csv                  (COATS unit label <-> CEMS unitId)

Output: data/unit_regime_flags.csv
  oris, cems_unit, coats_unit (null if not mapped), state, facility_name,
  coats_linked, then one boolean obligation column per regime.

Regimes (state participation windows):
  oblig_pre2009        -- before RGGI existed: False for everyone
  oblig_2020           -- 2020Q1-2020Q4: RGGI-10 (NJ rejoined 2020Q1)
  oblig_2021q1_2022q2  -- RGGI-10 + VA (VA joined 2021Q1; NY 15 MWe
                          threshold also effective 2021Q1, captured via the
                          COATS roster rather than a capacity test)
  oblig_2022q3_2023q4  -- RGGI-10 + VA + PA (PA regulation effective July
                          2022; emissions tracked in COATS and match RGGI's
                          official totals, though allowance surrender was
                          never enforced before courts voided the rule.
                          Both VA and PA exited after 2023Q4)
  oblig_2024q1_2026q2  -- RGGI-10 only
  oblig_2026q3_on      -- RGGI-10 + VA (VA compliance obligations resume
                          July 1, 2026 per HB 29 / DEQ Revision A26,
                          effective April 24, 2026)

A unit is obligated under a regime if it is COATS-linked (exact unit match,
facility-level match, or CAMD RGGI program code -- same basis as
build_cems_clean.py) AND its state participates in that regime.
"""

import pandas as pd

CLEAN_PATH = "data/cems_quarterly_clean_2020_2025.csv"
XWALK_PATH = "data/unit_crosswalk.csv"
OUT_PATH = "data/unit_regime_flags.csv"

RGGI_10 = {"CT", "DE", "MA", "MD", "ME", "NH", "NJ", "NY", "RI", "VT"}

# regime column -> (first (year, q) inclusive, last (year, q) inclusive or
# None for open-ended, set of participating states)
REGIMES = {
    "oblig_pre2009":       ((1900, 1), (2008, 4), set()),
    "oblig_2020":          ((2020, 1), (2020, 4), RGGI_10),
    "oblig_2021q1_2022q2": ((2021, 1), (2022, 2), RGGI_10 | {"VA"}),
    "oblig_2022q3_2023q4": ((2022, 3), (2023, 4), RGGI_10 | {"VA", "PA"}),
    "oblig_2024q1_2026q2": ((2024, 1), (2026, 2), RGGI_10),
    "oblig_2026q3_on":     ((2026, 3), None,      RGGI_10 | {"VA"}),
}


def regime_for(year, quarter):
    """Return the regime column name covering (year, quarter)."""
    for name, (start, end, _) in REGIMES.items():
        if start <= (year, quarter) and (end is None or (year, quarter) <= end):
            return name
    raise ValueError(f"No regime covers {year}Q{quarter}")


def main():
    cems = pd.read_csv(CLEAN_PATH, dtype={"unitId": str})
    units = (
        cems.groupby(["facilityId", "unitId"], as_index=False)
        .agg(
            state=("stateCode", "first"),
            facility_name=("facilityName", "first"),
            camd_rggi_program=("camd_rggi_program", "any"),
            coats_unit_match=("coats_unit_match", "any"),
            coats_facility_match=("coats_facility_match", "any"),
        )
        .rename(columns={"facilityId": "oris", "unitId": "cems_unit"})
    )
    units["oris"] = units["oris"].astype(str)
    units["cems_unit_norm"] = units["cems_unit"].str.strip().str.upper()

    xwalk = pd.read_csv(XWALK_PATH, dtype=str)
    matched = xwalk[xwalk["status"] == "matched"][["oris", "coats_unit", "cems_unit"]]
    units = units.merge(
        matched.rename(columns={"cems_unit": "cems_unit_norm"}),
        on=["oris", "cems_unit_norm"], how="left",
    )

    units["coats_linked"] = (
        units["camd_rggi_program"]
        | units["coats_unit_match"]
        | units["coats_facility_match"]
    )

    for name, (_, _, states) in REGIMES.items():
        units[name] = units["coats_linked"] & units["state"].isin(states)

    out_cols = (
        ["oris", "cems_unit", "coats_unit", "state", "facility_name", "coats_linked"]
        + list(REGIMES)
    )
    out = units[out_cols].sort_values(["state", "oris", "cems_unit"])
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out):,} units -> {OUT_PATH}")

    print(f"\nCOATS label mapped: {out['coats_unit'].notna().sum():,} "
          f"/ {len(out):,} units")
    print("\nObligated units per regime:")
    print(out[list(REGIMES)].sum().to_string())
    print("\nObligated units per regime by state (nonzero rows):")
    by_state = out.groupby("state")[list(REGIMES)].sum()
    print(by_state[by_state.sum(axis=1) > 0].to_string())


if __name__ == "__main__":
    main()
