"""Colors and fonts for the light and dark themes."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

PALETTES = {
    "light": {
        "bg": "#fbf8f1",          # the "paper" behind the story
        "fg": "#2b2925",
        "muted": "#7a746a",
        "heading": "#8a4b14",
        "echo": "#2f5d8a",        # the player's typed commands
        "ending": "#5b3a87",
        "bar": "#ece5d6",         # status bar and buttons
        "bar_fg": "#3a362f",
        "field": "#ffffff",       # input line and dropdowns
        "select": "#cfe0f3",
        "active": "#dfd6c3",
    },
    "dark": {
        "bg": "#1f2023",
        "fg": "#e6e2d8",
        "muted": "#9a958b",
        "heading": "#e5b36c",
        "echo": "#8fbbe9",
        "ending": "#c3a6ec",
        "bar": "#2c2d31",
        "bar_fg": "#d9d5cb",
        "field": "#2a2b2f",
        "select": "#3d5a7a",
        "active": "#3a3b40",
    },
}

# The first of these that is installed is used for the story text.
STORY_FONTS = ["Georgia", "Cambria", "DejaVu Serif", "Liberation Serif",
               "Times New Roman", "Times"]
UI_FONTS = ["Segoe UI", "Ubuntu", "Cantarell", "DejaVu Sans", "Helvetica", "Arial"]


def pick_family(root: tk.Misc, wanted: list[str], fallback: str) -> str:
    installed = {f.lower(): f for f in tkfont.families(root)}
    for name in wanted:
        if name.lower() in installed:
            return installed[name.lower()]
    return tkfont.nametofont(fallback).actual("family")


class Fonts:
    """Named fonts. Changing the size here updates every widget using them."""

    def __init__(self, root: tk.Misc, size: int):
        story = pick_family(root, STORY_FONTS, "TkTextFont")
        ui = pick_family(root, UI_FONTS, "TkDefaultFont")
        self.story = tkfont.Font(root, family=story, size=size)
        self.story_bold = tkfont.Font(root, family=story, size=size, weight="bold")
        self.story_italic = tkfont.Font(root, family=story, size=size, slant="italic")
        self.heading = tkfont.Font(root, family=story, size=size + 3, weight="bold")
        self.ui = tkfont.Font(root, family=ui, size=max(9, size - 2))
        self.ui_bold = tkfont.Font(root, family=ui, size=max(9, size - 2), weight="bold")
        self.title = tkfont.Font(root, family=story, size=size + 12, weight="bold")

    def set_size(self, size: int) -> None:
        for f in (self.story, self.story_bold, self.story_italic):
            f.configure(size=size)
        self.heading.configure(size=size + 3)
        self.ui.configure(size=max(9, size - 2))
        self.ui_bold.configure(size=max(9, size - 2))
        self.title.configure(size=size + 12)


def apply_ttk(root: tk.Tk, style: ttk.Style, p: dict, fonts: Fonts) -> None:
    """Color the ttk widgets (buttons, dropdowns, lists) for a palette."""
    style.theme_use("clam")
    root.configure(background=p["bg"])
    style.configure(".", background=p["bg"], foreground=p["fg"], font=fonts.ui,
                    fieldbackground=p["field"], bordercolor=p["active"],
                    lightcolor=p["bar"], darkcolor=p["bar"], troughcolor=p["bar"],
                    selectbackground=p["select"], selectforeground=p["fg"],
                    insertcolor=p["fg"])
    style.configure("TButton", background=p["bar"], foreground=p["bar_fg"],
                    padding=(12, 6))
    style.map("TButton", background=[("active", p["active"]), ("disabled", p["bg"])],
              foreground=[("disabled", p["muted"])])
    style.configure("TCombobox", fieldbackground=p["field"], background=p["bar"],
                    foreground=p["fg"], arrowcolor=p["fg"], padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", p["field"])],
              foreground=[("readonly", p["fg"])],
              selectbackground=[("readonly", p["field"])],
              selectforeground=[("readonly", p["fg"])])
    style.configure("Muted.TLabel", foreground=p["muted"])
    style.configure("Title.TLabel", font=fonts.title, foreground=p["heading"])
    style.configure("Bold.TLabel", font=fonts.ui_bold)
    style.configure("Vertical.TScrollbar", background=p["bar"], arrowcolor=p["fg"])
    # The drop-down list of a combobox is a plain Tk listbox.
    root.option_add("*TCombobox*Listbox.background", p["field"])
    root.option_add("*TCombobox*Listbox.foreground", p["fg"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["select"])
    root.option_add("*TCombobox*Listbox.selectForeground", p["fg"])
    root.option_add("*TCombobox*Listbox.font", fonts.ui)
