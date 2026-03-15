# Site Visual System Extractor

Production-ready skill для Codex Desktop, который извлекает из существующего сайта или веб-приложения не код приложения целиком, а только переиспользуемую визуальную систему: токены, темы, паттерны компонентов, состояния и layout-поведение.

## Что делает skill

Skill анализирует именно реальное отрендеренное состояние интерфейса. Он не ограничивается чтением CSS-файлов и учитывает:

- hydrated DOM
- computed styles
- CSS custom properties
- theme switching
- inline styles
- runtime class toggles
- responsive layout behavior
- безопасные interactive states: `hover`, `focus`, `active`

Результат ориентирован на Figma-first workflow и пригоден для ручного переноса, дальнейшего импорта или использования в Tokens Studio / Figma Variables workflows.

## Что именно извлекается

### Foundation tokens

- colors
- typography
- spacing
- sizing
- radii
- shadows
- borders
- opacity
- motion-related visual values, если они реально наблюдаются

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

Если на сайте есть соответствующие элементы, skill пытается извлечь стили для:

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

Для компонентов по возможности фиксируются:

- base
- hover
- focus
- active
- disabled
- selected
- checked
- open

## Что skill не делает

- Не клонирует backend и API-логику
- Не восстанавливает JS business logic
- Не копирует тексты страниц
- Не сохраняет пользовательские данные
- Не делает рабочую копию сайта
- Не пытается превратить продукт в полную реплику

## Когда использовать

Используй skill, когда нужно:

- выделить дизайн-систему из готового сайта
- перенести визуальный язык продукта в Figma
- собрать token base перед редизайном
- сравнить темы `light` / `dark`
- извлечь reusable UI patterns из SPA или JS-heavy интерфейса
- подготовить foundation и semantic tokens для Tokens Studio

## Структура репозитория

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

Основной skill находится в папке [`site-visual-system-extractor`](./site-visual-system-extractor).

## Установка в Codex Desktop

1. Склонируй репозиторий.
2. Скопируй папку [`site-visual-system-extractor`](./site-visual-system-extractor) в каталог skills твоего Codex Desktop, например:

```bash
cp -R site-visual-system-extractor "$CODEX_HOME/skills/"
```

3. После этого skill можно вызывать по имени:

```text
$site-visual-system-extractor
```

## Зависимости

Перейди в папку skill:

```bash
cd site-visual-system-extractor
```

Установи зависимости:

```bash
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

## Основной способ использования

### 1. Полный end-to-end extraction

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

### 2. Только rendered inspection

```bash
python3 scripts/inspect_rendered_ui.py \
  --source https://example.com \
  --page / \
  --theme auto \
  --output ./output/raw-inspection \
  --keep-intermediate
```

### 3. Пересборка токенов из сохранённого inspection

```bash
python3 scripts/normalize_tokens.py \
  --inspection ./output/raw-inspection/inspection.raw.json \
  --output ./output/normalized
```

### 4. Пересборка Figma mapping и отчётов

```bash
python3 scripts/build_figma_mapping.py \
  --inspection ./output/raw-inspection/inspection.raw.json \
  --tokens-dir ./output/normalized \
  --output ./output/normalized
