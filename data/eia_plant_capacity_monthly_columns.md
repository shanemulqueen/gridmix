# `eia_plant_capacity_monthly.csv` — Column Reference

**28,654 rows | 411 plants | 15 states | 2020-01 to 2026-03**

Source: `scripts/fetch_eia_capacity.py`, `electricity/operating-generator-capacity` endpoint
with capacity data columns requested. Plant-level aggregate of all generators' nameplate
capacity by month. Used to compute capacity factor in `state_quarter_covered_summary.csv`.

34 of 445 CEMS plants have no EIA capacity data (retired/industrial sources and CAMD 880xxx
IDs not in EIA's operating generator inventory). DC has no EIA-reporting plants.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | str | — | Calendar month, `YYYY-MM` format |
| `plantid` | str | — | EIA plant code (= EPA ORIS = CAMD `facilityId`) |
| `plantName` | str | — | Plant name |
| `stateid` | str | — | Two-letter state code |
| `nameplate_mw` | float | MW | Sum of nameplate capacity across all generators at the plant for this month |
| `net_summer_mw` | float | MW | Sum of net summer capacity rating |
| `n_generators` | int | — | Number of distinct generators contributing to this plant-month row |

## Notes

- Monthly granularity reflects EIA-860M inventory updates. Capacity can change month-to-month as generators are commissioned, retired, or derated.
- For capacity factor calculation in `build_covered_table.py`, three monthly values per quarter are averaged to get quarterly-average nameplate MW.
- `nameplate_mw` reflects total plant capacity (all generators, all fuels), not just fossil/CEMS-monitored units. This is appropriate for plant-level capacity factor.
- Net summer capacity is the standard regulatory and market capacity metric; nameplate is higher (design rating, not derated for conditions).
