# Phase 2 Birth-Time Rectification Handoff

Implemented from `会审平台-开发方案.md` Phase 2 as a backend-first slice.

## Endpoint

- `POST /api/birth-time/rectify`

The endpoint accepts a birth profile, birth-time accuracy level, optional known
life events, and returns ranked candidate Chinese hours.

## Accuracy Modes

- `exact`: returns the provided hour as a single candidate.
- `approximate`: returns neighboring two-hour candidates around the approximate hour.
- `period`: returns candidates inside `morning`, `afternoon`, `evening`, or `night`.
- `unknown`: compares all 12 Chinese hours.

## Product Rules Covered

- Unknown birth time does not block use.
- Output is candidate-based and uncertainty-aware.
- The response explicitly says it does not absolutely recover the real birth time.
- If top candidates are close, the API can return one additional differentiating question.
- Scoring is deterministic for the same input; no random stub is used.

## Current Scoring

The first implementation uses Bazi hour-pillar summaries plus deterministic
event-category heuristics. It is intentionally conservative and should be
expanded later with Zi Wei, Western astrology, and Vedic comparisons as planned.

## Tests

Covered by `tests/test_birth_time_api.py`.
