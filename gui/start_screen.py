"""The start screen: pick an adventure, then play.

If the adventure has saved games, Play goes to the saved-game screen first.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tkinter import ttk

from engine import load_adventure, paths, saves
from engine.model import World

from . import dialogs

WARNING_MARK = "⚠ "


def load_safely(path: Path) -> World:
    """Load an adventure; a file that can't even be read becomes a broken World."""
    try:
        return load_adventure(path)
    except OSError as problem:
        world = World(path=path)
        world.report.error(None, f"The file couldn't be opened: {problem}")
        return world


def open_folder(folder: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(folder)                       # noqa: S606 (Windows only)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


class StartScreen(ttk.Frame):
    def __init__(self, app, select: Path | None = None):
        super().__init__(app.root, padding=(36, 28))
        self.app = app
        self.worlds: list[World] = []

        ttk.Label(self, text="Adventure Engine", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Choose an adventure, then press Play.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 22))

        ttk.Label(self, text="Adventure", style="Bold.TLabel").pack(anchor="w")
        self.adventure = ttk.Combobox(self, state="readonly", width=50,
                                      font=app.fonts.story)
        self.adventure.pack(anchor="w", fill="x", pady=(4, 10))
        self.adventure.bind("<<ComboboxSelected>>", lambda e: self._adventure_changed())

        self.author = ttk.Label(self, style="Muted.TLabel")
        self.author.pack(anchor="w")
        self.description = ttk.Label(self, wraplength=560, justify="left",
                                     font=app.fonts.story)
        self.description.pack(anchor="w", fill="x", pady=(4, 26))

        buttons = ttk.Frame(self)
        buttons.pack(anchor="w", fill="x")
        self.play_button = ttk.Button(buttons, text="Play", command=self.play)
        self.play_button.pack(side="left")
        ttk.Button(buttons, text="Check Adventure", command=self.check).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Refresh List", command=self.refresh).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Open Adventures Folder",
                   command=lambda: open_folder(paths.adventures_dir())).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Quit", command=app.quit).pack(side="right")

        # Enter anywhere on the start screen means Play.
        app.root.bind("<Return>", lambda e: self.play())
        self.refresh(select)

    def destroy(self) -> None:
        self.app.root.unbind("<Return>")
        super().destroy()

    # ------------------------------------------------------------------
    def refresh(self, select: Path | None = None) -> None:
        current = select or (self.selected.path if self.selected else None)
        if current is None and self.app.settings.last_adventure:
            current = paths.adventures_dir() / self.app.settings.last_adventure
        files = sorted(paths.adventures_dir().glob("*.adv"))
        self.worlds = sorted((load_safely(f) for f in files), key=lambda w: w.title.lower())
        labels = [("" if w.ok else WARNING_MARK) + w.title for w in self.worlds]
        self.adventure.configure(values=labels)
        if not self.worlds:
            self.adventure.set("")
            self.author.configure(text="")
            self.description.configure(
                text="There are no adventures yet. Put .adv files in the adventures "
                     "folder (use Open Adventures Folder), then press Refresh List.")
            self.play_button.state(["disabled"])
            return
        self.play_button.state(["!disabled"])
        index = 0
        for n, world in enumerate(self.worlds):
            if current and world.path and world.path.name == Path(current).name:
                index = n
        self.adventure.current(index)
        self._adventure_changed()

    @property
    def selected(self) -> World | None:
        if not self.worlds:
            return None
        index = self.adventure.current()
        return self.worlds[index] if 0 <= index < len(self.worlds) else None

    def _adventure_changed(self) -> None:
        world = self.selected
        if world is None:
            return
        g = world.game
        self.author.configure(text=f"by {g.author}" if g.author else "")
        text = g.description
        if not world.ok:
            text = ("This adventure has problems that need fixing before it can be "
                    "played. Press Check Adventure to see them.\n\n" + text).strip()
        self.description.configure(text=text)

    # ------------------------------------------------------------------
    def check(self) -> None:
        world = self.selected
        if world is None:
            return
        world = load_safely(world.path)        # always check the file as it is now
        dialogs.show_text(self.app, "Check Adventure", world.report.format(),
                          heading=f"{world.title}  ({world.path.name})")
        self.refresh(world.path)

    def play(self) -> None:
        world = self.selected
        if world is None:
            return
        world = load_safely(world.path)        # pick up any edits made since the list loaded
        if not world.ok:
            dialogs.show_text(self.app, "This adventure can't be played yet",
                              world.report.format(),
                              heading=f"{world.title}  ({world.path.name})")
            self.refresh(world.path)
            return
        self.app.settings.last_adventure = world.path.name
        if saves.list_saves(world.path):
            self.app.show_saves(world)
        else:
            self.app.show_game(world)
