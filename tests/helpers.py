"""Shared bits for the tests."""

import textwrap
from pathlib import Path

from engine import Game, load_text

ROOT = Path(__file__).resolve().parent.parent
ADVENTURES = ROOT / "adventures"

# A small adventure used by many tests. Kept deliberately plain.
BASIC = """
[game]
title = Test Yard
start = yard

[room: yard]
name = Back Yard
first = A tidy yard. A shed stands to the east.
again = The yard.
exits = east: shed, north: cellar
points = 1

[room: shed]
name = Tool Shed
first = Dusty shelves.
exits = west: yard

[room: cellar]
name = Cellar
first = Damp stone walls.
dark = yes
exits = south: yard

[item: key]
name = brass key
aliases = key
location = yard
here = A brass key glints in the grass.
points = 10

[item: iron_key]
name = iron key
aliases = key
location = shed
here = An iron key hangs on a nail.

[item: lamp]
name = lamp
location = shed
here = A lamp sits on a shelf.
light = yes

[item: hammer]
name = hammer
location = cellar
here = A hammer lies in the corner.
points = 40

[action: go east]
where = yard
if = has key
fail = The shed door is locked.
message = You unlock the shed door.

[ending: done]
type = win
when = has hammer, in yard
text = Well done!
"""


def world_from(text: str):
    return load_text(textwrap.dedent(text))


def game_from(text: str) -> Game:
    world = world_from(text)
    assert world.ok, world.report.format()
    game = Game(world)
    game.start()
    return game


def run(game: Game, *commands: str) -> str:
    """Run commands and return the text of the last one."""
    result = None
    for c in commands:
        result = game.command(c)
    return result.text if result else ""
