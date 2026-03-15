# Site Visual System Extractor

Production-ready Codex Desktop skill for extracting a reusable visual system from an existing website or web application instead of cloning the full product.

## Overview

This repository is an installable Codex Skill. The repository root already contains the standard Codex Desktop skill structure: `SKILL.md`, `agents/`, `references/`, `scripts/`, and `assets/`.

The skill inspects rendered UI instead of relying only on source CSS. It works with hydrated DOM, computed styles, CSS custom properties, theme switches, inline styles, runtime class toggles, responsive behavior, and safe interactive states such as `hover`, `focus`, and `active`.

The result is optimized for Figma-first workflows and is suitable for Tokens Studio, Figma Variables, design audits, and design-system reconstruction without copying product logic or content.

## Install from GitHub

- Release bundle: [skill.zip](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip)
- Repository: [ppl636gpt/codex-site-visual-system-extractor](https://github.com/ppl636gpt/codex-site-visual-system-extractor)

After you place the extracted folder into your Codex Desktop skills directory, Codex detects the skill automatically. No special command is required to “start” it.

## How it works in Codex

- Install the skill into your skills directory.
- Keep dependencies available for the bundled Python scripts.
- Then just describe your task in plain language.
- Codex will use the skill automatically when the request matches the skill description in `SKILL.md`.
- If you ever want to force an explicit reference, you can mention the skill name in the prompt, but that is optional rather than required.

## Install dependencies

```bash
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

## What it extracts

- Foundation tokens: colors, typography, spacing and sizing scales, radii, borders, shadows, opacity, and motion-related visual values when they are visibly present.
- Semantic tokens: roles for background, surface, text, muted and inverse text, brand accents, status colors, border semantics, overlays, and focus rings.
- Component styling: reusable patterns for buttons, form controls, navigation, cards, tables, dialogs, overlays, feedback UI, and similar primitives, including states such as base, hover, focus, active, disabled, selected, checked, and open when available.

## What it does not do

- It does not clone backend or API behavior.
- It does not reconstruct business logic.
- It does not copy page text or user data.
- It does not rebuild the source site as a working app clone.

## Manual script usage

If you want to run the bundled tooling directly instead of relying on Codex skill activation, use the scripts below.

```bash
python3 scripts/extract_site_tokens.py \
  --source https://example.com \
  --page / \
  --page /pricing \
  --theme light \
  --theme dark \
  --state hover \
  --state focus \
  --output ./output/example-site
```

```bash
python3 scripts/inspect_rendered_ui.py --source https://example.com --page / --theme auto --output ./output/raw
python3 scripts/normalize_tokens.py --inspection ./output/raw/inspection.raw.json --output ./output/normalized
python3 scripts/build_figma_mapping.py --inspection ./output/raw/inspection.raw.json --tokens-dir ./output/normalized --output ./output/normalized
```

## Inputs and outputs

- Inputs: `--source` accepts a remote URL, a local static site directory, or a local HTML file. You can repeat `--page`, `--theme`, `--viewport`, and `--state`.
- Outputs: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md`, and `design-audit.md`.

## Repository layout

- Root skill definition: [`SKILL.md`](./SKILL.md)
- UI metadata: [`agents/openai.yaml`](./agents/openai.yaml)
- Script entrypoint: [`scripts/extract_site_tokens.py`](./scripts/extract_site_tokens.py)
- Bundle packager: [`scripts/package_skill_bundle.py`](./scripts/package_skill_bundle.py)
- Russian-only file: [`README.ru.md`](./README.ru.md)
