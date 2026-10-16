"""The pieces of an adventure once it has been read from its file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .conditions import Condition
from .normalizer import Command, Normalizer
from .report import Report

# A piece of text that is only used when its conditions are true.
Variant = tuple  # (list[Condition], str, line)


@dataclass
class GameInfo:
    title: str = ""
    author: str = ""
    description: str = ""
    start: str = ""
    intro: str = ""
    max_score: int | None = None
    lines: dict = field(default_factory=dict)


@dataclass
class Room:
    id: str
    name: str
    first: str = ""
    again: str = ""
    exits: dict = field(default_factory=dict)      # direction -> (room id, line)
    points: int = 0
    dark: bool = False
    dark_text: str = ""
    extras: list = field(default_factory=list)     # [Variant]
    line: int = 0


@dataclass
class Item:
    id: str
    name: str
    aliases: list = field(default_factory=list)
    location: str = "nowhere"
    here: str = ""
    here_variants: list = field(default_factory=list)
    examine: str = ""
    examine_variants: list = field(default_factory=list)
    takeable: bool = True
    take_fail: str = ""
    points: int = 0
    light: bool = False
    line: int = 0
    lines: dict = field(default_factory=dict)


@dataclass
class Action:
    id: str
    phrase: str
    also: list = field(default_factory=list)
    commands: list = field(default_factory=list)   # normalized phrase + also
    where: list | None = None                      # None means anywhere
    conditions: list = field(default_factory=list)
    fail: str = ""
    message: str = ""
    go: str = ""
    score: int = 0
    set_flags: list = field(default_factory=list)
    clear_flags: list = field(default_factory=list)
    moves: list = field(default_factory=list)      # [(item id, place)]
    end: str = ""
    once: bool = False
    done: str = ""
    line: int = 0
    lines: dict = field(default_factory=dict)

    def applies_in(self, room_id: str) -> bool:
        return self.where is None or room_id in self.where

    def matches(self, command: Command, loose: bool = False) -> bool:
        return any(c.matches(command, loose) for c in self.commands)


@dataclass
class Ending:
    id: str
    type: str                      # "win" or "lose"
    conditions: list | None = None
    text: str = ""
    line: int = 0


@dataclass
class World:
    """Everything read from one .adv file."""
    path: Path | None = None
    fingerprint: str = ""
    report: Report = field(default_factory=Report)
    game: GameInfo = field(default_factory=GameInfo)
    rooms: dict = field(default_factory=dict)
    items: dict = field(default_factory=dict)
    actions: list = field(default_factory=list)
    endings: dict = field(default_factory=dict)
    vocabulary: list = field(default_factory=list)  # (word, other word, line)
    normalizer: Normalizer | None = None
    known_verbs: set = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.report.has_errors

    @property
    def title(self) -> str:
        if self.game.title:
            return self.game.title
        return self.path.stem if self.path else "Untitled"

    @property
    def total_points(self) -> int:
        return (sum(r.points for r in self.rooms.values())
                + sum(i.points for i in self.items.values())
                + sum(a.score for a in self.actions))

    @property
    def max_score(self) -> int:
        if self.game.max_score is not None:
            return self.game.max_score
        return self.total_points


def all_conditions(world: World):
    """Every (condition, line) anywhere in the adventure, for the validator."""
    for room in world.rooms.values():
        for conds, _, line in room.extras:
            for c in conds:
                yield c, line
    for item in world.items.values():
        for conds, _, line in item.here_variants + item.examine_variants:
            for c in conds:
                yield c, line
    for action in world.actions:
        for c in action.conditions:
            yield c, action.lines.get("if", action.line)
    for ending in world.endings.values():
        for c in ending.conditions or []:
            yield c, ending.line
