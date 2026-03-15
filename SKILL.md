---
name: site-visual-system-extractor
description: Извлекай переиспользуемую визуальную систему и design tokens из живого сайта, веб-приложения по URL или локально сохранённой папки сайта в Figma-friendly output. Use this skill when Codex needs to inspect rendered UI, computed styles, CSS variables, themes, responsive layouts, component states, and reusable UI patterns without cloning business logic or copying content.
---

# Site Visual System Extractor

Извлекай только переиспользуемый визуальный слой из существующего сайта или приложения и преобразуй его в артефакты дизайн-системы для Figma-first workflow. Считай источником истины именно отрендеренный интерфейс: анализируй hydrated DOM, computed styles, активные CSS variables, responsive-поведение и безопасные interactive states, а не только исходные CSS-файлы.

## Область применения

- Извлекай foundation tokens: color, typography, spacing, sizing, radius, shadow, border, opacity и motion-related визуальные параметры, если они реально наблюдаются.
- Извлекай semantic roles: primary, secondary, accent, background, surface, text, muted text, inverse text, success, warning, danger, info, border roles, overlay и focus ring.
- Извлекай component tokens и переиспользуемые UI-паттерны для распространённых контролов и поверхностей.
- Экспортируй Figma-friendly outputs: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md` и `design-audit.md`.

## Что skill не делает

- Не клонируй backend, API-поведение или JS-бизнес-логику.
- Не копируй тексты, пользовательские данные и контентные payload.
- Не восстанавливай исходный сайт как рабочий продукт.
- Не считай обязательными скрытые или недоступные маршруты. Вместо этого фиксируй пробелы в отчёте.

## Обязательные ресурсы

- Используй `scripts/extract_site_tokens.py` для полного end-to-end workflow.
- Используй `scripts/inspect_rendered_ui.py`, если нужен только сырой rendered inspection.
- Используй `scripts/normalize_tokens.py`, чтобы пересобрать token-файлы из сохранённого inspection.
- Используй `scripts/build_figma_mapping.py`, чтобы пересобрать Figma mapping и markdown-отчёты.

Читайте reference-файлы только по необходимости:

- Читай [references/extraction-workflow.md](references/extraction-workflow.md), когда нужно скорректировать порядок захвата или решить, сколько страниц, тем и состояний анализировать.
- Читай [references/token-model.md](references/token-model.md), когда меняешь token schema, aliases или traceability fields.
- Читай [references/figma-output-guidelines.md](references/figma-output-guidelines.md), когда настраиваешь Figma collections, modes или совместимость с Tokens Studio.
- Читай [references/component-detection-guidelines.md](references/component-detection-guidelines.md), когда нужно уточнить эвристики детекции компонентов.
- Читай [references/quality-checklist.md](references/quality-checklist.md) перед финальной сдачей результата.

## Подготовка

1. Установи Python-зависимости:

```bash
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

2. Выбери источник:
   - Удалённый сайт: передай `--source https://example.com`.
   - Локальную папку со статическим экспортом: передай `--source /path/to/site-export`.
   - Локальный HTML-файл: передай `--source /path/to/index.html`.
3. Выбери репрезентативные страницы или маршруты. Предпочитай 3-8 экранов, покрывающих основные поверхности, формы, навигацию, таблицы, диалоги и статусы.
4. Выбери покрытие тем. По умолчанию используй `auto`. Добавляй `light` и `dark`, когда тема действительно важна.

## Стандартный workflow

1. Определи scope.
   - Предпочитай явные `--page` для важных маршрутов.
   - По возможности включай auth, dashboard, settings, marketing, table, form и modal-маршруты.
2. Запусти extractor.

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

3. Проверь сгенерированные файлы.
   - Сначала открой `design-audit.md`, чтобы увидеть confidence, limitations и inconsistencies.
   - Затем открой `components-summary.md`, чтобы оценить покрытие компонентов и состояний.
   - После этого смотри token JSON-файлы, если нужно скорректировать naming или aliasing.
4. Перезапусти extraction с более узким scope, если результат шумный.
   - Сократи `--page`.
   - Ограничь `--viewport`.
   - Оставь только нужные темы.
   - Используй `--max-elements`, чтобы уменьшить over-sampling.

## Правила входных данных

- Принимай `--source` как URL или локальный путь.
- Принимай повторяющиеся `--page`. Интерпретируй относительные значения относительно base URL или корня локального сервера.
- Принимай повторяющиеся `--theme` из набора `auto`, `light`, `dark`.
- Принимай повторяющиеся `--state` из набора `hover`, `focus`, `active`. Всегда захватывай `base`. Производные состояния `disabled`, `checked`, `selected` и `open` бери из реального DOM, если они уже есть.
- Принимай повторяющиеся `--viewport` в формате `name=WIDTHxHEIGHT` для responsive inspection.

