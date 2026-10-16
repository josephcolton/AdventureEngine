"""A plain text front end, for testing the engine without the window.

    python -m engine.textmode                      (choose from adventures/)
    python -m engine.textmode adventures/agnes_and_the_well.adv
    python -m engine.textmode --check FILE         (just run the validator)
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from . import paths, saves
from .game import ENDING, HEADING, Game, TurnResult
from .loader import load_adventure

WIDTH = 78


def show(result: TurnResult) -> None:
    for style, text in result.output:
        if style == HEADING:
            print("\n" + text.upper())
            continue
        for n, paragraph in enumerate(text.split("\n\n")):
            if n:
                print()
            for line in paragraph.split("\n"):
                print(textwrap.fill(line, WIDTH) if line.strip() else "")
        if style == ENDING:
            print()


def choose_adventure() -> Path | None:
    files = sorted(paths.adventures_dir().glob("*.adv"))
    if not files:
        print("There are no .adv files in", paths.adventures_dir())
        return None
    worlds = [(load_adventure(f), f) for f in files]
    for n, (world, _) in enumerate(worlds, 1):
        mark = "" if world.ok else "  (has errors)"
        print(f"  {n}. {world.title}{mark}")
    choice = input("Which adventure? ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(worlds):
        return worlds[int(choice) - 1][1]
    return None


def handle_meta(game: Game, meta: str) -> Game | None:
    """Do save/load/restart/quit. Returns the game to continue with, or None to quit."""
    world = game.world
    if meta == "save":
        name = input("Save name: ").strip() or game.save_name or "my save"
        saves.write_save(world.path, game.to_save(name))
        game.save_name, game.unsaved = name, False
        print("Saved.")
    elif meta == "load":
        found = saves.list_saves(world.path, world.max_score)
        if not found:
            print("There are no saved games for this adventure yet.")
            return game
        for n, info in enumerate(found, 1):
            print(f"  {n}. {info.label}")
        choice = input("Load which? ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(found):
            game, warnings = Game.from_save(world, saves.read_save(found[int(choice) - 1].path))
            for w in warnings:
                print(w)
            print("\n".join(game.transcript[-15:]))
    elif meta == "restart":
        game = Game(world)
        show(game.start())
    elif meta == "quit":
        return None
    return game


def play(path: Path) -> None:
    world = load_adventure(path)
    if not world.ok:
        print(world.report.format())
        return
    game = Game(world)
    show(game.start())
    while True:
        try:
            line = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        result = game.command(line)
        show(result)
        if result.meta:
            game = handle_meta(game, result.meta)
            if game is None:
                return
        if result.ending:
            try:
                answer = input("\nPlay again? (y/n) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if not answer.startswith("y"):
                return
            game = Game(world)
            show(game.start())


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--check":
        world = load_adventure(argv[1])
        print(f"{world.title}\n")
        print(world.report.format())
        return
    paths.copy_old_data()       # bring along saves from older versions
    path = Path(argv[0]) if argv else choose_adventure()
    if path:
        play(path)


if __name__ == "__main__":
    main(sys.argv[1:])
