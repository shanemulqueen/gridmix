# `cems_extended_quarterly.csv` — Column Reference

**32,174 rows | 573 unique units | 16 states | 2020Q1–2026Q4**

Source: `scripts/build_yoy_extension.py`. Combines CEMS actual quarterly unit-level
data (2020–2025) with estimates for 2026Q1–Q4, built by applying plant-level
year-over-year percentage changes (from EIA) to each unit's same-quarter prior-year values.

This is the primary dataset for analysis requiring coverage beyond 2025Q4.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `facilityId` | int | — | EPA ORIS code |
| `unitId` | str | — | CEMS unit identifier |
| `stateCode` | str | — | Two-letter state code |
| `year` | int | — | Calendar year |
| `quarter` | int | — | Calendar quarter (1–4) |
| `gross_mwh` | float | MWh | Gross generation (CEMS actual for `cems_actual` rows; YoY-scaled estimate for `cems_extended`) |
| `co2_tons` | float | short tons | CO₂ emissions (CEMS actual or YoY-scaled; null where CEMS did not report CO₂) |
| `rggi_obligated` | bool | — | RGGI obligation flag copied from 2020–2025 CEMS data (see `cems_quarterly_clean_columns.md`); for extended rows, reflects the prior-year flag |
| `camd_rggi_program` | bool | — | CAMD RGGI program enrollment flag |
| `coats_unit_match` | bool | — | Exact COATS unit match flag |
| `coats_facility_match` | bool | — | COATS facility-level match flag |
| `source` | str | — | `cems_actual` (2020–2025 CEMS) or `cems_extended` (2026Q1–Q4 estimate) |
| `yoy_pct_applied` | float | — | The quarterly YoY % applied to derive estimated values; null for `cems_actual` rows |

## Extension methodology

For each `cems_extended` quarter (2026Q1–Q4):
1. Base values come from the same unit's same quarter one year prior (e.g. 2026Q1 ← 2025Q1).
2. Plant-level quarterly YoY is looked up from `plant_yoy_monthly_eia.csv` (aggregated to quarterly ratio of 3-month sums). Fallback: state-median YoY for that quarter.
3. `gross_mwh = prior_gross_mwh × (1 + yoy_pct)` and `co2_tons = prior_co2_tons × (1 + yoy_pct)`.
4. Emission intensity is implicitly held constant (same CO₂/MWh as prior year).

## Assumptions

- Unit-level generation change equals plant-level change (all units at a plant move proportionally).
- CO₂ emission intensity (lb/MWh) is constant year-over-year.
- YoY values are winsorised to [−75%, +100%] and require prior-year plant fossil generation ≥ 10 GWh; otherwise state-median fallback is used.

## Row counts by source

| Source | Rows | Units |
|---|---|---|
| `cems_actual` | 27,860 | 573 |
| `cems_extended` | 4,314 | 482 |

The difference in unit count (573 vs 482) reflects units at plants with insufficient
EIA history or no 2025 prior-year CEMS data to extend from.
