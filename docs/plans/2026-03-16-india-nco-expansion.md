# India NCO Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the India occupation universe beyond the current NCS sector scrape so `site/data.json` covers substantially more of PLFS Table 25 and can approach full workforce representation with government-only sources.

**Architecture:** Keep the existing India pipeline, but change the occupation-universe builder from "NCS sector pages only" to "full official NCO-based universe plus NCS enrichment where available". First, stabilize the current NCS rebuild and measurement path. Next, introduce a new canonical source for missing NCO groups, then merge those occupations into the existing stats/scoring/site builders without losing NCS URLs and descriptions where they exist.

**Tech Stack:** Python 3, CSV/JSON builders, `pdftotext`/PDF extraction if the official NCO volumes are available, static HTML frontend.

---

### Task 1: Stabilize the current NCS rebuild path

**Files:**
- Modify: `site/index.html`
- Test: manual rebuild + coverage check

**Step 1: Write the failing test**

Define the expected behavior: the intro occupation count should reflect the actual number of rows in `site/data.json`, not a hardcoded stale value.

**Step 2: Run test to verify it fails**

Run: manual inspection after rebuilding `site/data.json`
Expected: the site still shows `471 occupations` even after the rebuild produced more rows.

**Step 3: Write minimal implementation**

Make the intro count dynamic from `rows.length` during frontend load.

**Step 4: Run test to verify it passes**

Run:
```bash
python3 india/build_occupations.py
python3 india/build_stats.py
python3 india/build_site_data.py
python3 - <<'PY'
import json
print(len(json.load(open('site/data.json'))))
PY
```
Expected: the UI count matches the rebuilt row count.

**Step 5: Commit**

```bash
git add site/index.html
git commit -m "fix: make India occupation count dynamic"
```

### Task 2: Snapshot current coverage and missing PLFS groups

**Files:**
- Create: `india/analyze_coverage.py`
- Create: `india/test_analyze_coverage.py`

**Step 1: Write the failing test**

Write a test that verifies the analyzer:
- reads PLFS 3-digit group shares
- reads the current occupation universe
- reports covered groups, missing groups, and total represented share

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest india/test_analyze_coverage.py -v
```
Expected: FAIL because the analyzer does not exist yet.

**Step 3: Write minimal implementation**

Implement a small script that reports:
- current occupation count
- current covered PLFS share
- missing PLFS share
- missing 3-digit groups ranked by share

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_analyze_coverage.py -v
python3 india/analyze_coverage.py
```
Expected: PASS, plus a machine-readable coverage report.

**Step 5: Commit**

```bash
git add india/analyze_coverage.py india/test_analyze_coverage.py
git commit -m "feat(india): add workforce coverage analysis"
```

### Task 3: Acquire a full official NCO occupation source

**Files:**
- Create or replace: `india/raw/nco-2015-vol-1.pdf`
- Create or replace: `india/raw/nco-2015-vol-2b.pdf`
- Create: `india/raw/nco-2015-vol-1.txt` (optional generated artifact)
- Create: `india/raw/nco-2015-vol-2b.txt` (optional generated artifact)
- Document: `README.md`

**Step 1: Write the failing test**

Write a test that asserts the NCO source loader rejects HTML stubs/404 pages and accepts real source documents.

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest india/test_nco_source_loader.py -v
```
Expected: FAIL because the loader/validator does not exist.

**Step 3: Write minimal implementation**

Add a loader/validator that:
- detects whether a local NCO artifact is real PDF/text or a saved HTML error page
- surfaces a clear error if the source is invalid

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_nco_source_loader.py -v
python3 india/validate_nco_source.py
```
Expected: PASS, plus a clear validation result for the local NCO sources.

**Step 5: Commit**

```bash
git add README.md india/validate_nco_source.py india/test_nco_source_loader.py
git commit -m "feat(india): validate official NCO source files"
```

### Task 4: Parse the full NCO occupation universe

**Files:**
- Create: `india/build_nco_master.py`
- Create: `india/test_build_nco_master.py`
- Create: `india/output/occupations_nco_master.json`

**Step 1: Write the failing test**

