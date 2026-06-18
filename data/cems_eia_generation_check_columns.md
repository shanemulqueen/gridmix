# `cems_eia_generation_check.csv` — Column Reference

**8,074 rows | 410 plants | plant-quarter level | 2020Q1–2025Q4**

Source: `scripts/check_cems_vs_eia.py`. Cross-check of EPA CEMS quarterly gross
generation against EIA facility-fuel monthly data aggregated to quarterly, for the
410 plants present in both datasets. Used to validate consistency and understand
structural differences between the two sources.

Key finding: EIA gross generation is +2.86% above CEMS in aggregate. Median
plant-quarter difference is 0.02%. Divergence is explained by non-fossil generation
(biomass, CHP steam turbines, small sub-threshold units) present in EIA but not CEMS.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `facilityId` | int | — | EPA ORIS code (from CEMS) |
| `stateCode` | str | — | Two-letter state code (from CEMS) |
| `year` | int | — | Calendar year |
| `quarter` | int | — | Calendar quarter (1–4) |
| `cems_gross_mwh` | float | MWh | Gross generation summed across all units at the plant for the quarter (from CEMS `grossLoad`) |
| `cems_co2_tons` | float | short tons | CO₂ summed across all units at the plant (from CEMS `co2Mass`) |
| `oris` | str | — | ORIS as string (join key to EIA) |
| `state` | str | — | State from EIA (matches `stateCode`) |
| `eia_gross_mwh` | float | MWh | Gross generation summed across all fuel/prime-mover rows for the plant-quarter (from EIA `gross-generation`; ALL-rollup rows excluded) |
| `eia_net_mwh` | float | MWh | Net generation for the plant-quarter (from EIA `generation`) |
| `eia_mmbtu` | float | MMBtu | Fuel consumed for electricity generation at the plant-quarter (from EIA `consumption-for-eg-btu`) |
| `pct_diff` | float | % | `(eia_gross_mwh − cems_gross_mwh) / cems_gross_mwh × 100`; positive = EIA higher |
| `abs_diff_mwh` | float | MWh | `eia_gross_mwh − cems_gross_mwh` |

## Notes

- Only plant-quarters where the plant appears in both CEMS and EIA are included (inner join).
- For analysis, filter to `cems_gross_mwh > 0` to exclude quarters where CEMS shows no generation (noise ratio).
- See `scripts/check_cems_vs_eia.py` for state-level breakdown and systematic gap diagnosis.
