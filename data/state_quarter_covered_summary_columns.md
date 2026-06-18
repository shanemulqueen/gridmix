# `state_quarter_covered_summary.csv` — Column Reference

**954 rows | 16 states × 24 quarters × 3 groups**

Source: `scripts/build_covered_table.py`. Aggregates CEMS quarterly data to
state × quarter × coverage-group level. The applicable RGGI regime flag is
selected automatically per quarter via `regime_for()` from `build_regime_flags.py`.
Coverage is evaluated at the **plant level**: a plant is covered if any of its
units carries the regime obligation flag.

Validated: plant-level covered CO₂ equals unit-level `rggi_obligated` totals
exactly for 2024. VA covered rows appear only in 2021Q1–2023Q4, PA only in
2022Q3–2023Q4.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `state` | str | — | Two-letter state code |
| `year` | int | — | Calendar year |
| `quarter` | int | — | Calendar quarter (1–4) |
| `regime` | str | — | Regime flag column applied for this quarter (from `unit_regime_flags.csv`; see `unit_regime_flags_columns.md`) |
| `group` | str | — | `covered` / `not_covered` / `all` |
| `n_plants` | float | plants | Count of distinct plants in this state-quarter-group |
| `co2_tons` | float | short tons | Total CO₂ emissions (CEMS `co2Mass`) |
| `gross_mwh` | float | MWh | Total gross generation (CEMS `grossLoad`) |
| `co2_lb_per_mwh` | float | lb CO₂/MWh | Generation-weighted carbon intensity; NaN where `gross_mwh = 0` |
| `nameplate_mw` | float | MW | Sum of quarterly-average EIA nameplate capacity for plants with an EIA capacity match |
| `gross_mwh_capmatched` | float | MWh | Gross MWh for the subset of plants with EIA capacity data (denominator basis for `capacity_factor`) |
| `capacity_factor` | float | — | `gross_mwh_capmatched / (nameplate_mw × hours_in_quarter)`; dimensionless ratio 0–1 |

## Notes on capacity factor

- **Gross generation basis**: uses gross MWh (at generator terminals), not net, consistent with CEMS and RGGI's intensity calculations.
- **Partial coverage**: ~2% of gross load is at plants with no EIA capacity match (34 plants; mostly retired/industrial sources and CAMD 880xxx IDs). These plants are excluded from both numerator and denominator of the capacity factor but are still counted in `co2_tons` and `gross_mwh`.
- **Hours in quarter**: computed from actual calendar days (leap-year aware) × 24.
- Sorting: state → year → quarter → group.
