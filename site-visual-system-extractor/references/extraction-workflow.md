# Workflow извлечения

## Назначение

Используй этот workflow, когда нужно настроить pipeline rendered inspection или определить, что именно анализировать.

## Последовательность

1. Разреши источник.
   - Удалённый URL: используй как есть.
   - Локальная папка: подними её через HTTP с SPA fallback.
   - Локальный HTML-файл: подними родительскую папку и открой путь к этому файлу.
2. Разверни список целевых страниц.
   - Предпочитай репрезентативные маршруты, а не полное crawling-покрытие.
   - Ищи разнообразие layout и состояний, а не разнообразие контента.
3. Разверни список целевых тем.
   - `auto`: тема по умолчанию на странице.
   - `light` / `dark`: эмулируй browser color scheme.
4. Разверни список viewport.
   - По умолчанию покрывай mobile, tablet и desktop.
   - Добавляй кастомные ширины только там, где layout реально меняется.
5. Загрузи каждую страницу через Playwright.
   - Жди `domcontentloaded`.
   - Жди `networkidle`.
   - Выдержи настроенную settle delay.
   - Дай ещё один animation frame для post-hydration paint.
6. Собери rendered evidence.
   - Computed styles для root и body.
   - Активные custom properties.
   - Доступные CSSOM media queries и имена custom properties.
   - Видимые component candidates.
   - Structural layout containers.
7. Захвати безопасные interactive states.
   - Hover для interactive candidates.
   - Focus для keyboard-addressable controls.
   - Active state через pointer down без полноценного business action.
   - Уже существующие disabled, selected, checked, expanded и open states бери из DOM.
8. Нормализуй evidence в tokens.
   - Дедуплицируй значения.
   - Строй scale и aliases.
   - Разделяй foundation, semantic, theme и component layers.
9. Экспортируй Figma-oriented mapping и markdown audit.

## Рекомендации по scope

- Предпочитай 3-8 страниц вместо десятков.
- Предпочитай 1-3 темы вместо спекулятивного theme inference.
- Предпочитай 3 базовых viewport, если продукт не экстремально layout-heavy.
- Предпочитай безопасную симуляцию состояний вместо action chains, которые меняют business state.

## Шкала надёжности

- Высокая confidence: computed values, напрямую замеченные в rendered UI или активных CSS variables.
- Средняя confidence: роли, выведенные по повторяемому использованию, layout position или component heuristics.
- Низкая confidence: semantic role guesses, где есть только palette evidence.

## Обработка сбоев

- Если маршрут не загрузился, продолжай и зафиксируй это в audit.
- Если состояние не удалось захватить, сохраняй base state и явно отмечай пробел.
- Если CSSOM недоступен из-за cross-origin ограничений, опирайся на computed styles и DOM evidence.
