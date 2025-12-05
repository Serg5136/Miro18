from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.main import BoardApp


class DragController:
    def __init__(self, app: "BoardApp") -> None:
        self.app = app

    def on_canvas_click(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)
        item = app.canvas.find_withtag("current")
        item_id = item[0] if item else None
        tags = app.canvas.gettags(item_id) if item_id else ()

        if "resize_handle" in tags:
            card_id = app.get_card_id_from_item(item)
            if card_id is not None:
                app.selection_controller.select_card(card_id, additive=False)
                card = app.cards[card_id]
                x1 = card.x - card.width / 2
                y1 = card.y - card.height / 2
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "resize_card"
                app.drag_data["resize_card_id"] = card_id
                app.drag_data["resize_origin"] = (x1, y1)
                app.drag_data["moved"] = False
                app.drag_data["dragged_cards"] = {card_id}
            return

        if "connect_handle" in tags:
            card_id = app.get_card_id_from_item(item)
            if card_id is not None:
                app.selection_controller.select_card(card_id, additive=False)
                card = app.cards[card_id]
                sx = card.x + card.width / 2
                sy = card.y
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "connect_drag"
                app.drag_data["connect_from_card"] = card_id
                app.drag_data["connect_start"] = (sx, sy)
                app.drag_data["temp_line_id"] = app.canvas.create_line(
                    sx, sy, sx, sy,
                    fill=app.theme["connection"],
                    width=2,
                    dash=(4, 2),
                    arrow=tk.LAST,
                    tags=("temp_connection",)
                )
            return

        card_id = app.get_card_id_from_item(item)
        frame_id = app.get_frame_id_from_item(item)

        if app.connect_mode:
            if card_id is not None:
                if app.connect_from_card_id is None:
                    app.connect_from_card_id = card_id
                    app.selection_controller.select_card(card_id, additive=False)
                else:
                    if card_id != app.connect_from_card_id:
                        app.create_connection(app.connect_from_card_id, card_id)
                        app.push_history()
                    app.connect_controller.set_connect_mode(False)
                    app.selection_controller.select_card(card_id, additive=False)
            return

        app.drag_data["dragging"] = False
        app.drag_data["dragged_cards"] = set()
        app.drag_data["moved"] = False
        app.drag_data["mode"] = None
        app.drag_data["frame_id"] = None
        app.drag_data["resize_card_id"] = None
        app.drag_data["resize_origin"] = None
        app.drag_data["connect_from_card"] = None
        if app.drag_data["temp_line_id"]:
            app.canvas.delete(app.drag_data["temp_line_id"])
        app.drag_data["temp_line_id"] = None
        app.selection_start = None
        if app.selection_rect_id is not None:
            app.canvas.delete(app.selection_rect_id)
            app.selection_rect_id = None

        if card_id is not None:
            if card_id in app.selected_cards:
                app.selected_card_id = card_id
            else:
                app.selection_controller.select_card(card_id, additive=False)

            app.drag_data["dragging"] = True
            app.drag_data["dragged_cards"] = set(app.selected_cards)
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            app.drag_data["mode"] = "cards"

        elif frame_id is not None:
            app.selection_controller.select_frame(frame_id)
            app.drag_data["dragging"] = True
            app.drag_data["mode"] = "frame"
            app.drag_data["frame_id"] = frame_id
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            x1, y1, x2, y2 = app.canvas.coords(app.frames[frame_id].rect_id)
            app.drag_data["dragged_cards"] = {
                cid for cid, card in app.cards.items()
                if x1 <= card.x <= x2 and y1 <= card.y <= y2
            }
        else:
            app.selection_controller.select_card(None)
            app.selection_start = (cx, cy)
            app.selection_rect_id = app.canvas.create_rectangle(
                cx, cy, cx, cy,
                outline="#999999",
                dash=(2, 2),
                fill="",
                tags=("selection_rect",),
            )

    def on_mouse_drag(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)

        if app.drag_data["dragging"]:
            mode = app.drag_data["mode"]

            if mode == "resize_card":
                card_id = app.drag_data["resize_card_id"]
                card = app.cards.get(card_id)
                if not card:
                    return
                ox1, oy1 = app.drag_data["resize_origin"]
                min_w, min_h = 60, 40
                new_x2 = max(ox1 + min_w, cx)
                new_y2 = max(oy1 + min_h, cy)
                w = new_x2 - ox1
                h = new_y2 - oy1
                card.width = w
                card.height = h
                card.x = ox1 + w / 2
                card.y = oy1 + h / 2
                x1 = ox1
                y1 = oy1
                x2 = new_x2
                y2 = new_y2
                app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                app.update_card_layout(card_id)
                app.update_card_handles_positions(card_id)
                app.update_connections_for_card(card_id)
                app.drag_data["moved"] = True
                return

            if mode == "connect_drag":
                line_id = app.drag_data["temp_line_id"]
                if line_id:
                    sx, sy = app.drag_data["connect_start"]
                    app.canvas.coords(line_id, sx, sy, cx, cy)
                    app.drag_data["moved"] = True
                return

            dx = cx - app.drag_data["last_x"]
            dy = cy - app.drag_data["last_y"]
            if dx == 0 and dy == 0:
                return
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            app.drag_data["moved"] = True

            if mode == "cards":
                for card_id in app.drag_data["dragged_cards"]:
                    card = app.cards.get(card_id)
                    if not card:
                        continue
                    card.x += dx
                    card.y += dy
                    x1 = card.x - card.width / 2
                    y1 = card.y - card.height / 2
                    x2 = card.x + card.width / 2
                    y2 = card.y + card.height / 2
                    app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                    app.update_card_layout(card_id, redraw_attachment=False)
                    app.update_card_handles_positions(card_id)
                    app.update_connections_for_card(card_id)

            elif mode == "frame":
                frame_id = app.drag_data["frame_id"]
                frame = app.frames.get(frame_id)
                if frame:
                    app.canvas.move(frame.rect_id, dx, dy)
                    app.canvas.move(frame.title_id, dx, dy)

                for card_id in app.drag_data["dragged_cards"]:
                    card = app.cards.get(card_id)
                    if not card:
                        continue
                    card.x += dx
                    card.y += dy
                    x1 = card.x - card.width / 2
                    y1 = card.y - card.height / 2
                    x2 = card.x + card.width / 2
                    y2 = card.y + card.height / 2
                    app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                    app.update_card_layout(card_id, redraw_attachment=False)
                    app.update_card_handles_positions(card_id)
                    app.update_connections_for_card(card_id)

        elif app.selection_start is not None and app.selection_rect_id is not None:
            x0, y0 = app.selection_start
            app.canvas.coords(app.selection_rect_id, x0, y0, cx, cy)

    def on_mouse_release(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)
        mode = app.drag_data["mode"]

        if mode == "connect_drag":
            from_id = app.drag_data["connect_from_card"]
            if app.drag_data["temp_line_id"]:
                app.canvas.delete(app.drag_data["temp_line_id"])
            target_id = None
            items = app.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                cid = app.get_card_id_from_item((it,))
                if cid is not None:
                    target_id = cid
                    break
            if from_id is not None and target_id is not None and target_id != from_id:
                app.create_connection(from_id, target_id)
                app.push_history()

            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["connect_from_card"] = None
            app.drag_data["temp_line_id"] = None
            app.drag_data["moved"] = False
            return

        if mode == "resize_card":
            if app.drag_data["moved"]:
                app.snap_cards_to_grid(app.drag_data["dragged_cards"])
                app.push_history()
            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["resize_card_id"] = None
            app.drag_data["resize_origin"] = None
            app.drag_data["dragged_cards"] = set()
            app.drag_data["moved"] = False
            return

        if app.drag_data["dragging"] and app.drag_data["moved"]:
            app.snap_cards_to_grid(app.drag_data["dragged_cards"])
            app.push_history()

        app.drag_data["dragging"] = False
        app.drag_data["dragged_cards"] = set()
        app.drag_data["moved"] = False
        app.drag_data["mode"] = None

        if app.selection_start is not None and app.selection_rect_id is not None:
            x1, y1, x2, y2 = app.canvas.coords(app.selection_rect_id)
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)

            app.selection_controller.select_card(None)
            for card_id, card in app.cards.items():
                if left <= card.x <= right and top <= card.y <= bottom:
                    app.selection_controller.select_card(card_id, additive=True)

            app.canvas.delete(app.selection_rect_id)
            app.selection_rect_id = None
            app.selection_start = None


# Keep tkinter import local to avoid circular import issues
import tkinter as tk  # noqa: E402  pylint: disable=wrong-import-position
