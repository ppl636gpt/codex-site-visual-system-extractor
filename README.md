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

### Verified against OpenAI Codex docs

This skill has been aligned against the official Codex documentation:

- [Codex Skills documentation](https://developers.openai.com/codex/skills/)
- [Codex documentation hub](https://developers.openai.com/codex/)

Official docs state that a skill is a directory containing `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`, and that Codex can use a skill either implicitly from its `description` or explicitly when mentioned in a prompt.

### Overview

This repository is an installable Codex Skill. The repository root is the skill directory itself and contains the standard Codex skill structure: `SKILL.md`, `agents/`, `references/`, `scripts/`, and `assets/`.

The skill inspects rendered UI instead of relying only on source CSS. It works with hydrated DOM, computed styles, CSS custom properties, theme switches, inline styles, runtime class toggles, responsive behavior, and safe interactive states such as `hover`, `focus`, and `active`.

The result is optimized for Figma-first workflows and is suitable for Tokens Studio, Figma Variables, design audits, and design-system reconstruction without copying product logic or content.

### Install from GitHub

- Release bundle: [skill.zip](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip)
- Repository: [ppl636gpt/codex-site-visual-system-extractor](https://github.com/ppl636gpt/codex-site-visual-system-extractor)

To be detected by Codex automatically, the extracted skill folder must live in one of the official scanned locations described in the docs. The most relevant ones are:

- User scope: `~/.agents/skills/site-visual-system-extractor`
- Repository scope: `<repo>/.agents/skills/site-visual-system-extractor`

After the folder is placed in one of those locations, Codex detects the skill automatically. No separate start command is required.

### How it works in Codex

- Install the skill into an official skills directory.
- Keep dependencies available for the bundled Python scripts.
- Then describe your task in plain language.
- Codex can activate the skill automatically when the request matches the skill description in `SKILL.md`.
- Explicit skill mention is optional, not required.

### Install dependencies

```bash
cd ~/.agents/skills/site-visual-system-extractor
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

If you keep the skill in a repository-local `.agents/skills` directory, run the same commands from that installed folder instead.

### What it extracts

- Foundation tokens: colors, typography, spacing and sizing scales, radii, borders, shadows, opacity, and motion-related visual values when they are visibly present.
- Semantic tokens: roles for background, surface, text, muted and inverse text, brand accents, status colors, border semantics, overlays, and focus rings.
- Component styling: reusable patterns for buttons, form controls, navigation, cards, tables, dialogs, overlays, feedback UI, and similar primitives, including states such as base, hover, focus, active, disabled, selected, checked, and open when available.

### What it does not do

- It does not clone backend or API behavior.
- It does not reconstruct business logic.
- It does not copy page text or user data.
- It does not rebuild the source site as a working app clone.

### Manual script usage

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

### Проверено по официальной документации OpenAI Codex

Skill перепроверен по официальным страницам OpenAI:

- [Документация Codex Skills](https://developers.openai.com/codex/skills/)
- [База документации Codex](https://developers.openai.com/codex/)

Согласно официальной документации, skill представляет собой директорию с `SKILL.md` и опциональными `scripts/`, `references/`, `assets/` и `agents/openai.yaml`, а Codex может применять skill либо неявно по `description`, либо явно при упоминании skill в prompt.

### Обзор

Этот репозиторий является устанавливаемым Codex Skill. Корень репозитория и есть директория skill, в которой лежит стандартная структура: `SKILL.md`, `agents/`, `references/`, `scripts/` и `assets/`.

Skill анализирует rendered UI, а не только исходные CSS-файлы. Он учитывает hydrated DOM, computed styles, CSS custom properties, переключение тем, inline styles, runtime class toggles, responsive-поведение и безопасные интерактивные состояния вроде `hover`, `focus` и `active`.

Результат ориентирован на Figma-first workflow и подходит для Tokens Studio, Figma Variables, дизайн-аудита и восстановления дизайн-системы без копирования контента и логики продукта.

### Установка из GitHub

- Готовый архив: [skill.zip](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip)
- Репозиторий: [ppl636gpt/codex-site-visual-system-extractor](https://github.com/ppl636gpt/codex-site-visual-system-extractor)

Чтобы Codex обнаружил skill автоматически, распакованная папка должна лежать в одном из официальных каталогов skills, указанных в документации. Самые полезные для практики варианты:

- Пользовательский уровень: `~/.agents/skills/site-visual-system-extractor`
- Уровень репозитория: `<repo>/.agents/skills/site-visual-system-extractor`

После помещения папки в один из этих каталогов Codex подхватывает skill автоматически. Отдельная команда запуска не нужна.

### Как это работает в Codex

- Установи skill в официальный каталог skills.
- Убедись, что для bundled Python scripts доступны зависимости.
- После этого просто формулируй задачу обычным языком.
- Codex может активировать skill автоматически, если запрос соответствует описанию в `SKILL.md`.
- Явное упоминание skill в prompt возможно, но не обязательно.

### Установка зависимостей

```bash
cd ~/.agents/skills/site-visual-system-extractor
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Если skill хранится не в пользовательской папке, а в `.agents/skills` внутри репозитория, запускай те же команды из установленной директории skill.

### Что извлекается

- Foundation tokens: цвета, типографика, шкалы spacing и sizing, радиусы, границы, тени, opacity и motion-related visual values, если они реально наблюдаются.
- Semantic tokens: роли для background, surface, text, muted и inverse text, brand accents, status colors, border semantics, overlay и focus ring.
- Component styling: переиспользуемые паттерны для кнопок, form controls, navigation, cards, tables, dialogs, overlays, feedback UI и других UI-примитивов, включая состояния base, hover, focus, active, disabled, selected, checked и open, если они доступны.

### Что skill не делает

- Не клонирует backend и API-поведение.
- Не восстанавливает business logic.
- Не копирует тексты страниц и пользовательские данные.
- Не собирает рабочий клон исходного сайта.

### Ручной запуск скриптов

Если нужно использовать bundled tooling напрямую, а не через автоматическую активацию skill в Codex, можно запускать скрипты вручную.

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
