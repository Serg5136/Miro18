import tkinter as tk

from .icon_with_tooltip import IconWithTooltip
from .localization import DEFAULT_LOCALE, get_string
from .tooltips import add_canvas_tooltip, add_tooltip


class SidebarFactory:
    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        self.locale = locale

    def create(self, app) -> tk.Frame:
        sidebar = tk.Frame(app.root, width=260, bg="#f0f0f0")
        sidebar.grid(row=1, column=1, sticky="ns")
        sidebar.grid_propagate(False)

        controls_frame = tk.Frame(sidebar, bg="#f0f0f0")

        collapse_button = tk.Button(
            sidebar,
            text=get_string("sidebar.toggle.collapse", self.locale),
            takefocus=True,
        )
        collapse_button.pack(fill="x", padx=10, pady=(10, 5))
        controls_frame.pack(fill="both", expand=True)

        manage_section = tk.Frame(controls_frame, bg="#f0f0f0")
        manage_section.pack(fill="both", expand=False)
        other_sections = tk.Frame(controls_frame, bg="#f0f0f0")
        other_sections.pack(fill="both", expand=True)

        def toggle_sidebar():
            if manage_section.winfo_ismapped():
                manage_section.pack_forget()
                collapse_button.config(
                    text=get_string("sidebar.toggle.expand", self.locale)
                )
            else:
                manage_section.pack(fill="both", expand=False, before=other_sections)
                collapse_button.config(
                    text=get_string("sidebar.toggle.collapse", self.locale)
                )

        collapse_button.configure(command=toggle_sidebar)

        tk.Label(
            manage_section,
            text=get_string("sidebar.section.manage", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(5, 5))

        btn_add = IconWithTooltip(
            manage_section,
            icon=app.icon_loader.get("icon-card-add"),
            tooltip=get_string("sidebar.add.tooltip", self.locale),
            ariaLabel=get_string("sidebar.add.aria", self.locale),
            command=app.add_card_dialog,
            bg=manage_section["bg"],
        )
        btn_add.pack(anchor="w", padx=10, pady=5)
        app.btn_add_card = btn_add.button

        btn_color = IconWithTooltip(
            manage_section,
            icon=app.icon_loader.get("icon-card-color"),
            tooltip=get_string("sidebar.color.tooltip", self.locale),
            ariaLabel=get_string("sidebar.color.aria", self.locale),
            command=app.change_color,
            bg=manage_section["bg"],
        )
        btn_color.pack(anchor="w", padx=10, pady=5)
        app.btn_change_color = btn_color.button

        btn_connect = IconWithTooltip(
            manage_section,
            icon=app.icon_loader.get("icon-connect"),
            tooltip=get_string("sidebar.connect.tooltip", self.locale),
            ariaLabel=get_string("sidebar.connect.aria", self.locale),
            command=app.toggle_connect_mode,
            bg=manage_section["bg"],
        )
        btn_connect.pack(anchor="w", padx=10, pady=5)
        app.btn_connect_mode = btn_connect.button
        app.btn_connect_mode_default_bg = btn_connect.button.cget("bg")

        btn_edit = IconWithTooltip(
            manage_section,
            icon=app.icon_loader.get("icon-text-edit"),
            tooltip=get_string("sidebar.edit.tooltip", self.locale),
            ariaLabel=get_string("sidebar.edit.aria", self.locale),
            command=app.edit_card_text_dialog,
            bg=manage_section["bg"],
        )
        btn_edit.pack(anchor="w", padx=10, pady=5)
        app.btn_edit_text = btn_edit.button

        btn_delete = IconWithTooltip(
            manage_section,
            icon=app.icon_loader.get("icon-delete"),
            tooltip=get_string("sidebar.delete.tooltip", self.locale),
            ariaLabel=get_string("sidebar.delete.aria", self.locale),
            command=app.delete_selected_cards,
            bg=manage_section["bg"],
        )
        btn_delete.pack(anchor="w", padx=10, pady=5)
        app.btn_delete_cards = btn_delete.button

        tk.Label(
            other_sections,
            text=get_string("sidebar.section.frames", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        btn_add_frame = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-frame-add"),
            tooltip=get_string("sidebar.frame_add.tooltip", self.locale),
            ariaLabel=get_string("sidebar.frame_add.aria", self.locale),
            command=app.add_frame_dialog,
            bg=other_sections["bg"],
        )
        btn_add_frame.pack(anchor="w", padx=10, pady=5)
        app.btn_add_frame = btn_add_frame.button

        btn_toggle_frame = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-frame-collapse"),
            tooltip=get_string("sidebar.frame_toggle.tooltip", self.locale),
            ariaLabel=get_string("sidebar.frame_toggle.aria", self.locale),
            command=app.toggle_selected_frame_collapse,
            bg=other_sections["bg"],
        )
        btn_toggle_frame.pack(anchor="w", padx=10, pady=5)
        app.btn_toggle_frame = btn_toggle_frame.button

        tk.Label(
            other_sections,
            text=get_string("sidebar.section.file", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        btn_save = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-save"),
            tooltip=get_string("sidebar.save.tooltip", self.locale),
            ariaLabel=get_string("sidebar.save.aria", self.locale),
            command=app.save_board,
            bg=other_sections["bg"],
        )
        btn_save.pack(anchor="w", padx=10, pady=5)

        btn_load = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-load"),
            tooltip=get_string("sidebar.load.tooltip", self.locale),
            ariaLabel=get_string("sidebar.load.aria", self.locale),
            command=app.load_board,
            bg=other_sections["bg"],
        )
        btn_load.pack(anchor="w", padx=10, pady=5)

        btn_export = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-export-png"),
            tooltip=get_string("sidebar.export.tooltip", self.locale),
            ariaLabel=get_string("sidebar.export.aria", self.locale),
            command=app.export_png,
            bg=other_sections["bg"],
        )
        btn_export.pack(anchor="w", padx=10, pady=5)

        btn_attach_image = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-attach-image"),
            tooltip=get_string("sidebar.attach.tooltip", self.locale),
            ariaLabel=get_string("sidebar.attach.aria", self.locale),
            command=app.attach_image_from_file,
            bg=other_sections["bg"],
        )
        btn_attach_image.pack(anchor="w", padx=10, pady=5)

        tk.Label(
            other_sections,
            text=get_string("sidebar.section.view", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(15, 5))

        theme_button = IconWithTooltip(
            other_sections,
            icon=app.icon_loader.get("icon-theme-toggle"),
            tooltip=app.get_theme_button_text(),
            ariaLabel=get_string("sidebar.theme.aria", self.locale),
            command=app.toggle_theme,
            bg=other_sections["bg"],
        )
        theme_button.pack(anchor="w", padx=10, pady=5)
        app.btn_theme = theme_button.button
        app.btn_theme_tooltip = theme_button._tooltip

        tk.Label(
            other_sections,
            text=get_string("sidebar.section.grid", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        chk_show_grid = tk.Checkbutton(
            other_sections,
            text=get_string("sidebar.grid.toggle", self.locale),
            variable=app.var_show_grid,
            bg="#f0f0f0",
            command=app.on_toggle_show_grid,
            takefocus=True,
        )
        chk_show_grid.pack(fill="x", padx=10, pady=2)
        add_tooltip(chk_show_grid, get_string("sidebar.grid.tooltip", self.locale))

        chk_snap = tk.Checkbutton(
            other_sections,
            text=get_string("sidebar.grid.snap", self.locale),
            variable=app.var_snap_to_grid,
            bg="#f0f0f0",
            command=app.on_toggle_snap_to_grid,
            takefocus=True,
        )
        chk_snap.pack(fill="x", padx=10, pady=2)
        add_tooltip(chk_snap, get_string("sidebar.grid.snap.tooltip", self.locale))

        frame_grid = tk.Frame(other_sections, bg="#f0f0f0")
        frame_grid.pack(fill="x", padx=10, pady=2)

        tk.Label(
            frame_grid,
            text=get_string("sidebar.grid.step_label", self.locale),
            bg="#f0f0f0",
        ).pack(side="left")

        spn_grid = tk.Spinbox(
            frame_grid,
            from_=5,
            to=200,
            increment=5,
            textvariable=app.var_grid_size,
            width=5,
            command=app.on_grid_size_change,
            takefocus=True,
        )
        spn_grid.pack(side="left", padx=(5, 0))
        spn_grid.bind("<Return>", app.on_grid_size_change)
        spn_grid.bind("<FocusOut>", app.on_grid_size_change)
        add_tooltip(spn_grid, get_string("sidebar.grid.step.tooltip", self.locale))

        tk.Label(
            controls_frame,
            text=get_string("sidebar.minimap.title", self.locale),
            bg="#f0f0f0",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        app.minimap = tk.Canvas(
            controls_frame, width=240, height=160,
            bg=app.theme["minimap_bg"], highlightthickness=1, highlightbackground="#cccccc"
        )
        app.minimap.pack(padx=10, pady=(0, 10))
        app.minimap.bind("<Button-1>", app.on_minimap_click)
        add_tooltip(app.minimap, get_string("sidebar.minimap.tooltip", self.locale))
        add_canvas_tooltip(
            app.minimap,
            "minimap_card",
            get_string("sidebar.minimap.card.tooltip", self.locale),
        )
        add_canvas_tooltip(
            app.minimap,
            "minimap_frame",
            get_string("sidebar.minimap.frame.tooltip", self.locale),
        )
        add_canvas_tooltip(
            app.minimap,
            "minimap_viewport",
            get_string("sidebar.minimap.viewport.tooltip", self.locale),
        )

        tk.Label(
            controls_frame,
            text=(
                "Подсказки:\n"
                "— Двойной клик по пустому месту: новая карточка\n"
                "— Двойной клик по карточке: редактировать текст\n"
                "— Двойной клик по связи: текст связи\n"
                "— ЛКМ по карточке: выбрать, перетаскивать\n"
                "— ЛКМ по пустому месту + движение: прямоугольное выделение\n"
                "— ЛКМ по связи: выбрать (Delete — удалить, Ctrl+Shift+D — направление)\n"
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

        return sidebar
