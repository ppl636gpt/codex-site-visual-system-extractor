# Site Visual System Extractor

Русский | [English](#english)

## Русский

`site-visual-system-extractor` — standalone bundle для Codex Desktop, который можно отдельно скопировать в каталог skills и использовать без корневых файлов репозитория.

### Что внутри

- `SKILL.md` — основная инструкция skill
- `agents/openai.yaml` — UI metadata
- `references/` — документация по workflow, token model и quality checks
- `scripts/` — Playwright-based extraction pipeline и экспорт в Figma-friendly outputs

### Быстрая установка

```bash
cp -R site-visual-system-extractor "$CODEX_HOME/skills/"
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

### Быстрый запуск

```bash
python3 scripts/extract_site_tokens.py \
  --source https://example.com \
  --page / \
  --theme auto \
  --output ./output/example
```

### Что получится на выходе

- `tokens.foundation.json`
- `tokens.semantic.json`
- `tokens.components.json`
- `tokens.themes.json`
- `figma-mapping.json`
- `components-summary.md`
- `design-audit.md`

### Для чего использовать

- перенос визуальной системы сайта в Figma
- extraction design tokens из готового продукта
- анализ light/dark themes
- сбор reusable UI patterns перед редизайном

### Важные ограничения

- не копирует тексты и пользовательские данные
- не клонирует бизнес-логику
- не восстанавливает backend
- не делает рабочий клон приложения

## English

`site-visual-system-extractor` is a standalone bundle for Codex Desktop. You can copy this folder directly into your skills directory and use it without the repository root files.

### Contents

- `SKILL.md` — main skill instructions
- `agents/openai.yaml` — UI metadata
- `references/` — workflow, token model, and quality docs
- `scripts/` — Playwright-based extraction pipeline and Figma-friendly exporters

### Quick install

```bash
cp -R site-visual-system-extractor "$CODEX_HOME/skills/"
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

### Quick start

```bash
python3 scripts/extract_site_tokens.py \
  --source https://example.com \
  --page / \
  --theme auto \
  --output ./output/example
```

### Output files

- `tokens.foundation.json`
- `tokens.semantic.json`
- `tokens.components.json`
- `tokens.themes.json`
- `figma-mapping.json`
- `components-summary.md`
- `design-audit.md`

### Best uses

- moving a website visual language into Figma
- extracting design tokens from an existing product
- analyzing light/dark themes
- collecting reusable UI patterns before redesign work

### Important limitations

- does not copy page text or user data
- does not clone business logic
- does not reconstruct backend behavior
- does not create a working app clone
