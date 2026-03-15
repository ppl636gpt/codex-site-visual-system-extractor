# Рекомендации по детекции компонентов

## Цель

Распознавай переиспользуемые UI-примитивы из rendered HTML без зависимости от текстового содержимого страницы.

## Основные сигналы

- Tag и input type
- ARIA role
- Стабильные class-name keywords
- Визуальная сигнатура из computed styles
- Layout role внутри структуры страницы
- Уже существующие DOM state attributes: `disabled`, `checked`, `selected`, `open`, `aria-expanded`

## Эвристики компонентов

- `button`
  - элемент `button`
  - `input[type=button|submit|reset]`
  - `role=button`
  - button-like keywords в классах
- `input`
  - text-like типы `input`
- `textarea`
  - `textarea`
- `select`
  - `select`
  - `role=combobox` или `role=listbox`
- `checkbox`
  - `input[type=checkbox]`
  - `role=checkbox` или `role=switch`
- `radio`
  - `input[type=radio]`
  - `role=radio`
- `modal` / `dialog`
  - `dialog`
  - `role=dialog`
  - `aria-modal=true`
- `card`
  - контейнер с surface-стилизацией и повторяемой сигнатурой
- `tabs`
  - `role=tablist`, `role=tab` или `role=tabpanel`
- `table`
  - `table`, `role=table` или `role=grid`
- `badge` / `chip`
  - маленькая pill-like inline surface
- `tooltip`
  - `role=tooltip`
- `navbar`
  - `header` или `nav` с горизонтальной компоновкой
- `sidebar`
  - `aside` или вертикальный `nav`
- `pagination`
  - контейнер с паттерном page-link
- `toast`
  - `role=alert` или `role=status` с floating surface styling
- `accordion`
  - `details`, `summary` или expandable section patterns
- `menu` / `dropdown`
  - `role=menu`, `role=menubar`, popup listbox или disclosure menu containers
- `link`
  - `a[href]`
- `breadcrumb`
  - breadcrumb-like классы или trail pattern
- `form-group`
  - field wrapper вокруг input-like controls

## Рекомендации по confidence

- Высокая confidence: tag или ARIA role совпадают явно.
- Средняя confidence: есть class keywords и совпадающая визуальная сигнатура.
- Низкая confidence: тип компонента предполагается только по визуальному сходству.

## Эвристики вариантов

- `solid`
  - выраженная заливка
- `outline`
  - заметная рамка и прозрачный или почти прозрачный фон
- `ghost`
  - минимальный chrome, без рамки, прозрачный фон
- `soft`
  - tinted background с низкоакцентной рамкой
- `elevated`
  - surface с тенью
- `underlined`
  - input-like control с акцентом на нижней границе
- `pill`
  - radius близок к половине высоты

## Рекомендации по состояниям

- Захватывай `hover`, `focus` и `active` через безопасные interactions.
- Производные `disabled`, `checked`, `selected`, `open` и `closed` бери из существующего DOM state.
- Не подменяй отсутствующие состояния предположениями.
