# Site Visual System Extractor

Production-ready skill for Codex Desktop that extracts a reusable visual system from an existing website or web application instead of cloning the full product.

The skill focuses on rendered UI evidence: tokens, themes, component styling, visual states, layout behavior, and reusable patterns.

## What the skill does

The skill analyzes the actual rendered interface rather than relying only on static CSS files. It takes into account:

- hydrated DOM
- computed styles
- CSS custom properties
- theme switching
- inline styles
- runtime class toggles
- responsive layout behavior
- safe interactive states: `hover`, `focus`, `active`

The result is optimized for Figma-first workflows and is suitable for manual transfer, structured token cleanup, or later use in Tokens Studio / Figma Variables pipelines.

## What gets extracted

### Foundation tokens

- colors
- typography
- spacing
- sizing
- radii
- shadows
- borders
- opacity
- motion-related visual values when observed

### Semantic tokens

- primary
- secondary
- accent
- background
- surface
- text
- muted text
- inverse text
- success
- warning
- danger
- info
- border roles
- overlay
- focus ring

### Component-level styling

When corresponding UI elements exist, the skill attempts to extract styling for:

- button
- input
- textarea
- select
- checkbox
- radio
- dropdown
- modal
- card
- tabs
- table
- badge
- chip
- tooltip
- navbar
- sidebar
- pagination
- toast
- accordion
- menu
- link
- breadcrumb
- form-group
- dialog

Whenever possible, the skill captures:

- base
- hover
- focus
- active
- disabled
- selected
- checked
- open

## What the skill does not do

- It does not clone backend or API logic
- It does not reconstruct JS business logic
- It does not copy page text
- It does not preserve user data
- It does not rebuild the source site as a working clone
- It does not attempt to reproduce the full product

## When to use it

Use this skill when you need to:

- extract a design system from an existing website
- move a product’s visual language into Figma
- build a token base before redesign work
- compare `light` and `dark` themes
- extract reusable UI patterns from SPA or JS-heavy interfaces
- prepare foundation and semantic tokens for Tokens Studio

## Repository structure

```text
.
├── README.md
├── README.ru.md
├── README.en.md
└── site-visual-system-extractor/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    └── scripts/
```

The main skill lives in [`site-visual-system-extractor`](./site-visual-system-extractor).

## Install in Codex Desktop

1. Clone this repository.
2. Copy [`site-visual-system-extractor`](./site-visual-system-extractor) into your Codex Desktop skills directory, for example:

```bash
cp -R site-visual-system-extractor "$CODEX_HOME/skills/"
```

3. Invoke the skill by name:

```text
$site-visual-system-extractor
```

## Dependencies

Move into the skill directory:

```bash
cd site-visual-system-extractor
```

Install dependencies:

```bash
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

## Main usage patterns

### 1. Full end-to-end extraction

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

### 2. Rendered inspection only

```bash
python3 scripts/inspect_rendered_ui.py \
  --source https://example.com \
  --page / \
  --theme auto \
  --output ./output/raw-inspection \
  --keep-intermediate
```

### 3. Rebuild tokens from a saved inspection

```bash
python3 scripts/normalize_tokens.py \
  --inspection ./output/raw-inspection/inspection.raw.json \
  --output ./output/normalized
```

### 4. Rebuild Figma mapping and reports

```bash
python3 scripts/build_figma_mapping.py \
  --inspection ./output/raw-inspection/inspection.raw.json \
  --tokens-dir ./output/normalized \
  --output ./output/normalized
