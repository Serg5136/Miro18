from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Card:
    """
    Логическая модель карточки без привязки к Tkinter.
    Используется только для сериализации/десериализации.
    """
    id: int
    x: float
    y: float
    width: float
    height: float
    text: str = ""
    color: str = "#fff9b1"


@dataclass
class Connection:
    """
    Логическая модель связи между карточками.
    """
    from_id: int
    to_id: int
    label: str = ""


@dataclass
class Frame:
    """
    Логическая модель рамки (группы карточек).
    """
    id: int
    x1: float
    y1: float
    x2: float
    y2: float
    title: str = "Группа"
    collapsed: bool = False


@dataclass
class BoardData:
    """
    Полный снимок доски: карточки, связи, рамки.
    """
    cards: Dict[int, Card]
    connections: List[Connection]
    frames: Dict[int, Frame]

    def to_primitive(self) -> Dict[str, Any]:
        """
        Преобразовать в чистый dict для JSON-сериализации.
        Добавляем schema_version и явно раскладываем поля.
        """
        return {
            "schema_version": 1,
            "cards": [
                {
                    "id": c.id,
                    "x": c.x,
                    "y": c.y,
                    "width": c.width,
                    "height": c.height,
                    "text": c.text,
                    "color": c.color,
                }
                for c in self.cards.values()
            ],
            "connections": [
                {
                    "from": conn.from_id,
                    "to": conn.to_id,
                    "label": conn.label,
                }
                for conn in self.connections
            ],
            "frames": [
                {
                    "id": f.id,
                    "x1": f.x1,
                    "y1": f.y1,
                    "x2": f.x2,
                    "y2": f.y2,
                    "title": f.title,
                    "collapsed": f.collapsed,
                }
                for f in self.frames.values()
            ],
        }

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "BoardData":
        """
        Восстановить BoardData из dict (например, после json.load()).
        Поддерживает старые и новые форматы connections.
        Ожидаемый формат:

        {
          "schema_version": 1,
          "cards": [
            {
              "id": int,
              "x": float,
              "y": float,
              "width": float,
              "height": float,
              "text": str,
              "color": str
            }, ...
          ],
          "connections": [
            {
              "from": int,
              "to": int,
              "label": str
            }, ...
          ],
          "frames": [
            {
              "id": int,
              "x1": float,
              "y1": float,
              "x2": float,
              "y2": float,
              "title": str,
              "collapsed": bool
            }, ...
          ]
        }
        """
        # Карточки
        cards: Dict[int, Card] = {}
        for c in data.get("cards", []):
            card = Card(
                id=c["id"],
                x=c["x"],
                y=c["y"],
                width=c["width"],
                height=c["height"],
                text=c.get("text", ""),
                color=c.get("color", "#fff9b1"),
            )
            cards[card.id] = card

        # Связи (поддержка старых ключей from_id/to_id)
        connections: List[Connection] = []
        for c in data.get("connections", []):
            from_raw = c.get("from", c.get("from_id"))
            to_raw = c.get("to", c.get("to_id"))
            if from_raw is None or to_raw is None:
                # Битые записи пропускаем, чтобы не падать на старых файлах
                continue
            connections.append(
                Connection(
                    from_id=from_raw,
                    to_id=to_raw,
                    label=c.get("label", ""),
                )
            )

        # Рамки
        frames: Dict[int, Frame] = {}
        for f in data.get("frames", []):
            frame = Frame(
                id=f["id"],
                x1=f["x1"],
                y1=f["y1"],
                x2=f["x2"],
                y2=f["y2"],
                title=f.get("title", "Группа"),
                collapsed=f.get("collapsed", False),
            )
            frames[frame.id] = frame

        return BoardData(cards=cards, connections=connections, frames=frames)
