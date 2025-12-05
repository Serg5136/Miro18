import copy

from src.board_model import (
    Attachment,
    BoardData,
    Card,
    Connection,
    Frame,
    SCHEMA_VERSION,
    bulk_update_card_colors,
)
from src.config import THEMES
from src.history import History


def test_card_serialization_roundtrip():
    card = Card(id=1, x=10.5, y=20.5, width=100, height=50, text="Note", color="#abc123")

    primitive = card.to_primitive()
    assert primitive == {
        "id": 1,
        "x": 10.5,
        "y": 20.5,
        "width": 100,
        "height": 50,
        "text": "Note",
        "color": "#abc123",
        "attachments": [],
    }

    restored = Card.from_primitive(primitive)
    assert restored == card


def test_connection_backward_compatibility_and_label_change():
    legacy_data = {"from_id": 1, "to_id": 2, "label": "old"}
    connection = Connection.from_primitive(legacy_data)

    assert connection.from_id == 1
    assert connection.to_id == 2
    assert connection.label == "old"

    connection.label = "updated"
    assert connection.to_primitive() == {"from": 1, "to": 2, "label": "updated"}


def test_frame_serialization_and_update():
    frame = Frame(id=3, x1=0, y1=0, x2=10, y2=20, title="Group", collapsed=True)

    frame.title = "Renamed"
    primitive = frame.to_primitive()

    assert primitive == {
        "id": 3,
        "x1": 0,
        "y1": 0,
        "x2": 10,
        "y2": 20,
        "title": "Renamed",
        "collapsed": True,
    }

    restored = Frame.from_primitive(primitive)
    assert restored == frame


def test_board_data_roundtrip_and_invalid_connections_skipped():
    board = BoardData(
        cards={
            1: Card(id=1, x=1, y=2, width=3, height=4, text="A"),
            2: Card(id=2, x=5, y=6, width=7, height=8, text="B", color="#ffff00"),
        },
        connections=[Connection(from_id=1, to_id=2, label="edge")],
        frames={1: Frame(id=1, x1=0, y1=0, x2=10, y2=10, title="Frame")},
    )

    primitive = board.to_primitive()
    assert primitive["schema_version"] == SCHEMA_VERSION
    assert primitive["cards"][0]["text"] == "A"
    assert primitive["connections"][0]["label"] == "edge"

    primitive_with_broken_connection = {
        **primitive,
        "connections": primitive["connections"] + [{"from": None, "to": None}],
    }

    restored = BoardData.from_primitive(primitive_with_broken_connection)

    assert list(restored.cards.keys()) == [1, 2]
    assert len(restored.connections) == 1
    assert restored.connections[0].from_id == 1
    assert restored.frames[1].title == "Frame"


def test_attachment_restores_base64():
    attachment = Attachment(
        id=1,
        name="image.png",
        source_type="file",
        mime_type="image/png",
        width=10,
        height=10,
        preview_scale=0.5,
        data_base64="YWJj",
    )

    card = Card(
        id=1,
        x=0,
        y=0,
        width=10,
        height=10,
        attachments=[attachment],
    )

    primitive = card.to_primitive()
    assert primitive["attachments"][0]["data_base64"] == "YWJj"
    assert primitive["attachments"][0]["preview_scale"] == 0.5
    restored = Card.from_primitive(primitive)
    assert restored.attachments[0].data_base64 == "YWJj"
    assert restored.attachments[0].preview_scale == 0.5


def test_attachment_file_storage_roundtrip_preserves_path():
    attachment = Attachment(
        id=2,
        name="photo.jpg",
        source_type="file",
        mime_type="image/jpeg",
        width=50,
        height=60,
        preview_scale=1.0,
        storage_path="attachments/1-2.jpg",
    )

    card = Card(
        id=1,
        x=10,
        y=20,
        width=100,
        height=50,
        attachments=[attachment],
    )

    primitive = card.to_primitive()
    assert primitive["attachments"][0]["storage_path"] == "attachments/1-2.jpg"
    restored = Card.from_primitive(primitive)
    restored_attachment = restored.attachments[0]
    assert restored_attachment.storage_path == "attachments/1-2.jpg"
    assert restored_attachment.preview_scale == 1.0
    assert restored_attachment.data_base64 is None


def test_attachment_preview_scale_defaults_for_legacy_data():
    legacy_attachment = {
        "id": 3,
        "name": "legacy.png",
        "width": 100,
        "height": 100,
        "source_type": "file",
        "mime_type": "image/png",
        # preview_scale отсутствует
    }

    restored = Attachment.from_primitive(legacy_attachment)

    assert restored.preview_scale == 1.0


def test_bulk_color_update_for_multiple_cards():
    cards = {
        1: Card(id=1, x=0, y=0, width=50, height=50, color="#123456"),
        2: Card(id=2, x=10, y=10, width=50, height=50, color="#abcdef"),
        3: Card(id=3, x=20, y=20, width=50, height=50, color="#123456"),
    }

    changed = bulk_update_card_colors(cards, [1, 3], "#ffffff")

    assert set(changed) == {1, 3}
    assert cards[1].color == "#ffffff"
    assert cards[3].color == "#ffffff"
    assert cards[2].color == "#abcdef"


def test_bulk_color_update_integrates_with_history_undo_redo():
    initial_cards = {
        1: Card(id=1, x=0, y=0, width=50, height=50),
        2: Card(id=2, x=1, y=1, width=50, height=50),
    }

    history = History()
    initial_board = BoardData(
        cards=copy.deepcopy(initial_cards), connections=[], frames={}
    )
    history.clear_and_init(initial_board.to_primitive())

    working_cards = copy.deepcopy(initial_cards)
    bulk_update_card_colors(working_cards, working_cards.keys(), "#ff00ff")
    updated_board = BoardData(cards=working_cards, connections=[], frames={})
    history.push(updated_board.to_primitive())

    class DummyBoardApp:
        def __init__(self):
            self.board: BoardData | None = None

        def set_board_from_data(self, data):
            self.board = BoardData.from_primitive(data)

    app = DummyBoardApp()

    undo_state = history.undo(app)
    assert undo_state["cards"][0]["color"] == "#fff9b1"
    assert app.board and app.board.cards[1].color == "#fff9b1"

    redo_state = history.redo(app)
    assert redo_state["cards"][0]["color"] == "#ff00ff"
    assert app.board and app.board.cards[2].color == "#ff00ff"


def test_bulk_color_update_preserves_theme_defaults():
    default_light = THEMES["light"]["card_default"]
    cards = {1: Card(id=1, x=0, y=0, width=30, height=30, color=default_light)}

    bulk_update_card_colors(cards, [1, 999], "#101010")

    serialized = BoardData(cards=cards, connections=[], frames={}).to_primitive()
    restored = BoardData.from_primitive(serialized)

    assert restored.cards[1].color == "#101010"
    assert THEMES["light"]["card_default"] == default_light
