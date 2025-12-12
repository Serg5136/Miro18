"""Localized strings for UI elements and accessibility helpers."""

from __future__ import annotations

from typing import Dict

DEFAULT_LOCALE = "ru"

# Strings are grouped by logical UI area to make future translation easier.
LOCALIZED_STRINGS: Dict[str, Dict[str, str]] = {
    "ru": {
        # Toolbar controls
        "toolbar.undo.tooltip": "Отменить последнее действие",
        "toolbar.undo.aria": "Отменить",
        "toolbar.redo.tooltip": "Повторить отменённое действие",
        "toolbar.redo.aria": "Повторить",
        "toolbar.attach.tooltip": "Прикрепить файл-изображение к выделенной карточке без создания новой",
        "toolbar.attach.aria": "Прикрепить к карточке",
        "toolbar.text_color.tooltip": "Изменить цвет текста карточек для текущей темы",
        "toolbar.text_color.aria": "Цвет текста",
        "toolbar.width.label": "Ширина:",
        "toolbar.width.tooltip": "Задайте ширину карточки в пикселях",
        "toolbar.height.label": "Высота:",
        "toolbar.height.tooltip": "Задайте высоту карточки в пикселях",
        "toolbar.apply_size.tooltip": "Применить указанные ширину и высоту к выбранным карточкам",
        "toolbar.apply_size.aria": "Применить размеры",
        # Sidebar controls
        "sidebar.toggle.collapse": "Свернуть управление ▴",
        "sidebar.toggle.expand": "Показать управление ▾",
        "sidebar.section.manage": "Управление",
        "sidebar.section.frames": "Группы / рамки",
        "sidebar.section.file": "Файл",
        "sidebar.section.view": "Вид",
        "sidebar.section.grid": "Сетка",
        "sidebar.add.tooltip": "Создать новую карточку на холсте",
        "sidebar.add.aria": "Добавить карточку",
        "sidebar.color.tooltip": "Изменить цвет выделенной карточки",
        "sidebar.color.aria": "Изменить цвет",
        "sidebar.connect.tooltip": "Включить режим соединения карточек",
        "sidebar.connect.aria": "Соединить карточки",
        "sidebar.edit.tooltip": "Изменить текст выделенной карточки",
        "sidebar.edit.aria": "Редактировать текст",
        "sidebar.delete.tooltip": "Удалить выбранные карточки",
        "sidebar.delete.aria": "Удалить карточку",
        "sidebar.frame_add.tooltip": "Создать новую рамку для группировки",
        "sidebar.frame_add.aria": "Добавить рамку",
        "sidebar.frame_toggle.tooltip": "Свернуть или развернуть выделенную рамку",
        "sidebar.frame_toggle.aria": "Свернуть или развернуть рамку",
        "sidebar.save.tooltip": "Сохранить текущую доску в файл",
        "sidebar.save.aria": "Сохранить",
        "sidebar.load.tooltip": "Загрузить доску из файла",
        "sidebar.load.aria": "Загрузить",
        "sidebar.export.tooltip": "Сохранить доску как изображение PNG",
        "sidebar.export.aria": "Экспорт в PNG",
        "sidebar.attach.tooltip": "Добавить изображение к выделенной карточке",
        "sidebar.attach.aria": "Прикрепить изображение",
        "sidebar.theme.tooltip.light": "Тёмная тема",
        "sidebar.theme.tooltip.dark": "Светлая тема",
        "sidebar.theme.aria": "Переключить тему",
        "sidebar.grid.toggle": "Показывать сетку",
        "sidebar.grid.tooltip": "Отобразить или скрыть сетку на холсте",
        "sidebar.grid.snap": "Привязка к сетке",
        "sidebar.grid.snap.tooltip": "Включить или выключить привязку карточек к сетке",
        "sidebar.grid.step_label": "Шаг:",
        "sidebar.grid.step.tooltip": "Изменить шаг сетки (Enter для применения)",
        "sidebar.minimap.title": "Мини-карта",
        "sidebar.minimap.tooltip": "Нажмите, чтобы переместить вид по доске",
        "sidebar.minimap.card.tooltip": "Карточка на доске",
        "sidebar.minimap.frame.tooltip": "Рамка на доске",
        "sidebar.minimap.viewport.tooltip": "Текущая область просмотра",
    }
}


def get_string(key: str, locale: str = DEFAULT_LOCALE) -> str:
    """Return a localized string by key with graceful fallback."""

    # Primary lookup
    if locale in LOCALIZED_STRINGS and key in LOCALIZED_STRINGS[locale]:
        return LOCALIZED_STRINGS[locale][key]

    # Fallback to default locale
    if key in LOCALIZED_STRINGS.get(DEFAULT_LOCALE, {}):
        return LOCALIZED_STRINGS[DEFAULT_LOCALE][key]

    return key
