# India Jobs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild this repository as an India-specific AI exposure visualization using NCO 2015, NCS, and PLFS/MoSPI data while preserving the treemap-based labour-market story.

**Architecture:** Add a parallel India data pipeline rather than trying to force the current BLS scripts to fit India inputs. Normalize India sources into the repo’s existing downstream shape: occupation metadata, markdown descriptions, structured stats, scores, and final `site/data.json`. Update the frontend only where the India data model requires it, especially replacing the U.S.-only outlook view.

**Tech Stack:** Python 3, static HTML/CSS/JS frontend, JSON/CSV data artifacts, BeautifulSoup/httpx/Playwright when needed

---

### Task 1: Inventory current U.S.-specific assumptions

**Files:**
- Modify: `README.md`
- Inspect: `scrape.py`
- Inspect: `process.py`
- Inspect: `make_csv.py`
- Inspect: `score.py`
- Inspect: `build_site_data.py`
- Inspect: `site/index.html`

**Step 1: Write the failing test**

Create a checklist in the implementation notes of every place that assumes:

- BLS as the source
- U.S. occupations
- `outlook` existing
- pages coming from `html/*.html`

**Step 2: Run test to verify it fails**

Run: manual inspection with `rg -n "BLS|outlook|Occupational Outlook|html/|pages/" .`
Expected: multiple matches showing the current repo is U.S.-specific.

**Step 3: Write minimal implementation**

Document the exact assumptions and decide which are removed, replaced, or kept for the India path.

**Step 4: Run test to verify it passes**

Run: repeat `rg` searches
Expected: a precise migration checklist exists in the implementation notes.

**Step 5: Commit**

```bash
git add README.md docs/plans/2026-03-15-india-jobs-design.md docs/plans/2026-03-15-india-jobs-implementation.md
git commit -m "docs: add india conversion design and plan"
```

### Task 2: Introduce an India data workspace

**Files:**
- Create: `india/README.md`
- Create: `india/raw/.gitkeep`
- Create: `india/intermediate/.gitkeep`
- Create: `india/output/.gitkeep`

**Step 1: Write the failing test**

Define the target folder layout in `india/README.md`:

- raw source files
- normalized intermediate files
- final output files consumed by the main site pipeline

**Step 2: Run test to verify it fails**

Run: `ls india`
Expected: directory does not exist.

**Step 3: Write minimal implementation**

Create the `india/` workspace and explain each folder’s purpose in `india/README.md`.

**Step 4: Run test to verify it passes**

Run: `find india -maxdepth 2 -type f | sort`
Expected: the README and placeholder files exist.

**Step 5: Commit**

```bash
git add india
git commit -m "feat: add india data workspace"
```

### Task 3: Build India occupation master list ingestion

**Files:**
- Create: `india/build_occupations.py`
- Create: `india/output/occupations_india.json`
- Test: `india/README.md`

**Step 1: Write the failing test**

Define a sample expected record shape in the docstring:

```python
{
    "title": "Software Developers",
    "slug": "software-developers",
    "nco_code": "2512.0100",
    "category": "Information and communications technology professionals",
    "source_urls": ["https://..."]
}
```

**Step 2: Run test to verify it fails**

Run: `python3 india/build_occupations.py`
Expected: file not found or script missing.

**Step 3: Write minimal implementation**

Create a script that reads the chosen NCO source input and emits normalized occupation records to `india/output/occupations_india.json`.

**Step 4: Run test to verify it passes**

Run: `python3 india/build_occupations.py`
Expected: output JSON exists and contains normalized occupation records.

**Step 5: Commit**

```bash
git add india/build_occupations.py india/output/occupations_india.json
git commit -m "feat: add india occupation list builder"
```

### Task 4: Build NCS description ingestion

**Files:**
- Create: `india/fetch_descriptions.py`
- Create: `india/output/pages_india.json`
- Create: `india/output/pages/`

**Step 1: Write the failing test**

Specify the normalized description shape in the script docstring:

```python
{
    "slug": "software-developers",
    "title": "Software Developers",
    "description": "...",
    "education": "...",
    "source_urls": ["https://..."]
}
```

**Step 2: Run test to verify it fails**

Run: `python3 india/fetch_descriptions.py --limit 3`
Expected: script missing.

**Step 3: Write minimal implementation**

Implement fetching or local-source normalization for NCS descriptions, then emit:

- structured JSON for downstream merging
- markdown pages for scoring in `india/output/pages/`

**Step 4: Run test to verify it passes**

Run: `python3 india/fetch_descriptions.py --limit 3`
Expected: 3 normalized records and matching markdown files are created.

**Step 5: Commit**

```bash
git add india/fetch_descriptions.py india/output/pages_india.json india/output/pages
git commit -m "feat: add india occupation descriptions"
```

### Task 5: Build PLFS/MoSPI stats normalization

**Files:**
- Create: `india/build_stats.py`
- Create: `india/output/occupations_india.csv`

**Step 1: Write the failing test**

Document the expected CSV columns:

```text
title,slug,nco_code,category,median_pay_annual,jobs,employment_share,education,url
```

**Step 2: Run test to verify it fails**

Run: `python3 india/build_stats.py`
Expected: script missing.

