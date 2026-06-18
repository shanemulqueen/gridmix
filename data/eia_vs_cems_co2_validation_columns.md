# `eia_vs_cems_co2_validation.csv` — Column Reference

**7,127 rows | plant-quarter level | 2020Q1–2025Q4 (CEMS > 0 only)**

Source: `scripts/estimate_emissions_eia.py`. Compares EIA-estimated CO₂ (from
fuel consumption × emission factors) against CEMS actual CO₂ for the overlap period.
Used to assess bias and reliability of the EIA factor method before applying it
to gap-fill and forecast periods. Filtered to plant-quarters where CEMS records
positive CO₂ to avoid zero-denominator noise.

---

## Columns

| Column | Type | Unit | Description |
|---|---|---|---|
| `facilityId` | int | — | EPA ORIS code (from CEMS) |
| `stateCode` | str | — | Two-letter state code |
| `year` | int | — | Calendar year |
| `quarter` | int | — | Calendar quarter (1–4) |
| `cems_co2_tons` | float | short tons | CEMS-measured CO₂ summed to plant-quarter (authoritative) |
| `cems_gross_mwh` | float | MWh | CEMS gross generation summed to plant-quarter |
| `oris` | str | — | ORIS as string |
| `plantCode` | str | — | EIA plant code (matches `oris`) |
| `eia_co2_tons` | float | short tons | Estimated CO₂ from EIA fuel consumption × EPA emission factors |
| `eia_gross_mwh` | float | MWh | EIA gross generation for plant-quarter (all fuels) |
| `eia_mmbtu` | float | MMBtu | EIA fuel consumed for electricity generation (`consumption-for-eg-btu`) |
| `pct_diff` | float | % | `(eia_co2_tons − cems_co2_tons) / cems_co2_tons × 100`; negative = EIA underestimates |
| `abs_diff_tons` | float | short tons | `eia_co2_tons − cems_co2_tons` |

## Summary statistics from validation run

| Metric | Value |
|---|---|
| Plant-quarters compared | 7,127 |
| Aggregate CEMS CO₂ | 2,127,737,136 short tons |
| Aggregate EIA estimated CO₂ | 2,050,340,877 short tons |
| Aggregate delta | −77,396,259 short tons (−3.64%) |
| Median plant-quarter pct_diff | −1.33% |
| p5 / p95 | −66.9% / +52.4% |
