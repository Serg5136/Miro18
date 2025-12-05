import tkinter as tk
from typing import Optional

from .sidebar import SidebarFactory
from .tooltips import add_tooltip
from ..input import EventBinder


class ToolbarFactory:
    def create(self, app) -> tk.Frame:
        toolbar = tk.Frame(app.root, bg="#e0e0e0", height=32)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="new")

        btn_undo_toolbar = tk.Button(
            toolbar,
            text="⟲ Отменить",
            command=app.on_undo,
        )
        btn_undo_toolbar.pack(side="left", padx=(8, 2), pady=4)
        app.btn_undo_toolbar = btn_undo_toolbar
        add_tooltip(btn_undo_toolbar, "Отменить последнее действие")

        btn_redo_toolbar = tk.Button(
            toolbar,
            text="⟳ Повторить",
            command=app.on_redo,
        )
        btn_redo_toolbar.pack(side="left", padx=2, pady=4)
        app.btn_redo_toolbar = btn_redo_toolbar
        add_tooltip(btn_redo_toolbar, "Повторить отменённое действие")

        btn_attach_image = tk.Button(
            toolbar,
            text="📎 Прикрепить к карточке",
            command=app.attach_image_from_file,
        )
        btn_attach_image.pack(side="left", padx=(10, 2), pady=4)
        add_tooltip(
            btn_attach_image,
            "Прикрепить файл-изображение к выделенной карточке без создания новой",
        )

        btn_text_color = tk.Button(
            toolbar,
            text="🎨 Цвет текста",
            command=app.change_text_color,
        )
        btn_text_color.pack(side="left", padx=2, pady=4)
        add_tooltip(btn_text_color, "Изменить цвет текста карточек для текущей темы")
        return toolbar


class CanvasFactory:
    def create_canvas(self, app) -> tk.Canvas:
        canvas = tk.Canvas(app.root, bg=app.theme["bg"])
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.config(scrollregion=(0, 0, 4000, 4000))
        return canvas


class LayoutBuilder:
    def __init__(
        self,
        toolbar_factory: Optional[ToolbarFactory] = None,
        sidebar_factory: Optional[SidebarFactory] = None,
        canvas_factory: Optional[CanvasFactory] = None,
        events_binder: Optional[EventBinder] = None,
    ):
        self.toolbar_factory = toolbar_factory or ToolbarFactory()
        self.sidebar_factory = sidebar_factory or SidebarFactory()
        self.canvas_factory = canvas_factory or CanvasFactory()
        self.events_binder = events_binder or EventBinder()

    def configure_root_grid(self, root: tk.Tk) -> None:
        root.rowconfigure(0, weight=0)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)

    def build(self, app) -> None:
        self.configure_root_grid(app.root)
        self.toolbar_factory.create(app)
        app.canvas = self.canvas_factory.create_canvas(app)
        self.sidebar_factory.create(app)
        self.events_binder.bind(app)