**Step 3: Write minimal implementation**

Normalize the selected PLFS/MoSPI tables into a consistent CSV, even if some fields are blank or approximate. Prefer explicit `employment_share` when direct occupation counts are unavailable.

**Step 4: Run test to verify it passes**

Run: `python3 india/build_stats.py`
Expected: CSV exists with normalized rows matching the occupation master list where possible.

**Step 5: Commit**

```bash
git add india/build_stats.py india/output/occupations_india.csv
git commit -m "feat: add india occupation stats builder"
```

### Task 6: Add India scoring pipeline

**Files:**
- Create: `india/score_india.py`
- Create: `india/output/scores_india.json`
- Inspect: `score.py`

**Step 1: Write the failing test**

Reuse the output contract from the current repo:

```json
{
  "slug": "software-developers",
  "title": "Software Developers",
  "exposure": 8,
  "rationale": "..."
}
```

**Step 2: Run test to verify it fails**

Run: `python3 india/score_india.py --limit 2`
Expected: script missing.

**Step 3: Write minimal implementation**

Create an India scoring script that reads markdown pages from `india/output/pages/`, uses the same JSON response contract, and writes incremental checkpoints to `india/output/scores_india.json`.

**Step 4: Run test to verify it passes**

Run: `python3 india/score_india.py --limit 2`
Expected: two occupations are scored or cached cleanly.

**Step 5: Commit**

```bash
git add india/score_india.py india/output/scores_india.json
git commit -m "feat: add india exposure scoring"
```

### Task 7: Build final India site dataset

**Files:**
- Create: `india/build_site_data.py`
- Modify: `site/data.json`

**Step 1: Write the failing test**

Define the final record shape in the script docstring:

```python
{
    "title": "...",
    "slug": "...",
    "category": "...",
    "pay": 1200000,
    "jobs": 5000000,
    "employment_share": 3.2,
    "education": "...",
    "exposure": 7,
    "exposure_rationale": "...",
    "url": "..."
}
```

**Step 2: Run test to verify it fails**

Run: `python3 india/build_site_data.py`
Expected: script missing.

**Step 3: Write minimal implementation**

Merge India occupations, descriptions, stats, and scores into the site dataset expected by the frontend.

**Step 4: Run test to verify it passes**

Run: `python3 india/build_site_data.py`
Expected: `site/data.json` is rebuilt from India data and passes basic sanity checks.

**Step 5: Commit**

```bash
git add india/build_site_data.py site/data.json
git commit -m "feat: build india site data"
```

### Task 8: Update frontend from U.S. to India

**Files:**
- Modify: `site/index.html`

**Step 1: Write the failing test**

List the required UI changes:

- title and subtitle refer to India
- source links refer to Indian sources
- `Exposure vs Outlook` becomes `Exposure vs Pay`
- tooltip labels no longer assume outlook exists

**Step 2: Run test to verify it fails**

Run: `rg -n "US Job Market|BLS|Outlook" site/index.html`
Expected: matches confirm current U.S.-specific copy and view labels remain.

**Step 3: Write minimal implementation**

Update labels, stats, and scatterplot logic so the site accurately represents the India data model.

**Step 4: Run test to verify it passes**

Run: `rg -n "US Job Market|BLS|Outlook" site/index.html`
Expected: no stale U.S.-specific strings remain unless intentionally retained in comments.

**Step 5: Commit**

```bash
git add site/index.html
git commit -m "feat: adapt frontend for india data"
```

### Task 9: Update documentation and local run instructions

**Files:**
- Modify: `README.md`

**Step 1: Write the failing test**

List the README sections that must change:

- project summary
- data pipeline
- key files
- setup
- usage
- source methodology

**Step 2: Run test to verify it fails**

Run: `rg -n "BLS|U.S.|Occupational Outlook Handbook|outlook" README.md`
Expected: multiple stale references remain.

**Step 3: Write minimal implementation**

Rewrite the README to describe the India-specific source stack, pipeline, limitations, and commands.

**Step 4: Run test to verify it passes**

Run: `rg -n "BLS|Occupational Outlook Handbook" README.md`
Expected: no stale U.S.-specific methodology remains.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update project for india workflow"
```

### Task 10: Verify end-to-end output

**Files:**
- Verify: `india/output/occupations_india.json`
- Verify: `india/output/pages/`
- Verify: `india/output/occupations_india.csv`
- Verify: `india/output/scores_india.json`
- Verify: `site/data.json`
- Verify: `site/index.html`

**Step 1: Write the failing test**

Define end-to-end checks:

- occupation count is non-zero
- score count matches normalized descriptions
- site data rows are non-zero
- exposure values fall within `0..10`
- at least one size field exists per rendered record

**Step 2: Run test to verify it fails**

Run: a local verification script or one-off Python checks before the pipeline is complete
Expected: at least one mismatch or missing artifact.

**Step 3: Write minimal implementation**

Add a small verification command or script to validate the India dataset after regeneration.

**Step 4: Run test to verify it passes**

Run: `python3 -m compileall .` and the final verification command
Expected: scripts compile and the India data sanity checks pass.

**Step 5: Commit**

```bash
git add .
git commit -m "chore: verify india pipeline outputs"
```
