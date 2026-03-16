# India Occupation Visualizer

A research tool for visually exploring how AI may reshape occupations in India. This repo adapts the original `jobs` project to India-specific public data sources and turns them into an interactive treemap and comparison view for occupations, pay, education coverage, and Digital AI Exposure.

**Live demo:** GitHub Pages deploys the static site from [`site/`](/home/subhajit/project/jobs/site)

## What's here

The India version currently covers **471 occupations** sourced from the National Career Service (`NCS`). Each rectangle's **area** represents the best available labor-market size proxy for that occupation, while **color** can be switched between:

- `Digital AI Exposure`
- `Annual Pay`
- `Education`

The site also includes an `Exposure vs Pay` view to compare where occupations sit in the wage distribution once grouped by AI exposure.

## LLM-powered coloring

The repo includes a full India pipeline for generating occupation pages, matching education data from government qualification records, and scoring occupations with an LLM. The current "Digital AI Exposure" layer is only one example. The same workflow can be reused for other questions such as robotics exposure, outsourcing risk, climate sensitivity, or modernization pressure.

**What "AI Exposure" is NOT:**
- It does **not** predict that an occupation disappears.
- It does **not** model demand elasticity, regulation, or social preference for human work.
- It is a rough LLM estimate intended for exploration, not a final labor-economics forecast.

## India source stack

The India version currently uses:

- `NCS (National Career Service)` for occupation titles, NCO codes, and source pages  
  https://www.ncs.gov.in/
- `NCO 2015` as the occupation taxonomy  
  https://labour.gov.in/sites/default/files/National%20Classification%20of%20Occupations%20_Vol%20I-%202015.pdf
- `PLFS / MoSPI Annual Report 2023-24` for:
  - occupation-group workforce share from `Table 25`
  - occupation-division wage data from `Table 50`
  https://www.mospi.gov.in/
  https://www.mospi.gov.in/sites/default/files/publication_reports/AnnualReport_PLFS2023-24L2.pdf
- `NQR / NCVET` for official qualification pages and minimum eligibility criteria used in the education field where a reliable occupation match exists  
  https://www.nqr.gov.in/  
  https://ncvet.gov.in/national-qualifications-register/

## Current status

This repo is wired for an India workflow, but it is still a `v1 / WIP` data product.

What is working:
- India occupation list ingestion
- India markdown page generation
- India stats normalization
- India scoring pipeline
- India site data build
- India-specific frontend with treemap, exposure-vs-pay view, and multi-layer coloring

Current limitations:
- many NCS detail pages only yield metadata-first markdown, not rich descriptions
- labor-market size is currently an `employment_share` proxy for much of the dataset, not absolute job counts
- pay is a PLFS-based occupation-division estimate, not a perfect occupation-level wage
- education is only shown where a conservative NCS-to-NQR match succeeded; unmatched occupations stay blank by design

## India pipeline

1. `india/build_occupations.py`
   Builds the India occupation master list from cached NCS sector pages.

2. `india/fetch_descriptions.py`
   Creates markdown pages in `india/output/pages/` for scoring. When rich NCS text is unavailable, it still writes stable metadata pages so the pipeline can continue.

3. `india/build_stats.py`
   Normalizes PLFS 2023-24 table data into `india/output/occupations_india.csv`.

4. `india/fetch_education.py`
   Matches occupations to official NQR qualifications and extracts minimum eligibility text and education buckets where a reliable government match exists.

5. `india/score_india.py`
   Scores occupations with OpenRouter, caches each success immediately, retries failures, and refreshes `site/data.json` after every saved score.

6. `india/build_site_data.py`
   Merges India stats and India scores into `site/data.json`.

7. `site/index.html`
   Static frontend with treemap, exposure-vs-pay columns, and Karpathy-style top-header controls adapted for India metrics.

## Key files

| File | Description |
|------|-------------|
| `india/output/occupations_india.json` | India occupation master list from NCS |
| `india/output/pages/` | Markdown pages used as scoring inputs |
| `india/output/education_india.json` | Official NQR-based education matches and buckets |
| `india/output/occupations_india.csv` | India stats table with pay and employment share |
| `india/output/scores_india.json` | Cached AI exposure scores for India occupations |
| `site/data.json` | Final frontend dataset |
| `site/index.html` | Static treemap frontend |

## Setup

Create [.env](/home/subhajit/project/jobs/.env) with:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=your/model-name
```

`OPENROUTER_MODEL` is optional. If omitted, the scorer falls back to its default model.

## Usage

```bash
# Build India occupation list
python3 india/build_occupations.py

# Generate India markdown pages
python3 india/fetch_descriptions.py

# Fetch official education matches from NQR
python3 india/fetch_education.py

# Build India stats from cached PLFS source
python3 india/build_stats.py

# Score occupations incrementally
python3 india/score_india.py --delay 0.1 --retry-delay 5 --max-retries 20

# Rebuild site data explicitly if needed
python3 india/build_site_data.py

# Serve the site locally
cd site && python3 -m http.server 8000
```

## GitHub Pages

This site can be hosted directly on GitHub Pages because the frontend is fully static.

Deploy steps:

1. Push the repo to GitHub.
2. Open `Settings -> Pages`.
3. Set `Source` to `GitHub Actions`.
4. The workflow in `.github/workflows/pages.yml` will deploy the `site/` folder automatically on each push to `master`.

Notes:
- GitHub Pages only needs the built static files under `site/`.
- No `.env` is needed for hosting the already-generated website.
- The site reads `data.json` with a relative path, so it works under the normal GitHub Pages repo URL structure.

## Incremental scoring workflow

The scorer is designed for long-running, resumable use:

- it skips already-scored occupations
- it retries transient failures
- it writes `india/output/scores_india.json` after each successful score
- it rebuilds `site/data.json` after each successful score

That means the website can always show the latest completed India scores, and you can rerun the scorer later to continue from cache.

## Verification

Useful checks:

```bash
python3 -m unittest india/test_build_occupations.py \
  india/test_fetch_descriptions.py \
  india/test_fetch_education.py \
  india/test_build_stats.py \
  india/test_build_site_data.py \
  india/test_score_india.py -v

python3 -m compileall india
```

## Legacy note

The original U.S.-specific scripts are still in the repo for reference, but the active workflow for this project is now the India pipeline under `india/`.
