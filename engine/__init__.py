"""The text adventure engine: loading, checking and playing .adv files.

Nothing in this package uses tkinter, so it can be tested on its own and
used by any front end.
"""

from .game import Game, TurnResult
from .loader import load_adventure, load_text

__all__ = ["Game", "TurnResult", "load_adventure", "load_text"]
