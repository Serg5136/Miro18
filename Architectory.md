mini-miro-board/
├─ src/
│  ├─ main.py              # Точка входа: класс BoardApp и запуск приложения
│  ├─ board_model.py       # Модель данных (Card, Frame, Connection, BoardData)
│  ├─ history.py           # История и команды (SnapshotCommand, History)
│  └─ __init__.py          # (пустой, чтобы src был пакетом)
│
├─ assets/
│  └─ icons/               # (опционально) иконки, картинки
│
├─ tests/
│  └─ test_dummy.py        # (опционально) тесты, если решишь писать
│
├─ .gitignore
├─ README.md
├─ requirements.txt        # Зависимости (Pillow + опциональные)
└─ LICENSE                 # (опционально) лицензия, например MIT



Архитектура
Модули

src/main.py

Класс BoardApp — основное окно и логика:

создание/редактирование карточек;

рамки;

связи;

обработка событий мыши/клавиатуры;

мини-карта;

сохранение/загрузка/экспорт;

применение темы и сетки.

src/board_model.py

Card, Frame, Connection — dataclasses для сущностей;

BoardData — агрегирует все сущности борда;

методы to_primitive() / from_primitive() для сериализации в/из JSON-совместимого dict.

src/history.py

SnapshotCommand(before, after) — команда, умеющая undo() / redo() через set_board_from_data;

History — менеджер истории:

хранит initial_state (борд до изменений);

хранит список команд;

реализует push(), undo(), redo(), current_state().