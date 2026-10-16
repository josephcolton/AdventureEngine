"""The game window: status bar, story text, input line, and the menus."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from engine import Game, saves
from engine.game import ENDING, HEADING, TurnResult
from engine.model import World
from engine.vocabulary import HELP_TEXT

from . import dialogs
from .start_screen import load_safely

ABOUT = """Adventure Engine

Write your own adventures in a plain text file, then play them here.
See docs/AUTHORING.md for how to write one.

Inspired by Zork and the other great text adventures."""


class GameScreen(tk.Frame):
    def __init__(self, app, world: World, game: Game | None = None):
        super().__init__(app.root)
        self.app = app
        self.world = world
        self.game: Game | None = None
        self.typed: list[str] = []          # for the Up/Down arrow keys
        self.typed_pos = 0
        self.state_window: tk.Toplevel | None = None
        self._build()
        self._build_menu()
        self.apply_theme(app.palette)
        if game is None:
            self.new_game()
        else:
            self.use_game(game)

    # ==================================================================
    # Building the window
    # ==================================================================
    def _build(self) -> None:
        fonts = self.app.fonts
        self.status = tk.Frame(self, padx=14, pady=6)
        self.status.pack(side="top", fill="x")
        self.room_label = tk.Label(self.status, font=fonts.ui_bold, anchor="w")
        self.room_label.pack(side="left")
        self.score_label = tk.Label(self.status, font=fonts.ui, anchor="e")
        self.score_label.pack(side="right")

        # The bottom row is either the input line or, after an ending, buttons.
        self.bottom = tk.Frame(self, padx=14, pady=10)
        self.bottom.pack(side="bottom", fill="x")
        self.input_row = tk.Frame(self.bottom)
        self.prompt = tk.Label(self.input_row, text=">", font=fonts.story_bold)
        self.prompt.pack(side="left", padx=(0, 6))
        self.entry = tk.Entry(self.input_row, font=fonts.story, relief="flat",
                              highlightthickness=1, borderwidth=4)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<Up>", lambda e: self._recall(-1))
        self.entry.bind("<Down>", lambda e: self._recall(+1))

        self.ending_row = tk.Frame(self.bottom)
        ttk.Button(self.ending_row, text="Restart",
                   command=self.new_game).pack(side="left")
        ttk.Button(self.ending_row, text="Load a Save",
                   command=self.load).pack(side="left", padx=(8, 0))
        ttk.Button(self.ending_row, text="Choose Another Adventure",
                   command=self.change_adventure).pack(side="left", padx=(8, 0))

        story_frame = tk.Frame(self)
        story_frame.pack(side="top", fill="both", expand=True)
        self.story = tk.Text(story_frame, wrap="word", font=fonts.story, padx=28,
                             pady=18, borderwidth=0, highlightthickness=0,
                             spacing1=2, spacing3=2, cursor="arrow", state="disabled")
        bar = ttk.Scrollbar(story_frame, command=self.story.yview)
        self.story.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.story.pack(side="left", fill="both", expand=True)
        self.story.tag_configure(HEADING, font=fonts.heading, spacing1=10, spacing3=4)
        self.story.tag_configure("echo", font=fonts.story_bold, spacing1=12)
        self.story.tag_configure(ENDING, font=fonts.story_italic, lmargin1=20,
                                 lmargin2=20, spacing1=6)
        self.story.tag_configure("notice", font=fonts.story_italic, spacing1=8)
        # Clicking in the story (without selecting text) puts you back in the input line.
        self.story.bind("<ButtonRelease-1>", self._story_clicked)

    def _build_menu(self) -> None:
        root = self.app.root
        menu = tk.Menu(root)
        game = tk.Menu(menu, tearoff=False)
        game.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        game.add_command(label="Save As…", command=self.save_as)
        game.add_command(label="Load…", command=self.load)
        game.add_separator()
        game.add_command(label="Restart", command=self.restart)
        game.add_command(label="Change Adventure…", command=self.change_adventure)
        game.add_separator()
        game.add_command(label="Quit", command=self.app.quit)
        menu.add_cascade(label="Game", menu=game)

        view = tk.Menu(menu, tearoff=False)
        view.add_command(label="Larger Text", accelerator="Ctrl+=",
                         command=lambda: self.app.change_font(+1))
        view.add_command(label="Smaller Text", accelerator="Ctrl+-",
                         command=lambda: self.app.change_font(-1))
        view.add_separator()
        view.add_radiobutton(label="Light Theme", variable=self.app.theme_var,
                             value="light", command=self.app.apply_theme)
        view.add_radiobutton(label="Dark Theme", variable=self.app.theme_var,
                             value="dark", command=self.app.apply_theme)
        menu.add_cascade(label="View", menu=view)

        author = tk.Menu(menu, tearoff=False)
        author.add_command(label="Check Adventure", command=self.check)
        author.add_command(label="Reload Adventure File", command=self.reload)
        author.add_command(label="Reload and Replay", command=lambda: self.reload(replay=True))
        author.add_separator()
        author.add_command(label="Show Flags & State", command=self.show_state)
        author.add_command(label="Go To Room…", command=self.go_to_room)
        menu.add_cascade(label="Author", menu=author)

        help_ = tk.Menu(menu, tearoff=False)
        help_.add_command(label="How to Play", command=lambda: dialogs.show_text(
            self.app, "How to Play", HELP_TEXT))
        help_.add_command(label="About", command=lambda: dialogs.info(
            self.app, "About", ABOUT))
        menu.add_cascade(label="Help", menu=help_)

        root.configure(menu=menu)
        self.keys = {
            "<Control-s>": self.save, "<Control-S>": self.save,
            "<Control-equal>": lambda: self.app.change_font(+1),
            "<Control-plus>": lambda: self.app.change_font(+1),
            "<Control-KP_Add>": lambda: self.app.change_font(+1),
            "<Control-minus>": lambda: self.app.change_font(-1),
            "<Control-KP_Subtract>": lambda: self.app.change_font(-1),
        }
        for key, action in self.keys.items():
            root.bind(key, lambda e, a=action: (a(), "break")[1])

    def destroy(self) -> None:
        root = self.app.root
        root.configure(menu="")
        for key in self.keys:
            root.unbind(key)
        if self.state_window:
            self.state_window.destroy()
        super().destroy()

    def apply_theme(self, p: dict) -> None:
        self.status.configure(background=p["bar"])
        for w in (self.room_label, self.score_label):
            w.configure(background=p["bar"], foreground=p["bar_fg"])
        for w in (self.bottom, self.input_row, self.ending_row, self):
            w.configure(background=p["bg"])
        self.prompt.configure(background=p["bg"], foreground=p["echo"])
        self.entry.configure(background=p["field"], foreground=p["fg"],
                             insertbackground=p["fg"], highlightcolor=p["echo"],
                             highlightbackground=p["active"],
                             selectbackground=p["select"], selectforeground=p["fg"])
        self.story.configure(background=p["bg"], foreground=p["fg"],
                             selectbackground=p["select"], selectforeground=p["fg"],
                             inactiveselectbackground=p["select"])
        self.story.master.configure(background=p["bg"])
        self.story.tag_configure(HEADING, foreground=p["heading"])
        self.story.tag_configure("echo", foreground=p["echo"])
        self.story.tag_configure(ENDING, foreground=p["ending"])
        self.story.tag_configure("notice", foreground=p["muted"])

    # ==================================================================
    # Showing text
    # ==================================================================
    def _write(self, text: str, tag: str | None = None) -> None:
        self.story.configure(state="normal")
        self.story.insert("end", text, (tag,) if tag else ())
        self.story.configure(state="disabled")

    def _clear(self) -> None:
        self.story.configure(state="normal")
        self.story.delete("1.0", "end")
        self.story.configure(state="disabled")

    def notice(self, text: str) -> None:
        self._write(text + "\n", "notice")
        self.story.see("end")

    def show(self, result: TurnResult, echo: str | None = None) -> None:
        if echo is not None:
            self._write("> " + echo + "\n", "echo")
        for style, text in result.output:
            self._write(text + "\n", style if style != "text" else None)
        self.story.see("end")
        self.update_status()
        if result.ending:
            self._ended()

    def update_status(self) -> None:
        name, score = self.game.status()
        self.room_label.configure(text=name)
        self.score_label.configure(text=score)
        self.app.root.title(f"{self.world.title} — Adventure Engine")
        self._refresh_state()

    def _playing(self) -> None:
        self.ending_row.pack_forget()
        self.input_row.pack(fill="x")
        self.entry.configure(state="normal")
        self.entry.focus_set()

    def _ended(self) -> None:
        self.entry.configure(state="disabled")
        self.input_row.pack_forget()
        self.ending_row.pack(anchor="w")

    # ==================================================================
    # Playing
    # ==================================================================
    def new_game(self) -> None:
        self.game = Game(self.world)
        self._clear()
        self._playing()
        self.show(self.game.start())

    def use_game(self, game: Game) -> None:
        """Continue a game loaded from a save, showing its recent story."""
        self.game = game
        self._clear()
        self._playing()
        for line in game.transcript:
            self._write(line + "\n", "echo" if line.startswith("> ") else None)
        self.notice(f"(Loaded “{game.save_name}”.)" if game.save_name else "(Loaded.)")
        self.update_status()
        if game.ended:
            self._ended()

    def _submit(self, event=None) -> str:
        line = self.entry.get().strip()
        self.entry.delete(0, "end")
        if not line:
            return "break"
        if not self.typed or self.typed[-1] != line:
            self.typed.append(line)
        self.typed_pos = len(self.typed)
        result = self.game.command(line)
        self.show(result, echo=line)
        if result.meta:
            {"save": self.save, "load": self.load, "restart": self.restart,
             "quit": self.app.quit}[result.meta]()
        return "break"

    def _recall(self, step: int) -> str:
        if not self.typed:
            return "break"
        self.typed_pos = max(0, min(len(self.typed), self.typed_pos + step))
        self.entry.delete(0, "end")
        if self.typed_pos < len(self.typed):
            self.entry.insert(0, self.typed[self.typed_pos])
        return "break"

    def _story_clicked(self, event=None) -> None:
        if not self.story.tag_ranges("sel") and str(self.entry["state"]) == "normal":
            self.entry.focus_set()

    # ==================================================================
    # Saving and loading
    # ==================================================================
    def save(self) -> bool:
        if self.game.save_name:
            return self._write_save(self.game.save_name)
        return self.save_as()

    def save_as(self) -> bool:
        name = dialogs.ask_text(self.app, "Save As", "Name this save:",
                                self.game.save_name or "")
        if not name:
            return False
        existing = saves.save_path(self.world.path, name)
        if existing.exists() and name != self.game.save_name:
            if not dialogs.confirm(self.app, "Save As", f"There is already a save called "
                                   f"“{name}”. Replace it?", "Replace", "Cancel"):
                return False
        return self._write_save(name)

    def _write_save(self, name: str) -> bool:
        try:
            saves.write_save(self.world.path, self.game.to_save(name))
        except OSError as problem:
            dialogs.info(self.app, "Couldn't save", f"The game couldn't be saved: {problem}")
            return False
        self.game.save_name = name
        self.game.unsaved = False
        self.notice(f"(Saved as “{name}”.)")
        return True

    def confirm_unsaved(self) -> bool:
        """Offer to save first. Returns False if the player chose Cancel."""
        if not self.game or not self.game.unsaved or self.game.ended:
            return True
        choice = dialogs.choose(self.app, "Unsaved progress", "Save your progress first?",
                                ["Save", "Don't Save", "Cancel"], cancel="Cancel")
        if choice == "Save":
            return self.save()
        return choice == "Don't Save"

    def load(self) -> None:
        found = saves.list_saves(self.world.path, self.world.max_score)
        if not found:
            dialogs.info(self.app, "Load", "There are no saved games for this adventure yet.")
            return
        if not self.confirm_unsaved():
            return
        index = dialogs.pick(self.app, "Load", "Choose a saved game:",
                             [s.label for s in found], ok="Load")
        if index is None:
            return
        try:
            game, warnings = Game.from_save(self.world, saves.read_save(found[index].path))
        except (OSError, ValueError) as problem:
            dialogs.info(self.app, "Couldn't load", f"That save couldn't be read: {problem}")
            return
        for warning in warnings:
            dialogs.info(self.app, "Loading a save", warning)
        self.use_game(game)

    def restart(self) -> None:
        if self.confirm_unsaved() and (self.game.moves == 0 or self.game.ended or dialogs.confirm(
                self.app, "Restart", "Start this adventure again from the beginning?",
                "Restart", "Cancel")):
            self.new_game()

    def change_adventure(self) -> None:
        if self.confirm_unsaved():
            self.app.show_start(self.world.path)

    # ==================================================================
    # Author tools
    # ==================================================================
    def check(self) -> None:
        world = load_safely(self.world.path)
        dialogs.show_text(self.app, "Check Adventure", world.report.format(),
                          heading=f"{world.title}  ({world.path.name})")

    def reload(self, replay: bool = False) -> None:
        world = load_safely(self.world.path)
        if not world.ok:
            dialogs.show_text(self.app, "Not reloaded", world.report.format(),
                              heading="The adventure has problems, so the old version "
                                      "is still running.")
            return
        commands = list(self.game.history) if replay else []
        save_name = self.game.save_name
        self.world = world
        self.game = Game(world)
        self.game.save_name = save_name
        self._clear()
        self._playing()
        if not replay:
            self.notice("(Adventure reloaded.)")
            self.show(self.game.start())
            return
        self.game.start()
        ending = None
        for line in commands:
            result = self.game.command(line)
            if result.ending:
                ending = result
                break
        self.notice(f"(Adventure reloaded and {len(commands)} "
                    f"command{'s' if len(commands) != 1 else ''} replayed.)")
        self.show(ending or self.game.look())

    def show_state(self) -> None:
        if self.state_window:
            self.state_window.lift()
            return
        p = self.app.palette
        win = tk.Toplevel(self.app.root, background=p["bg"])
        win.title("Flags & State")
        win.geometry("420x520")
        self.state_text = tk.Text(win, wrap="word", font=self.app.fonts.ui, padx=12, pady=10,
                                  background=p["field"], foreground=p["fg"],
                                  borderwidth=0, highlightthickness=0)
        self.state_text.pack(fill="both", expand=True)

        def closed():
            self.state_window = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", closed)
        self.state_window = win
        self._refresh_state()

    def _refresh_state(self) -> None:
        if not self.state_window:
            return
        g = self.game
        items = self.world.items
        held = [i.name for i in g.inventory()]
        where = [f"  {item_id}: {place}" for item_id, place in g.item_locations.items()
                 if place != "inventory" and item_id in items]
        lines = [
            f"Room: {g.room.name}  ({g.current_room})",
            f"Score: {g.score} / {g.max_score}    Moves: {g.moves}",
            "",
            "Flags:", "  " + (", ".join(sorted(g.flags)) or "(none)"),
            "",
            "Carrying:", "  " + (", ".join(held) or "(nothing)"),
            "",
            "Visited:", "  " + ", ".join(g.visited),
            "",
            "Actions completed:", "  " + (", ".join(sorted(g.completed)) or "(none)"),
            "",
            "Where things are:", *where,
        ]
        text = self.state_text
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("end", "\n".join(lines))
        text.configure(state="disabled")

    def go_to_room(self) -> None:
        rooms = list(self.world.rooms.values())
        index = dialogs.pick(self.app, "Go To Room", "Jump straight to a room (for testing):",
                             [f"{r.name}  ({r.id})" for r in rooms], ok="Go")
        if index is None:
            return
        self.notice(f"(Jumped to {rooms[index].name}.)")
        self.show(self.game.teleport(rooms[index].id))
        if not self.game.ended:
            self._playing()
