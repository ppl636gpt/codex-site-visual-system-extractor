# Рекомендации по Figma output

## Задача

Преобразуй извлечённые tokens в форму, удобную для Figma Variables, Styles и Tokens Studio.

## Рекомендуемые collections

- `Foundation`
  - Только Base mode
  - Сырая palette, spacing, sizing, radius, shadow, border, opacity, motion
- `Semantic`
  - Default mode плюс по одному mode на каждую извлечённую тему
  - Background, surface, text, action, border, status, overlay и focus roles
- `Components`
  - Документационный mapping, не обязательно отдельная variable collection
  - Используй component properties для variant, size, state и theme

## Рекомендации по типам variables

- Colors -> `COLOR`
- Spacing, sizing, radii, border widths -> `FLOAT`
- Opacity -> `FLOAT`
- Typography composites -> документируй как styles или composite tokens для Tokens Studio
- Shadows -> effect styles или shadow tokens для Tokens Studio
- Borders -> composite border tokens для Tokens Studio

## Рекомендации по именованию

- Преобразуй token paths в slash-separated Figma names.
- Держи foundation names нейтральными:
  - `foundation/colors/palette/blue/500`
  - `foundation/spacing/space-16`
- Держи semantic names role-oriented:
  - `semantic/colors/background/canvas`
  - `semantic/colors/text/default`
- Держи component docs короткими:
  - `Button / solid / md`
  - `Input / outline / md`

## Mapping тем

- Каждую тему из `tokens.themes.json` отображай в отдельный Figma mode.
- Оставляй `auto` отдельным mode только если он реально отличается от `light`.
- Если извлечена только одна тема, всё равно сохраняй semantic collection. Используй один mode с именем найденной темы.

## Заметки для Tokens Studio

- Сохраняй `$type`.
- Сохраняй alias strings без предварительного разворачивания.
- По возможности сохраняй composite typography, border и shadow values как есть.
- Сохраняй `$extensions.codex`, чтобы при ручной доработке не терялся evidence trail.

## English

Translate extracted tokens into a structure that is easy to map into Figma Variables, Styles, and Tokens Studio.

### Recommended collections

- `Foundation`
- `Semantic`
- `Components`

### Guidance

- Map themes to Figma modes.
- Preserve aliases instead of flattening them.
- Keep composite typography, border, and shadow values whenever possible.
- Preserve `$extensions.codex` for traceability.
