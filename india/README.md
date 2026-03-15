# India Data Workspace

This directory holds the India-specific data pipeline for the AI exposure project.

The existing repository is built around U.S. Bureau of Labor Statistics data. The India migration should run in parallel until the India pipeline can fully replace the U.S. artifacts consumed by the static site.

## Directory Layout

- `raw/`
  Stores manually downloaded or fetched source files from official India data sources such as NCO 2015, NCS, and MoSPI/PLFS.
- `intermediate/`
  Stores normalized but not final artifacts, such as extracted tables, cleaned text, and source-specific mappings.
- `output/`
  Stores final India pipeline outputs used by downstream scripts, including occupation metadata, markdown pages, CSV stats, scores, and other merged artifacts.

## Source Stack

- `NCO 2015`
  Occupation taxonomy and official codes.
- `NCS`
  Occupation descriptions and education/career information where available.
- `PLFS / MoSPI`
  Employment and wage statistics.

## Scripts

- `build_occupations.py`
  Parses the downloaded NCS browse page and any cached `ncs-sector-*.html` files,
  then writes `output/occupations_india.json`.
- `fetch_sector_pages.py`
  Uses the cached sector index to download sector detail pages into `raw/` for
  later parsing.

## Migration Checklist

The current repository has several U.S.-specific assumptions that the India pipeline must replace or bypass:

- `README.md` describes the project as U.S. labour-market analysis based on BLS Occupational Outlook Handbook data.
- `scrape.py`, `parse_detail.py`, `parse_occupations.py`, and `process.py` are BLS-specific ingestion/parsing scripts.
- `make_csv.py` expects BLS quick facts and outlook tables.
- `build_site_data.py` expects U.S. CSV columns including `outlook_pct` and `outlook_desc`.
- `make_prompt.py` is explicitly framed around U.S. jobs and BLS projections.
- `site/index.html` contains U.S.-specific copy and an `Exposure vs Outlook` secondary view.
- The current `occupations.json`, `occupations.csv`, `scores.json`, and `site/data.json` are all U.S. artifacts.

## India Product Rules

- Preserve the treemap as the main view.
- Keep area tied to workforce size or employment share.
- Keep color tied to AI exposure.
- Keep hover text focused on explanation and economic context.
- Remove the U.S.-style `outlook` field in the India pipeline unless a credible India equivalent is found.
- Prefer explicit uncertainty over false precision when source coverage is incomplete.
