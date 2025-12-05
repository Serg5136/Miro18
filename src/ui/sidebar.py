import tkinter as tk


class SidebarFactory:
    def create(self, app) -> tk.Frame:
        sidebar = tk.Frame(app.root, width=260, bg="#f0f0f0")
        sidebar.grid(row=1, column=1, sticky="ns")
        sidebar.grid_propagate(False)

        tk.Label(sidebar, text="Управление", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))

        btn_add = tk.Button(sidebar, text="Добавить карточку",
                            command=app.add_card_dialog)
        btn_add.pack(fill="x", padx=10, pady=5)

        btn_color = tk.Button(sidebar, text="Изменить цвет",
                              command=app.change_color)
        btn_color.pack(fill="x", padx=10, pady=5)

        btn_connect = tk.Button(sidebar, text="Соединить карточки (режим)",
                                command=app.toggle_connect_mode)
        btn_connect.pack(fill="x", padx=10, pady=5)

        btn_edit = tk.Button(sidebar, text="Редактировать текст",
                             command=app.edit_card_text_dialog)
        btn_edit.pack(fill="x", padx=10, pady=5)

        btn_delete = tk.Button(sidebar, text="Удалить карточку(и) (Del)",
                               command=app.delete_selected_cards)
        btn_delete.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Группы / рамки", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        btn_add_frame = tk.Button(sidebar, text="Добавить рамку",
                                  command=app.add_frame_dialog)
        btn_add_frame.pack(fill="x", padx=10, pady=5)

        btn_toggle_frame = tk.Button(sidebar, text="Свернуть/развернуть рамку",
                                     command=app.toggle_selected_frame_collapse)
        btn_toggle_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Файл", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        btn_save = tk.Button(sidebar, text="Сохранить...",
                             command=app.save_board)
        btn_save.pack(fill="x", padx=10, pady=5)

        btn_load = tk.Button(sidebar, text="Загрузить...",
                             command=app.load_board)
        btn_load.pack(fill="x", padx=10, pady=5)

        btn_export = tk.Button(sidebar, text="Экспорт в PNG",
                               command=app.export_png)
        btn_export.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Вид", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))

        app.btn_theme = tk.Button(sidebar, text=app.get_theme_button_text(),
                                   command=app.toggle_theme)
        app.btn_theme.pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="Сетка", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        chk_snap = tk.Checkbutton(
            sidebar,
            text="Привязка к сетке",
            variable=app.var_snap_to_grid,
            bg="#f0f0f0",
            command=app.on_toggle_snap_to_grid,
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
            textvariable=app.var_grid_size,
            width=5,
            command=app.on_grid_size_change,
        )
        spn_grid.pack(side="left", padx=(5, 0))
        spn_grid.bind("<Return>", app.on_grid_size_change)
        spn_grid.bind("<FocusOut>", app.on_grid_size_change)

        tk.Label(sidebar, text="Мини-карта", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        app.minimap = tk.Canvas(
            sidebar, width=240, height=160,
            bg=app.theme["minimap_bg"], highlightthickness=1, highlightbackground="#cccccc"
        )
        app.minimap.pack(padx=10, pady=(0, 10))
        app.minimap.bind("<Button-1>", app.on_minimap_click)

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

        return sidebar
