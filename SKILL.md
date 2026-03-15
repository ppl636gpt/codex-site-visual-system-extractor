---
name: site-visual-system-extractor
description: Extract a reusable visual system and design tokens from a live website, web app, or local static export into Figma-friendly outputs. Use this skill when Codex needs rendered UI inspection, computed styles, CSS variables, themes, responsive layouts, component states, and reusable UI patterns without copying content or business logic.
---

# Site Visual System Extractor

Extract only the reusable visual layer from an existing site or app and convert it into design-system artifacts for a Figma-first workflow. Treat the rendered interface as the source of truth: inspect hydrated DOM, computed styles, active CSS variables, responsive behavior, and safe interaction states instead of relying on source CSS alone.

## Use This Skill When

- The source is a public URL, local static site folder, or local HTML file.
- The goal is to recover design tokens, themes, reusable component styling, or layout patterns.
- The output must be Figma-friendly and safe to reuse as a design-system baseline.
- The task must avoid copying content, user data, backend behavior, or business logic.

## Do Not Use This Skill For

- Rebuilding the source product as a working clone.
- Extracting backend or API behavior.
- Copying page text, form values, or user-specific data.
- Recovering hidden flows that require privileged authentication or unsafe actions.

## Required Resources

- `scripts/extract_site_tokens.py` -> default end-to-end path
- `scripts/inspect_rendered_ui.py` -> raw rendered inspection only
- `scripts/normalize_tokens.py` -> rebuild token files from saved inspection
- `scripts/build_figma_mapping.py` -> rebuild Figma mapping and markdown reports

Read references only when needed:

- `references/extraction-workflow.md` -> scope planning, capture order, themes, viewports, states
- `references/token-model.md` -> token schema, aliases, traceability, confidence
- `references/figma-output-guidelines.md` -> Figma variables, collections, modes, Tokens Studio mapping
- `references/component-detection-guidelines.md` -> component heuristics and state classification
- `references/quality-checklist.md` -> final QA before delivery

## Default Workflow

1. Define scope.
   - Prefer 3-8 representative pages.
   - Include key surfaces such as navigation, forms, tables, dialogs, cards, and status UI.
   - Include `light` and `dark` only when they actually exist.
2. Run the end-to-end extractor.

```bash
python3 scripts/extract_site_tokens.py \
  --source https://example.com \
  --page / \
  --page /pricing \
  --page /dashboard \
  --theme light \
  --theme dark \
  --state hover \
  --state focus \
  --state active \
  --output ./output/example-site
```

3. Review outputs in this order:
   - `design-audit.md`
   - `components-summary.md`
   - token JSON files
4. If the result is noisy, rerun with narrower scope:
   - fewer `--page`
   - fewer themes
   - fewer viewports
   - lower `--max-elements`

## Input Rules

- `--source`: remote URL, local site directory, or local HTML file
- `--page`: repeatable route or page path
- `--theme`: `auto`, `light`, `dark`
- `--viewport`: `name=WIDTHxHEIGHT`
- `--state`: `hover`, `focus`, `active`

Always treat `base` as required. Capture derived states such as `disabled`, `checked`, `selected`, and `open` only when they already exist in the rendered UI or can be observed safely.

## Extraction Rules

- Use rendered DOM and computed styles as the source of truth.
- Collect active CSS custom properties from root, body, and sampled elements.
- Sample visible component candidates and structural layout containers instead of the entire DOM.
- Capture only safe interaction states.
- Preserve traceability for page, theme, viewport, selector, component classification, and state.

## Safety Rules

- Never copy page text into outputs.
- Never serialize form values or user-specific data.
- Never preserve API payloads in outputs.
- Never trigger unsafe actions just to discover a state.
- Keep the output limited to reusable visual-system evidence.

## Output Contract

Write these files to the output directory:

- `tokens.foundation.json`
- `tokens.semantic.json`
- `tokens.components.json`
- `tokens.themes.json`
- `figma-mapping.json`
- `components-summary.md`
- `design-audit.md`

Optional:

- `inspection.raw.json` when `--keep-intermediate` is enabled

## Delivery Rules

- Separate reliable observations from heuristic assignments via confidence metadata.
- Prefer aliases over repeated literal values when a stable token already exists.
- Keep theme-specific overrides in `tokens.themes.json`.
- Record missing routes, unavailable states, and ambiguous semantics in `design-audit.md`.

## Troubleshooting

- If Playwright is missing, install Chromium before rerunning.
- If hydration is slow, increase `--wait-ms`.
- If a local SPA needs routing, point `--source` at the exported site directory so the script can serve it with SPA fallback.
- If the UI depends on an already running dev server, start that server first and pass its URL as `--source`.
