# Модель токенов

## Цель

Генерируй DTCG-like JSON, который остаётся понятным человеку, сохраняет traceability и практически пригоден для Figma Variables и Tokens Studio.

## Границы файлов

- `tokens.foundation.json`
  - `foundation.colors`
  - `foundation.typography`
  - `foundation.spacing`
  - `foundation.sizing`
  - `foundation.radii`
  - `foundation.shadows`
  - `foundation.borders`
  - `foundation.opacity`
  - `foundation.motion`
- `tokens.semantic.json`
  - `semantic.colors`
- `tokens.components.json`
  - `components.<component>.variants.<variant>.sizes.<size>.themes.<theme>.states.<state>`
- `tokens.themes.json`
  - `themes.<theme>.semantic.colors`

## Форма токена

Используй следующую форму для leaf token:

```json
{
  "$value": "#1D4ED8",
  "$type": "color",
  "$description": "Наблюдаемый основной action color",
  "$extensions": {
    "codex": {
      "confidence": 0.93,
      "observationCount": 18,
      "trace": [
        {
          "page": "/dashboard",
          "theme": "dark",
          "viewport": "desktop",
          "selector": "button.btn-primary",
          "state": "hover"
        }
      ]
    }
  }
}
```

## Правила alias

- Используй DTCG alias form: `"{foundation.spacing.space-16}"`.
- Для component tokens предпочитай semantic aliases, если semantic role уже существует.
- Используй theme aliases внутри `tokens.themes.json`, если тема действительно переопределяет базовую semantic token.

## Правила traceability

Храни trace samples в `$extensions.codex.trace`.

Поля trace:

- `page`
- `theme`
- `viewport`
- `selector`
- `state`
- `component`
- `sourceVariable`

Ограничивай trace небольшим репрезентативным набором. Количество наблюдений храни отдельно.

## Правила confidence

- `0.85-1.00`: значение или состояние наблюдалось напрямую.
- `0.60-0.84`: стабильный inference на основе повторяемого использования или последовательных component patterns.
- `0.35-0.59`: эвристическое semantic assignment или fallback.

## Правила именования

- Держи foundation names предсказуемыми и scale-like.
- Держи semantic names role-oriented, а не palette-oriented.
- Держи component names привязанными к UI-примитивам, а не к продуктовой терминологии.
- Держи theme names буквальными: `auto`, `light`, `dark` или реально обнаруженные имена режимов.