## Правила извлечения

- Используй rendered DOM и computed styles как основной источник истины.
- Собирай активные CSS custom properties из root, body и sampled elements.
- Семплируй видимые component candidates и structural containers, а не весь DOM целиком.
- Захватывай безопасные состояния через Playwright:
  - `hover`
  - `focus`
  - `active` через pointer down без полного submit/click flow
- Записывай traceability для каждого token sample:
  - page
  - theme
  - viewport
  - selector
  - component classification
  - state
  - CSS variable source, если он есть

## Правила безопасности

- Никогда не копируй текст страницы в deliverable.
- Никогда не сериализуй значения форм или пользовательские данные.
- Никогда не пытайся проходить privileged auth flows только ради скрытого UI.
- Никогда не сохраняй API-ответы, даже если они были нужны для рендера страницы.
- Держи output сфокусированным только на evidence переиспользуемой визуальной системы.

## Контракт результата

Записывай в output directory следующие файлы:

- `tokens.foundation.json`
- `tokens.semantic.json`
- `tokens.components.json`
- `tokens.themes.json`
- `figma-mapping.json`
- `components-summary.md`
- `design-audit.md`

Опционально:

- `inspection.raw.json`, если включён `--keep-intermediate`.

## Правила сдачи

- Отделяй надёжные наблюдения от эвристических предположений через confidence metadata.
- Предпочитай token aliases сырым literal values, когда уже найден стабильный foundation или semantic token.
- Сохраняй theme-specific overrides в `tokens.themes.json`.
- Сохраняй различия component states только если они реально наблюдались или были безопасно смоделированы.
- Отмечай отсутствующие маршруты, недоступные состояния и неоднозначную семантику в `design-audit.md`.

## Troubleshooting

- Если отсутствует Playwright, установи его и Chromium перед повторным запуском.
- Если локальному SPA нужен routing, укажи `--source` на build/export directory; скрипт поднимет локальный сервер с SPA fallback.
- Если hydration занимает дольше обычного, увеличь `--wait-ms`.
- Если страница зависит от уже работающего dev server, запусти его отдельно и передай его URL в `--source`.

## English

Extract only the reusable visual layer from an existing site or application and convert it into design-system artifacts for a Figma-first workflow. Treat the rendered interface as the source of truth: inspect hydrated DOM, computed styles, active CSS variables, responsive behavior, and safe interaction states instead of relying on source CSS alone.

### Scope

- Extract foundation tokens: color, typography, spacing, sizing, radius, shadow, border, opacity, and observed motion-related visual timing.
- Extract semantic roles: primary, secondary, accent, background, surface, text, muted text, inverse text, success, warning, danger, info, border roles, overlay, and focus ring.
- Extract component tokens and reusable UI patterns for common controls and surfaces.
- Export Figma-friendly outputs: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md`, and `design-audit.md`.

### Non-goals

- Do not clone backend, API behavior, or JS business logic.
- Do not copy page text, user data, or content-heavy payloads.
- Do not rebuild the source site as a working product.

### Required scripts

- `scripts/extract_site_tokens.py` for end-to-end extraction
- `scripts/inspect_rendered_ui.py` for raw rendered inspection
- `scripts/normalize_tokens.py` to rebuild token files from `inspection.raw.json`
- `scripts/build_figma_mapping.py` to rebuild Figma mapping and markdown reports

### Setup

```bash
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

### Standard run

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

### Input rules

- `--source`: remote URL, local HTML file, or local site directory
- `--page`: repeatable route or page path
- `--theme`: `auto`, `light`, `dark`
- `--viewport`: `name=WIDTHxHEIGHT`
- `--state`: `hover`, `focus`, `active`

### Extraction rules

- Use rendered DOM and computed styles as the source of truth.
- Collect active CSS custom properties from root, body, and sampled elements.
- Sample visible component candidates and layout containers instead of the entire DOM.
- Capture safe states only.
- Preserve traceability for page, theme, viewport, selector, component classification, and state.

### Safety rules

- Never copy page text into outputs.
- Never serialize form values or user-specific data.
- Never preserve API responses in outputs.
- Keep the result focused on reusable visual-system evidence only.

### Output contract

- `tokens.foundation.json`
- `tokens.semantic.json`
- `tokens.components.json`
- `tokens.themes.json`
- `figma-mapping.json`
- `components-summary.md`
- `design-audit.md`

Optional:

- `inspection.raw.json` when `--keep-intermediate` is enabled.
