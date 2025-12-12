# Иконки действий

Подготовлен набор монохромных SVG-иконок (stroke, без заливки) с размером viewBox 40×40. Цвет определяется через `currentColor`,
поэтому можно перекрашивать их в светлых/тёмных темах без создания отдельных файлов: достаточно менять цвет родительского виджета
или CSS при встраивании в HTML.

## Формат и стиль
- Формат: **SVG** для чёткости на любом масштабе и возможности перекрашивания.
- Стиль: монохромный outline (`stroke-width="2"`, скруглённые окончания), без фоновых заливок.
- Оптимизация под 40×40: все основные элементы вписаны в viewBox 40×40, ключевые детали занимают центральные 28–30 px, чтобы
  оставаться читабельными при отображении кнопок 40×40.

## Правила использования
- Размер клика: 40×40 px. Не масштабируйте сами SVG, меняйте только цвет через `currentColor`.
- Подсказки: у каждого интерактивного элемента должна быть подсказка с действием и горячей клавишей (если есть), а также `ariaLabel`/`ariaDescribedby` для доступности.
- Компонент: используйте `IconWithTooltip`, чтобы автоматически подключить наведение, фокус и активацию клавишами Enter/Space.
- Добавление новых файлов: сохраняйте стиль (outline, `stroke-width="2"`, скругление линий) и viewBox 40×40.

## Имена файлов
Файлы лежат в `assets/icons` и названы по действию:

- `icon-card-add.svg`
- `icon-card-color.svg`
- `icon-connect.svg`
- `icon-text-edit.svg`
- `icon-delete.svg`
- `icon-frame-add.svg`
- `icon-frame-collapse.svg`
- `icon-save.svg`
- `icon-load.svg`
- `icon-export-png.svg`
- `icon-attach-image.svg`
- `icon-theme-toggle.svg`
- `icon-grid-show.svg`
- `icon-grid-snap.svg`
- `icon-undo.svg`
- `icon-redo.svg`
- `icon-text-color.svg`
- `icon-apply-size.svg`

## Пример кода с `IconWithTooltip`

```python
from tkinter import PhotoImage
from src.ui.icon_with_tooltip import IconWithTooltip

icon_connect = PhotoImage(file="assets/icons/icon-connect.svg")
btn_connect = IconWithTooltip(
    parent,
    icon=icon_connect,
    tooltip="Режим соединения (C)",
    ariaLabel="Создать связь",
    ariaDescribedby="Создать связь между карточками",
    size=40,
    command=start_connection_mode,
)
btn_connect.pack()
```

## Использование тем
- Светлая тема: используйте тёмный цвет stroke (например, `#2b2b2b`).
- Тёмная тема: задайте `currentColor` в светлый оттенок (например, `#f0f0f0`).
- При необходимости можно добавить CSS-правило для контейнера с иконками, чтобы менять цвет при переключении темы.
