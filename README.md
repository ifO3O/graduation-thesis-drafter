# graduation-thesis-drafter

A reusable Codex skill for software graduation thesis drafting.

It supports three core steps:

1. Extract evidence-oriented facts from a project repository.
2. Extract formatting rules from a school DOCX template.
3. Render a thesis markdown draft into a school-formatted DOCX.

## Features

- Project fact extraction: `scripts/extract_project_facts.py`
- Template style extraction: `scripts/extract_docx_style_spec.py`
- Markdown to school DOCX rendering: `scripts/render_thesis_docx.py`
- Optional cover copy: `--cover-docx`
- Evidence appendix workflow for claim traceability

## Folder Structure

```text
graduation-thesis-drafter/
?? SKILL.md
?? README.md
?? agents/openai.yaml
?? assets/thesis-draft-template.md
?? references/chapter-outline.md
?? references/evidence-sources.md
?? scripts/
   ?? extract_project_facts.py
   ?? extract_docx_style_spec.py
   ?? render_thesis_docx.py
```

## Requirements

- Python 3.11+
- `python-docx`
- `pandoc`

Install dependency:

```bash
pip install python-docx
```

## Quick Start

### 1) Extract project facts

```bash
python shared-skills/graduation-thesis-drafter/scripts/extract_project_facts.py   --project-root .   --output docs/thesis_facts.json
```

### 2) Extract school template style spec

```bash
python shared-skills/graduation-thesis-drafter/scripts/extract_docx_style_spec.py   --template-docx "<school-template.docx>"   --output docs/school_style_spec.json
```

### 3) Render markdown to school-formatted DOCX

```bash
python shared-skills/graduation-thesis-drafter/scripts/render_thesis_docx.py   --markdown docs/thesis_draft_YYYY-MM-DD.md   --template-docx "<school-template.docx>"   --style-spec-json docs/school_style_spec.json   --output-docx docs/thesis_draft_YYYY-MM-DD_school.docx   --cover-docx "<optional-cover.docx>"
```

Notes:

- Add `--number-sections` only when markdown headings are not already numbered.
- In Word, update TOC fields after opening the generated DOCX.

## Using As a Codex Skill

Place this folder under:

`~/.codex/skills/graduation-thesis-drafter/`

Then trigger by skill name in a Codex session.

## Recommended Output Files

- `docs/thesis_facts_YYYY-MM-DD.json`
- `docs/school_style_spec_YYYY-MM-DD.json`
- `docs/thesis_draft_YYYY-MM-DD.md`
- `docs/thesis_draft_YYYY-MM-DD_school.docx`

## Known Limitations

- Very complex school headers/footers may still need manual adjustments.
- Pandoc and Word TOC rendering can differ slightly until fields are updated.
- Draft content quality depends on repository documentation and evaluation evidence.

## License

This repository includes a LICENSE file in the root.
