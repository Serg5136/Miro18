import tkinter as tk
from tkinter import simpledialog, colorchooser, filedialog, messagebox
import json
import os
import copy
from typing import Dict, List
from .board_model import Card as ModelCard, Connection as ModelConnection, Frame as ModelFrame, BoardData

class BoardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mini Miro Board (Python)")
        self.root.geometry("1200x800")

        # Темы
        self.themes = {
            "light": {
                "bg": "#ffffff",
                "grid": "#f0f0f0",
                "card_default": "#fff9b1",
                "card_outline": "#444444",
                "frame_bg": "#f5f5f5",
                "frame_outline": "#888888",
                "frame_collapsed_bg": "#e0e0ff",
                "frame_collapsed_outline": "#aaaaaa",
                "text": "#000000",
                "connection": "#555555",
                "connection_label": "#333333",
                "minimap_bg": "#ffffff",
                "minimap_card_outline": "#888888",
                "minimap_frame_outline": "#aaaaaa",
                "minimap_viewport": "#ff0000",
            },
            "dark": {
                "bg": "#222222",
                "grid": "#333333",
                "card_default": "#444444",
                "card_outline": "#dddddd",
                "frame_bg": "#333333",
                "frame_outline": "#aaaaaa",
                "frame_collapsed_bg": "#444466",
                "frame_collapsed_outline": "#cccccc",
                "text": "#ffffff",
                "connection": "#dddddd",
                "connection_label": "#eeeeee",
                "minimap_bg": "#222222",
                "minimap_card_outline": "#aaaaaa",
                "minimap_frame_outline": "#888888",
                "minimap_viewport": "#ff6666",
            }
        }
        self.theme_name = "light"
        self.theme = self.themes[self.theme_name]

        # Конфиг
        self.config_filename = "_mini_miro_config.json"
        self.load_config()

        # Данные борда
        self.cards = {}          # card_id -> dict с данными
        self.connections = []    # список {from, to, line_id, label, label_id}
        self.next_card_id = 1

        # Группы / рамки
        self.frames = {}         # frame_id -> dict
        self.next_frame_id = 1
        self.selected_frame_id = None

        # Выделение карточек
        self.selected_card_id = None
        self.selected_cards = set()

        # Прямоугольник выделения (lasso)
        self.selection_rect_id = None
        self.selection_start = None  # (x, y) в координатах canvas

        # Перетаскивание / перемещение / resize / connect-drag
        self.drag_data = {
            "dragging": False,
            "dragged_cards": set(),
            "last_x": 0,
            "last_y": 0,
            "moved": False,
            "mode": None,            # "cards", "frame", "resize_card", "connect_drag"
            "frame_id": None,
            "resize_card_id": None,
            "resize_origin": None,   # (x1, y1) левый верх при ресайзе
            "connect_from_card": None,
            "connect_start": None,   # (sx, sy)
            "temp_line_id": None,
        }

        # Режим соединения (кнопкой)
        self.connect_mode = False
        self.connect_from_card_id = None

        # Зум
        self.zoom_factor = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 2.5

        # Сетка
        self.grid_size = 20
        self.snap_to_grid = True
        # Привязка к сетке — переменные для UI
        self.var_snap_to_grid = tk.BooleanVar(value=self.snap_to_grid)
        self.var_grid_size = tk.IntVar(value=self.grid_size)

        # История (Undo/Redo) и автосохранение
        self.history = []
        self.history_index = -1
        self.last_saved_history_index = -1
        self.unsaved_changes = False
        self.autosave_filename = "_mini_miro_autosave.json"

        # Буфер обмена (копирование карточек)
        self.clipboard = None  # {"cards":[...], "connections":[...], "center":(x,y)}

        # Inline-редактор текста карточек
        self.inline_editor = None
        self.inline_editor_window_id = None
        self.inline_editor_card_id = None

        # Контекстные меню
        self.context_card_id = None
        self.context_frame_id = None
        self.context_connection = None
        self.context_click_x = 0
        self.context_click_y = 0

        # Мини-карта
        self.minimap = None

        self._build_ui()
        self.init_board_state()

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Конфиг (тема) ----------

    def load_config(self):
        if os.path.exists(self.config_filename):
            try:
                with open(self.config_filename, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                theme_name = cfg.get("theme")
                if theme_name in self.themes:
                    self.theme_name = theme_name
                    self.theme = self.themes[self.theme_name]
            except Exception:
                pass

    def save_config(self):
        try:
            with open(self.config_filename, "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme_name}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_theme_button_text(self):
        return "Тёмная тема" if self.theme_name == "light" else "Светлая тема"

    def _build_ui(self):
        # Макет
        # Строка 0 — панель инструментов, строка 1 — основная область
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)

        # Панель инструментов (Undo/Redo) сверху слева
        toolbar = tk.Frame(self.root, bg="#e0e0e0", height=32)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="new")

        btn_undo_toolbar = tk.Button(
            toolbar,
            text="⟲ Отменить",
            command=self.on_undo,
        )
        btn_undo_toolbar.pack(side="left", padx=(8, 2), pady=4)

        btn_redo_toolbar = tk.Button(
            toolbar,
            text="⟳ Повторить",
            command=self.on_redo,
        )
        btn_redo_toolbar.pack(side="left", padx=2, pady=4)

        self.canvas = tk.Canvas(self.root, bg=self.theme["bg"])
        self.canvas.grid(row=1, column=0, sticky="nsew")

        # Большой холст для панорамирования
        self.canvas.config(scrollregion=(0, 0, 4000, 4000))

        sidebar = tk.Frame(self.root, width=260, bg="#f0f0f0")
        sidebar.grid(row=1, column=1, sticky="ns")
        sidebar.grid_propagate(False)

        tk.Label(sidebar, text="Управление", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))

        btn_add = tk.Button(sidebar, text="Добавить карточку",
                            command=self.add_card_dialog)
        btn_add.pack(fill="x", padx=10, pady=5)

        btn_color = tk.Button(sidebar, text="Изменить цвет",
                              command=self.change_color)
        btn_color.pack(fill="x", padx=10, pady=5)

        btn_connect = tk.Button(sidebar, text="Соединить карточки (режим)",
                                command=self.toggle_connect_mode)
        btn_connect.pack(fill="x", padx=10, pady=5)

        btn_edit = tk.Button(sidebar, text="Редактировать текст",
                             command=self.edit_card_text_dialog)
        btn_edit.pack(fill="x", padx=10, pady=5)

        btn_delete = tk.Button(sidebar, text="Удалить карточку(и) (Del)",
                               command=self.delete_selected_cards)
        btn_delete.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Группы / рамки", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        btn_add_frame = tk.Button(sidebar, text="Добавить рамку",
                                  command=self.add_frame_dialog)
        btn_add_frame.pack(fill="x", padx=10, pady=5)

        btn_toggle_frame = tk.Button(sidebar, text="Свернуть/развернуть рамку",
                                     command=self.toggle_selected_frame_collapse)
        btn_toggle_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Файл", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        btn_save = tk.Button(sidebar, text="Сохранить...",
                             command=self.save_board)
        btn_save.pack(fill="x", padx=10, pady=5)

        btn_load = tk.Button(sidebar, text="Загрузить...",
                             command=self.load_board)
        btn_load.pack(fill="x", padx=10, pady=5)

        btn_export = tk.Button(sidebar, text="Экспорт в PNG",
                               command=self.export_png)
        btn_export.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Вид", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))

        self.btn_theme = tk.Button(sidebar, text=self.get_theme_button_text(),
                                   command=self.toggle_theme)
        self.btn_theme.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Сетка", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        chk_snap = tk.Checkbutton(
            sidebar,
            text="Привязка к сетке",
            variable=self.var_snap_to_grid,
            bg="#f0f0f0",
            command=self.on_toggle_snap_to_grid,
        )
        chk_snap.pack(fill="x", padx=10, pady=2)

        frame_grid = tk.Frame(sidebar, bg="#f0f0f0")
        frame_grid.pack(fill="x", padx=10, pady=2)

        tk.Label(frame_grid, text="Шаг:", bg="#f0f0f0").pack(side="left")

        spn_grid = tk.Spinbox(
            frame_grid,
            from_=5,
            to=200,
            increment=5,
            textvariable=self.var_grid_size,
            width=5,
            command=self.on_grid_size_change,
        )
        spn_grid.pack(side="left", padx=(5, 0))
        spn_grid.bind("<Return>", self.on_grid_size_change)
        spn_grid.bind("<FocusOut>", self.on_grid_size_change)

        tk.Label(sidebar, text="Мини-карта", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        self.minimap = tk.Canvas(
            sidebar, width=240, height=160,
            bg=self.theme["minimap_bg"], highlightthickness=1, highlightbackground="#cccccc"
        )
        self.minimap.pack(padx=10, pady=(0, 10))
        self.minimap.bind("<Button-1>", self.on_minimap_click)

        tk.Label(
            sidebar,
            text=(
                "Подсказки:\n"
                "— Двойной клик по пустому месту: новая карточка\n"
                "— Двойной клик по карточке: редактировать текст\n"
                "— Двойной клик по связи: текст связи\n"
                "— ЛКМ по карточке: выбрать, перетаскивать\n"
                "— ЛКМ по пустому месту + движение: прямоугольное выделение\n"
                "— Колёсико мыши: зум\n"
                "— Средняя кнопка: панорамирование\n"
                "— Правая кнопка: контекстное меню\n"
                "— Ctrl+Z / Ctrl+Y: отмена / повтор\n"
                "— Ctrl+C / Ctrl+V: копирование / вставка\n"
                "— Ctrl+D: дубликат\n"
                "— Delete: удалить выбранные карточки\n"
                "— Рамка: перетаскивание двигает и карточки внутри\n"
                "— Из карточки: кружок справа — перетягиваем на другую\n"
                "   карточку, чтобы соединить\n"
                "— Квадрат внизу справа — изменение размера карточки"
            ),
            bg="#f0f0f0", justify="left", anchor="w", wraplength=240
        ).pack(padx=10, pady=10)

        # Обработчики мыши
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        # Панорамирование — средней кнопкой
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)

        # Правая кнопка — контекстное меню
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        # Двойной щелчок правой кнопкой — копирование карточки
        self.canvas.bind("<Double-Button-3>", self.on_canvas_right_double_click)

        # Зум колёсиком (Windows / Mac / Linux)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)      # Windows/Mac
        self.canvas.bind("<Button-4>", self.on_mousewheel_linux)  # Linux вверх
        self.canvas.bind("<Button-5>", self.on_mousewheel_linux)  # Linux вниз

        # Клавиатура
        self.root.bind("<Delete>", lambda event: self.delete_selected_cards())
        self.root.bind("<Control-z>", self.on_undo)
        self.root.bind("<Control-Z>", self.on_undo)
        self.root.bind("<Control-y>", self.on_redo)
        self.root.bind("<Control-Y>", self.on_redo)
        self.root.bind("<Control-c>", self.on_copy)
        self.root.bind("<Control-C>", self.on_copy)
        self.root.bind("<Control-v>", self.on_paste)
        self.root.bind("<Control-V>", self.on_paste)
        self.root.bind("<Control-d>", self.on_duplicate)
        self.root.bind("<Control-D>", self.on_duplicate)

        # Контекстные меню
        self._build_context_menus()

    def _build_context_menus(self):
        # Меню карточки
        self.card_menu = tk.Menu(self.root, tearoff=0)
        self.card_menu.add_command(
            label="Редактировать текст",
            command=self._context_edit_card_text,
        )
        self.card_menu.add_command(
            label="Изменить цвет...",
            command=self._context_change_card_color,
        )
        self.card_menu.add_separator()
        self.card_menu.add_command(
            label="Выровнять по левому краю",
            command=self.align_selected_cards_left,
        )
        self.card_menu.add_command(
            label="Выровнять по верхнему краю",
            command=self.align_selected_cards_top,
        )
        self.card_menu.add_command(
            label="Одинаковая ширина",
            command=self.equalize_selected_cards_width,
        )
        self.card_menu.add_command(
            label="Одинаковая высота",
            command=self.equalize_selected_cards_height,
        )
        self.card_menu.add_separator()
        self.card_menu.add_command(
            label="Удалить",
            command=self._context_delete_cards,
        )
    
        # Меню рамки
        self.frame_menu = tk.Menu(self.root, tearoff=0)
        self.frame_menu.add_command(
            label="Переименовать",
            command=self._context_rename_frame,
        )
        self.frame_menu.add_command(
            label="Свернуть/развернуть",
            command=self._context_toggle_frame,
        )
        self.frame_menu.add_separator()
        self.frame_menu.add_command(
            label="Удалить рамку",
            command=self._context_delete_frame,
        )
    
        # Меню связи
        self.connection_menu = tk.Menu(self.root, tearoff=0)
        self.connection_menu.add_command(
            label="Редактировать подпись",
            command=self._context_edit_connection_label,
        )
        self.connection_menu.add_command(
            label="Удалить связь",
            command=self._context_delete_connection,
        )
    
        # Меню пустого места
        self.canvas_menu = tk.Menu(self.root, tearoff=0)
        self.canvas_menu.add_command(
            label="Новая карточка здесь",
            command=self._context_add_card_here,
        )
        self.canvas_menu.add_separator()
        self.canvas_menu.add_command(
            label="Вставить",
            command=self.on_paste,
        )
    
    def on_canvas_right_click(self, event):
        """
        Показывает контекстное меню в зависимости от того, что под курсором.
        """
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        self.context_click_x = cx
        self.context_click_y = cy
    
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        # Сбрасываем контекст
        self.context_card_id = None
        self.context_frame_id = None
        self.context_connection = None
    
        if item_id:
            conn = self.get_connection_from_item(item_id)
            if conn is not None:
                self.context_connection = conn
                self.connection_menu.tk_popup(event.x_root, event.y_root)
                return
    
            card_id = self.get_card_id_from_item((item_id,))
            if card_id is not None:
                self.context_card_id = card_id
                if card_id not in self.selected_cards:
                    self.select_card(card_id, additive=False)
                self.card_menu.tk_popup(event.x_root, event.y_root)
                return
    
            frame_id = self.get_frame_id_from_item((item_id,))
            if frame_id is not None:
                self.context_frame_id = frame_id
                self.select_frame(frame_id)
                self.frame_menu.tk_popup(event.x_root, event.y_root)
                return
    
        # Пустое место
        self.canvas_menu.tk_popup(event.x_root, event.y_root)
    
    # --- Действия контекстного меню ---
    
    def on_canvas_right_double_click(self, event):
        """
        Двойной щелчок правой кнопкой мыши по карточке —
        создаёт её копию немного смещённой.
        """
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        card_id = self.get_card_id_from_item(item)
        if card_id is None:
            return
    
        card = self.cards.get(card_id)
        if not card:
            return
    
        # Смещаем копию относительно исходной карточки
        offset = 30
        new_x = card["x"] + offset
        new_y = card["y"] + offset
    
        new_card_id = self.create_card(new_x, new_y, card["text"], color=card["color"])
        # Выделим новую карточку
        self.select_card(new_card_id, additive=False)
        self.push_history()


    def _context_edit_card_text(self):
        if self.context_card_id is None:
            return
        self.start_inline_edit_card(self.context_card_id)
    
    def _context_change_card_color(self):
        if self.context_card_id is None:
            return
        self.selected_card_id = self.context_card_id
        self.selected_cards = {self.context_card_id}
        self.change_color()
    
    def _context_delete_cards(self):
        if self.context_card_id is not None:
            if self.context_card_id not in self.selected_cards:
                self.select_card(self.context_card_id, additive=False)
        self.delete_selected_cards()
    
    def _context_rename_frame(self):
        if self.context_frame_id is None or self.context_frame_id not in self.frames:
            return
        frame = self.frames[self.context_frame_id]
        new_title = simpledialog.askstring(
            "Название рамки",
            "Заголовок:",
            initialvalue=frame.get("title", ""),
            parent=self.root,
        )
        if new_title is None:
            return
        frame["title"] = new_title
        self.canvas.itemconfig(frame["title_id"], text=new_title)
        self.push_history()
    
    def _context_toggle_frame(self):
        if self.context_frame_id is None:
            return
        self.selected_frame_id = self.context_frame_id
        self.toggle_selected_frame_collapse()
    
    def _context_delete_frame(self):
        frame_id = self.context_frame_id
        if frame_id is None or frame_id not in self.frames:
            return
        frame = self.frames.pop(frame_id)
        self.canvas.delete(frame["rect_id"])
        self.canvas.delete(frame["title_id"])
        if self.selected_frame_id == frame_id:
            self.selected_frame_id = None
        self.push_history()
    
    def _context_edit_connection_label(self):
        conn = self.context_connection
        if not conn:
            return
        current_label = conn.get("label", "")
        new_label = simpledialog.askstring(
            "Подпись связи",
            "Текст связи:",
            initialvalue=current_label,
            parent=self.root,
        )
        if new_label is None:
            return
        conn["label"] = new_label.strip()
        if conn.get("label_id"):
            if conn["label"]:
                self.canvas.itemconfig(
                    conn["label_id"],
                    text=conn["label"],
                    state="normal",
                    fill=self.theme["connection_label"],
                )
            else:
                self.canvas.delete(conn["label_id"])
                conn["label_id"] = None
        elif conn["label"]:
            coords = self.canvas.coords(conn["line_id"])
            if len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
            else:
                mx, my = self.context_click_x, self.context_click_y
            label_id = self.canvas.create_text(
                mx,
                my,
                text=conn["label"],
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",),
            )
            conn["label_id"] = label_id
    
        self.push_history()
    
    def _context_delete_connection(self):
        conn = self.context_connection
        if not conn:
            return
        self.canvas.delete(conn["line_id"])
        if conn.get("label_id"):
            self.canvas.delete(conn["label_id"])
        try:
            self.connections.remove(conn)
        except ValueError:
            pass
        self.push_history()
    
    def _context_add_card_here(self):
        text_value = simpledialog.askstring(
            "Новая карточка",
            "Введите текст карточки:",
            parent=self.root,
        )
        if text_value is None or text_value.strip() == "":
            return
        self.create_card(self.context_click_x, self.context_click_y, text_value.strip(), color=None)
        self.push_history()

    # ---------- Инициализация борда, история, автосейв ----------

    def init_board_state(self):
        """Запускается один раз при старте приложения."""
        restored = False

        # Попытка восстановиться из автосейва
        if os.path.exists(self.autosave_filename):
            res = messagebox.askyesnocancel(
                "Автовосстановление",
                "Найден файл автосохранения.\n"
                "Восстановить последний сеанс?"
            )
            if res:  # Да
                try:
                    with open(self.autosave_filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.set_board_from_data(data)
                    self.history = [copy.deepcopy(data)]
                    self.history_index = 0
                    self.last_saved_history_index = -1
                    restored = True
                except Exception as e:
                    messagebox.showerror("Ошибка автозагрузки", str(e))
                    restored = False
            elif res is None:
                restored = False
            else:
                restored = False

        if not restored:
            self.canvas.delete("all")
            self.cards.clear()
            self.connections.clear()
            self.frames.clear()
            self.selected_card_id = None
            self.selected_cards.clear()
            self.selected_frame_id = None
            self.connect_mode = False
            self.connect_from_card_id = None
            self.zoom_factor = 1.0
            self.canvas.config(scrollregion=(0, 0, 4000, 4000),
                               bg=self.theme["bg"])
            self.next_card_id = 1
            self.next_frame_id = 1

            self.history = []
            self.history_index = -1
            self.last_saved_history_index = -1

            self.draw_grid()
            self.push_history()
            self.last_saved_history_index = self.history_index

        self.update_unsaved_flag()
        self.update_minimap()

    def get_board_data(self):
        """
        Собирает текущее состояние доски в BoardData
        и возвращает примитивный dict (готовый к JSON-сериализации).
        """
        cards: Dict[int, ModelCard] = {}
        for card_id, card in self.cards.items():
            cards[card_id] = ModelCard(
                id=card_id,
                x=card["x"],
                y=card["y"],
                width=card["width"],
                height=card["height"],
                text=card["text"],
                color=card["color"],
            )

        connections: List[ModelConnection] = []
        for conn in self.connections:
            connections.append(
                ModelConnection(
                    from_id=conn["from"],
                    to_id=conn["to"],
                    label=conn.get("label", ""),
                )
            )

        frames: Dict[int, ModelFrame] = {}
        for frame_id, frame in self.frames.items():
            x1, y1, x2, y2 = self.canvas.coords(frame["rect_id"])
            frames[frame_id] = ModelFrame(
                id=frame_id,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                title=frame.get("title", ""),
                collapsed=frame.get("collapsed", False),
            )

        board = BoardData(cards=cards, connections=connections, frames=frames)
        return board.to_primitive()

    def set_board_from_data(self, data):
        """
        Принимает dict (как из JSON), конвертирует в BoardData
        и пересоздаёт объекты на холсте.
        """
        self.canvas.delete("all")
        self.cards.clear()
        self.connections.clear()
        self.frames.clear()
        self.selected_card_id = None
        self.selected_cards.clear()
        self.selected_frame_id = None
        self.connect_mode = False
        self.connect_from_card_id = None
        self.zoom_factor = 1.0
        self.canvas.config(scrollregion=(0, 0, 4000, 4000),
                           bg=self.theme["bg"])
        self.next_card_id = 1
        self.next_frame_id = 1

        self.draw_grid()

        # --- новая часть: используем модель BoardData ---
        board = BoardData.from_primitive(data)

        # Рамки
        for frame in board.frames.values():
            self.create_frame(
                frame.x1,
                frame.y1,
                frame.x2,
                frame.y2,
                title=frame.title,
                frame_id=frame.id,
                collapsed=frame.collapsed,
            )

        # Карточки
        for card in board.cards.values():
            self.create_card(
                card.x,
                card.y,
                card.text,
                color=card.color,
                card_id=card.id,
                width=card.width,
                height=card.height,
            )

        # Связи
        for conn in board.connections:
            from_id = conn.from_id
            to_id = conn.to_id
            if from_id in self.cards and to_id in self.cards:
                self.create_connection(from_id, to_id, label=conn.label)

        # Обновляем scrollregion и миникарту
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.update_minimap()


    def push_history(self):
        state = self.get_board_data()
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        self.history.append(copy.deepcopy(state))
        self.history_index = len(self.history) - 1
        self.update_unsaved_flag()
        self.write_autosave()
        self.update_minimap()

    def on_undo(self, event=None):
        if self.history_index > 0:
            self.history_index -= 1
            state = copy.deepcopy(self.history[self.history_index])
            self.set_board_from_data(state)
            self.update_unsaved_flag()
            self.write_autosave()
            self.update_minimap()

    def on_redo(self, event=None):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = copy.deepcopy(self.history[self.history_index])
            self.set_board_from_data(state)
            self.update_unsaved_flag()
            self.write_autosave()
            self.update_minimap()

    def update_unsaved_flag(self):
        self.unsaved_changes = (self.history_index != self.last_saved_history_index)
        title = "Mini Miro Board (Python)"
        if self.unsaved_changes:
            title += " *"
        self.root.title(title)

    def write_autosave(self):
        try:
            data = self.get_board_data()
            with open(self.autosave_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ---------- Сетка ----------

    def draw_grid(self):
        self.canvas.delete("grid")
        spacing = self.grid_size
        x_max = 4000
        y_max = 4000
        for x in range(0, x_max + 1, spacing):
            self.canvas.create_line(
                x, 0, x, y_max,
                fill=self.theme["grid"],
                tags=("grid",)
            )
        for y in range(0, y_max + 1, spacing):
            self.canvas.create_line(
                0, y, x_max, y,
                fill=self.theme["grid"],
                tags=("grid",)
            )
        self.canvas.tag_lower("grid")

    def snap_cards_to_grid(self, card_ids):
        if not self.snap_to_grid or not card_ids:
            return
        for card_id in card_ids:
            card = self.cards.get(card_id)
            if not card:
                continue
            gx = round(card["x"] / self.grid_size) * self.grid_size
            gy = round(card["y"] / self.grid_size) * self.grid_size
            dx = gx - card["x"]
            dy = gy - card["y"]
            if dx == 0 and dy == 0:
                continue
            card["x"] = gx
            card["y"] = gy
            x1 = gx - card["width"] / 2
            y1 = gy - card["height"] / 2
            x2 = gx + card["width"] / 2
            y2 = gy + card["height"] / 2
            self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(card["text_id"], gx, gy)
            self.update_card_handles_positions(card_id)
            self.update_connections_for_card(card_id)

    # ---------- Карточки ----------

    def add_card_dialog(self):
        text = simpledialog.askstring("Новая карточка",
                                      "Введите текст карточки:",
                                      parent=self.root)
        if text is None or text.strip() == "":
            return
        x = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        y = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        self.create_card(x, y, text, color=None)
        self.push_history()

    def on_canvas_double_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        # Двойной клик по связи — редактируем подпись
        conn = self.get_connection_from_item(item_id)
        if conn is not None:
            current_label = conn.get("label", "")
            new_label = simpledialog.askstring(
                "Подпись связи",
                "Текст связи:",
                initialvalue=current_label,
                parent=self.root,
            )
            if new_label is None:
                return
            conn["label"] = new_label.strip()
            if conn.get("label_id"):
                if conn["label"]:
                    self.canvas.itemconfig(
                        conn["label_id"],
                        text=conn["label"],
                        state="normal",
                        fill=self.theme["connection_label"],
                    )
                else:
                    self.canvas.delete(conn["label_id"])
                    conn["label_id"] = None
            elif conn["label"]:
                coords = self.canvas.coords(conn["line_id"])
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    mx = (x1 + x2) / 2
                    my = (y1 + y2) / 2
                else:
                    mx, my = cx, cy
                label_id = self.canvas.create_text(
                    mx,
                    my,
                    text=conn["label"],
                    font=("Arial", 9, "italic"),
                    fill=self.theme["connection_label"],
                    tags=("connection_label",),
                )
                conn["label_id"] = label_id
            self.push_history()
            return
    
        # Двойной клик по карточке — inline-редактирование
        card_id = self.get_card_id_from_item(item)
        if card_id is not None:
            self.start_inline_edit_card(card_id)
            return
    
        # Двойной клик по пустому месту — новая карточка
        text = simpledialog.askstring(
            "Новая карточка",
            "Введите текст карточки:",
            parent=self.root,
        )
        if text is None or text.strip() == "":
            return
        self.create_card(cx, cy, text.strip(), color=None)
        self.push_history()
    def create_card(self, x, y, text, color=None, card_id=None,
                    width=None, height=None):
        if width is None:
            width = 180
        if height is None:
            height = 100
        if color is None:
            color = self.theme["card_default"]
        if card_id is None:
            card_id = self.next_card_id
            self.next_card_id += 1
        else:
            self.next_card_id = max(self.next_card_id, card_id + 1)

        x1 = x - width / 2
        y1 = y - height / 2
        x2 = x + width / 2
        y2 = y + height / 2

        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            outline=self.theme["card_outline"],
            width=1.5,
            tags=("card", f"card_{card_id}")
        )
        text_id = self.canvas.create_text(
            x, y,
            text=text,
            width=width - 10,
            font=("Arial", 10),
            fill=self.theme["text"],
            tags=("card_text", f"card_{card_id}")
        )

        self.cards[card_id] = {
            "id": card_id,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "text": text,
            "color": color,
            "rect_id": rect_id,
            "text_id": text_id,
            "resize_handle_id": None,
            "connect_handle_id": None,
        }
        return card_id

    def get_card_id_from_item(self, item_ids):
        if not item_ids:
            return None
        item_id = item_ids[0]
        tags = self.canvas.gettags(item_id)
        for tag in tags:
            if tag.startswith("card_"):
                try:
                    return int(tag.split("_")[1])
                except ValueError:
                    continue
        return None

    # ---------- Рамки / группы ----------

    def add_frame_dialog(self):
        title = simpledialog.askstring(
            "Новая рамка",
            "Заголовок группы:",
            parent=self.root
        )
        if title is None:
            return

        cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        width = 400
        height = 250
        x1 = cx - width / 2
        y1 = cy - height / 2
        x2 = cx + width / 2
        y2 = cy + height / 2

        self.create_frame(x1, y1, x2, y2, title=title)
        self.push_history()

    def create_frame(self, x1, y1, x2, y2, title="Группа",
                     frame_id=None, collapsed=False):
        if frame_id is None:
            frame_id = self.next_frame_id
            self.next_frame_id += 1
        else:
            self.next_frame_id = max(self.next_frame_id, frame_id + 1)

        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.theme["frame_collapsed_bg"] if collapsed else self.theme["frame_bg"],
            outline=self.theme["frame_outline"],
            width=2,
            dash=(3, 3) if collapsed else (),
            tags=("frame", f"frame_{frame_id}")
        )
        title_id = self.canvas.create_text(
            x1 + 10, y1 + 15,
            text=title,
            anchor="w",
            font=("Arial", 10, "bold"),
            fill=self.theme["text"],
            tags=("frame_title", f"frame_{frame_id}")
        )

        self.canvas.tag_lower(rect_id)
        self.canvas.tag_lower("grid")

        self.frames[frame_id] = {
            "id": frame_id,
            "rect_id": rect_id,
            "title_id": title_id,
            "title": title,
            "collapsed": collapsed,
        }

        if collapsed:
            self.apply_frame_collapse_state(frame_id)

    def get_frame_id_from_item(self, item_ids):
        if not item_ids:
            return None
        item_id = item_ids[0]
        tags = self.canvas.gettags(item_id)
        for tag in tags:
            if tag.startswith("frame_"):
                try:
                    return int(tag.split("_")[1])
                except ValueError:
                    continue
        for tag in tags:
            if tag.startswith("frame_title"):
                try:
                    return int(tag.split("_")[2])
                except Exception:
                    continue
        return None

    def select_frame(self, frame_id):
        self._clear_card_selection()
        if self.selected_frame_id is not None and self.selected_frame_id in self.frames:
            self._set_frame_outline(self.selected_frame_id, width=2)

        self.selected_frame_id = frame_id
        if frame_id is not None and frame_id in self.frames:
            self._set_frame_outline(frame_id, width=3)

    def _set_frame_outline(self, frame_id, width):
        frame = self.frames.get(frame_id)
        if not frame:
            return
        self.canvas.itemconfig(frame["rect_id"], width=width)

    def toggle_selected_frame_collapse(self):
        frame_id = self.selected_frame_id
        if frame_id is None or frame_id not in self.frames:
            messagebox.showwarning("Нет выбора", "Сначала выберите рамку.")
            return
        frame = self.frames[frame_id]
        frame["collapsed"] = not frame.get("collapsed", False)

        rect_id = frame["rect_id"]
        if frame["collapsed"]:
            self.canvas.itemconfig(
                rect_id,
                dash=(3, 3),
                fill=self.theme["frame_collapsed_bg"],
                outline=self.theme["frame_collapsed_outline"]
            )
        else:
            self.canvas.itemconfig(
                rect_id,
                dash=(),
                fill=self.theme["frame_bg"],
                outline=self.theme["frame_outline"]
            )

        self.apply_frame_collapse_state(frame_id)
        self.push_history()

    def apply_frame_collapse_state(self, frame_id):
        frame = self.frames.get(frame_id)
        if not frame:
            return
        collapsed = frame.get("collapsed", False)
        state = "hidden" if collapsed else "normal"

        x1, y1, x2, y2 = self.canvas.coords(frame["rect_id"])
        cards_in_frame = [
            cid for cid, card in self.cards.items()
            if x1 <= card["x"] <= x2 and y1 <= card["y"] <= y2
        ]

        for cid in cards_in_frame:
            card = self.cards[cid]
            self.canvas.itemconfig(card["rect_id"], state=state)
            self.canvas.itemconfig(card["text_id"], state=state)
            if card["resize_handle_id"]:
                self.canvas.itemconfig(card["resize_handle_id"], state=state)
            if card["connect_handle_id"]:
                self.canvas.itemconfig(card["connect_handle_id"], state=state)

        for conn in self.connections:
            if conn["from"] in cards_in_frame or conn["to"] in cards_in_frame:
                self.canvas.itemconfig(conn["line_id"], state=state)
                if conn.get("label_id"):
                    self.canvas.itemconfig(conn["label_id"], state=state)

    # ---------- Хэндлы карточек (resize / connect) ----------

    def show_card_handles(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        x = card["x"]
        y = card["y"]
        w = card["width"]
        h = card["height"]
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        # Resize handle (square внизу справа)
        if not card["resize_handle_id"]:
            size = 10
            rx1 = x2 - size
            ry1 = y2 - size
            rx2 = x2
            ry2 = y2
            rid = self.canvas.create_rectangle(
                rx1, ry1, rx2, ry2,
                fill=self.theme["connection"],
                outline="",
                tags=("resize_handle", f"card_{card_id}")
            )
            card["resize_handle_id"] = rid

        # Connect handle (circle справа по центру)
        if not card["connect_handle_id"]:
            r = 6
            cx = x2
            cy = y
            cid = self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=self.theme["connection"],
                outline="",
                tags=("connect_handle", f"card_{card_id}")
            )
            card["connect_handle_id"] = cid

        self.canvas.tag_raise(card["resize_handle_id"])
        self.canvas.tag_raise(card["connect_handle_id"])

    def hide_card_handles(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        if card["resize_handle_id"]:
            self.canvas.delete(card["resize_handle_id"])
            card["resize_handle_id"] = None
        if card["connect_handle_id"]:
            self.canvas.delete(card["connect_handle_id"])
            card["connect_handle_id"] = None

    def update_card_handles_positions(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        x = card["x"]
        y = card["y"]
        w = card["width"]
        h = card["height"]
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        if card["resize_handle_id"]:
            size = 10
            rx1 = x2 - size
            ry1 = y2 - size
            rx2 = x2
            ry2 = y2
            self.canvas.coords(card["resize_handle_id"], rx1, ry1, rx2, ry2)

        if card["connect_handle_id"]:
            r = 6
            cx = x2
            cy = y
            self.canvas.coords(card["connect_handle_id"],
                               cx - r, cy - r, cx + r, cy + r)

    # ---------- Выделение карточек ----------

    def _clear_card_selection(self):
        for cid in list(self.selected_cards):
            if cid in self.cards:
                self._set_card_outline(cid, width=1.5)
                self.hide_card_handles(cid)
        self.selected_cards.clear()
        self.selected_card_id = None

    def select_card(self, card_id, additive=False):
        if self.selected_frame_id is not None:
            self._set_frame_outline(self.selected_frame_id, width=2)
            self.selected_frame_id = None

        if not additive:
            self._clear_card_selection()

        if card_id is not None and card_id in self.cards:
            self.selected_cards.add(card_id)
            self.selected_card_id = card_id
            self._set_card_outline(card_id, width=3)
            self.show_card_handles(card_id)
        else:
            if not additive:
                self.selected_card_id = None

    def _set_card_outline(self, card_id, width):
        card = self.cards.get(card_id)
        if not card:
            return
        self.canvas.itemconfig(card["rect_id"], width=width)

    # ---------- Мышь: выбор/перетаскивание/resize/connect-drag ----------

    def on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
        tags = self.canvas.gettags(item_id) if item_id else ()

        # Сначала — хэндлы
        if "resize_handle" in tags:
            card_id = self.get_card_id_from_item(item)
            if card_id is not None:
                self.select_card(card_id, additive=False)
                card = self.cards[card_id]
                x1 = card["x"] - card["width"] / 2
                y1 = card["y"] - card["height"] / 2
                self.drag_data["dragging"] = True
                self.drag_data["mode"] = "resize_card"
                self.drag_data["resize_card_id"] = card_id
                self.drag_data["resize_origin"] = (x1, y1)
                self.drag_data["moved"] = False
                self.drag_data["dragged_cards"] = {card_id}
            return

        if "connect_handle" in tags:
            card_id = self.get_card_id_from_item(item)
            if card_id is not None:
                self.select_card(card_id, additive=False)
                card = self.cards[card_id]
                sx = card["x"] + card["width"] / 2
                sy = card["y"]
                self.drag_data["dragging"] = True
                self.drag_data["mode"] = "connect_drag"
                self.drag_data["connect_from_card"] = card_id
                self.drag_data["connect_start"] = (sx, sy)
                self.drag_data["temp_line_id"] = self.canvas.create_line(
                    sx, sy, cx, cy,
                    arrow=tk.LAST,
                    width=2,
                    fill=self.theme["connection"],
                    dash=(2, 2),
                    tags=("temp_connection",)
                )
                self.drag_data["moved"] = False
            return

        # Дальше — обычные режимы
        card_id = self.get_card_id_from_item(item)
        frame_id = None
        if card_id is None:
            frame_id = self.get_frame_id_from_item(item)

        if self.connect_mode:
            if card_id is not None:
                if self.connect_from_card_id is None:
                    self.connect_from_card_id = card_id
                    self.select_card(card_id, additive=False)
                else:
                    if card_id != self.connect_from_card_id:
                        self.create_connection(self.connect_from_card_id, card_id)
                        self.push_history()
                    self.connect_mode = False
                    self.connect_from_card_id = None
                    self.select_card(card_id, additive=False)
            return

        # Сброс drag/lasso
        self.drag_data["dragging"] = False
        self.drag_data["dragged_cards"] = set()
        self.drag_data["moved"] = False
        self.drag_data["mode"] = None
        self.drag_data["frame_id"] = None
        self.drag_data["resize_card_id"] = None
        self.drag_data["resize_origin"] = None
        self.drag_data["connect_from_card"] = None
        if self.drag_data["temp_line_id"]:
            self.canvas.delete(self.drag_data["temp_line_id"])
        self.drag_data["temp_line_id"] = None
        self.selection_start = None
        if self.selection_rect_id is not None:
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None

        if card_id is not None:
            if card_id in self.selected_cards:
                self.selected_card_id = card_id
            else:
                self.select_card(card_id, additive=False)

            self.drag_data["dragging"] = True
            self.drag_data["dragged_cards"] = set(self.selected_cards)
            self.drag_data["last_x"] = cx
            self.drag_data["last_y"] = cy
            self.drag_data["mode"] = "cards"

        elif frame_id is not None:
            self.select_frame(frame_id)
            self.drag_data["dragging"] = True
            self.drag_data["mode"] = "frame"
            self.drag_data["frame_id"] = frame_id
            self.drag_data["last_x"] = cx
            self.drag_data["last_y"] = cy
            x1, y1, x2, y2 = self.canvas.coords(self.frames[frame_id]["rect_id"])
            self.drag_data["dragged_cards"] = {
                cid for cid, card in self.cards.items()
                if x1 <= card["x"] <= x2 and y1 <= card["y"] <= y2
            }
        else:
            self.select_card(None)
            self.selection_start = (cx, cy)
            self.selection_rect_id = self.canvas.create_rectangle(
                cx, cy, cx, cy,
                outline="#999999",
                dash=(2, 2),
                fill="",
                tags=("selection_rect",)
            )

    def on_mouse_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        if self.drag_data["dragging"]:
            mode = self.drag_data["mode"]

            if mode == "resize_card":
                card_id = self.drag_data["resize_card_id"]
                card = self.cards.get(card_id)
                if not card:
                    return
                ox1, oy1 = self.drag_data["resize_origin"]
                min_w, min_h = 60, 40
                new_x2 = max(ox1 + min_w, cx)
                new_y2 = max(oy1 + min_h, cy)
                w = new_x2 - ox1
                h = new_y2 - oy1
                card["width"] = w
                card["height"] = h
                card["x"] = ox1 + w / 2
                card["y"] = oy1 + h / 2
                x1 = ox1
                y1 = oy1
                x2 = new_x2
                y2 = new_y2
                self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
                self.canvas.coords(card["text_id"], card["x"], card["y"])
                self.update_card_handles_positions(card_id)
                self.update_connections_for_card(card_id)
                self.drag_data["moved"] = True
                return

            if mode == "connect_drag":
                line_id = self.drag_data["temp_line_id"]
                if line_id:
                    sx, sy = self.drag_data["connect_start"]
                    self.canvas.coords(line_id, sx, sy, cx, cy)
                    self.drag_data["moved"] = True
                return

            dx = cx - self.drag_data["last_x"]
            dy = cy - self.drag_data["last_y"]
            if dx == 0 and dy == 0:
                return
            self.drag_data["last_x"] = cx
            self.drag_data["last_y"] = cy
            self.drag_data["moved"] = True

            if mode == "cards":
                for card_id in self.drag_data["dragged_cards"]:
                    card = self.cards.get(card_id)
                    if not card:
                        continue
                    card["x"] += dx
                    card["y"] += dy
                    x1 = card["x"] - card["width"] / 2
                    y1 = card["y"] - card["height"] / 2
                    x2 = card["x"] + card["width"] / 2
                    y2 = card["y"] + card["height"] / 2
                    self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
                    self.canvas.coords(card["text_id"], card["x"], card["y"])
                    self.update_card_handles_positions(card_id)
                    self.update_connections_for_card(card_id)

            elif mode == "frame":
                frame_id = self.drag_data["frame_id"]
                frame = self.frames.get(frame_id)
                if frame:
                    self.canvas.move(frame["rect_id"], dx, dy)
                    self.canvas.move(frame["title_id"], dx, dy)

                for card_id in self.drag_data["dragged_cards"]:
                    card = self.cards.get(card_id)
                    if not card:
                        continue
                    card["x"] += dx
                    card["y"] += dy
                    x1 = card["x"] - card["width"] / 2
                    y1 = card["y"] - card["height"] / 2
                    x2 = card["x"] + card["width"] / 2
                    y2 = card["y"] + card["height"] / 2
                    self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
                    self.canvas.coords(card["text_id"], card["x"], card["y"])
                    self.update_card_handles_positions(card_id)
                    self.update_connections_for_card(card_id)

        elif self.selection_start is not None and self.selection_rect_id is not None:
            x0, y0 = self.selection_start
            self.canvas.coords(self.selection_rect_id, x0, y0, cx, cy)

    def on_mouse_release(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        mode = self.drag_data["mode"]

        # Завершение connect-drag
        if mode == "connect_drag":
            from_id = self.drag_data["connect_from_card"]
            if self.drag_data["temp_line_id"]:
                self.canvas.delete(self.drag_data["temp_line_id"])
            target_id = None
            items = self.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                cid = self.get_card_id_from_item((it,))
                if cid is not None:
                    target_id = cid
                    break
            if from_id is not None and target_id is not None and target_id != from_id:
                self.create_connection(from_id, target_id)
                self.push_history()

            self.drag_data["dragging"] = False
            self.drag_data["mode"] = None
            self.drag_data["connect_from_card"] = None
            self.drag_data["temp_line_id"] = None
            self.drag_data["moved"] = False
            return

        # Завершение ресайза
        if mode == "resize_card":
            if self.drag_data["moved"]:
                self.snap_cards_to_grid(self.drag_data["dragged_cards"])
                self.push_history()
            self.drag_data["dragging"] = False
            self.drag_data["mode"] = None
            self.drag_data["resize_card_id"] = None
            self.drag_data["resize_origin"] = None
            self.drag_data["dragged_cards"] = set()
            self.drag_data["moved"] = False
            return

        # Завершение перемещения
        if self.drag_data["dragging"] and self.drag_data["moved"]:
            self.snap_cards_to_grid(self.drag_data["dragged_cards"])
            self.push_history()

        self.drag_data["dragging"] = False
        self.drag_data["dragged_cards"] = set()
        self.drag_data["moved"] = False
        self.drag_data["mode"] = None

        # Завершение прямоугольного выделения
        if self.selection_start is not None and self.selection_rect_id is not None:
            x1, y1, x2, y2 = self.canvas.coords(self.selection_rect_id)
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)

            self.select_card(None)
            for card_id, card in self.cards.items():
                if left <= card["x"] <= right and top <= card["y"] <= bottom:
                    self.select_card(card_id, additive=True)

            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
            self.selection_start = None

    # ---------- Панорамирование ----------

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.update_minimap()

    # ---------- Зум ----------

    def on_mousewheel(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.apply_zoom(scale, event)

    def on_mousewheel_linux(self, event):
        scale = 1.1 if event.num == 4 else 0.9
        self.apply_zoom(scale, event)

    def apply_zoom(self, scale, event):
        new_zoom = self.zoom_factor * scale
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        self.canvas.scale("all", cx, cy, scale, scale)
        self.zoom_factor = new_zoom

        for card in self.cards.values():
            x1, y1, x2, y2 = self.canvas.coords(card["rect_id"])
            card["x"] = (x1 + x2) / 2
            card["y"] = (y1 + y2) / 2
            card["width"] = x2 - x1
            card["height"] = y2 - y1
            self.update_card_handles_positions(card["id"])

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.update_minimap()

    # ---------- Связи ----------

    def get_connection_from_item(self, item_id):
        if not item_id:
            return None
        for conn in self.connections:
            if conn["line_id"] == item_id or conn.get("label_id") == item_id:
                return conn
        return None

    def _connection_anchors(self, from_card, to_card):
        x1, y1 = from_card["x"], from_card["y"]
        x2, y2 = to_card["x"], to_card["y"]
        dx = x2 - x1
        dy = y2 - y1

        if abs(dx) > abs(dy):
            sx = x1 + (from_card["width"] / 2) * (1 if dx > 0 else -1)
            sy = y1
        else:
            sx = x1
            sy = y1 + (from_card["height"] / 2) * (1 if dy > 0 else -1)

        if abs(dx) > abs(dy):
            tx = x2 - (to_card["width"] / 2) * (1 if dx > 0 else -1)
            ty = y2
        else:
            tx = x2
            ty = y2 - (to_card["height"] / 2) * (1 if dy > 0 else -1)

        return sx, sy, tx, ty

    def create_connection(self, from_id, to_id, label=""):
        if from_id not in self.cards or to_id not in self.cards:
            return
        card_from = self.cards[from_id]
        card_to = self.cards[to_id]

        sx, sy, tx, ty = self._connection_anchors(card_from, card_to)

        line_id = self.canvas.create_line(
            sx, sy, tx, ty,
            arrow=tk.LAST,
            width=2,
            fill=self.theme["connection"],
            tags=("connection",)
        )
        label_id = None
        if label:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            label_id = self.canvas.create_text(
                mx, my,
                text=label,
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",)
            )
        self.connections.append({
            "from": from_id,
            "to": to_id,
            "line_id": line_id,
            "label": label,
            "label_id": label_id,
        })

    def update_connections_for_card(self, card_id):
        for conn in self.connections:
            if conn["from"] == card_id or conn["to"] == card_id:
                from_card = self.cards.get(conn["from"])
                to_card = self.cards.get(conn["to"])
                if from_card and to_card:
                    sx, sy, tx, ty = self._connection_anchors(from_card, to_card)
                    self.canvas.coords(conn["line_id"], sx, sy, tx, ty)
                    if conn.get("label_id"):
                        mx = (sx + tx) / 2
                        my = (sy + ty) / 2
                        self.canvas.coords(conn["label_id"], mx, my)

    def toggle_connect_mode(self):
        if not self.connect_mode:
            self.connect_mode = True
            self.connect_from_card_id = None
            messagebox.showinfo(
                "Режим соединения",
                "Кликните по первой карточке, затем по второй, чтобы соединить их."
            )
        else:
            self.connect_mode = False
            self.connect_from_card_id = None

    # ---------- Цвет и текст карточки ----------

    def change_color(self):
        if self.selected_card_id is None or self.selected_card_id not in self.cards:
            messagebox.showwarning("Нет выбора", "Сначала выберите карточку.")
            return
        card = self.cards[self.selected_card_id]
        initial = card["color"]
        color = colorchooser.askcolor(initialcolor=initial, parent=self.root)[1]
        if not color:
            return
        card["color"] = color
        self.canvas.itemconfig(card["rect_id"], fill=color)
        self.push_history()

    def edit_card_text_dialog(self):
        if self.selected_card_id is None or self.selected_card_id not in self.cards:
            messagebox.showwarning("Нет выбора", "Сначала выберите карточку.")
            return
        self.edit_card_text(self.selected_card_id)
        self.push_history()

    def edit_card_text(self, card_id):
        card = self.cards[card_id]
        new_text = simpledialog.askstring("Редактировать текст",
                                          "Текст карточки:",
                                          initialvalue=card["text"],
                                          parent=self.root)
        if new_text is None:
            return
        card["text"] = new_text
        self.canvas.itemconfig(card["text_id"], text=new_text)

    # ---------- Inline-редактирование карточек и выравнивание ----------
    
    def start_inline_edit_card(self, card_id: int):
        """
        Запускает inline-редактирование текста карточки через Text,
        встроенный в canvas.
        """
        card = self.cards.get(card_id)
        if not card:
            return
    
        # Если уже есть редактор — сначала завершим его с сохранением
        if self.inline_editor is not None:
            self.finish_inline_edit(commit=True)
    
        self.inline_editor_card_id = card_id
    
        # Берём bbox текста карточки
        try:
            x1, y1, x2, y2 = self.canvas.bbox(card["text_id"])
        except Exception:
            x = card["x"]
            y = card["y"]
            w = card["width"]
            h = card["height"]
            x1 = x - w / 2 + 4
            y1 = y - h / 2 + 4
            x2 = x + w / 2 - 4
            y2 = y + h / 2 - 4
    
        pad_x = 2
        pad_y = 2
        width = max(40, x2 - x1 + pad_x * 2)
        height = max(20, y2 - y1 + pad_y * 2)
    
        self.inline_editor = tk.Text(
            self.canvas,
            font=("Arial", 10),
            wrap="word",
            undo=True,
            borderwidth=1,
            relief="solid",
        )
        self.inline_editor.insert("1.0", card["text"])
        self.inline_editor.focus_set()
    
        self.inline_editor_window_id = self.canvas.create_window(
            x1 - pad_x,
            y1 - pad_y,
            anchor="nw",
            window=self.inline_editor,
            width=width,
            height=height,
        )
    
        self.inline_editor.bind("<Control-Return>", self._inline_edit_commit_event)
        self.inline_editor.bind("<Escape>", self._inline_edit_cancel_event)
        self.inline_editor.bind("<FocusOut>", self._inline_edit_commit_event)
    
    def _inline_edit_commit_event(self, event=None):
        self.finish_inline_edit(commit=True)
        return "break"
    
    def _inline_edit_cancel_event(self, event=None):
        self.finish_inline_edit(commit=False)
        return "break"
    
    def finish_inline_edit(self, commit: bool = True):
        """
        Завершает inline-редактирование.
        commit=True — сохранить изменения,
        commit=False — отменить.
        """
        if self.inline_editor is None:
            return
    
        editor = self.inline_editor
        window_id = self.inline_editor_window_id
        card_id = self.inline_editor_card_id
    
        self.inline_editor = None
        self.inline_editor_window_id = None
        self.inline_editor_card_id = None
    
        if window_id is not None:
            self.canvas.delete(window_id)
    
        try:
            editor_text = editor.get("1.0", "end-1c")
        except Exception:
            editor_text = None
    
        editor.destroy()
    
        if not commit or card_id is None or editor_text is None:
            return
    
        card = self.cards.get(card_id)
        if not card:
            return
    
        new_text = editor_text.strip()
        card["text"] = new_text
        self.canvas.itemconfig(card["text_id"], text=new_text)
        self.canvas.itemconfig(card["text_id"], width=card["width"] - 10)
    
        self.push_history()
    
    def _require_multiple_selected_cards(self):
        cards = [cid for cid in self.selected_cards if cid in self.cards]
        if len(cards) < 2:
            messagebox.showwarning(
                "Недостаточно карточек",
                "Для этой операции нужно выбрать минимум две карточки.",
            )
            return None
        return cards
    
    def align_selected_cards_left(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        left_min = min(
            self.cards[cid]["x"] - self.cards[cid]["width"] / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_x = left_min + card["width"] / 2
            card["x"] = new_x
            x1 = card["x"] - card["width"] / 2
            y1 = card["y"] - card["height"] / 2
            x2 = card["x"] + card["width"] / 2
            y2 = card["y"] + card["height"] / 2
            self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(card["text_id"], card["x"], card["y"])
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
    
        self.push_history()
    
    def align_selected_cards_top(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        top_min = min(
            self.cards[cid]["y"] - self.cards[cid]["height"] / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_y = top_min + card["height"] / 2
            card["y"] = new_y
            x1 = card["x"] - card["width"] / 2
            y1 = card["y"] - card["height"] / 2
            x2 = card["x"] + card["width"] / 2
            y2 = card["y"] + card["height"] / 2
            self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(card["text_id"], card["x"], card["y"])
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
    
        self.push_history()
    
    def equalize_selected_cards_width(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_w = ref["width"]
    
        for cid in cards:
            card = self.cards[cid]
            card["width"] = ref_w
            x1 = card["x"] - ref_w / 2
            y1 = card["y"] - card["height"] / 2
            x2 = card["x"] + ref_w / 2
            y2 = card["y"] + card["height"] / 2
            self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
            self.canvas.itemconfig(card["text_id"], width=ref_w - 10)
            self.canvas.coords(card["text_id"], card["x"], card["y"])
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
    
        self.push_history()
    
    def equalize_selected_cards_height(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_h = ref["height"]
    
        for cid in cards:
            card = self.cards[cid]
            card["height"] = ref_h
            x1 = card["x"] - card["width"] / 2
            y1 = card["y"] - ref_h / 2
            x2 = card["x"] + card["width"] / 2
            y2 = card["y"] + ref_h / 2
            self.canvas.coords(card["rect_id"], x1, y1, x2, y2)
            self.canvas.coords(card["text_id"], card["x"], card["y"])
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
    
        self.push_history()
    
    # ---------- Настройки сетки (UI-обработчики) ----------
    
    def on_toggle_snap_to_grid(self):
        """
        Включаем / выключаем привязку к сетке.
        """
        self.snap_to_grid = bool(self.var_snap_to_grid.get())
    
    def on_grid_size_change(self, event=None):
        """
        Меняет шаг сетки и перерисовывает её.
        """
        try:
            value = int(self.var_grid_size.get())
        except Exception:
            value = self.grid_size
    
        if value < 5:
            value = 5
        if value > 200:
            value = 200
    
        self.grid_size = value
        self.var_grid_size.set(value)
    
        self.draw_grid()

    # ---------- Удаление карточек ----------

    def delete_selected_cards(self):
        if not self.selected_cards:
            return
        to_delete = list(self.selected_cards)

        new_connections = []
        for conn in self.connections:
            if conn["from"] in to_delete or conn["to"] in to_delete:
                self.canvas.delete(conn["line_id"])
                if conn.get("label_id"):
                    self.canvas.delete(conn["label_id"])
            else:
                new_connections.append(conn)
        self.connections = new_connections

        for card_id in to_delete:
            card = self.cards.get(card_id)
            if not card:
                continue
            if card["resize_handle_id"]:
                self.canvas.delete(card["resize_handle_id"])
            if card["connect_handle_id"]:
                self.canvas.delete(card["connect_handle_id"])
            self.canvas.delete(card["rect_id"])
            self.canvas.delete(card["text_id"])
            del self.cards[card_id]

        self.selected_cards.clear()
        self.selected_card_id = None
        self.push_history()

    # ---------- Копирование / вставка / дубликат ----------

    def on_copy(self, event=None):
        if not self.selected_cards:
            return
        ids = set(self.selected_cards)
        cards_data = []
        connections_data = []
        sx = sy = 0
        for cid in ids:
            c = self.cards[cid]
            cards_data.append({
                "id": cid,
                "x": c["x"],
                "y": c["y"],
                "width": c["width"],
                "height": c["height"],
                "text": c["text"],
                "color": c["color"],
            })
            sx += c["x"]
            sy += c["y"]
        center = (sx / len(ids), sy / len(ids))
        for conn in self.connections:
            if conn["from"] in ids and conn["to"] in ids:
                connections_data.append({
                    "from": conn["from"],
                    "to": conn["to"],
                    "label": conn.get("label", ""),
                })
        self.clipboard = {
            "cards": cards_data,
            "connections": connections_data,
            "center": center,
        }

    def on_paste(self, event=None):
        if not self.clipboard:
            return
        data = self.clipboard
        cards_data = data["cards"]
        connections_data = data["connections"]
        src_cx, src_cy = data["center"]

        dst_cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        dst_cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        dx = dst_cx - src_cx + 30
        dy = dst_cy - src_cy + 30

        id_map = {}
        for c in cards_data:
            new_x = c["x"] + dx
            new_y = c["y"] + dy
            new_id = self.create_card(
                new_x, new_y,
                c["text"],
                color=c["color"],
                card_id=None,
                width=c["width"],
                height=c["height"],
            )
            id_map[c["id"]] = new_id

        for conn in connections_data:
            from_new = id_map.get(conn["from"])
            to_new = id_map.get(conn["to"])
            if from_new and to_new:
                self.create_connection(from_new, to_new, label=conn.get("label", ""))

        self.select_card(None)
        for nid in id_map.values():
            self.select_card(nid, additive=True)

        self.push_history()

    def on_duplicate(self, event=None):
        self.on_copy()
        self.on_paste()

    # ---------- Сохранение/загрузка ----------

    def save_board(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if not filename:
            return

        data = self.get_board_data()
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.last_saved_history_index = self.history_index
            self.update_unsaved_flag()
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def load_board(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))
            return

        self.set_board_from_data(data)
        state = self.get_board_data()
        self.history = [copy.deepcopy(state)]
        self.history_index = 0
        self.last_saved_history_index = 0
        self.update_unsaved_flag()
        self.write_autosave()
        self.update_minimap()

    # ---------- Экспорт в PNG (как было раньше) ----------

    def export_png(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            messagebox.showerror(
                "Экспорт в PNG",
                "Для экспорта нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow"
            )
            return

        if not self.cards and not self.frames and not self.connections:
            messagebox.showinfo("Экспорт в PNG", "Нечего экспортировать: борд пуст.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG изображения", "*.png"), ("Все файлы", "*.*")]
        )
        if not filename:
            return

        items_bbox = None

        def update_bbox(bbox, x1, y1, x2, y2):
            if bbox is None:
                return (x1, y1, x2, y2)
            bx1, by1, bx2, by2 = bbox
            return (min(bx1, x1), min(by1, y1), max(bx2, x2), max(by2, y2))

        for frame in self.frames.values():
            coords = self.canvas.coords(frame["rect_id"])
            if coords:
                fx1, fy1, fx2, fy2 = coords
                items_bbox = update_bbox(items_bbox, fx1, fy1, fx2, fy2)
        for card in self.cards.values():
            cx1 = card["x"] - card["width"] / 2
            cy1 = card["y"] - card["height"] / 2
            cx2 = card["x"] + card["width"] / 2
            cy2 = card["y"] + card["height"] / 2
            items_bbox = update_bbox(items_bbox, cx1, cy1, cx2, cy2)
        for conn in self.connections:
            coords = self.canvas.coords(conn["line_id"])
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                items_bbox = update_bbox(items_bbox, x1, y1, x2, y2)

        if items_bbox is None:
            messagebox.showinfo("Экспорт в PNG", "Не найдено объектов для экспорта.")
            return

        x1, y1, x2, y2 = items_bbox
        padding = 20
        width = int(x2 - x1 + 2 * padding)
        height = int(y2 - y1 + 2 * padding)
        if width <= 0 or height <= 0:
            messagebox.showerror("Экспорт в PNG", "Некорректный размер изображения.")
            return

        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), self.theme["bg"])
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        def map_xy(x, y):
            return (x - x1 + padding, y - y1 + padding)

        for frame in self.frames.values():
            coords = self.canvas.coords(frame["rect_id"])
            if not coords:
                continue
            fx1, fy1, fx2, fy2 = coords
            mx1, my1 = map_xy(fx1, fy1)
            mx2, my2 = map_xy(fx2, fy2)
            collapsed = frame.get("collapsed", False)
            fill = self.theme["frame_collapsed_bg"] if collapsed else self.theme["frame_bg"]
            outline = self.theme["frame_outline"]
            draw.rectangle([mx1, my1, mx2, my2], outline=outline, fill=fill)
            title = frame.get("title", "")
            if title:
                draw.text((mx1 + 8, my1 + 8), title, font=font, fill=self.theme["text"])

        for conn in self.connections:
            from_card = self.cards.get(conn["from"])
            to_card = self.cards.get(conn["to"])
            if not from_card or not to_card:
                continue
            sx, sy, tx, ty = self._connection_anchors(from_card, to_card)
            msx, msy = map_xy(sx, sy)
            mtx, mty = map_xy(tx, ty)
            draw.line([msx, msy, mtx, mty], fill=self.theme["connection"], width=2)
            if conn.get("label"):
                mx = (msx + mtx) / 2
                my = (msy + mty) / 2
                try:
                    draw.text((mx, my), conn["label"], font=font,
                              fill=self.theme["connection_label"], anchor="mm")
                except TypeError:
                    draw.text((mx, my), conn["label"], font=font,
                              fill=self.theme["connection_label"])

        for card in self.cards.values():
            cx1 = card["x"] - card["width"] / 2
            cy1 = card["y"] - card["height"] / 2
            cx2 = card["x"] + card["width"] / 2
            cy2 = card["y"] + card["height"] / 2
            mx1, my1 = map_xy(cx1, cy1)
            mx2, my2 = map_xy(cx2, cy2)
            fill = card.get("color") or self.theme["card_default"]
            outline = self.theme["card_outline"]
            draw.rectangle([mx1, my1, mx2, my2], fill=fill, outline=outline)
            text = card.get("text", "")
            if text:
                tx, ty = map_xy(card["x"], card["y"])
                try:
                    draw.multiline_text((tx, ty), text, font=font,
                                        fill=self.theme["text"], align="center", anchor="mm")
                except TypeError:
                    draw.multiline_text((mx1 + 5, my1 + 5), text, font=font,
                                        fill=self.theme["text"])

        try:
            img.save(filename, "PNG")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
            return

        messagebox.showinfo("Экспорт в PNG", "Изображение сохранено:\n" + filename)

    # ---------- Мини-карта ----------

    def update_minimap(self):
        if not self.minimap:
            return
        self.minimap.delete("all")
        self.minimap.config(bg=self.theme["minimap_bg"])
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        if x2 == x1 or y2 == y1:
            return

        width = int(self.minimap.cget("width"))
        height = int(self.minimap.cget("height"))
        scale_x = width / (x2 - x1)
        scale_y = height / (y2 - y1)
        scale = min(scale_x, scale_y)

        def map_point(px, py):
            mx = (px - x1) * scale
            my = (py - y1) * scale
            return mx, my

        for card in self.cards.values():
            cx, cy = card["x"], card["y"]
            w, h = card["width"], card["height"]
            mx1, my1 = map_point(cx - w / 2, cy - h / 2)
            mx2, my2 = map_point(cx + w / 2, cy + h / 2)
            self.minimap.create_rectangle(mx1, my1, mx2, my2,
                                          outline=self.theme["minimap_card_outline"], fill="")

        for frame in self.frames.values():
            fx1, fy1, fx2, fy2 = self.canvas.coords(frame["rect_id"])
            mx1, my1 = map_point(fx1, fy1)
            mx2, my2 = map_point(fx2, fy2)
            self.minimap.create_rectangle(mx1, my1, mx2, my2,
                                          outline=self.theme["minimap_frame_outline"], dash=(2, 2))

        vx0, vx1 = self.canvas.xview()
        vy0, vy1 = self.canvas.yview()
        view_x1 = x1 + vx0 * (x2 - x1)
        view_x2 = x1 + vx1 * (x2 - x1)
        view_y1 = y1 + vy0 * (y2 - y1)
        view_y2 = y1 + vy1 * (y2 - y1)
        mvx1, mvy1 = map_point(view_x1, view_y1)
        mvx2, mvy2 = map_point(view_x2, view_y2)
        self.minimap.create_rectangle(mvx1, mvy1, mvx2, mvy2,
                                      outline=self.theme["minimap_viewport"])

    def on_minimap_click(self, event):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        if x2 == x1 or y2 == y1:
            return

        width = int(self.minimap.cget("width"))
        height = int(self.minimap.cget("height"))
        scale_x = width / (x2 - x1)
        scale_y = height / (y2 - y1)
        scale = min(scale_x, scale_y)

        board_x = x1 + event.x / scale
        board_y = y1 + event.y / scale

        vx0, vx1 = self.canvas.xview()
        vy0, vy1 = self.canvas.yview()
        view_frac_w = vx1 - vx0
        view_frac_h = vy1 - vy0

        view_width = (x2 - x1) * view_frac_w
        view_height = (y2 - y1) * view_frac_h

        new_view_x1 = board_x - view_width / 2
        new_view_y1 = board_y - view_height / 2

        new_xview = (new_view_x1 - x1) / (x2 - x1)
        new_yview = (new_view_y1 - y1) / (y2 - y1)

        new_xview = max(0.0, min(new_xview, 1.0 - view_frac_w))
        new_yview = max(0.0, min(new_yview, 1.0 - view_frac_h))

        self.canvas.xview_moveto(new_xview)
        self.canvas.yview_moveto(new_yview)
        self.update_minimap()

    # ---------- Переключение темы ----------

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme = self.themes[self.theme_name]
        self.save_config()
        state = self.get_board_data()
        self.set_board_from_data(state)
        self.canvas.config(bg=self.theme["bg"])
        if self.minimap:
            self.minimap.config(bg=self.theme["minimap_bg"])
        self.btn_theme.config(text=self.get_theme_button_text())
        self.update_minimap()

    # ---------- Закрытие ----------

    def on_close(self):
        if self.unsaved_changes:
            res = messagebox.askyesnocancel(
                "Выход",
                "Есть несохранённые изменения.\n"
                "Сохранить перед выходом?"
            )
            if res is None:
                return
            if res:
                self.save_board()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BoardApp()
    app.run()
