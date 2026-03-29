---
name: graduation-thesis-drafter
description: Generate evidence-based first drafts of software-engineering graduation theses from a real project repository. Use when users ask for 毕业论文初稿, 技术论文草稿, 项目论文, or chaptered academic writing that must map claims to code/doc evidence, evaluation metrics, and implementation details.
---

# Graduation Thesis Drafter

## Goal
Produce a complete and editable Chinese thesis first draft from repository artifacts, and keep every core claim traceable to concrete evidence.

## Non-Negotiable Rules
1. Use local repository files first (`README`, `docs/`, source code, tests, configs).
2. Never expose secrets from `.env`, keys, tokens, cookies, private identifiers, or production credentials.
3. Mark uncertain statements as `待补证据` instead of guessing.
4. Distinguish clearly between `已实现` and `规划中`.
5. Keep claim-evidence links explicit with file paths and (when possible) line anchors.

## Inputs
1. Project root path.
2. Thesis metadata: title, author placeholder, target major/direction, expected length.
3. Optional school/chapter constraints (if absent, use the bundled chapter guide).

If metadata is missing, continue with placeholders and state assumptions in the draft.

## Workflow
1. Extract repository facts with `scripts/extract_project_facts.py`.
2. Build chapter plan from `references/chapter-outline.md`.
3. Draft full text using `assets/thesis-draft-template.md`.
4. Add an evidence appendix using `references/evidence-sources.md`.
5. Add `风险与局限` and `后续工作` with concrete, verifiable action items.
6. Export to Markdown first, then convert to DOCX/PDF if requested.

## Use Bundled Resources
1. Run `scripts/extract_project_facts.py` to generate thesis facts JSON.
2. Read `references/chapter-outline.md` for chapter order, depth, and writing rules.
3. Read `references/evidence-sources.md` for evidence quality and citation format.
4. Start drafting from `assets/thesis-draft-template.md`.

## Commands
```bash
python shared-skills/graduation-thesis-drafter/scripts/extract_project_facts.py \
  --project-root . \
  --output docs/thesis_facts.json
```

```bash
pandoc docs/毕业论文初稿_YYYY-MM-DD.md -o docs/毕业论文初稿_YYYY-MM-DD.docx
pandoc docs/毕业论文初稿_YYYY-MM-DD.md -o docs/毕业论文初稿_YYYY-MM-DD.pdf
```

## Output Contract
1. Use Chinese academic style and avoid empty jargon.
2. Include measurable metrics where available (for example Recall/Precision/Top1/Latency).
3. Provide a section-level evidence table:
   - `结论`
   - `证据路径`
   - `关键行号/片段`
   - `备注（已实现/规划中/待补证据）`
4. Explicitly list assumptions and unknowns.
5. Keep the result editable in Markdown.

## Definition of Done
1. The draft has complete chaptered structure.
2. Major technical claims are evidence-backed.
3. Risks, limitations, and follow-up work are concrete.
4. No secret leakage or fabricated metrics.