```

## Поддерживаемые входы

### Удалённый URL

```bash
--source https://example.com
```

### Локальная папка со статическим сайтом

```bash
--source /path/to/site-export
```

### Локальный HTML-файл

```bash
--source /path/to/index.html
```

## Основные CLI-параметры

- `--source`: URL, локальная папка или HTML-файл
- `--page`: страницы или маршруты для анализа, можно указывать несколько раз
- `--theme`: `auto`, `light`, `dark`
- `--viewport`: формат `name=WIDTHxHEIGHT`
- `--state`: `hover`, `focus`, `active`
- `--output`: каталог для результатов
- `--wait-ms`: дополнительная задержка после `networkidle`
- `--max-elements`: лимит sampled elements на один capture
- `--max-state-probes`: лимит интерактивных элементов для state probing
- `--keep-intermediate`: сохранять `inspection.raw.json`

## Рекомендуемый workflow

1. Выбери 3-8 репрезентативных страниц.
2. Если есть темы, проверь `light` и `dark`.
3. Если нужен responsive analysis, оставь стандартные viewport или добавь свои.
4. Запусти `extract_site_tokens.py`.
5. Сначала открой `design-audit.md`.
6. Затем проверь `components-summary.md`.
7. После этого посмотри JSON outputs и скорректируй scope при необходимости.

## Выходные файлы

### `tokens.foundation.json`

Содержит базовые токены:

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

Содержит смысловые роли:

- background
- surface
- text
- link
- status roles
- border roles
- overlay
- focus

### `tokens.components.json`

Содержит:

- компоненты
- варианты
- размеры
- темы
- состояния
- ссылки на foundation / semantic tokens
- traceability и confidence

### `tokens.themes.json`

Содержит theme overrides и semantic mappings по темам.

### `figma-mapping.json`

Содержит:

- collections
- modes
- variable mapping
- component property mapping
- notes для Figma workflow

### `components-summary.md`

Человеко-читаемая сводка по найденным компонентам.

### `design-audit.md`

Аудит извлечённой дизайн-системы:

- palette summary
- typography scale
- spacing scale
- theme model
- repeated patterns
- inconsistencies
- confidence notes
- limitations

## Как работает pipeline

### Шаг 1. Resolve source

Если источник локальный, skill поднимает временный HTTP server. Для SPA используется fallback на `index.html`.

### Шаг 2. Rendered inspection

Через Playwright открываются страницы по заданным темам и viewport. После `domcontentloaded`, `networkidle` и дополнительной задержки собирается snapshot.

### Шаг 3. DOM sampling

Skill не пытается обойти весь DOM без разбора. Он выбирает:

- interactive candidates
- styled surfaces
- structural layout containers
- элементы с признаками reusable components

### Шаг 4. State probing

Для безопасных интерактивных элементов выполняются:

- hover
- focus
- active через pointer down

При этом skill старается не запускать бизнес-операции и не мутировать реальные данные.

### Шаг 5. Token normalization

Собранные значения:

- дедуплицируются
- группируются в foundation scale
- сопоставляются с semantic roles
- собираются в component token structure
- снабжаются traceability и confidence

### Шаг 6. Figma-oriented export

Финальный слой создаёт:

- token JSON
- Figma variable mapping
- markdown summary
- design audit

## Примеры использования в Codex

### Пример 1

```text
Используй $site-visual-system-extractor, чтобы извлечь визуальную систему из https://example.com, проанализировать light и dark темы и сохранить output в ./output/example.
```

### Пример 2

```text
Используй $site-visual-system-extractor для локального экспорта сайта в /Users/me/site-build и проверь страницы /, /pricing и /dashboard.
```

### Пример 3

```text
Используй $site-visual-system-extractor, чтобы собрать Figma-friendly токены только для форм, таблиц и модалок из SPA-приложения.
```

## Ограничения

- Skill не проходит приватную авторизацию автоматически.
- Некоторые состояния нельзя безопасно извлечь без side effects.
- Cross-origin stylesheet rules могут быть частично недоступны из CSSOM.
- Semantic roles в части случаев назначаются эвристически, это отражается в confidence metadata.

## Безопасность

Skill специально спроектирован так, чтобы извлекать только reusable visual system evidence:

- без текстового контента
- без пользовательских данных
- без backend reconstruction
- без восстановления бизнес-логики

## Полезные файлы skill

- Спецификация skill: [site-visual-system-extractor/SKILL.md](./site-visual-system-extractor/SKILL.md)
- Workflow extraction: [site-visual-system-extractor/references/extraction-workflow.md](./site-visual-system-extractor/references/extraction-workflow.md)
- Token model: [site-visual-system-extractor/references/token-model.md](./site-visual-system-extractor/references/token-model.md)
- Figma output guidelines: [site-visual-system-extractor/references/figma-output-guidelines.md](./site-visual-system-extractor/references/figma-output-guidelines.md)

## Статус репозитория

- Репозиторий опубликован и готов к использованию
- Skill production-ready
- В репозитории есть draft release `v0.1.0`
