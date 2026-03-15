# Site Visual System Extractor

Production-ready Codex Desktop skill for extracting a reusable visual system from an existing website or web application instead of cloning the full product.

## Overview

This repository is itself an installable Codex Skill. The root already contains `SKILL.md`, `agents/`, `references/`, `scripts/`, and `assets/` in the same overall shape as built-in Codex Desktop skills.

The skill inspects the rendered interface rather than relying only on source CSS. It works with hydrated DOM, computed styles, CSS custom properties, theme switches, inline styles, runtime class toggles, responsive behavior, and safe interactive states such as `hover`, `focus`, and `active`.

The result is optimized for Figma-first workflows and is suitable for Tokens Studio, Figma Variables, design audits, and design-system reconstruction without copying product logic or content.

## Install from GitHub

Download the ready-to-install bundle from GitHub Releases:

```text
https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip
```

Install it into Codex Desktop:

```bash
mkdir -p "$CODEX_HOME/skills"
curl -L https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip -o skill.zip
unzip skill.zip -d "$CODEX_HOME/skills"
```

If you prefer Git instead of release assets:

```bash
git clone https://github.com/ppl636gpt/codex-site-visual-system-extractor.git "$CODEX_HOME/skills/site-visual-system-extractor"
```

## Install dependencies

```bash
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Invoke the skill with:

```text
$site-visual-system-extractor
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

## Typical usage

Run the full pipeline when you want rendered inspection, token normalization, Figma mapping, and audit reports in one pass:

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

Use the modular scripts when you want to inspect first and export later:

```bash
python3 scripts/inspect_rendered_ui.py --source https://example.com --page / --theme auto --output ./output/raw
python3 scripts/normalize_tokens.py --inspection ./output/raw/inspection.raw.json --output ./output/normalized
python3 scripts/build_figma_mapping.py --inspection ./output/raw/inspection.raw.json --tokens-dir ./output/normalized --output ./output/normalized
```

## Inputs and outputs

- Inputs: `--source` accepts a remote URL, a local static site directory, or a local HTML file. You can repeat `--page`, `--theme`, `--viewport`, and `--state` to widen coverage.
- Outputs: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md`, and `design-audit.md`.

## Repository layout

- Root skill definition: [`SKILL.md`](./SKILL.md)
- UI metadata: [`agents/openai.yaml`](./agents/openai.yaml)
- Script entrypoint: [`scripts/extract_site_tokens.py`](./scripts/extract_site_tokens.py)
- Bundle packager: [`scripts/package_skill_bundle.py`](./scripts/package_skill_bundle.py)
- Russian-only file: [`README.ru.md`](./README.ru.md)
