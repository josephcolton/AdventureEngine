"""Builds a World from an .adv file: reads every section and setting.

Problems are added to world.report. Loading always returns a World (even a
broken one) so the start screen can still show the adventure's title.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from collections import Counter
from pathlib import Path

from .conditions import ConditionError, parse_conditions
from .model import Action, Ending, GameInfo, Item, Room, World
from .normalizer import Normalizer
from .report import Report
from .textfile import Section, decode, parse_text
from .validator import validate
from .vocabulary import DIRECTIONS, KNOWN_VERBS

ALLOWED_KEYS = {
    "game": {"title", "author", "description", "start", "intro", "max_score"},
    "room": {"name", "first", "again", "exits", "points", "score", "dark",
             "dark_text", "when", "hint", "hint when"},
    "item": {"name", "aliases", "location", "here", "examine", "take", "take_fail",
             "points", "score", "light", "here when", "examine when", "dropped"},
    "action": {"id", "also", "where", "if", "fail", "message", "go", "score",
               "points", "set", "clear", "move", "end", "once", "done"},
    "ending": {"type", "when", "text"},
}
REPEATABLE_KEYS = {"when", "here when", "examine when", "hint when", "also"}

_ID = re.compile(r"^[a-z0-9_]+$")
_YES = {"yes", "y", "true", "on"}
_NO = {"no", "n", "false", "off"}


def load_adventure(path: str | Path) -> World:
    path = Path(path)
    data = path.read_bytes()
    world = World(path=path, fingerprint=hashlib.sha256(data).hexdigest())
    report = world.report
    sections = parse_text(decode(data, report), report)
    _Builder(world, report).build(sections)
    validate(world)
    return world


def load_text(text: str, name: str = "test.adv") -> World:
    """Load an adventure from a string (handy for tests)."""
    data = text.encode("utf-8")
    world = World(path=Path(name), fingerprint=hashlib.sha256(data).hexdigest())
    sections = parse_text(text, world.report)
    _Builder(world, world.report).build(sections)
    validate(world)
    return world


def make_id(raw: str) -> str:
    return re.sub(r"\s+", "_", raw.strip().lower())


def pretty(item_or_room_id: str) -> str:
    return item_or_room_id.replace("_", " ")


class _Builder:
    def __init__(self, world: World, report: Report):
        self.world = world
        self.report = report

    # ------------------------------------------------------------------
    def build(self, sections: list[Section]) -> None:
        games = [s for s in sections if s.kind == "game"]
        if not games:
            self.report.error(None, "The file has no [game] section. Every adventure "
                              "needs one, with at least a title and a start room.")
        for extra in games[1:]:
            self.report.error(extra.line, "There is more than one [game] section. "
                              "Only one is allowed.")
        for section in sections:
            self._check_keys(section)
            if section.kind == "game" and section is games[0]:
                self._game(section)
            elif section.kind == "room":
                self._room(section)
            elif section.kind == "item":
                self._item(section)
            elif section.kind == "ending":
                self._ending(section)
            elif section.kind == "vocabulary":
                self._vocabulary(section)

        aliases = {i.id: i.aliases for i in self.world.items.values()}
        vocab = [(word, other) for word, other, _ in self.world.vocabulary]
        self.world.normalizer = Normalizer(aliases, vocab)

        for section in sections:
            if section.kind == "action":
                self._action(section)
        self._name_actions()
        self.world.known_verbs = set(KNOWN_VERBS) | {
            c.verb for a in self.world.actions for c in a.commands}

    # ------------------------------------------------------------------
    def _check_keys(self, section: Section) -> None:
        allowed = ALLOWED_KEYS.get(section.kind)
        if allowed is None:          # [vocabulary] keys are words, anything goes
            return
        for entry in section.entries:
            if entry.key in allowed:
                continue
            if entry.key == "when" and section.kind == "room":
                continue
            if section.kind == "room" and entry.key in ("here when", "examine when"):
                self.report.warning(entry.line, f"'{entry.key}' lines belong in an "
                                    f"[item] section, not a room. Use 'when' in rooms.")
                continue
            guess = difflib.get_close_matches(entry.key, sorted(allowed), n=1)
            hint = f" Did you mean '{guess[0]}'?" if guess else ""
            self.report.warning(entry.line, f"'{entry.key}' isn't a setting I know in "
                                f"a [{section.kind}] section, so it will be ignored.{hint}")
        counts = Counter(e.key for e in section.entries
                         if e.key not in REPEATABLE_KEYS)
        if "points" in counts and "score" in counts:
            self.report.warning(section.line, f"{section.label} has both 'points' and "
                                f"'score'. They mean the same thing; only one is used.")
        for key, n in counts.items():
            if n > 1:
                line = section.all(key)[-1].line
                self.report.warning(line, f"'{key}' appears {n} times in "
                                    f"{section.label}. Only the last one is used.")

    def _id(self, section: Section) -> str | None:
        ident = make_id(section.name)
        if not _ID.match(ident):
            self.report.error(section.line, f"The name '{section.name}' can only contain "
                              f"letters, numbers, spaces and underscores.")
            return None
        return ident

    def _int(self, section: Section, *keys: str) -> int:
        for key in keys:
            entry = section.last(key)
            if entry:
                try:
                    return int(entry.value)
                except ValueError:
                    self.report.error(entry.line, f"'{key}' should be a whole number, "
                                      f"but it is '{entry.value}'.")
        return 0

    def _bool(self, section: Section, key: str, default: bool) -> bool:
        entry = section.last(key)
        if not entry:
            return default
        word = entry.value.strip().lower()
        if word in _YES:
            return True
        if word in _NO:
            return False
        self.report.error(entry.line, f"'{key}' should be yes or no, but it is "
                          f"'{entry.value}'.")
        return default

    def _conditions(self, text: str, line: int) -> list:
        try:
            return parse_conditions(text)
        except ConditionError as problem:
            self.report.error(line, f"Malformed condition. {problem}")
            return []

    def _variants(self, section: Section, key: str) -> list:
        variants = []
        for e in section.all(key):
            if e.condition_text is None:
                self.report.error(e.line, f"This '{key}' line needs a condition before "
                                  f"the =, for example: {key} flag door_open = The door "
                                  f"stands open.")
                continue
            variants.append((self._conditions(e.condition_text, e.line), e.value, e.line))
        return variants

    @staticmethod
    def _list(text: str) -> list[str]:
        return [part.strip() for part in text.split(",") if part.strip()]

    # ------------------------------------------------------------------
    def _game(self, s: Section) -> None:
        g = GameInfo(
            title=s.value("title"), author=s.value("author"),
            description=s.value("description"), start=make_id(s.value("start")),
            intro=s.value("intro"),
            lines={e.key: e.line for e in s.entries},
        )
        if s.last("max_score"):
            g.max_score = self._int(s, "max_score")
        if not g.title:
            self.report.error(s.line, "The [game] section needs a title, "
                              "for example: title = The Riverbank")
        if not g.start:
            self.report.error(s.line, "The [game] section needs a start room, "
                              "for example: start = kitchen")
        self.world.game = g

    def _room(self, s: Section) -> None:
        ident = self._id(s)
        if ident is None:
            return
        if ident in self.world.rooms:
            self.report.error(s.line, f"There are two rooms called '{ident}' "
                              f"(the other is on line {self.world.rooms[ident].line}).")
            return
        room = Room(
            id=ident, name=s.value("name") or pretty(ident).title(),
            first=s.value("first"), again=s.value("again"),
            points=self._int(s, "points", "score"),
            dark=self._bool(s, "dark", False), dark_text=s.value("dark_text"),
            extras=self._variants(s, "when"), hint=s.value("hint"),
            hint_variants=self._variants(s, "hint when"), line=s.line,
        )
        if not room.first:
            self.report.warning(s.line, f"Room '{ident}' has no description. "
                                f"Add a line like: first = A small, cozy room.")
        exits = s.last("exits")
        if exits:
            room.exits = self._exits(exits.value, exits.line)
        self.world.rooms[ident] = room

    def _exits(self, text: str, line: int) -> dict:
        exits = {}
        for part in self._list(text):
            if ":" not in part:
                self.report.error(line, f"The exit '{part}' should look like "
                                  f"'north: kitchen' (a direction, a colon, then a room).")
                continue
            word, target = (x.strip() for x in part.split(":", 1))
            direction = DIRECTIONS.get(word.lower())
            if direction is None:
                self.report.error(line, f"'{word}' isn't a direction. Use north, south, "
                                  f"east, west, northeast, northwest, southeast, "
                                  f"southwest, up, down, in or out.")
                continue
            if direction in exits:
                self.report.warning(line, f"The direction '{direction}' is listed "
                                    f"twice in these exits.")
            exits[direction] = (make_id(target), line)
        return exits

    def _item(self, s: Section) -> None:
        ident = self._id(s)
        if ident is None:
            return
        if ident in self.world.items:
            self.report.error(s.line, f"There are two items called '{ident}' "
                              f"(the other is on line {self.world.items[ident].line}).")
            return
        name = s.value("name") or pretty(ident)
        aliases = [name, pretty(ident), ident] + self._list(s.value("aliases"))
        location = make_id(s.value("location"))
        if not s.last("location"):
            self.report.warning(s.line, f"Item '{ident}' has no location, so it starts "
                                f"out of the game ('nowhere'). Add a line like: "
                                f"location = kitchen")
            location = "nowhere"
        item = Item(
            id=ident, name=name, aliases=aliases, location=location,
            here=s.value("here"), here_variants=self._variants(s, "here when"),
            dropped=s.value("dropped"),
            examine=s.value("examine"), examine_variants=self._variants(s, "examine when"),
            takeable=self._bool(s, "take", True), take_fail=s.value("take_fail"),
            points=self._int(s, "points", "score"), light=self._bool(s, "light", False),
            line=s.line, lines={e.key: e.line for e in s.entries},
        )
        self.world.items[ident] = item

    def _ending(self, s: Section) -> None:
        ident = self._id(s)
        if ident is None:
            return
        if ident in self.world.endings:
            self.report.error(s.line, f"There are two endings called '{ident}' "
                              f"(the other is on line {self.world.endings[ident].line}).")
            return
        kind = s.value("type").strip().lower()
        if kind not in ("win", "lose"):
            entry = s.last("type")
            self.report.error(entry.line if entry else s.line,
                              f"Ending '{ident}' needs 'type = win' or 'type = lose'.")
        when = s.last("when")
        conditions = None
        if when and when.condition_text is not None:
            self.report.error(when.line, "In an ending, write the conditions after the "
                              "=, for example: when = has locket, in riverbank")
        elif when:
            conditions = self._conditions(when.value, when.line)
        self.world.endings[ident] = Ending(ident, kind, conditions, s.value("text"), s.line)

    def _vocabulary(self, s: Section) -> None:
        for entry in s.entries:
            for other in self._list(entry.value):
                self.world.vocabulary.append((entry.key, other, entry.line))

    def _action(self, s: Section) -> None:
        lines = {e.key: e.line for e in s.entries}
        action = Action(id=make_id(s.value("id")), phrase=s.name, line=s.line, lines=lines)
        for entry in s.all("also"):
            action.also.extend(self._list(entry.value))

        normalizer = self.world.normalizer
        for phrase in [action.phrase] + action.also:
            command = normalizer.parse(phrase)
            if command is None:
                self.report.error(lines.get("also", s.line),
                                  f"The phrase '{phrase}' has no words I can use.")
            else:
                action.commands.append(command)

        where = s.value("where").strip()
        if not where:
            self.report.error(s.line, f"[action: {s.name}] needs a 'where' line saying "
                              f"which room(s) it works in, or 'where = anywhere'.")
            action.where = []
        elif where.lower() != "anywhere":
            action.where = [make_id(w) for w in self._list(where)]

        action.conditions = self._conditions(s.value("if"), lines.get("if", s.line))
        action.fail = s.value("fail")
        action.message = s.value("message")
        action.go = make_id(s.value("go"))
        action.score = self._int(s, "score", "points")
        action.set_flags = [make_id(f) for f in self._list(s.value("set"))]
        action.clear_flags = [make_id(f) for f in self._list(s.value("clear"))]
        action.end = make_id(s.value("end"))
        action.once = self._bool(s, "once", False)
        action.done = s.value("done")
        for part in self._list(s.value("move")):
            m = re.match(r"^(.+?)\s+to\s+(.+)$", part, re.IGNORECASE)
            if not m:
                self.report.error(lines.get("move"), f"'{part}' should look like "
                                  f"'lamp to inventory' (an item, the word 'to', "
                                  f"then a room, here, inventory or nowhere).")
                continue
            action.moves.append((make_id(m.group(1)), make_id(m.group(2))))
        self.world.actions.append(action)

    def _name_actions(self) -> None:
        """Give every action an id, generating one where the author didn't."""
        seen: dict[str, int] = {}
        explicit: dict[str, int] = {}
        for action in self.world.actions:
            if action.id:
                if action.id in explicit:
                    self.report.error(action.lines.get("id"), f"Two actions use the id "
                                      f"'{action.id}' (the other is on line "
                                      f"{explicit[action.id]}). Each id must be different.")
                explicit[action.id] = action.lines.get("id", action.line)
                continue
            form = action.commands[0].form if action.commands else make_id(action.phrase)
            place = action.where[0] if action.where else "anywhere"
            base = f"{form}@{place}"
            seen[base] = seen.get(base, 0) + 1
            action.id = base if seen[base] == 1 else f"{base}#{seen[base]}"
