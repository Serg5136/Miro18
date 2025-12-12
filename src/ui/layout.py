import tkinter as tk
from typing import Optional

from .icon_with_tooltip import IconWithTooltip
from .sidebar import SidebarFactory
from .tooltips import add_tooltip
from ..input import EventBinder


class ToolbarFactory:
    def create(self, app) -> tk.Frame:
        toolbar = tk.Frame(app.root, bg="#e0e0e0", height=56)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="new")
        toolbar.grid_propagate(False)

        btn_undo_toolbar = IconWithTooltip(
            toolbar,
            icon=app.icon_loader.get("icon-undo"),
            tooltip="Отменить последнее действие",
            ariaLabel="Отменить",
            command=app.on_undo,
            bg="#e0e0e0",
        )
        btn_undo_toolbar.pack(side="left", padx=(8, 2), pady=8)
        app.btn_undo_toolbar = btn_undo_toolbar.button

        btn_redo_toolbar = IconWithTooltip(
            toolbar,
            icon=app.icon_loader.get("icon-redo"),
            tooltip="Повторить отменённое действие",
            ariaLabel="Повторить",
            command=app.on_redo,
            bg="#e0e0e0",
        )
        btn_redo_toolbar.pack(side="left", padx=2, pady=8)
        app.btn_redo_toolbar = btn_redo_toolbar.button

        btn_attach_image = IconWithTooltip(
            toolbar,
            icon=app.icon_loader.get("icon-attach-image"),
            tooltip="Прикрепить файл-изображение к выделенной карточке без создания новой",
            ariaLabel="Прикрепить к карточке",
            command=app.attach_image_from_file,
            bg="#e0e0e0",
        )
        btn_attach_image.pack(side="left", padx=(10, 2), pady=8)

        btn_text_color = IconWithTooltip(
            toolbar,
            icon=app.icon_loader.get("icon-text-color"),
            tooltip="Изменить цвет текста карточек для текущей темы",
            ariaLabel="Цвет текста",
            command=app.change_text_color,
            bg="#e0e0e0",
        )
        btn_text_color.pack(side="left", padx=2, pady=8)

        size_frame = tk.Frame(toolbar, bg="#e0e0e0")
        size_frame.pack(side="left", padx=(12, 2), pady=8)

        tk.Label(size_frame, text="Ширина:", bg="#e0e0e0").grid(row=0, column=0, padx=(0, 4))
        spn_width = tk.Spinbox(
            size_frame,
            from_=60,
            to=1200,
            width=6,
            textvariable=app.var_card_width,
        )
        spn_width.grid(row=0, column=1, padx=(0, 8))
        add_tooltip(spn_width, "Задайте ширину карточки в пикселях")

        tk.Label(size_frame, text="Высота:", bg="#e0e0e0").grid(row=0, column=2, padx=(0, 4))
        spn_height = tk.Spinbox(
            size_frame,
            from_=40,
            to=1200,
            width=6,
            textvariable=app.var_card_height,
        )
        spn_height.grid(row=0, column=3, padx=(0, 8))
        add_tooltip(spn_height, "Задайте высоту карточки в пикселях")

        btn_apply_size = IconWithTooltip(
            size_frame,
            icon=app.icon_loader.get("icon-apply-size"),
            tooltip="Применить указанные ширину и высоту к выбранным карточкам",
            ariaLabel="Применить размеры",
            command=app.apply_card_size_from_controls,
            bg="#e0e0e0",
        )
        btn_apply_size.grid(row=0, column=4, padx=(4, 0))
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
