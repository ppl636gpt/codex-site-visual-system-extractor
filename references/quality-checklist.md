# Quality checklist

Используй этот checklist перед финальной сдачей результата.

## Покрытие

- Подтверди, что были проанализированы репрезентативные страницы.
- Подтверди, что были проанализированы нужные темы.
- Подтверди, что responsive layouts были проверены на релевантных viewport.
- Подтверди, что основные component families найдены или явно отмечены как отсутствующие.

## Безопасность

- Подтверди, что в JSON и markdown outputs нет текста страницы и пользовательских данных.
- Подтверди, что outputs описывают только переиспользуемые визуальные паттерны.
- Подтверди, что backend и business logic не были воспроизведены.

## Качество токенов

- Подтверди, что foundation tokens дедуплицированы и образуют понятные scale.
- Подтверди, что semantic roles отражают устойчивый смысл, а не случайные palette names.
- Подтверди, что component tokens по возможности ссылаются на aliases, а не на raw values.
- Подтверди, что сохранены confidence и trace samples.

## Готовность к Figma

- Подтверди, что `figma-mapping.json` группирует tokens в разумные collections и modes.
- Подтверди, что theme overrides заданы явно.
- Подтверди, что composite tokens сохранены в виде, пригодном для Figma или Tokens Studio.

## Качество audit

- Подтверди, что `design-audit.md` описывает limitations и неоднозначности.
- Подтверди, что повторяемые patterns и inconsistencies явно отмечены.
- Подтверди, что надёжно извлечённые факты отделены от эвристики.

## English

Use this checklist before delivery.

### Coverage

- Confirm representative pages were inspected.
- Confirm required themes were inspected.
- Confirm responsive layouts were sampled at relevant viewports.
- Confirm major component families were found or explicitly marked missing.

### Safety and quality

- Confirm outputs contain no copied page text or user data.
- Confirm tokens are deduplicated and aliases are used where possible.
- Confirm `figma-mapping.json`, `components-summary.md`, and `design-audit.md` are present and coherent.
