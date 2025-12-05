from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.main import BoardApp


class SelectionController:
    def __init__(self, app: "BoardApp") -> None:
        self.app = app

    def clear_card_selection(self) -> None:
        app = self.app
        for cid in list(app.selected_cards):
            if cid in app.cards:
                app.hide_card_handles(cid)
        app.selected_cards.clear()
        app.selected_card_id = None
        app.render_selection()
        app.update_controls_state()

    def select_card(self, card_id: int | None, additive: bool = False) -> None:
        app = self.app
        if app.selected_frame_id is not None:
            app.selected_frame_id = None
            app.hide_all_frame_handles()

        if not additive:
            self.clear_card_selection()

        if card_id is not None and card_id in app.cards:
            app.selected_cards.add(card_id)
            app.selected_card_id = card_id
            app.show_card_handles(card_id)
        elif not additive:
            app.selected_card_id = None

        app.render_selection()
        app.update_controls_state()

    def select_frame(self, frame_id: int | None) -> None:
        self.clear_card_selection()
        self.app.hide_all_frame_handles()
        self.app.selected_frame_id = frame_id
        if frame_id is not None and frame_id in self.app.frames:
            self.app.show_frame_handles(frame_id)
        self.app.render_selection()
        self.app.update_controls_state()
