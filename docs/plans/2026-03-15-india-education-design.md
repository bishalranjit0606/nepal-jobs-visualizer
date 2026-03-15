# India Education Design

**Goal:** Restore education as a meaningful India-specific field and chart using only official Government of India sources.

## Product Constraint

The education panel should remain in the site because it helps explain how AI exposure relates to training and qualification requirements. The previous all-zero chart was misleading, and the temporary occupation-division replacement changed the meaning of the product.

The India version must therefore:

- keep an education-based hover field
- keep an education-based summary chart
- avoid guessed or non-government data

## Source Strategy

The education source stack will be:

- `NQR / NCVET` for occupation-level qualification records and minimum eligibility text
- `NCS` for occupation titles, NCO codes, and source occupation pages
- `PLFS / MoSPI` only for metrics already supported in the repo, not for inventing occupation-level education where the report does not publish it

## Matching Strategy

The repo already has India occupations from `NCS`. Education will be attached in two layers:

1. match each `NCS` occupation against official `NQR` qualification exports and pages
2. extract minimum education text from the matched `NQR` qualification page

This yields a government-backed occupation-level education value where a match exists.

## Fallback Rules

Fallback must stay honest:

- if an occupation has a reliable `NQR` match, use the extracted education label
- if no reliable official qualification match exists, leave the occupation education blank
- the site should explicitly say when education is unavailable in current official sources

The chart should operate only on occupations with a known official education bucket and should not fabricate values for the rest.

## UI Direction

The secondary sidebar chart should be restored to education semantics:

- heading: `Exposure by education`
- buckets: broad, human-readable education bands
- weighting: same labour-market size signal already used elsewhere

The UI should also surface partial coverage clearly so the user can see how much of the current India dataset has an official education label.

## Data Model Additions

Each India occupation row may now carry:

- `education_raw`
- `education_bucket`
- `education_source_url`
- `education_source_type`

The existing `education` field can remain as the display string, backed by `education_raw`.

## Quality Bar

This work is successful when:

- the chart no longer shows all-zero values
- hover cards show education for occupations with official matches
- unmatched occupations remain explicitly unknown rather than guessed
- all education values in the repo can be traced back to an official government page
