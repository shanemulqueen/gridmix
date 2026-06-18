# `va_co2_by_quarter_groups.csv` — Column Reference

**24 rows | one row per quarter, 2020Q1–2025Q4 | Virginia only**

Source: earlier analysis session. Splits Virginia CO₂ emissions and carbon
intensity between units that are RGGI-covered (per COATS/CAMD match) and
those that are not, for all 24 quarters in the dataset window.

Note: `state_quarter_covered_summary.csv` supersedes this file for general
multi-state analysis and uses a more rigorous regime-aware coverage definition.
This file is retained as the original VA-specific output.

---

## Columns

| Column | Unit | Description |
|---|---|---|
| `quarter_label` | — | Quarter identifier, e.g. `2020Q1` |
| `covered_co2_tons` | short tons | CO₂ from VA units matched to RGGI COATS (covered group) |
| `covered_lb_per_mwh` | lb CO₂/MWh | Generation-weighted carbon intensity for covered units |
| `notcovered_co2_tons` | short tons | CO₂ from VA units not in COATS |
| `all_co2_tons` | short tons | Total VA CO₂ (covered + not covered) |
| `all_lb_per_mwh` | lb CO₂/MWh | Generation-weighted carbon intensity, all VA units |

## Notes

- `covered_lb_per_mwh` is blank for quarters where covered units had zero gross generation (i.e. intensity is undefined, not zero).
- The 28 non-covered VA units are all steam/thermal units with zero gross load in CEMS — they emit CO₂ but generate no electricity, so no intensity is reported.
- VA obligation periods within this window: 2021Q1–2023Q4.
