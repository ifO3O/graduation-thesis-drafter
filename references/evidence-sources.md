# Evidence Sources Guide

## Priority Inputs
1. `README*` and onboarding docs
2. `docs/` requirement/design/evaluation files
3. framework config (`settings.py`, routing, env templates)
4. domain models/services/controllers
5. tests, evaluation scripts, and reports
6. deployment/ops artifacts (compose, CI, runbooks)

## Evidence Quality Levels
1. A: reproducible and locatable (code + line/function + output)
2. B: locatable but not yet reproducible
3. C: doc-only claim, mark as `TBD_EVIDENCE`

## Citation Format
Use `claim + evidence` format:

- claim: async parser supports concurrent processing.
- evidence: `app/services/parser.py:142` (`ThreadPoolExecutor`), `tests/test_parser.py:55`.

## Red Flags
1. production-ready claim without readiness evidence
2. improvement claim without baseline/metric definition
3. stability claim without load-test or monitoring data
4. security claim without auth/audit evidence

## Minimal Evidence Appendix Columns
1. claim
2. evidence_path
3. line_or_snippet
4. evidence_level (A/B/C)
5. status (implemented/planned/TBD_EVIDENCE)
