class CanvasEventsBinder:
    def bind(self, app) -> None:
        canvas = app.canvas
        # Обработчики мыши
        canvas.bind("<Double-Button-1>", app.on_canvas_double_click)
        canvas.bind("<Button-1>", app.on_canvas_click)
        canvas.bind("<B1-Motion>", app.on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", app.on_mouse_release)

        # Панорамирование — средней кнопкой
        canvas.bind("<ButtonPress-2>", app.start_pan)
        canvas.bind("<B2-Motion>", app.do_pan)

        # Правая кнопка — контекстное меню
        canvas.bind("<Button-3>", app.on_canvas_right_click)

        # Двойной щелчок правой кнопкой — копирование карточки
        canvas.bind("<Double-Button-3>", app.on_canvas_right_double_click)

        # Зум колёсиком (Windows / Mac / Linux)
        canvas.bind("<MouseWheel>", app.on_mousewheel)      # Windows/Mac
        canvas.bind("<Button-4>", app.on_mousewheel_linux)  # Linux вверх
        canvas.bind("<Button-5>", app.on_mousewheel_linux)  # Linux вниз

        # Клавиатура
        app.root.bind("<Delete>", lambda event: app.delete_selected_cards())
        app.root.bind("<Control-z>", app.on_undo)
        app.root.bind("<Control-Z>", app.on_undo)
        app.root.bind("<Control-y>", app.on_redo)
        app.root.bind("<Control-Y>", app.on_redo)
        app.root.bind("<Control-c>", app.on_copy)
        app.root.bind("<Control-C>", app.on_copy)
        app.root.bind("<Control-v>", app.on_paste)
        app.root.bind("<Control-V>", app.on_paste)
        app.root.bind("<Control-d>", app.on_duplicate)
        app.root.bind("<Control-D>", app.on_duplicate)
