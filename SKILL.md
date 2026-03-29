---
name: graduation-thesis-drafter
description: Generate evidence-based first drafts of software-engineering graduation theses from a project repository and a school DOCX template. Use when users ask for graduation thesis drafts, thesis formatting by school template, or chaptered writing with traceable code/doc evidence.
---

# Graduation Thesis Drafter

## Goal
Produce a complete and editable thesis first draft in markdown, then render a school-formatted DOCX that follows the provided template style.

## Non-Negotiable Rules
1. Use local repository files first (`README`, `docs/`, source code, tests, configs).
2. Never expose secrets from `.env`, keys, tokens, cookies, or private identifiers.
3. Mark uncertain statements as `TBD_EVIDENCE` instead of guessing.
4. Distinguish clearly between `implemented` and `planned`.
5. Keep every major claim traceable to file paths and, when possible, line anchors.

## Required Inputs
1. Project root path.
2. School thesis template DOCX path.
3. Optional cover DOCX path.
4. Thesis metadata: title, major, student placeholders, expected length.

If metadata is missing, continue with placeholders and list assumptions explicitly.

## Workflow
1. Extract repository facts with `scripts/extract_project_facts.py`.
2. Draft thesis markdown using `assets/thesis-draft-template.md`.
3. Extract school format spec from template DOCX with `scripts/extract_docx_style_spec.py`.
4. Render markdown to DOCX with `scripts/render_thesis_docx.py`.
5. Verify headings, TOC, margins, and evidence appendix before final delivery.

## Bundled Resources
1. `scripts/extract_project_facts.py`: collect project facts and evidence index.
2. `scripts/extract_docx_style_spec.py`: detect page setup and style mapping from school template.
3. `scripts/render_thesis_docx.py`: render markdown into school-formatted DOCX.
4. `references/chapter-outline.md`: chapter plan and depth guidance.
5. `references/evidence-sources.md`: evidence quality and citation rules.
6. `assets/thesis-draft-template.md`: markdown starter template.

## Commands
```bash
python shared-skills/graduation-thesis-drafter/scripts/extract_project_facts.py \
  --project-root . \
  --output docs/thesis_facts.json
```

```bash
python shared-skills/graduation-thesis-drafter/scripts/extract_docx_style_spec.py \
  --template-docx "<school-template.docx>" \
  --output docs/school_style_spec.json
```

```bash
python shared-skills/graduation-thesis-drafter/scripts/render_thesis_docx.py \
  --markdown docs/thesis_draft_YYYY-MM-DD.md \
  --template-docx "<school-template.docx>" \
  --style-spec-json docs/school_style_spec.json \
  --output-docx docs/thesis_draft_YYYY-MM-DD.docx \
  --cover-docx "<optional-cover.docx>"
```

## Environment Requirements
1. Python package: `python-docx`.
2. `pandoc` available in PATH for markdown-to-DOCX conversion.

## Output Contract
1. Chinese academic writing style, no empty jargon.
2. Include measurable metrics whenever available.
3. Include an evidence appendix table with columns:
   - `claim`
   - `evidence_path`
   - `line_or_snippet`
   - `status`
4. Keep markdown editable and DOCX school-formatted.

## Definition of Done
1. Markdown draft is complete and evidence-grounded.
2. DOCX follows school template page and heading conventions.
3. Risks, limitations, and next steps are concrete.
4. No secret leakage and no fabricated metrics.
