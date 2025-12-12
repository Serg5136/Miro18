"""Reusable icon button with keyboard-friendly tooltip support."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .tooltips import Tooltip


class IconWithTooltip(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        icon: tk.PhotoImage,
        tooltip: str,
        ariaLabel: str,
        ariaDescribedby: str | None = None,
        size: int = 40,
        fallback_text: str | None = None,
        command: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        """Create an icon-only control that remains usable with the keyboard.

        Args:
            master: Parent widget.
            icon: Tk image displayed in the control.
            tooltip: Text displayed on hover/focus.
            ariaLabel: Accessible label for assistive technologies.
            size: Width/height of the clickable area in pixels (default: 40).
            fallback_text: Optional text that can be read by screen readers if
                the icon is not accessible.
            command: Optional callback invoked on activation (click/Enter/Space).
            **kwargs: Additional Frame options.
        """

        super().__init__(master, **kwargs)
        self.icon = icon
        label_text = fallback_text or ariaLabel
        describedby = ariaDescribedby or tooltip

        self.button = tk.Button(
            self,
            image=self.icon,
            width=size,
            height=size,
            command=command,
            takefocus=True,
            text=label_text,
            compound="center",
            relief="flat",
        )
        self.button.pack(fill="both", expand=True)

        # Keep the text accessible for screen readers while minimizing visual noise.
        self.button.configure(padx=0, pady=0)
        self.button.configure(highlightcolor="#4a90e2", highlightbackground="#4a90e2")

        self._tooltip = Tooltip(self.button, tooltip, delay=300)
        self._tooltip.bind_to_widget()
        self._tooltip.bind_focus()

        self.button.bind("<Return>", self._on_activate, add="+")
        self.button.bind("<space>", self._on_activate, add="+")
        self.button.bind("<FocusIn>", self._set_focus_style, add="+")
        self.button.bind("<FocusOut>", self._unset_focus_style, add="+")

        # Store aria label for potential introspection/testing.
        self.button._aria_label = ariaLabel  # type: ignore[attr-defined]
        self.button._aria_describedby = describedby  # type: ignore[attr-defined]

    def _on_activate(self, event: tk.Event) -> str:
        self.button.invoke()
        return "break"

    def _set_focus_style(self, _event: tk.Event) -> None:
        self.button.configure(relief="groove", highlightthickness=1)

    def _unset_focus_style(self, _event: tk.Event) -> None:
        self.button.configure(relief="flat", highlightthickness=0)