```

## Supported inputs

### Remote URL

```bash
--source https://example.com
```

### Local static site directory

```bash
--source /path/to/site-export
```

### Local HTML file

```bash
--source /path/to/index.html
```

## Main CLI parameters

- `--source`: URL, local directory, or HTML file
- `--page`: pages or routes to inspect, repeatable
- `--theme`: `auto`, `light`, `dark`
- `--viewport`: `name=WIDTHxHEIGHT`
- `--state`: `hover`, `focus`, `active`
- `--output`: destination directory
- `--wait-ms`: extra delay after `networkidle`
- `--max-elements`: maximum sampled elements per capture
- `--max-state-probes`: maximum interactive elements to probe for states
- `--keep-intermediate`: write `inspection.raw.json`

## Recommended workflow

1. Choose 3-8 representative pages.
2. If themes exist, inspect both `light` and `dark`.
3. If responsive analysis matters, keep the default viewports or add custom ones.
4. Run `extract_site_tokens.py`.
5. Open `design-audit.md` first.
6. Review `components-summary.md` second.
7. Inspect token JSON files and tighten scope if needed.

## Output files

### `tokens.foundation.json`

Contains base tokens for:

- palette
- typography
- spacing
- sizing
- radii
- shadows
- borders
- opacity
- motion

### `tokens.semantic.json`

Contains semantic roles for:

- background
- surface
- text
- link
- status roles
- border roles
- overlay
- focus

### `tokens.components.json`

Contains:

- components
- variants
- sizes
- themes
- states
- references to foundation / semantic tokens
- traceability and confidence

### `tokens.themes.json`

Contains theme overrides and semantic mappings per theme.

### `figma-mapping.json`

Contains:

- collections
- modes
- variable mapping
- component property mapping
- notes for the Figma workflow

### `components-summary.md`

Human-readable summary of detected components.

### `design-audit.md`

Audit of the extracted design system:

- palette summary
- typography scale
- spacing scale
- theme model
- repeated patterns
- inconsistencies
- confidence notes
- limitations

## How the pipeline works

### Step 1. Resolve source

If the source is local, the skill starts a temporary HTTP server. For SPA builds it uses an `index.html` fallback.

### Step 2. Rendered inspection

Playwright opens each requested page for the selected themes and viewports. After `domcontentloaded`, `networkidle`, and an extra settle delay, the script captures a snapshot.

### Step 3. DOM sampling

The skill does not blindly crawl the full DOM. It prioritizes:

- interactive candidates
- styled surfaces
- structural layout containers
- elements that resemble reusable components

### Step 4. State probing

For safe interactive targets, it probes:

- hover
- focus
- active via pointer down

The skill is designed to avoid triggering business actions or mutating real product data.

### Step 5. Token normalization

Collected values are:

- deduplicated
- grouped into foundation scales
- mapped to semantic roles
- assembled into component token structures
- annotated with traceability and confidence

### Step 6. Figma-oriented export

The final layer generates:

- token JSON
- Figma variable mapping
- markdown summaries
- design audit

## Example prompts in Codex

### Example 1

```text
Use $site-visual-system-extractor to extract the visual system from https://example.com, analyze both light and dark themes, and save the output into ./output/example.
```

### Example 2

```text
Use $site-visual-system-extractor for a local site export in /Users/me/site-build and inspect /, /pricing, and /dashboard.
```

### Example 3

```text
Use $site-visual-system-extractor to generate Figma-friendly tokens only for forms, tables, and modal surfaces from a SPA application.
```

## Limitations

- The skill does not automatically complete private authentication flows
- Some states cannot be captured safely without side effects
- Cross-origin stylesheet rules may be partially unavailable via CSSOM
- Some semantic roles are assigned heuristically, which is reflected in confidence metadata

## Safety model

The skill is intentionally designed to extract reusable visual-system evidence only:

- no page-copy extraction
- no user-data preservation
- no backend reconstruction
- no business-logic recovery

## Useful files

- Skill spec: [site-visual-system-extractor/SKILL.md](./site-visual-system-extractor/SKILL.md)
- Extraction workflow: [site-visual-system-extractor/references/extraction-workflow.md](./site-visual-system-extractor/references/extraction-workflow.md)
- Token model: [site-visual-system-extractor/references/token-model.md](./site-visual-system-extractor/references/token-model.md)
- Figma output guidelines: [site-visual-system-extractor/references/figma-output-guidelines.md](./site-visual-system-extractor/references/figma-output-guidelines.md)

## Repository status

- Repository is published and ready to use
- Skill is production-ready
- A draft release `v0.1.0` already exists in the repository
