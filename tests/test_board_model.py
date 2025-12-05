from src.board_model import BoardData, Card, Connection, Frame


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
    assert primitive["schema_version"] == 1
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
