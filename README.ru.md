# Site Visual System Extractor

Production-ready skill для Codex Desktop, который извлекает из существующего сайта или веб-приложения не код продукта целиком, а только переиспользуемую визуальную систему.

## Обзор

Skill анализирует именно отрендеренный интерфейс, а не только исходные CSS-файлы. Он учитывает hydrated DOM, computed styles, CSS custom properties, переключение тем, inline styles, runtime class toggles, responsive-поведение и безопасные интерактивные состояния вроде `hover`, `focus` и `active`.

Результат ориентирован на Figma-first workflow и подходит для Tokens Studio, Figma Variables, дизайн-аудита и восстановления дизайн-системы без копирования контента и логики продукта.

## Что извлекается

- Foundation tokens: цвета, типографика, шкалы spacing и sizing, радиусы, границы, тени, opacity и motion-related visual values, если они реально наблюдаются.
- Semantic tokens: роли для background, surface, text, muted и inverse text, brand accents, status colors, border semantics, overlay и focus ring.
- Component styling: переиспользуемые паттерны для кнопок, form controls, navigation, cards, tables, dialogs, overlays, feedback UI и других UI-примитивов, включая состояния base, hover, focus, active, disabled, selected, checked и open, если они доступны.

## Что skill не делает

- Не клонирует backend и API-поведение.
- Не восстанавливает business logic.
- Не копирует тексты страниц и пользовательские данные.
- Не собирает рабочий клон исходного сайта.

## Установка в Codex Desktop

```bash
cp -R site-visual-system-extractor "$CODEX_HOME/skills/"
cd "$CODEX_HOME/skills/site-visual-system-extractor"
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Вызывать skill можно так:

```text
$site-visual-system-extractor
```

## Типовой запуск

Полный pipeline стоит запускать, когда нужен rendered inspection, нормализация токенов, Figma mapping и audit reports за один проход:

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

Если нужен поэтапный запуск, используй модульные скрипты:

```bash
python3 scripts/inspect_rendered_ui.py --source https://example.com --page / --theme auto --output ./output/raw
python3 scripts/normalize_tokens.py --inspection ./output/raw/inspection.raw.json --output ./output/normalized
python3 scripts/build_figma_mapping.py --inspection ./output/raw/inspection.raw.json --tokens-dir ./output/normalized --output ./output/normalized
```

## Входы и выходы

- Входы: `--source` принимает URL, локальную папку со статическим сайтом или локальный HTML-файл. Для расширения охвата можно повторять `--page`, `--theme`, `--viewport` и `--state`.
- Выходы: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md` и `design-audit.md`.

## Рекомендуемый workflow

Начни с 3-8 репрезентативных страниц, при наличии тем проверь и `light`, и `dark`, сохрани хотя бы один desktop и один mobile viewport, а затем сначала открой `design-audit.md` и уже после этого уточняй token grouping или повторяй extraction с более узким scope.

## Структура репозитория

- Корневой README: `README.md`
- Standalone skill bundle: [`site-visual-system-extractor`](./site-visual-system-extractor)
- Спецификация skill: [`site-visual-system-extractor/SKILL.md`](./site-visual-system-extractor/SKILL.md)
- README для standalone bundle: [`site-visual-system-extractor/README.md`](./site-visual-system-extractor/README.md)
