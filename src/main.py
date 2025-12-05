import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
import copy
from pathlib import Path
from typing import Dict, List
from .autosave import AutoSaveService
from .controllers import ConnectController, DragController, SelectionController
from .board_model import Card as ModelCard, Connection as ModelConnection, Frame as ModelFrame, BoardData, Attachment
from .config import THEMES, load_theme_name, save_theme_name
from .history import History
from .io import files as file_io
from .ui import LayoutBuilder
from .view.canvas_view import CanvasView

class BoardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mini Miro Board (Python)")
        self.root.geometry("1200x800")

        # Темы
        self.theme_name = load_theme_name(THEMES)
        self.theme = THEMES[self.theme_name]

        # Данные борда
        self.cards: Dict[int, ModelCard] = {}
        self.connections: List[ModelConnection] = []
        self.next_card_id = 1

        # Группы / рамки
        self.frames: Dict[int, ModelFrame] = {}
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

        # Контроллеры поведения
        self.selection_controller = SelectionController(self)
        self.connect_controller = ConnectController(self)
        self.drag_controller = DragController(self)

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
        self.history = History()
        self.saved_history_index = -1
        self.unsaved_changes = False
        self.autosave_service = AutoSaveService()

        # Буфер обмена (копирование карточек)
        self.clipboard = None  # {"cards":[...], "connections":[...], "center":(x,y)}

        # Вложения
        self.attachments_dir = Path("attachments")
        self.attachment_items: Dict[tuple[int, int], int] = {}
        self.attachment_tk_images: Dict[tuple[int, int], tk.PhotoImage] = {}

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

        # UI helpers
        self.ui_builder = LayoutBuilder()

        self._build_ui()
        self.canvas_view = CanvasView(self.canvas, self.minimap, self.theme)
        self.init_board_state()
        self.update_controls_state()

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_theme_button_text(self):
        return "Тёмная тема" if self.theme_name == "light" else "Светлая тема"

    def _build_ui(self):
        self.ui_builder.build(self)
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
        new_x = card.x + offset
        new_y = card.y + offset
    
        new_card_id = self.create_card(new_x, new_y, card.text, color=card.color)
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
            initialvalue=frame.title,
            parent=self.root,
        )
        if new_title is None:
            return
        frame.title = new_title
        self.canvas.itemconfig(frame.title_id, text=new_title)
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
        self.canvas.delete(frame.rect_id)
        self.canvas.delete(frame.title_id)
        if self.selected_frame_id == frame_id:
            self.selected_frame_id = None
        self.push_history()
    
    def _context_edit_connection_label(self):
        conn = self.context_connection
        if not conn:
            return
        current_label = conn.label
        new_label = simpledialog.askstring(
            "Подпись связи",
            "Текст связи:",
            initialvalue=current_label,
            parent=self.root,
        )
        if new_label is None:
            return
        conn.label = new_label.strip()
        if conn.label_id:
            if conn.label:
                self.canvas.itemconfig(
                    conn.label_id,
                    text=conn.label,
                    state="normal",
                    fill=self.theme["connection_label"],
                )
            else:
                self.canvas.delete(conn.label_id)
                conn.label_id = None
        elif conn.label:
            coords = self.canvas.coords(conn.line_id)
            if len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
            else:
                mx, my = self.context_click_x, self.context_click_y
            label_id = self.canvas.create_text(
                mx,
                my,
                text=conn.label,
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",),
            )
            conn.label_id = label_id
    
        self.push_history()
    
    def _context_delete_connection(self):
        conn = self.context_connection
        if not conn:
            return
        self.canvas.delete(conn.line_id)
        if conn.label_id:
            self.canvas.delete(conn.label_id)
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
        if self.autosave_service.exists():
            res = messagebox.askyesnocancel(
                "Автовосстановление",
                "Найден файл автосохранения.\n"
                "Восстановить последний сеанс?",
            )
            if res:  # Да
                try:
                    data = self.autosave_service.load()
                    self.set_board_from_data(data)
                    self.history.clear_and_init(self.get_board_data())
                    self.saved_history_index = -1
                    self.push_history()
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
            self.set_connect_mode(False)
            self.zoom_factor = 1.0
            self.canvas.config(scrollregion=(0, 0, 4000, 4000),
                               bg=self.theme["bg"])
            self.next_card_id = 1
            self.next_frame_id = 1

            self.history.clear_and_init(self.get_board_data())
            self.draw_grid()
            self.push_history()
            self.saved_history_index = self.history.index

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
                x=card.x,
                y=card.y,
                width=card.width,
                height=card.height,
                text=card.text,
                color=card.color,
            )

        connections: List[ModelConnection] = []
        for conn in self.connections:
            connections.append(
                ModelConnection(
                    from_id=conn.from_id,
                    to_id=conn.to_id,
                    label=conn.label,
                )
            )

        frames: Dict[int, ModelFrame] = {}
        for frame_id, frame in self.frames.items():
            x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
            frames[frame_id] = ModelFrame(
                id=frame_id,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                title=frame.title,
                collapsed=frame.collapsed,
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
        self._clear_all_attachment_previews()
        self.selected_card_id = None
        self.selected_cards.clear()
        self.selected_frame_id = None
        self.set_connect_mode(False)
        self.zoom_factor = 1.0
        self.canvas.config(scrollregion=(0, 0, 4000, 4000), bg=self.theme["bg"])

        # --- новая часть: используем модель BoardData ---
        board = BoardData.from_primitive(data)
        self.cards = board.cards
        self.connections = board.connections
        self.frames = board.frames

        self.next_card_id = max(self.cards.keys(), default=0) + 1
        self.next_frame_id = max(self.frames.keys(), default=0) + 1

        self.render_board()
        self.update_controls_state()


    def push_history(self):
        state = self.get_board_data()
        self.history.push(state)
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def on_undo(self, event=None):
        state = self.history.undo(self)
        if state is None:
            return
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def on_redo(self, event=None):
        state = self.history.redo(self)
        if state is None:
            return
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def update_unsaved_flag(self):
        self.unsaved_changes = (self.history.index != self.saved_history_index)
        title = "Mini Miro Board (Python)"
        if self.unsaved_changes:
            title += " *"
        self.root.title(title)

    def write_autosave(self, state=None):
        try:
            data = state if state is not None else self.get_board_data()
            self.autosave_service.save(data)
        except Exception:
            pass

    # ---------- Сетка ----------

    def draw_grid(self):
        self.canvas_view.draw_grid(self.grid_size)

    def render_board(self):
        self.canvas_view.render_board(self.cards, self.frames, self.connections, self.grid_size)
        self._clear_all_attachment_previews()
        self.render_all_attachments()

    def render_selection(self):
        self.canvas_view.render_selection(
            self.cards, self.frames, self.selected_cards, self.selected_frame_id
        )

    def update_controls_state(self):
        has_card_selection = bool(self.selected_cards)
        has_frame_selection = self.selected_frame_id is not None

        if hasattr(self, "btn_change_color"):
            self.btn_change_color.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_edit_text"):
            self.btn_edit_text.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_delete_cards"):
            self.btn_delete_cards.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_toggle_frame"):
            self.btn_toggle_frame.config(state="normal" if has_frame_selection else "disabled")

        if hasattr(self, "btn_undo_toolbar"):
            self.btn_undo_toolbar.config(
                state="normal" if self.history and self.history.can_undo() else "disabled"
            )
        if hasattr(self, "btn_redo_toolbar"):
            self.btn_redo_toolbar.config(
                state="normal" if self.history and self.history.can_redo() else "disabled"
            )

    def update_connect_mode_indicator(self):
        self.connect_controller.update_connect_mode_indicator()

    def set_connect_mode(self, enabled: bool):
        self.connect_controller.set_connect_mode(enabled)

    # ---------- Вложения ----------

    def _ensure_attachments_dir(self) -> None:
        try:
            self.attachments_dir.mkdir(exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Вложения", f"Не удалось создать папку вложений:\n{exc}")
            raise

    def _clear_all_attachment_previews(self) -> None:
        for item_id in self.attachment_items.values():
            self.canvas.delete(item_id)
        self.attachment_items.clear()
        self.attachment_tk_images.clear()

    def _clear_attachment_previews_for_card(self, card_id: int) -> None:
        to_delete = [key for key in self.attachment_items if key[0] == card_id]
        for key in to_delete:
            item_id = self.attachment_items.pop(key, None)
            if item_id:
                self.canvas.delete(item_id)
            self.attachment_tk_images.pop(key, None)

    def _load_attachment_image(self, attachment: Attachment):
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                "Вложения",
                "Для работы с изображениями нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return None

        if not attachment.storage_path:
            return None
        path = Path(attachment.storage_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            return None
        try:
            return Image.open(path)
        except OSError:
            return None

    def _prepare_preview_image(self, image):
        max_size = (200, 200)
        copy_image = image.copy()
        copy_image.thumbnail(max_size)
        return copy_image.convert("RGBA")

    def render_card_attachments(self, card_id: int) -> None:
        card = self.cards.get(card_id)
        if not card or not card.attachments:
            self._clear_attachment_previews_for_card(card_id)
            return

        try:
            from PIL import ImageTk
        except ImportError:
            messagebox.showerror(
                "Вложения",
                "Для показа изображений нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return

        self._clear_attachment_previews_for_card(card_id)

        for idx, attachment in enumerate(card.attachments):
            image = self._load_attachment_image(attachment)
            if image is None:
                continue
            preview = self._prepare_preview_image(image)
            photo = ImageTk.PhotoImage(preview)
            offset_y = attachment.offset_y
            if offset_y == 0:
                offset_y = card.height / 2 + preview.height / 2 + 10 + idx * (preview.height + 10)
                attachment.offset_y = offset_y
            offset_x = attachment.offset_x
            canvas_x = card.x + offset_x
            canvas_y = card.y + offset_y
            item_id = self.canvas.create_image(
                canvas_x,
                canvas_y,
                image=photo,
                anchor="center",
                tags=("attachment_preview", f"attachment_{card_id}_{attachment.id}"),
            )
            self.attachment_items[(card_id, attachment.id)] = item_id
            self.attachment_tk_images[(card_id, attachment.id)] = photo

    def render_all_attachments(self) -> None:
        for card_id in list(self.cards.keys()):
            self.render_card_attachments(card_id)

    def update_attachment_positions(self, card_id: int, *, scale: float | None = None) -> None:
        card = self.cards.get(card_id)
        if not card or not card.attachments:
            return
        for attachment in card.attachments:
            key = (card_id, attachment.id)
            item_id = self.attachment_items.get(key)
            if item_id:
                if scale is not None:
                    attachment.offset_x *= scale
                    attachment.offset_y *= scale
                self.canvas.coords(
                    item_id,
                    card.x + attachment.offset_x,
                    card.y + attachment.offset_y,
                )

    def _read_clipboard_image(self):
        try:
            from PIL import ImageGrab, Image
        except ImportError:
            messagebox.showerror(
                "Вставка изображения",
                "Для вставки изображения нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return None

        try:
            grabbed = ImageGrab.grabclipboard()
        except Exception:
            return None

        if grabbed is None:
            return None

        if isinstance(grabbed, Image.Image):
            mime = Image.MIME.get(grabbed.format, "image/png")
            return grabbed, grabbed.format or "PNG", mime, "clipboard.png"

        if isinstance(grabbed, (list, tuple)) and grabbed:
            first = grabbed[0]
            path = Path(first)
            if path.is_file():
                try:
                    image = Image.open(path)
                except OSError:
                    return None
                mime = Image.MIME.get(image.format, "image/png")
                return image, image.format or "PNG", mime, path.name
        return None

    def _attach_clipboard_image_to_card(self) -> bool:
        result = self._read_clipboard_image()
        if result is None:
            return False

        if not self.selected_cards:
            messagebox.showwarning(
                "Вставка изображения",
                "Выберите карточку, чтобы добавить вложение.",
            )
            return True

        card_id = self.selected_card_id or next(iter(self.selected_cards))
        card = self.cards.get(card_id)
        if card is None:
            return True

        image, _fmt, mime_type, name = result
        try:
            self._ensure_attachments_dir()
        except OSError:
            return True

        attachment_id = max((a.id for a in card.attachments), default=0) + 1
        storage_path = self.attachments_dir / f"{card.id}-{attachment_id}.png"

        try:
            rgb_image = image.convert("RGBA")
            rgb_image.save(storage_path, format="PNG")
        except OSError as exc:
            messagebox.showerror("Вставка изображения", f"Не удалось сохранить изображение:\n{exc}")
            return True

        attachment = Attachment(
            id=attachment_id,
            name=name,
            source_type="clipboard",
            mime_type=mime_type,
            width=image.width,
            height=image.height,
            offset_x=0.0,
            offset_y=0.0,
            storage_path=str(storage_path.relative_to(Path.cwd())),
        )
        card.attachments.append(attachment)
        self.render_card_attachments(card_id)
        self.push_history()
        return True

    def snap_cards_to_grid(self, card_ids):
        if not self.snap_to_grid or not card_ids:
            return
        for card_id in card_ids:
            card = self.cards.get(card_id)
            if not card:
                continue
            gx = round(card.x / self.grid_size) * self.grid_size
            gy = round(card.y / self.grid_size) * self.grid_size
            dx = gx - card.x
            dy = gy - card.y
            if dx == 0 and dy == 0:
                continue
            card.x = gx
            card.y = gy
            x1 = gx - card.width / 2
            y1 = gy - card.height / 2
            x2 = gx + card.width / 2
            y2 = gy + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.canvas.coords(card.text_id, gx, gy)
            self.update_card_handles_positions(card_id)
            self.update_connections_for_card(card_id)
            self.update_attachment_positions(card_id)

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
            current_label = conn.label
            new_label = simpledialog.askstring(
                "Подпись связи",
                "Текст связи:",
                initialvalue=current_label,
                parent=self.root,
            )
            if new_label is None:
                return
            conn.label = new_label.strip()
            if conn.label_id:
                if conn.label:
                    self.canvas.itemconfig(
                        conn.label_id,
                        text=conn.label,
                        state="normal",
                        fill=self.theme["connection_label"],
                    )
                else:
                    self.canvas.delete(conn.label_id)
                    conn.label_id = None
            elif conn.label:
                coords = self.canvas.coords(conn.line_id)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    mx = (x1 + x2) / 2
                    my = (y1 + y2) / 2
                else:
                    mx, my = cx, cy
                label_id = self.canvas.create_text(
                    mx,
                    my,
                    text=conn.label,
                    font=("Arial", 9, "italic"),
                    fill=self.theme["connection_label"],
                    tags=("connection_label",),
                )
                conn.label_id = label_id
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

        card = ModelCard(
            id=card_id,
            x=x,
            y=y,
            width=width,
            height=height,
            text=text,
            color=color,
        )
        self.canvas_view.draw_card(card)
        self.cards[card_id] = card
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

        frame = ModelFrame(
            id=frame_id,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            title=title,
            collapsed=collapsed,
        )
        self.canvas_view.draw_frame(frame)
        self.frames[frame_id] = frame

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
        self.selection_controller.select_frame(frame_id)

    def toggle_selected_frame_collapse(self):
        frame_id = self.selected_frame_id
        if frame_id is None or frame_id not in self.frames:
            messagebox.showwarning("Нет выбора", "Сначала выберите рамку.")
            return
        frame = self.frames[frame_id]
        frame.collapsed = not frame.collapsed

        rect_id = frame.rect_id
        if frame.collapsed:
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
        collapsed = frame.collapsed
        state = "hidden" if collapsed else "normal"

        x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
        cards_in_frame = [
            cid for cid, card in self.cards.items()
            if x1 <= card.x <= x2 and y1 <= card.y <= y2
        ]

        for cid in cards_in_frame:
            card = self.cards[cid]
            self.canvas.itemconfig(card.rect_id, state=state)
            self.canvas.itemconfig(card.text_id, state=state)
            if card.resize_handle_id:
                self.canvas.itemconfig(card.resize_handle_id, state=state)
            if card.connect_handle_id:
                self.canvas.itemconfig(card.connect_handle_id, state=state)

        for conn in self.connections:
            if conn.from_id in cards_in_frame or conn.to_id in cards_in_frame:
                self.canvas.itemconfig(conn.line_id, state=state)
                if conn.label_id:
                    self.canvas.itemconfig(conn.label_id, state=state)

    # ---------- Хэндлы карточек (resize / connect) ----------

    def show_card_handles(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        x = card.x
        y = card.y
        w = card.width
        h = card.height
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        # Resize handle (square внизу справа)
        if not card.resize_handle_id:
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
            card.resize_handle_id = rid

        # Connect handle (circle справа по центру)
        if not card.connect_handle_id:
            r = 6
            cx = x2
            cy = y
            cid = self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=self.theme["connection"],
                outline="",
                tags=("connect_handle", f"card_{card_id}")
            )
            card.connect_handle_id = cid

        self.canvas.tag_raise(card.resize_handle_id)
        self.canvas.tag_raise(card.connect_handle_id)

    def hide_card_handles(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        if card.resize_handle_id:
            self.canvas.delete(card.resize_handle_id)
            card.resize_handle_id = None
        if card.connect_handle_id:
            self.canvas.delete(card.connect_handle_id)
            card.connect_handle_id = None

    def update_card_handles_positions(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        x = card.x
        y = card.y
        w = card.width
        h = card.height
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        if card.resize_handle_id:
            size = 10
            rx1 = x2 - size
            ry1 = y2 - size
            rx2 = x2
            ry2 = y2
            self.canvas.coords(card.resize_handle_id, rx1, ry1, rx2, ry2)

        if card.connect_handle_id:
            r = 6
            cx = x2
            cy = y
            self.canvas.coords(card.connect_handle_id,
                               cx - r, cy - r, cx + r, cy + r)

    # ---------- Выделение карточек ----------

    def _clear_card_selection(self):
        self.selection_controller.clear_card_selection()

    def select_card(self, card_id, additive=False):
        self.selection_controller.select_card(card_id, additive)

    # ---------- Мышь: выбор/перетаскивание/resize/connect-drag ----------

    def on_canvas_click(self, event):
        return self.drag_controller.on_canvas_click(event)

    def on_mouse_drag(self, event):
        return self.drag_controller.on_mouse_drag(event)

    def on_mouse_release(self, event):
        return self.drag_controller.on_mouse_release(event)

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
            x1, y1, x2, y2 = self.canvas.coords(card.rect_id)
            card.x = (x1 + x2) / 2
            card.y = (y1 + y2) / 2
            card.width = x2 - x1
            card.height = y2 - y1
            self.update_card_handles_positions(card.id)
            self.update_attachment_positions(card.id, scale=scale)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.update_minimap()

    # ---------- Связи ----------

    def get_connection_from_item(self, item_id):
        if not item_id:
            return None
        for conn in self.connections:
            if conn.line_id == item_id or conn.label_id == item_id:
                return conn
        return None

    def _connection_anchors(self, from_card, to_card):
        x1, y1 = from_card.x, from_card.y
        x2, y2 = to_card.x, to_card.y
        dx = x2 - x1
        dy = y2 - y1

        if abs(dx) > abs(dy):
            sx = x1 + (from_card.width / 2) * (1 if dx > 0 else -1)
            sy = y1
        else:
            sx = x1
            sy = y1 + (from_card.height / 2) * (1 if dy > 0 else -1)

        if abs(dx) > abs(dy):
            tx = x2 - (to_card.width / 2) * (1 if dx > 0 else -1)
            ty = y2
        else:
            tx = x2
            ty = y2 - (to_card.height / 2) * (1 if dy > 0 else -1)

        return sx, sy, tx, ty

    def create_connection(self, from_id, to_id, label=""):
        if from_id not in self.cards or to_id not in self.cards:
            return
        card_from = self.cards[from_id]
        card_to = self.cards[to_id]

        connection = ModelConnection(
            from_id=from_id,
            to_id=to_id,
            label=label,
        )
        self.canvas_view.draw_connection(connection, card_from, card_to)
        self.connections.append(connection)

    def update_connections_for_card(self, card_id):
        self.canvas_view.update_connection_positions(self.connections, self.cards, card_id)

    def toggle_connect_mode(self):
        self.connect_controller.toggle_connect_mode()

    # ---------- Цвет и текст карточки ----------

    def change_color(self):
        if self.selected_card_id is None or self.selected_card_id not in self.cards:
            messagebox.showwarning("Нет выбора", "Сначала выберите карточку.")
            return
        card = self.cards[self.selected_card_id]
        initial = card.color
        color = colorchooser.askcolor(initialcolor=initial, parent=self.root)[1]
        if not color:
            return
        card.color = color
        self.canvas.itemconfig(card.rect_id, fill=color)
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
                                          initialvalue=card.text,
                                          parent=self.root)
        if new_text is None:
            return
        card.text = new_text
        self.canvas.itemconfig(card.text_id, text=new_text)

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
            x1, y1, x2, y2 = self.canvas.bbox(card.text_id)
        except Exception:
            x = card.x
            y = card.y
            w = card.width
            h = card.height
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
        self.inline_editor.insert("1.0", card.text)
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
        card.text = new_text
        self.canvas.itemconfig(card.text_id, text=new_text)
        self.canvas.itemconfig(card.text_id, width=card.width - 10)
    
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
            self.cards[cid].x - self.cards[cid].width / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_x = left_min + card.width / 2
            card.x = new_x
            x1 = card.x - card.width / 2
            y1 = card.y - card.height / 2
            x2 = card.x + card.width / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.canvas.coords(card.text_id, card.x, card.y)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
            self.update_attachment_positions(cid)
    
        self.push_history()
    
    def align_selected_cards_top(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        top_min = min(
            self.cards[cid].y - self.cards[cid].height / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_y = top_min + card.height / 2
            card.y = new_y
            x1 = card.x - card.width / 2
            y1 = card.y - card.height / 2
            x2 = card.x + card.width / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.canvas.coords(card.text_id, card.x, card.y)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
            self.update_attachment_positions(cid)
    
        self.push_history()
    
    def equalize_selected_cards_width(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_w = ref.width
    
        for cid in cards:
            card = self.cards[cid]
            card.width = ref_w
            x1 = card.x - ref_w / 2
            y1 = card.y - card.height / 2
            x2 = card.x + ref_w / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.canvas.itemconfig(card.text_id, width=ref_w - 10)
            self.canvas.coords(card.text_id, card.x, card.y)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
            self.update_attachment_positions(cid)
    
        self.push_history()
    
    def equalize_selected_cards_height(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_h = ref.height
    
        for cid in cards:
            card = self.cards[cid]
            card.height = ref_h
            x1 = card.x - card.width / 2
            y1 = card.y - ref_h / 2
            x2 = card.x + card.width / 2
            y2 = card.y + ref_h / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.canvas.coords(card.text_id, card.x, card.y)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
            self.update_attachment_positions(cid)
    
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

    def delete_selected_cards(self, event=None):
        if not self.selected_cards:
            return
        to_delete = list(self.selected_cards)

        new_connections = []
        for conn in self.connections:
            if conn.from_id in to_delete or conn.to_id in to_delete:
                self.canvas.delete(conn.line_id)
                if conn.label_id:
                    self.canvas.delete(conn.label_id)
            else:
                new_connections.append(conn)
        self.connections = new_connections

        for card_id in to_delete:
            card = self.cards.get(card_id)
            if not card:
                continue
            for attachment in card.attachments:
                try:
                    path = Path(attachment.storage_path)
                    if not path.is_absolute():
                        path = Path.cwd() / path
                    if path.exists():
                        path.unlink()
                except Exception:
                    pass
            self._clear_attachment_previews_for_card(card_id)
            if card.resize_handle_id:
                self.canvas.delete(card.resize_handle_id)
            if card.connect_handle_id:
                self.canvas.delete(card.connect_handle_id)
            self.canvas.delete(card.rect_id)
            self.canvas.delete(card.text_id)
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
                "x": c.x,
                "y": c.y,
                "width": c.width,
                "height": c.height,
                "text": c.text,
                "color": c.color,
            })
            sx += c.x
            sy += c.y
        center = (sx / len(ids), sy / len(ids))
        for conn in self.connections:
            if conn.from_id in ids and conn.to_id in ids:
                connections_data.append({
                    "from": conn.from_id,
                    "to": conn.to_id,
                    "label": conn.label,
                })
        self.clipboard = {
            "cards": cards_data,
            "connections": connections_data,
            "center": center,
        }

    def on_paste(self, event=None):
        if self._attach_clipboard_image_to_card():
            return
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
        data = self.get_board_data()
        if file_io.save_board(data):
            self.saved_history_index = self.history.index
            self.update_unsaved_flag()

    def load_board(self):
        data = file_io.load_board()
        if data is None:
            return

        self.set_board_from_data(data)
        state = self.get_board_data()
        self.history.clear_and_init(state)
        self.push_history()
        self.saved_history_index = self.history.index
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()

    # ---------- Экспорт в PNG (как было раньше) ----------

    def export_png(self):
        file_io.export_png(
            canvas=self.canvas,
            cards=self.cards,
            frames=self.frames,
            connections=self.connections,
            theme=self.theme,
            connection_anchor_fn=self._connection_anchors,
        )

    # ---------- Мини-карта ----------

    def update_minimap(self):
        self.canvas_view.render_minimap(self.cards.values(), self.frames.values())

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
        self.theme = THEMES[self.theme_name]
        save_theme_name(self.theme_name)
        self.canvas_view.set_theme(self.theme)
        state = self.get_board_data()
        self.set_board_from_data(state)
        self.canvas.config(bg=self.theme["bg"])
        if self.minimap:
            self.minimap.config(bg=self.theme["minimap_bg"])
        self.btn_theme.config(text=self.get_theme_button_text())
        self.update_minimap()
        self.update_connect_mode_indicator()

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
