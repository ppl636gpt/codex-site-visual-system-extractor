![Codex Site Visual System Extractor](./assets/readme-banner.svg)

# Codex Site Visual System Extractor

[![Release](https://img.shields.io/github/v/release/ppl636gpt/codex-site-visual-system-extractor?display_name=tag)](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases)
[![Production Ready](https://img.shields.io/badge/Codex%20Skill-Production%20Ready-0F766E)](https://github.com/ppl636gpt/codex-site-visual-system-extractor)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Figma Workflow](https://img.shields.io/badge/Figma-Token%20Workflow-F24E1E?logo=figma&logoColor=white)](https://www.figma.com/)
[![Install Skill](https://img.shields.io/badge/Download-skill.zip-111827)](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip)

[English](#english) | [Русский](#russian)

<a id="english"></a>

## English

Production-ready Codex Desktop skill for extracting a reusable visual system from an existing website or web application instead of cloning the full product.

### Overview

This repository is itself an installable Codex Skill. The root already contains `SKILL.md`, `agents/`, `references/`, `scripts/`, and `assets/` in the same overall shape as built-in Codex Desktop skills.

The skill inspects the rendered interface rather than relying only on source CSS. It works with hydrated DOM, computed styles, CSS custom properties, theme switches, inline styles, runtime class toggles, responsive behavior, and safe interactive states such as `hover`, `focus`, and `active`.

The result is optimized for Figma-first workflows and is suitable for Tokens Studio, Figma Variables, design audits, and design-system reconstruction without copying product logic or content.

### Install from GitHub

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

### Install dependencies

```bash
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Invoke the skill with:

```text
$site-visual-system-extractor
```

### What it extracts

- Foundation tokens: colors, typography, spacing and sizing scales, radii, borders, shadows, opacity, and motion-related visual values when they are visibly present.
- Semantic tokens: roles for background, surface, text, muted and inverse text, brand accents, status colors, border semantics, overlays, and focus rings.
- Component styling: reusable patterns for buttons, form controls, navigation, cards, tables, dialogs, overlays, feedback UI, and similar primitives, including states such as base, hover, focus, active, disabled, selected, checked, and open when available.

### What it does not do

- It does not clone backend or API behavior.
- It does not reconstruct business logic.
- It does not copy page text or user data.
- It does not rebuild the source site as a working app clone.

### Typical usage

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

### Inputs and outputs

- Inputs: `--source` accepts a remote URL, a local static site directory, or a local HTML file. You can repeat `--page`, `--theme`, `--viewport`, and `--state`.
- Outputs: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md`, and `design-audit.md`.

### Repository layout

- Root skill definition: [`SKILL.md`](./SKILL.md)
- UI metadata: [`agents/openai.yaml`](./agents/openai.yaml)
- Script entrypoint: [`scripts/extract_site_tokens.py`](./scripts/extract_site_tokens.py)
- Bundle packager: [`scripts/package_skill_bundle.py`](./scripts/package_skill_bundle.py)
- English-only file: [`README.en.md`](./README.en.md)
- Russian-only file: [`README.ru.md`](./README.ru.md)

<a id="russian"></a>

## Русский

Production-ready skill для Codex Desktop, который извлекает из существующего сайта или веб-приложения не код продукта целиком, а только переиспользуемую визуальную систему.

### Обзор

Этот репозиторий сам является устанавливаемым Codex Skill. В корне уже лежат `SKILL.md`, `agents/`, `references/`, `scripts/` и `assets/` в той же общей форме, что и у встроенных skill для Codex Desktop.

Skill анализирует именно отрендеренный интерфейс, а не только исходные CSS-файлы. Он учитывает hydrated DOM, computed styles, CSS custom properties, переключение тем, inline styles, runtime class toggles, responsive-поведение и безопасные интерактивные состояния вроде `hover`, `focus` и `active`.

Результат ориентирован на Figma-first workflow и подходит для Tokens Studio, Figma Variables, дизайн-аудита и восстановления дизайн-системы без копирования контента и логики продукта.

### Установка из GitHub

Готовый installable bundle можно скачать из GitHub Releases:

```text
https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip
```

Установка в Codex Desktop:

```bash
mkdir -p "$CODEX_HOME/skills"
curl -L https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip -o skill.zip
unzip skill.zip -d "$CODEX_HOME/skills"
```

Если удобнее ставить через Git, а не через release asset:

```bash
git clone https://github.com/ppl636gpt/codex-site-visual-system-extractor.git "$CODEX_HOME/skills/site-visual-system-extractor"
```

### Установка зависимостей

```bash
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Вызывать skill можно так:

```text
$site-visual-system-extractor
```

### Что извлекается

- Foundation tokens: цвета, типографика, шкалы spacing и sizing, радиусы, границы, тени, opacity и motion-related visual values, если они реально наблюдаются.
- Semantic tokens: роли для background, surface, text, muted и inverse text, brand accents, status colors, border semantics, overlay и focus ring.
- Component styling: переиспользуемые паттерны для кнопок, form controls, navigation, cards, tables, dialogs, overlays, feedback UI и других UI-примитивов, включая состояния base, hover, focus, active, disabled, selected, checked и open, если они доступны.

### Что skill не делает

- Не клонирует backend и API-поведение.
- Не восстанавливает business logic.
- Не копирует тексты страниц и пользовательские данные.
- Не собирает рабочий клон исходного сайта.

### Типовой запуск

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

### Входы и выходы

- Входы: `--source` принимает URL, локальную папку со статическим сайтом или локальный HTML-файл. Для расширения охвата можно повторять `--page`, `--theme`, `--viewport` и `--state`.
- Выходы: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md` и `design-audit.md`.

### Структура репозитория

- Корневая спецификация skill: [`SKILL.md`](./SKILL.md)
- UI metadata: [`agents/openai.yaml`](./agents/openai.yaml)
- Основной entrypoint скрипта: [`scripts/extract_site_tokens.py`](./scripts/extract_site_tokens.py)
- Скрипт сборки bundle: [`scripts/package_skill_bundle.py`](./scripts/package_skill_bundle.py)
- Английский отдельный файл: [`README.en.md`](./README.en.md)
- Русский отдельный файл: [`README.ru.md`](./README.ru.md)
