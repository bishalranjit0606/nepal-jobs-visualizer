# India Jobs Design

**Goal:** Convert this repository from a U.S.-specific AI exposure visualization based on BLS Occupational Outlook Handbook data into an India-specific AI exposure visualization grounded in official Indian labour-market sources.

## Product Intent

The current project is not just a jobs dataset. It is a visual argument about how AI interacts with a labour market:

- rectangle size shows how much of the workforce is represented by an occupation
- color shows how exposed that occupation is to AI
- hover details explain the occupation and why it received its score

That product intent should remain unchanged for India. The India version should still answer:

1. Which occupations are most exposed to AI?
2. How large are those occupations in the labour market?
3. What economic context helps explain the score?

## Source Strategy

India does not appear to provide a single public source equivalent to the U.S. BLS Occupational Outlook Handbook. The India version will therefore use a source stack:

- `NCO 2015` for occupation taxonomy and codes
- `NCS` for occupation descriptions and career information
- `PLFS / MoSPI` for employment and wage statistics

This keeps the project grounded in official Indian data while accepting that some fields in the U.S. version cannot be reproduced directly.

## Deliberate Scope Changes

The U.S. project includes `job outlook` because BLS publishes occupation-level outlook/projection data. India does not appear to expose a comparable public dataset at the same level of detail and consistency.

For the India version:

- keep workforce size as the primary size signal
- keep AI exposure score as the primary color signal
- keep descriptive hover details and rationale
- remove the U.S.-style `outlook` field in v1

If a credible India projection source is found later, it can be added as a second-phase enhancement.

## Data Model

Each India occupation record should contain:

- `title`
- `slug`
- `nco_code`
- `category`
- `description`
- `pay`
- `jobs` or `employment_share`
- `education` when available from NCS
- `source_urls`
- `exposure`
- `exposure_rationale`

Notes:

- `jobs` is preferred when a defensible occupation-level estimate is available.
- If the source only supports grouped employment statistics, `employment_share` may be stored and rendered as area instead.
- The repo should avoid false precision. If only shares are credible, the UI and copy should say so explicitly.

## UI Direction

The treemap remains the primary view because it is the clearest way to preserve the project’s meaning.

- rectangle size = workforce size or workforce share
- color = AI exposure
- tooltip = occupation details, pay, source, exposure rationale

The current U.S. secondary chart `Exposure vs Outlook` should be replaced in the India version. The recommended replacement is:

- `Exposure vs Pay`

This preserves an interpretable economic comparison using a field that is more likely to be supported by India data.

## Pipeline Changes

The U.S. pipeline is:

1. scrape BLS pages
2. parse HTML into markdown
3. derive CSV statistics
4. score occupations
5. build site data

The India pipeline should become:

1. ingest `NCO 2015` occupation list
2. fetch or normalize `NCS` occupation descriptions
3. derive markdown descriptions for scoring
4. merge employment and wage data from `PLFS / MoSPI`
5. score occupations
6. build India-specific site data

## Repository Impact

Likely changes:

- replace or supplement `occupations.json` with an India master list
- add India-specific ingestion scripts for taxonomy and descriptions
- add a new stats-normalization step for `PLFS / MoSPI`
- update scoring inputs so they refer to Indian occupations
- update site copy from U.S. to India
- replace `Exposure vs Outlook` with `Exposure vs Pay`
- revise README to explain the India source stack and any data limitations

## Quality Bar

The first India release should prioritize:

- honest sourcing
- reproducibility from public inputs
- preserving the core visual argument
- avoiding unsupported fields and fake precision

The first release does not need to perfectly match every feature of the U.S. version as long as it faithfully preserves the project’s purpose.
