# `eia_generator_capacity_latest.csv` — Column Reference

**1,434 rows | one row per generator | 15 states | snapshot as of 2026-03**

Source: `scripts/fetch_eia_capacity.py`, `electricity/operating-generator-capacity` endpoint.
All 445 CEMS plants queried (16 states); 411 returned data. Most-recent available snapshot
per generator, deduplicated by plantid + generatorid. Covers both operating and recently
retired generators.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | str | — | Most recent month for this snapshot, `YYYY-MM` |
| `plantid` | str | — | EIA plant code (= EPA ORIS = CAMD `facilityId`) |
| `plantName` | str | — | Plant name |
| `stateid` | str | — | Two-letter state code |
| `generatorid` | str | — | EIA generator ID |
| `unit` | str | — | Unit label within a multi-unit configuration (e.g. `CC1`) |
| `technology` | str | — | Technology description (e.g. "Natural Gas Fired Combined Cycle") |
| `energy_source_code` | str | — | Primary fuel code (EIA-923; see fuel code reference in `eia_facility_fuel_monthly_all_columns.md`) |
| `prime_mover_code` | str | — | Prime mover code (ST/GT/CT/CA/CS/IC/etc.) |
| `status` | str | — | Operational status code (`OP` = Operating, `SB` = Standby, `RE` = Retired, `T` = Testing, etc.) |
| `statusDescription` | str | — | Status description |
| `nameplate-capacity-mw` | float | MW | Nameplate (design) capacity rating |
| `net-summer-capacity-mw` | float | MW | Net summer capacity (derated for ambient conditions; standard market metric) |
| `net-winter-capacity-mw` | float | MW | Net winter capacity (typically higher than summer for gas turbines) |

## Notes

- This file enables generator-level analysis such as identifying NY units in the 15–25 MWe band affected by the 2021Q1 threshold change, or filtering to fossil-only generators.
- For the RGGI 25 MWe threshold: compare `nameplate-capacity-mw` or `net-summer-capacity-mw` against 25 MW. The Model Rule uses nameplate capacity "at any time on or after January 1, 2005"; nameplate is the appropriate column.
- `generatorid` in EIA does not always correspond to CEMS `unitId` — use `unit_crosswalk.csv` for the COATS↔CEMS unit ID mapping.
