# `cems_quarterly_clean_2020_2025.csv` / `.parquet` — Column Reference

**27,860 rows | 1,338 unique units | 16 states | 2020Q1–2025Q4**

Source: `scripts/build_cems_clean.py` applied to `cems_quarterly_raw_2020_2025.csv`.
Adds RGGI obligation flags and carbon intensity columns; drops the duplicate `unit_id` field.
Also available as `cems_quarterly_clean_2020_2025.parquet` (requires pyarrow).

---

## Identity and operating columns

All columns from the raw file are retained (see `cems_quarterly_raw_columns.md`),
with `unit_id` removed. Key identity columns:

| Column | Type | Description |
|---|---|---|
| `stateCode` | str | Two-letter state code |
| `facilityId` | int | EPA ORIS code (= EIA `plantCode`) |
| `unitId` | str | CEMS unit identifier |
| `year` | int | Calendar year |
| `quarter` | int | Calendar quarter (1–4) |
| `grossLoad` | MWh | Gross generation at generator terminals |
| `co2Mass` | short tons | CO₂ stack emissions |
| `heatInput` | MMBtu | Fuel heat input |

*(All other raw columns retained — see raw column reference for full list.)*

---

## RGGI obligation flag columns

Three intermediate flags feed the final obligation column.

| Column | Type | Description |
|---|---|---|
| `camd_rggi_program` | bool | `True` if `"RGGI"` appears in `programCodeInfo`. Reflects CAMD's current program enrollment; may be stale for states that exited (e.g. VA after 2023). |
| `coats_unit_match` | bool | `True` if (ORIS, normalised unit ID) matches the RGGI COATS Sources list exactly. Most precise obligation indicator. |
| `coats_facility_match` | bool | `True` if the ORIS appears anywhere in COATS (facility-level fallback). Captures units at covered plants where unit ID naming differs between COATS and CEMS (5 facilities; see `unit_crosswalk.csv`). |
| `rggi_obligated` | bool | **Primary obligation flag.** `True` when (`camd_rggi_program` OR `coats_unit_match` OR `coats_facility_match`) AND the unit's state participated in RGGI that quarter (see regime table below). |

### State participation windows used in `rggi_obligated`

| State(s) | Obligated quarters |
|---|---|
| CT DE MA MD ME NH NJ NY RI VT | All of 2020Q1–2025Q4 |
| VA | 2021Q1–2023Q4 (withdrew end of 2023) |
| PA | 2022Q3–2023Q4 (regulation effective July 2022; courts later voided; COATS-verified) |
| OH WV DC NC | Never |

---

## Carbon intensity columns

Computed as `co2Mass / grossLoad` where `grossLoad > 0`; NaN where the unit did not generate.

| Column | Unit | Description |
|---|---|---|
| `co2_intensity_st_per_mwh` | short tons CO₂/MWh | CO₂ per gross MWh |
| `co2_intensity_lb_per_mwh` | lb CO₂/MWh | = `co2_intensity_st_per_mwh × 2000` |
| `co2_intensity_kg_per_mwh` | kg CO₂/MWh | = `co2_intensity_st_per_mwh × 907.18474` |

## Notes

- Intensity columns use gross generation (not net), consistent with RGGI's compliance basis.
- For generation-weighted average intensity across units, weight by `grossLoad` — do not average the rate columns directly.
- The `.parquet` file is identical in content; use it for faster loading in analytical workflows.
