# Phase 1 Case Flow Handoff

Implemented from `会审平台-开发方案.md` Phase 1 as a backend-first vertical slice.

## Scope

- `POST /api/cases`: create an event case from one concrete question.
- `POST /api/cases/{case_id}/context`: submit minimal follow-up answers, birth, space, and reality constraints.
- `POST /api/cases/{case_id}/cast`: create the one fixed official reading for the case.
- `GET /api/cases/{case_id}/result`: return the frozen result.
- `POST /api/cases/{case_id}/versions`: create a new case version when real conditions change.

## Current Storage

The implementation uses in-memory dictionaries in `server/api/cases.py`.
This is deliberate for local demo and test speed. Replace `_CASES`, `_RESULTS`,
and `_CAST_BY_KEY` with database-backed repositories when persistence is needed.

## Product Rules Covered

- Default zero follow-up; at most two minimal questions.
- Follow-up questions are button-style options.
- `Idempotency-Key` is required for formal cast.
- Repeated cast returns the original result.
- Existing fixed results cannot be edited through context updates.
- Changed real-world conditions create a new version instead of overwriting.

## Tests

Covered by `tests/test_cases_api.py`.