Write tests that assert the parser can:
- read official NCO source text
- extract occupation titles and NCO codes
- retain at least 3-digit group and 1-digit division information
- dedupe cleanly

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest india/test_build_nco_master.py -v
```
Expected: FAIL because the parser does not exist yet.

**Step 3: Write minimal implementation**

Implement `india/build_nco_master.py` to produce a normalized master list with fields like:
- `title`
- `slug`
- `nco_code`
- `nco_group_code`
- `nco_division_code`
- `source = "nco_2015"`

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_build_nco_master.py -v
python3 india/build_nco_master.py
```
Expected: PASS and a populated `india/output/occupations_nco_master.json`.

**Step 5: Commit**

```bash
git add india/build_nco_master.py india/test_build_nco_master.py india/output/occupations_nco_master.json
git commit -m "feat(india): build master occupation list from NCO 2015"
```

### Task 5: Merge NCO master data with NCS occupations

**Files:**
- Modify: `india/build_occupations.py`
- Create: `india/test_build_occupations_merge.py`

**Step 1: Write the failing test**

Write tests that assert:
- existing NCS occupations are preserved
- missing PLFS groups can be filled from NCO master occupations
- NCS URLs/descriptions remain attached where available
- merged rows are deduped by code/title safely

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest india/test_build_occupations_merge.py -v
```
Expected: FAIL because merge behavior is not implemented.

**Step 3: Write minimal implementation**

Update `india/build_occupations.py` so it:
- loads the current NCS occupations
- loads the NCO master list
- merges them into one occupation universe
- marks provenance (`ncs`, `nco_only`, or `ncs+nco`)

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_build_occupations_merge.py -v
python3 india/build_occupations.py
```
Expected: PASS and a larger `india/output/occupations_india.json`.

**Step 5: Commit**

```bash
git add india/build_occupations.py india/test_build_occupations_merge.py india/output/occupations_india.json
git commit -m "feat(india): merge NCO master occupations into India universe"
```

### Task 6: Rebuild downstream stats and measure coverage gain

**Files:**
- Modify: `india/build_stats.py`
- Modify: `india/build_site_data.py`
- Test: coverage output from `india/analyze_coverage.py`

**Step 1: Write the failing test**

Write tests that assert new `nco_only` occupations:
- receive `employment_share`
- receive division pay when possible
- flow into `site/data.json`

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest india/test_build_stats.py india/test_build_site_data.py -v
```
Expected: FAIL for the new merged-occupation cases.

**Step 3: Write minimal implementation**

Update downstream builders to preserve merged-source rows and continue assigning:
- PLFS 3-digit employment share
- PLFS 1-digit pay
- optional education/score fields

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_build_stats.py india/test_build_site_data.py -v
python3 india/build_stats.py
python3 india/build_site_data.py
python3 india/analyze_coverage.py
```
Expected: PASS and higher represented workforce than the current baseline.

**Step 5: Commit**

```bash
git add india/build_stats.py india/build_site_data.py india/output/occupations_india.csv site/data.json
git commit -m "feat(india): propagate expanded occupation universe into site data"
```

### Task 7: Handle unscored NCO-only occupations cleanly in the frontend

**Files:**
- Modify: `site/index.html`

**Step 1: Write the failing test**

Define expected behavior for rows without exposure scores:
- still appear in pay/education views
- appear neutrally in exposure mode
- tooltips clearly indicate missing score data

**Step 2: Run test to verify it fails**

Run: manual browser check against rebuilt `site/data.json`
Expected: ambiguous or misleading rendering for unscored NCO-only occupations.

**Step 3: Write minimal implementation**

Adjust frontend labels/tooltip copy for unscored rows while keeping sizing correct.

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m http.server 8000 -d site
```
Expected: unscored occupations are visible and clearly marked.

**Step 5: Commit**

```bash
git add site/index.html
git commit -m "feat(site): handle unscored expanded India occupations"
```

### Task 8: Refresh docs and final verification

**Files:**
- Modify: `README.md`

**Step 1: Write the failing test**

Define expected documentation updates:
- occupation count is no longer frozen to the old NCS subset
- workforce coverage caveat reflects the expanded universe
- data-source limitations remain explicit

**Step 2: Run test to verify it fails**

Run: manual README review
Expected: docs still describe the old narrower occupation universe.

**Step 3: Write minimal implementation**

Update README coverage language and data-source notes.

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest india/test_build_occupations.py india/test_build_stats.py india/test_build_site_data.py -v
python3 -m compileall india
python3 india/analyze_coverage.py
```
Expected: green tests, successful compile, and a final measured coverage report.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update India coverage and NCO expansion notes"
```
