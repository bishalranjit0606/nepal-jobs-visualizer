# AI Exposure of India's Occupations

An India-specific adaptation of the original jobs project: a static treemap that shows which occupations are likely to be reshaped by AI, how large those occupations are in the labor market, and why they received their scores.

## Purpose

The project is meant to answer three questions visually:

1. Which occupations are most exposed to AI?
2. How large are those occupations in the labor market?
3. What is the reasoning behind each score?

The main view is still a treemap:
- area = labor-market size proxy
- color = AI exposure
- hover = pay, occupation metadata, and scoring rationale

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

This repo is now wired for an India workflow, but it is still a `v1 / WIP` data product.

What is working:
- India occupation list ingestion
- India markdown page generation
- India stats normalization
- India scoring pipeline
- India site data build
- India-specific frontend copy and sizing logic

Current limitations:
- many NCS detail pages only yield metadata-first markdown, not rich descriptions
- labor-market size is currently an `employment_share` proxy, not absolute job counts
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
   Static frontend for the India dataset.

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
3. Choose `Deploy from a branch`.
4. Select your main branch.
5. Select the `/site` folder.
6. Save.

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
