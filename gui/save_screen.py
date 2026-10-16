"""The saved-game screen: carry on from a save, or start the adventure fresh."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from engine import Game, saves
from engine.model import World

from . import dialogs


class SaveScreen(ttk.Frame):
    def __init__(self, app, world: World):
        super().__init__(app.root, padding=(36, 28))
        self.app = app
        self.world = world
        self.saves: list[saves.SaveInfo] = []
        p = app.palette

        ttk.Label(self, text=world.title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Choose a saved game to carry on, or start a new adventure.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 22))

        buttons = ttk.Frame(self)
        buttons.pack(side="bottom", anchor="w", fill="x", pady=(18, 0))
        self.continue_button = ttk.Button(buttons, text="Continue", command=self.play)
        self.continue_button.pack(side="left")
        ttk.Button(buttons, text="New Adventure",
                   command=self.new_game).pack(side="left", padx=(8, 0))
        self.delete_button = ttk.Button(buttons, text="Delete Save", command=self.delete)
        self.delete_button.pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Back", command=self.back).pack(side="right")

        ttk.Label(self, text="Saved games", style="Bold.TLabel").pack(anchor="w")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, pady=(4, 0))
        self.list = tk.Listbox(frame, font=app.fonts.ui, activestyle="none",
                               exportselection=False, height=8,
                               background=p["field"], foreground=p["fg"],
                               selectbackground=p["select"], selectforeground=p["fg"],
                               relief="solid", borderwidth=1, highlightthickness=0)
        bar = ttk.Scrollbar(frame, command=self.list.yview)
        self.list.configure(yscrollcommand=bar.set)
        self.list.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.list.bind("<Double-Button-1>", lambda e: self.play())
        self.list.bind("<Delete>", lambda e: self.delete())

        # Enter means Continue; Escape goes back to the list of adventures.
        app.root.bind("<Return>", lambda e: self.play())
        app.root.bind("<Escape>", lambda e: self.back())
        self.refresh()
        self.list.focus_set()

    def destroy(self) -> None:
        self.app.root.unbind("<Return>")
        self.app.root.unbind("<Escape>")
        super().destroy()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self.saves = saves.list_saves(self.world.path, self.world.max_score)
        self.list.configure(state="normal")
        self.list.delete(0, "end")
        for info in self.saves:
            self.list.insert("end", info.label)
        if self.saves:
            self.list.selection_set(0)
            self.continue_button.state(["!disabled"])
            self.delete_button.state(["!disabled"])
        else:
            self.list.insert("end", "(no saved games yet)")
            self.list.configure(state="disabled")
            self.continue_button.state(["disabled"])
            self.delete_button.state(["disabled"])

    @property
    def selected(self) -> saves.SaveInfo | None:
        chosen = self.list.curselection()
        if not self.saves or not chosen:
            return None
        return self.saves[chosen[0]]

    # ------------------------------------------------------------------
    def play(self) -> None:
        info = self.selected
        if info is None:
            return
        try:
            game, warnings = Game.from_save(self.world, saves.read_save(info.path))
        except (OSError, ValueError) as problem:
            dialogs.info(self.app, "Couldn't load", f"That save couldn't be read: {problem}")
            return
        for warning in warnings:
            dialogs.info(self.app, "Loading a save", warning)
        self.app.show_game(self.world, game)

    def new_game(self) -> None:
        self.app.show_game(self.world)

    def delete(self) -> None:
        info = self.selected
        if info is None or not dialogs.confirm(
                self.app, "Delete Save", f"Delete the saved game “{info.name}”? "
                "This can't be undone.", "Delete", "Cancel"):
            return
        try:
            info.path.unlink()
        except OSError as problem:
            dialogs.info(self.app, "Couldn't delete", f"That save couldn't be deleted: {problem}")
        self.refresh()

    def back(self) -> None:
        self.app.show_start(self.world.path)
