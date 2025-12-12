import sys
import types

import tkinter as tk

import pytest

# Provide a lightweight stub for cairosvg so importing src.ui succeeds even when the
# dependency is unavailable in the test environment.
if "cairosvg" not in sys.modules:  # pragma: no cover - test setup
    sys.modules["cairosvg"] = types.SimpleNamespace(svg2png=lambda **_kwargs: b"")

from src.ui.icon_with_tooltip import IconWithTooltip


def _make_icon():
    icon = tk.PhotoImage(width=2, height=2)
    icon.put("#000000", to=(0, 0, 2, 2))
    return icon


def test_icon_with_tooltip_renders_button(tk_root):
    icon = _make_icon()
    component = IconWithTooltip(
        tk_root,
        icon=icon,
        tooltip="Example tooltip",
        ariaLabel="Accessible label",
        ariaDescribedby="desc",
        size=32,
    )
    component.pack()
    tk_root.update_idletasks()

    button = component.button
    assert int(button["width"]) == 32
    assert int(button["height"]) == 32
    assert button["text"] == "Accessible label"
    assert getattr(button, "_aria_label") == "Accessible label"
    assert getattr(button, "_aria_describedby") == "desc"
    assert component._tooltip.text == "Example tooltip"


def test_tooltip_shows_on_hover(tk_root):
    icon = _make_icon()
    component = IconWithTooltip(
        tk_root,
        icon=icon,
        tooltip="Hover text",
        ariaLabel="Hover label",
    )
    component.pack()
    tk_root.update_idletasks()

    hover_event = types.SimpleNamespace(x_root=15, y_root=25)
    component._tooltip._show(hover_event)
    tk_root.update_idletasks()

    window = component._tooltip._window
    assert window is not None
    label = window.winfo_children()[0]
    assert isinstance(label, tk.Label)
    assert label.cget("text") == "Hover text"

    component._tooltip._hide()
    tk_root.update_idletasks()
    assert component._tooltip._window is None


def test_tooltip_shows_and_hides_on_focus(tk_root):
    icon = _make_icon()
    component = IconWithTooltip(
        tk_root,
        icon=icon,
        tooltip="Focus text",
        ariaLabel="Focus label",
    )
    component.pack()
    tk_root.update_idletasks()

    component.button.focus_set()
    component.button.event_generate("<FocusIn>")
    tk_root.update()

    assert component._tooltip._window is not None

    component.button.event_generate("<FocusOut>")
    tk_root.update()
    assert component._tooltip._window is None
