"""The main window. Switches between the start, saved-game and game screens."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from engine import paths
from engine.model import World

from .game_screen import GameScreen
from .save_screen import SaveScreen
from .settings import MAX_FONT, MIN_FONT, Settings
from .start_screen import StartScreen
from .theme import PALETTES, Fonts, apply_ttk


class App:
    def __init__(self, root: tk.Tk, settings: Settings | None = None):
        self.root = root
        self.settings = settings or Settings.load()
        self.fonts = Fonts(root, self.settings.font_size)
        self.style = ttk.Style(root)
        self.theme_var = tk.StringVar(root, value=self.settings.theme)
        self.screen: tk.Widget | None = None

        root.title("Adventure Engine")
        root.minsize(560, 420)
        try:
            root.geometry(self.settings.geometry)
        except tk.TclError:
            pass
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.apply_theme()
        self.show_start()

    @property
    def palette(self) -> dict:
        return PALETTES[self.theme_var.get()]

    # ------------------------------------------------------------------
    def _switch(self, make) -> None:
        # The old screen goes first, so its key bindings are removed
        # before the new screen adds its own.
        if self.screen is not None:
            self.screen.destroy()
            self.screen = None
        self.screen = make()
        self.screen.pack(fill="both", expand=True)

    def show_start(self, select: Path | None = None) -> None:
        self.root.title("Adventure Engine")
        self._switch(lambda: StartScreen(self, select))

    def show_saves(self, world: World) -> None:
        self._switch(lambda: SaveScreen(self, world))

    def show_game(self, world: World, game=None) -> None:
        self._switch(lambda: GameScreen(self, world, game))

    # ------------------------------------------------------------------
    def apply_theme(self) -> None:
        self.settings.theme = self.theme_var.get()
        apply_ttk(self.root, self.style, self.palette, self.fonts)
        if isinstance(self.screen, GameScreen):
            self.screen.apply_theme(self.palette)
        self.settings.save()

    def change_font(self, step: int) -> None:
        size = max(MIN_FONT, min(MAX_FONT, self.settings.font_size + step))
        self.settings.font_size = size
        self.fonts.set_size(size)
        self.settings.save()

    def quit(self) -> None:
        if isinstance(self.screen, GameScreen) and not self.screen.confirm_unsaved():
            return
        if self.root.state() == "normal":
            self.settings.geometry = self.root.geometry()
        self.settings.save()
        self.root.destroy()


def main() -> None:
    paths.copy_old_data()       # bring along saves from older versions
    root = tk.Tk()
    App(root)
    root.mainloop()
