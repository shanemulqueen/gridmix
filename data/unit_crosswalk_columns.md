# `unit_crosswalk.csv` — Column Reference

**836 rows | 266 facilities**

Source: `scripts/build_unit_crosswalk.py`. Maps RGGI COATS source unit IDs to
EPA CAMD CEMS unit IDs for all 266 facilities that appear in both datasets.
All 266 COATS ORIS codes are present in CEMS; no facility-level gaps.

---

## Columns

| Column | Type | Description |
|---|---|---|
| `oris` | str | EPA ORIS code (= EIA `plantCode` = CAMD `facilityId`) |
| `facility_name` | str | Plant name from CEMS |
| `state` | str | Two-letter state code |
| `coats_unit` | str | Unit ID as listed in RGGI COATS Sources report (normalised: stripped, uppercased). Null for `cems_only` rows. |
| `cems_unit` | str | Unit ID as it appears in CEMS `unitId` (normalised). Null for `coats_only` rows. |
| `status` | str | Match status (see below) |

## Status values

| Value | Count | Meaning |
|---|---|---|
| `matched` | 765 | Unit ID appears in both COATS and CEMS — direct pairing confirmed |
| `coats_only` | 43 | Unit in COATS but absent from CEMS; typically a retired unit that no longer reports |
| `cems_only` | 28 | Unit in CEMS but absent from COATS; typically a new/repowered unit or stack-level ID added after COATS enrollment snapshot |

## Notes

- The mismatch root cause is **stale COATS rosters**, not naming convention differences. No systematic string transformation (e.g. stripping state prefixes) was needed.
- The 5 facilities with any mismatch: Mystic (MA), Kendall Green (MA), Bridgeport Harbor (CT), Indian River (DE), Delaware City Refinery (DE).
- `cems_only` units at covered facilities are correctly flagged as obligated in `cems_quarterly_clean_2020_2025.csv` via the `coats_facility_match` fallback.
- Sorted by state → ORIS → status → unit ID.
