# India Education Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an official-government-only education layer to the India jobs pipeline using NQR qualification data and restore the education chart in the site.

**Architecture:** Build a narrow education pipeline that reads the existing India occupation list, matches occupations to official NQR qualifications, extracts qualification text from official NQR pages, normalizes that text into broad education buckets, then merges the results into `occupations_india.csv` and `site/data.json`. The frontend will show education only where an official match exists and will compute the education chart from those matched rows.

**Tech Stack:** Python 3, CSV/JSON, static HTML/JS, official NCS and NQR HTML/XLSX artifacts

---

### Task 1: Add official education source plumbing

**Files:**
- Create: `india/fetch_education.py`
- Create: `india/test_fetch_education.py`
- Create: `india/output/education_india.json`

**Step 1: Write the failing test**

Add unit tests for:

- parsing NQR summary exports
- extracting education text from NQR qualification HTML
- mapping raw education text into broad display buckets

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest india/test_fetch_education.py -v`
Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Implement a script that:

- loads the existing India occupation list
- reads cached official NQR source files
- matches occupations to qualification records conservatively
- extracts education text from qualification pages
- emits normalized education rows with traceable source URLs

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest india/test_fetch_education.py -v`
Expected: PASS

### Task 2: Merge education into the India stats layer

**Files:**
- Modify: `india/build_stats.py`
- Modify: `india/test_build_stats.py`
- Modify: `india/output/occupations_india.csv`

**Step 1: Write the failing test**

Add assertions that `build_stats_rows()` copies normalized education fields into each row.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest india/test_build_stats.py -v`
Expected: FAIL because the new columns are not present.

**Step 3: Write minimal implementation**

Load `education_india.json`, merge by slug, and write:

- `education`
- `education_bucket`
- `education_source_url`
- `education_source_type`

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest india/test_build_stats.py -v`
Expected: PASS

### Task 3: Restore the education chart in the frontend

**Files:**
- Modify: `india/build_site_data.py`
- Modify: `india/test_build_site_data.py`
- Modify: `site/index.html`

**Step 1: Write the failing test**

Add tests that site rows carry the education fields needed by the UI.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest india/test_build_site_data.py -v`
Expected: FAIL because the site rows do not yet expose the new education fields.

**Step 3: Write minimal implementation**

Update the site dataset and frontend so:

- hover cards show official education labels where available
- the sidebar chart groups rows by education bucket
- the UI reports partial education coverage honestly

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest india/test_build_site_data.py -v`
Expected: PASS

### Task 4: Rebuild and verify the India artifacts

**Files:**
- Modify: `README.md`
- Refresh: `india/output/education_india.json`
- Refresh: `india/output/occupations_india.csv`
- Refresh: `site/data.json`

**Step 1: Run the pipeline**

Run:

```bash
python3 india/fetch_education.py
python3 india/build_stats.py
python3 india/build_site_data.py
```

**Step 2: Verify tests**

Run:

```bash
python3 -m unittest india/test_fetch_education.py india/test_build_stats.py india/test_build_site_data.py -v
```

Expected: PASS

**Step 3: Document source links and limitations**

Update the README so the education section explicitly cites `NQR / NCVET` and explains that unmatched occupations remain blank by design.
