import tkinter as tk
from typing import Dict, Iterable, Sequence

from ..board_model import Card, Connection, Frame


class CanvasView:
    def __init__(self, canvas: tk.Canvas, minimap: tk.Canvas | None, theme: Dict[str, str]):
        self.text_padding_min = 8
        self.text_padding_max = 16
        self.text_margin_min = 2
        self.text_margin_max = 6
        self.canvas = canvas
        self.minimap = minimap
        self.theme = theme

    def _compute_spacing(self, card: Card) -> tuple[float, float]:
        """Return adaptive (padding, margin) for the given card."""

        padding = max(self.text_padding_min, min(card.width * 0.05, self.text_padding_max))
        margin_base = padding * 0.4
        margin = max(self.text_margin_min, min(margin_base, self.text_margin_max))
        return padding, margin

    def set_theme(self, theme: Dict[str, str]) -> None:
        self.theme = theme
        self.canvas.config(bg=self.theme["bg"])
        if self.minimap:
            self.minimap.config(bg=self.theme["minimap_bg"])

    def compute_card_layout(self, card: Card) -> Dict[str, float]:
        """Calculate positions for text and image areas inside the card."""

        padding, margin = self._compute_spacing(card)
        y1 = card.y - card.height / 2
        text_width = max(card.width - 2 * padding, 20)

        measure_id = self.canvas.create_text(
            0,
            0,
            text=card.text or " ",
            width=text_width,
            anchor="nw",
            font=("Arial", 10, "bold"),
            state="hidden",
        )
        bbox = self.canvas.bbox(measure_id)
        self.canvas.delete(measure_id)
        text_height = (bbox[3] - bbox[1]) if bbox else 14

        text_top = y1 + padding
        image_top = text_top + text_height + padding
        image_height = max(card.height - (image_top - y1) - padding, 0)
        image_width = max(card.width - 2 * padding, 0)

        return {
            "text_top": text_top,
            "text_width": text_width,
            "image_top": image_top,
            "image_height": image_height,
            "image_width": image_width,
            "padding": padding,
            "margin": margin,
        }

    def apply_card_layout(self, card: Card, layout: Dict[str, float]) -> None:
        text_width = layout["text_width"]
        text_top = layout["text_top"]

        if card.text_id:
            self.canvas.itemconfig(card.text_id, width=text_width, anchor="n")
            self.canvas.coords(card.text_id, card.x, text_top)

        if card.text_bg_id:
            bbox = self.canvas.bbox(card.text_id) if card.text_id else None
            if bbox:
                margin = layout.get("margin", self.text_margin_min)
                self.canvas.coords(
                    card.text_bg_id,
                    bbox[0] - margin,
                    bbox[1] - margin,
                    bbox[2] + margin,
                    bbox[3] + margin,
                )
                self.canvas.tag_lower(card.text_bg_id, card.text_id)

    def draw_grid(self, grid_size: int) -> None:
        self.canvas.delete("grid")
        spacing = grid_size
        x_max = 4000
        y_max = 4000
        for x in range(0, x_max + 1, spacing):
            self.canvas.create_line(
                x,
                0,
                x,
                y_max,
                fill=self.theme["grid"],
                tags=("grid",),
            )
        for y in range(0, y_max + 1, spacing):
            self.canvas.create_line(
                0,
                y,
                x_max,
                y,
                fill=self.theme["grid"],
                tags=("grid",),
            )
        self.canvas.tag_lower("grid")

    def draw_card(self, card: Card) -> None:
        x1 = card.x - card.width / 2
        y1 = card.y - card.height / 2
        x2 = card.x + card.width / 2
        y2 = card.y + card.height / 2

        rect_id = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=card.color,
            outline=self.theme["card_outline"],
            width=1.5,
            tags=("card", f"card_{card.id}"),
        )
        layout = self.compute_card_layout(card)
        text_id = self.canvas.create_text(
            card.x,
            layout["text_top"],
            text=card.text,
            width=layout["text_width"],
            anchor="n",
            font=("Arial", 10, "bold"),
            fill=self.theme["text"],
            tags=("card_text", f"card_{card.id}"),
        )
        text_bbox = self.canvas.bbox(text_id) or (
            card.x,
            layout["text_top"],
            card.x,
            layout["text_top"] + 14,
        )
        margin = layout.get("margin", self.text_margin_min)
        text_bg_id = self.canvas.create_rectangle(
            text_bbox[0] - margin,
            text_bbox[1] - margin,
            text_bbox[2] + margin,
            text_bbox[3] + margin,
            fill=card.color,
            outline="",
            tags=("card_text_bg", f"card_{card.id}"),
        )
        self.canvas.tag_lower(text_bg_id, text_id)

        card.rect_id = rect_id
        card.text_id = text_id
        card.text_bg_id = text_bg_id

    def update_card_color(self, card: Card) -> None:
        if card.rect_id:
            self.canvas.itemconfig(card.rect_id, fill=card.color)
        if card.text_bg_id:
            self.canvas.itemconfig(card.text_bg_id, fill=card.color)

    def draw_frame(self, frame: Frame) -> None:
        rect_id = self.canvas.create_rectangle(
            frame.x1,
            frame.y1,
            frame.x2,
            frame.y2,
            fill=self.theme["frame_collapsed_bg"] if frame.collapsed else self.theme["frame_bg"],
            outline=self.theme["frame_outline"],
            width=2,
            dash=(3, 3) if frame.collapsed else (),
            tags=("frame", f"frame_{frame.id}"),
        )
        title_id = self.canvas.create_text(
            frame.x1 + 10,
            frame.y1 + 15,
            text=frame.title,
            anchor="w",
            font=("Arial", 10, "bold"),
            fill=self.theme["text"],
            tags=("frame_title", f"frame_{frame.id}"),
        )

        self.canvas.tag_lower(rect_id)
        self.canvas.tag_lower("grid")

        frame.rect_id = rect_id
        frame.title_id = title_id

    def card_handle_positions(self, card: Card) -> Dict[str, tuple[float, float]]:
        half_w = card.width / 2
        half_h = card.height / 2
        return {
            "n": (card.x, card.y - half_h),
            "e": (card.x + half_w, card.y),
            "s": (card.x, card.y + half_h),
            "w": (card.x - half_w, card.y),
        }

    def _auto_anchors(self, from_card: Card, to_card: Card) -> tuple[str, str]:
        dx = to_card.x - from_card.x
        dy = to_card.y - from_card.y
        if abs(dx) > abs(dy):
            return ("e" if dx > 0 else "w", "w" if dx > 0 else "e")
        return ("s" if dy > 0 else "n", "n" if dy > 0 else "s")

    def _resolve_anchor(
        self, card: Card, preferred: str | None, fallback: str
    ) -> tuple[str, tuple[float, float]]:
        positions = self.card_handle_positions(card)
        anchor = preferred if preferred in positions else fallback
        return anchor, positions[anchor]

    def _connection_anchors(
        self, from_card: Card, to_card: Card, connection: Connection | None = None
    ) -> Sequence[float]:
        default_from, default_to = self._auto_anchors(from_card, to_card)
        from_anchor, (sx, sy) = self._resolve_anchor(
            from_card, getattr(connection, "from_anchor", None), default_from
        )
        to_anchor, (tx, ty) = self._resolve_anchor(
            to_card, getattr(connection, "to_anchor", None), default_to
        )

        if connection is not None:
            connection.from_anchor = from_anchor
            connection.to_anchor = to_anchor

        return sx, sy, tx, ty

    def _arrow_for_direction(self, direction: str) -> str:
        return tk.FIRST if direction == "start" else tk.LAST

    def apply_connection_direction(self, connection: Connection) -> None:
        if not connection.line_id:
            return
        arrow = self._arrow_for_direction(connection.direction)
        self.canvas.itemconfig(connection.line_id, arrow=arrow)

    def draw_connection(self, connection: Connection, from_card: Card, to_card: Card) -> None:
        sx, sy, tx, ty = self._connection_anchors(from_card, to_card, connection)
        arrow = self._arrow_for_direction(connection.direction)

        line_id = self.canvas.create_line(
            sx,
            sy,
            tx,
            ty,
            arrow=arrow,
            width=2,
            fill=self.theme["connection"],
            tags=("connection",),
        )

        label_id = None
        if connection.label:
            mx = (sx + tx) / 2
            my = (sy + ty) / 2
            label_id = self.canvas.create_text(
                mx,
                my,
                text=connection.label,
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",),
            )

        connection.line_id = line_id
        connection.label_id = label_id

    def update_connection_positions(
        self,
        connections: Iterable[Connection],
        cards: Dict[int, Card],
        target_card_id: int | None = None,
    ) -> None:
        for conn in connections:
            if target_card_id is not None and conn.from_id != target_card_id and conn.to_id != target_card_id:
                continue
            from_card = cards.get(conn.from_id)
            to_card = cards.get(conn.to_id)
            if from_card is None or to_card is None:
                continue
            sx, sy, tx, ty = self._connection_anchors(from_card, to_card, conn)
            if conn.line_id:
                self.canvas.coords(conn.line_id, sx, sy, tx, ty)
                self.apply_connection_direction(conn)
            if conn.label_id:
                mx = (sx + tx) / 2
                my = (sy + ty) / 2
                self.canvas.coords(conn.label_id, mx, my)

    def render_board(
        self,
        cards: Dict[int, Card],
        frames: Dict[int, Frame],
        connections: Iterable[Connection],
        grid_size: int,
    ) -> None:
        self.canvas.delete("all")
        self.draw_grid(grid_size)

        for frame in frames.values():
            self.draw_frame(frame)
        for card in cards.values():
            self.draw_card(card)
        for connection in connections:
            from_card = cards.get(connection.from_id)
            to_card = cards.get(connection.to_id)
            if from_card is None or to_card is None:
                continue
            self.draw_connection(connection, from_card, to_card)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.render_minimap(cards.values(), frames.values())

    def render_selection(
        self,
        cards: Dict[int, Card],
        frames: Dict[int, Frame],
        selected_cards: Iterable[int],
        selected_frame_id: int | None,
    ) -> None:
        selected_cards_set = set(selected_cards)
        for cid, card in cards.items():
            if card.rect_id:
                width = 3 if cid in selected_cards_set else 1.5
                self.canvas.itemconfig(card.rect_id, width=width)
        for fid, frame in frames.items():
            if frame.rect_id:
                width = 3 if fid == selected_frame_id else 2
                self.canvas.itemconfig(frame.rect_id, width=width)

    def render_minimap(self, cards: Iterable[Card], frames: Iterable[Frame]) -> None:
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

        def map_point(px: float, py: float) -> tuple[float, float]:
            mx = (px - x1) * scale
            my = (py - y1) * scale
            return mx, my

        for card in cards:
            cx, cy = card.x, card.y
            w, h = card.width, card.height
            mx1, my1 = map_point(cx - w / 2, cy - h / 2)
            mx2, my2 = map_point(cx + w / 2, cy + h / 2)
            self.minimap.create_rectangle(
                mx1,
                my1,
                mx2,
                my2,
                outline=self.theme["minimap_card_outline"],
                fill="",
                tags=("minimap_card",),
            )

        for frame in frames:
            if frame.rect_id is None:
                fx1, fy1, fx2, fy2 = frame.x1, frame.y1, frame.x2, frame.y2
            else:
                fx1, fy1, fx2, fy2 = self.canvas.coords(frame.rect_id)
            mx1, my1 = map_point(fx1, fy1)
            mx2, my2 = map_point(fx2, fy2)
            self.minimap.create_rectangle(
                mx1,
                my1,
                mx2,
                my2,
                outline=self.theme["minimap_frame_outline"],
                dash=(2, 2),
                tags=("minimap_frame",),
            )

        vx0, vx1 = self.canvas.xview()
        vy0, vy1 = self.canvas.yview()
        view_x1 = x1 + vx0 * (x2 - x1)
        view_x2 = x1 + vx1 * (x2 - x1)
        view_y1 = y1 + vy0 * (y2 - y1)
        view_y2 = y1 + vy1 * (y2 - y1)
        mvx1, mvy1 = map_point(view_x1, view_y1)
        mvx2, mvy2 = map_point(view_x2, view_y2)
        self.minimap.create_rectangle(
            mvx1,
            mvy1,
            mvx2,
            mvy2,
            outline=self.theme["minimap_viewport"],
            tags=("minimap_viewport",),
        )
