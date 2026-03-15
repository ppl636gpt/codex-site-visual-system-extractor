# Site Visual System Extractor

Production-ready skill для Codex Desktop, который извлекает из существующего сайта или веб-приложения не код продукта целиком, а только переиспользуемую визуальную систему.

## Проверено по официальной документации OpenAI Codex

Skill перепроверен по официальным страницам OpenAI:

- [Документация Codex Skills](https://developers.openai.com/codex/skills/)
- [База документации Codex](https://developers.openai.com/codex/)

Согласно официальной документации, skill представляет собой директорию с `SKILL.md` и опциональными `scripts/`, `references/`, `assets/` и `agents/openai.yaml`, а Codex может применять skill либо неявно по `description`, либо явно при упоминании skill в prompt.

## Обзор

Этот репозиторий является устанавливаемым Codex Skill. Корень репозитория и есть директория skill, в которой лежит стандартная структура: `SKILL.md`, `agents/`, `references/`, `scripts/` и `assets/`.

Skill анализирует rendered UI, а не только исходные CSS-файлы. Он учитывает hydrated DOM, computed styles, CSS custom properties, переключение тем, inline styles, runtime class toggles, responsive-поведение и безопасные интерактивные состояния вроде `hover`, `focus` и `active`.

Результат ориентирован на Figma-first workflow и подходит для Tokens Studio, Figma Variables, дизайн-аудита и восстановления дизайн-системы без копирования контента и логики продукта.

## Установка из GitHub

- Готовый архив: [skill.zip](https://github.com/ppl636gpt/codex-site-visual-system-extractor/releases/latest/download/skill.zip)
- Репозиторий: [ppl636gpt/codex-site-visual-system-extractor](https://github.com/ppl636gpt/codex-site-visual-system-extractor)

Чтобы Codex обнаружил skill автоматически, распакованная папка должна лежать в одном из официальных каталогов skills, указанных в документации. Самые полезные для практики варианты:

- Пользовательский уровень: `~/.agents/skills/site-visual-system-extractor`
- Уровень репозитория: `<repo>/.agents/skills/site-visual-system-extractor`

После помещения папки в один из этих каталогов Codex подхватывает skill автоматически. Отдельная команда запуска не нужна.

## Как это работает в Codex

- Установи skill в официальный каталог skills.
- Убедись, что для bundled Python scripts доступны зависимости.
- После этого просто формулируй задачу обычным языком.
- Codex может активировать skill автоматически, если запрос соответствует описанию в `SKILL.md`.
- Явное упоминание skill в prompt возможно, но не обязательно.

## Установка зависимостей

```bash
cd ~/.agents/skills/site-visual-system-extractor
python3 -m pip install -r scripts/requirements.txt
python3 -m playwright install chromium
```

Если skill хранится не в пользовательской папке, а в `.agents/skills` внутри репозитория, запускай те же команды из установленной директории skill.

## Что извлекается

- Foundation tokens: цвета, типографика, шкалы spacing и sizing, радиусы, границы, тени, opacity и motion-related visual values, если они реально наблюдаются.
- Semantic tokens: роли для background, surface, text, muted и inverse text, brand accents, status colors, border semantics, overlay и focus ring.
- Component styling: переиспользуемые паттерны для кнопок, form controls, navigation, cards, tables, dialogs, overlays, feedback UI и других UI-примитивов, включая состояния base, hover, focus, active, disabled, selected, checked и open, если они доступны.

## Что skill не делает

- Не клонирует backend и API-поведение.
- Не восстанавливает business logic.
- Не копирует тексты страниц и пользовательские данные.
- Не собирает рабочий клон исходного сайта.

## Ручной запуск скриптов

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

```bash
python3 scripts/inspect_rendered_ui.py --source https://example.com --page / --theme auto --output ./output/raw
python3 scripts/normalize_tokens.py --inspection ./output/raw/inspection.raw.json --output ./output/normalized
python3 scripts/build_figma_mapping.py --inspection ./output/raw/inspection.raw.json --tokens-dir ./output/normalized --output ./output/normalized
```

## Входы и выходы

- Входы: `--source` принимает URL, локальную папку со статическим сайтом или локальный HTML-файл. Для расширения охвата можно повторять `--page`, `--theme`, `--viewport` и `--state`.
- Выходы: `tokens.foundation.json`, `tokens.semantic.json`, `tokens.components.json`, `tokens.themes.json`, `figma-mapping.json`, `components-summary.md` и `design-audit.md`.

## Структура репозитория

- Корневая спецификация skill: [`SKILL.md`](./SKILL.md)
- UI metadata: [`agents/openai.yaml`](./agents/openai.yaml)
- Основной entrypoint скрипта: [`scripts/extract_site_tokens.py`](./scripts/extract_site_tokens.py)
- Скрипт сборки bundle: [`scripts/package_skill_bundle.py`](./scripts/package_skill_bundle.py)
- Английский отдельный файл: [`README.en.md`](./README.en.md)
