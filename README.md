# TreeChecker

Screens agricultural supply chains for EU Deforestation Regulation (EUDR) risk. Give it a spreadsheet of supplier plots, and for each one it returns a compliance verdict, a risk score out of 100, an estimated financial exposure, and a PDF certificate with a satellite evidence map.

TreeChecker is a **triage tool**. It flags which suppliers need a full plot-level audit first. It does not give a final legal verdict.

**Write-up:** [TreeChecker report (PDF)](TreeChecker_Report.pdf): the problem, design decisions, market feedback and limitations.

## How it works

1. **Legal rules first.** EUDR requires full plot boundaries (polygons) above 4 hectares, so a point coordinate there is legally insufficient.
   - Over 4 ha → `LEGALLY_INCOMPLETE`
   - No plot size → `DATA_GAP`
   - 4 ha or less → goes to the satellite check
2. **Satellite check.** Google Earth Engine and the Hansen Global Forest Change dataset (v1.13). It sums forest loss from 2021 onwards (EUDR cut-off: 31 December 2020) within a 5km radius of the point. Above 1,000 m² → `NON_COMPLIANT`, otherwise `COMPLIANT`.
3. **Risk score (0–100).** Combines the verdict (up to 50), plot size (up to 30) and country risk tier (up to 20). Country tiers follow the EU's official EUDR country benchmarking; unlisted countries default to standard.
4. **Exposure estimate.** An illustrative worst case as a share of the importer's EU turnover: 4% for non-compliant plots (the level every member state's maximum fine must at least reach), and 2% for legally incomplete and 1% for data-gap plots (my own assumptions). Converted to euros only when turnover is supplied.

## Input

`coordinates_csv.xlsx`, one row per supplier plot:

| Column | Required | Example |
|---|---|---|
| `audit_id` | yes | `IVORY-COCOA-005` |
| `latitude`, `longitude` | yes | `6.45`, `-6.13` |
| `country_code` | yes | `CI` (ISO 3166 two-letter code) |
| `hectares` | yes | `3.0` |
| `supplier_name` | no | `Supplier A` |
| `eu_turnover_eur` | no | `50000000` |

## Running it

Requires Python 3.11+ and a Google Earth Engine account with a Cloud project.

```
pip install -r requirements.txt
python main.py        # runs the batch audit
python dashboard.py   # prints a summary of the audit log
```

On first run, Earth Engine opens a browser window to sign in. Set `PROJECT_ID` in `sensor.py` to your own Earth Engine project. On Windows, `RUN_AUDIT_SYSTEM.bat` runs the full cycle (it assumes a conda environment named `forest_env`).

## Outputs

- `outputs/certificate_<audit_id>.pdf`: per-plot certificate with verdict and evidence map
- `outputs/map_<audit_id>.png`: satellite map (green: tree cover in 2000; red: forest loss since 2021)
- `outputs/master_audit_log.csv`: running log of every audit
- `compliance_batch_2026.geojson`: all results, ready to load into a mapping tool

## Limitations

- **Point, not plot.** The 5km radius measures loss across the surrounding landscape, not strictly inside the plot boundary.
- **Deliberately sensitive.** The radius is far larger than a smallholder plot and the threshold is about one satellite pixel, so most plots in active forest landscapes are flagged. Next step: size the radius to the declared plot area.
- **Data coverage.** Hansen data is weaker in boreal regions, so a zero-loss reading there may reflect a data gap.
- **Illustrative fines.** Exposure figures are worst-case estimates, not predictions of actual penalties.

## Files

| File | Role |
|---|---|
| `main.py` | Batch pipeline: legal logic, risk score, exposure, output |
| `sensor.py` | Earth Engine analysis and evidence map |
| `report_gen.py` | PDF certificate |
| `dashboard.py` | Summary of the audit log |
| `clean_workspace.py` | Deletes old maps and PDFs (keeps the log) |
