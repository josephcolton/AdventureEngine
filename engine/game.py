"""Playing an adventure: the game state and what happens each turn.

This module knows nothing about windows or keyboards. A front end (the
tkinter window, the text-mode loop, or a test) calls Game.start() and then
Game.command(line) for each line the player types, and shows the output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .conditions import Condition, compare
from .model import Action, Item, World
from .normalizer import Command, Noun, clean, split_commands
from .vocabulary import (DEFAULT_DARK_TEXT, DIRECTION_NAMES, GENERIC_REPLIES, HELP_TEXT,
                         META_VERBS, NO_NOUN_REPLIES, NO_RESPONSE_VERBS,
                         NOTHING_HAPPENS_VERBS)

SAVE_FORMAT_VERSION = 1
TRANSCRIPT_LINES = 200

# Output styles a front end can show differently.
HEADING, TEXT, ENDING = "heading", "text", "ending"


@dataclass
class TurnResult:
    """What one call to start() or command() produced."""
    output: list = field(default_factory=list)   # [(style, text)]
    meta: str | None = None                       # save / load / restart / quit
    ending: object = None                         # the Ending, if the game just ended

    def say(self, text: str, style: str = TEXT) -> None:
        if text:
            self.output.append((style, text))

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.output)


class Game:
    def __init__(self, world: World):
        if world.normalizer is None:
            raise ValueError("The adventure didn't load.")
        self.world = world
        self.parser = world.normalizer
        self.reset()

    def reset(self) -> None:
        w = self.world
        self.current_room = w.game.start
        self.visited: list[str] = []
        self.item_locations = {i.id: i.location for i in w.items.values()}
        # Items the player has held. Their 'here' text described where they
        # started, so once moved they're described as just lying there.
        self.handled = {i for i, place in self.item_locations.items() if place == "inventory"}
        self.flags: set[str] = set()
        self.score = 0
        self.awarded: set[str] = set()
        self.completed: set[str] = set()
        self.moves = 0
        self.ended: str | None = None
        self.transcript: list[str] = []
        self.history: list[str] = []
        self.last_command: Command | None = None
        self.last_item: str | None = None
        self.pending: tuple[Command, int] | None = None   # waiting for "which one?"
        self.unsaved = False
        self.save_name: str | None = None

    # ==================================================================
    # Things front ends ask about
    # ==================================================================
    @property
    def room(self):
        return self.world.rooms[self.current_room]

    @property
    def max_score(self) -> int:
        return self.world.max_score

    def status(self) -> tuple[str, str]:
        """(room name, 'Score: X / MAX  Moves: N') for the status bar."""
        return (self.room.name,
                f"Score: {self.score} / {self.max_score}    Moves: {self.moves}")

    # ==================================================================
    # Starting and playing
    # ==================================================================
    def start(self) -> TurnResult:
        result = TurnResult()
        result.say(self.world.game.intro)
        self._arrive(result)
        self._log(result)
        return result

    def command(self, line: str) -> TurnResult:
        """Handle one line typed by the player (which may hold several commands)."""
        result = TurnResult()
        line = line.strip()
        if not line:
            return result
        if self.ended:
            result.say("The game is over. You can restart, load a saved game, or "
                       "choose another adventure.")
            return result

        self.transcript.append("> " + line)
        only_meta = True
        for part in split_commands(line):
            if not self._is_meta(part):
                only_meta = False
            self._one(part, result)
            if result.meta or self.ended:
                break
        if not only_meta:
            self.history.append(line)
        self._log(result)
        return result

    def look(self) -> TurnResult:
        """Describe the current room in full, without using up a move."""
        result = TurnResult()
        self._describe(result, full=True)
        return result

    def teleport(self, room_id: str) -> TurnResult:
        """Debug: jump to a room without scoring or marking it visited."""
        self.current_room = room_id
        self.pending = None
        return self.look()

    def replay(self, lines: list[str]) -> None:
        """Re-run earlier commands (used by Reload and Replay)."""
        for line in lines:
            if self.ended:
                break
            self.command(line)

    def _is_meta(self, part: str) -> bool:
        cmd = self.parser.parse(part)
        return bool(cmd and cmd.verb in META_VERBS and not cmd.nouns)

    def _log(self, result: TurnResult) -> None:
        self.transcript.extend(t for _, t in result.output)
        del self.transcript[:-TRANSCRIPT_LINES]

    # ------------------------------------------------------------------
    def _one(self, text: str, result: TurnResult) -> None:
        if self.pending:
            cmd = self._answer_which(text)
            if cmd is not None:
                self._execute(cmd, result)
                return

        cmd = self.parser.parse(text, present=self.is_present, last_item=self.last_item)
        if cmd is None:
            return

        if cmd.verb == "again" and not cmd.nouns:
            if self.last_command is None:
                result.say("There's nothing to repeat.")
                return
            cmd = self.last_command

        if cmd.verb in META_VERBS and not cmd.nouns:
            self._meta(cmd.verb, result)
            return

        for index, noun in enumerate(cmd.nouns):
            if noun.ambiguous:
                names = sorted(self.world.items[i].name for i in noun.ids)
                listed = ", the ".join(names[:-1]) + " or the " + names[-1]
                result.say(f"Which do you mean, the {listed}?")
                self.pending = (cmd, index)
                return

        self._execute(cmd, result)

    def _answer_which(self, text: str) -> Command | None:
        """Use the player's reply to "Which do you mean...?" if it is one."""
        cmd, index = self.pending
        self.pending = None
        choices = cmd.nouns[index].ids
        words = clean(text)
        named = self.parser.lookup(text) & choices
        if not named:     # let a single distinguishing word work: "brass"
            named = {i for i in choices
                     if words and all(w in clean(self.world.items[i].name) for w in words)}
        if len(named) == 1:
            item_id = next(iter(named))
            return cmd.with_noun(index, Noun("item", cmd.nouns[index].word,
                                             frozenset({item_id})))
        return None

    def _meta(self, verb: str, result: TurnResult) -> None:
        if verb == "score":
            result.say(f"Your score is {self.score} out of {self.max_score}, "
                       f"in {self.moves} move{'s' if self.moves != 1 else ''}.")
        elif verb == "exits":
            result.say(self.exits_text())
        elif verb == "hint":
            result.say(self.hint_text())
        elif verb == "help":
            result.say(HELP_TEXT)
        else:
            result.meta = verb      # the front end handles save/load/restart/quit

    def _execute(self, cmd: Command, result: TurnResult) -> None:
        self.last_command = cmd
        for noun in cmd.nouns:
            if noun.kind == "item" and len(noun.ids) == 1:
                self.last_item = next(iter(noun.ids))
                break

        handled, counts, end_id = self._try_actions(cmd, result)
        if not handled:
            counts = self._builtin(cmd, result)
        if not counts:
            return
        self.moves += 1
        self.unsaved = True
        if end_id:
            self._finish(end_id, result)
        else:
            self._check_endings(result)

    # ==================================================================
    # Author actions
    # ==================================================================
    def _try_actions(self, cmd: Command, result: TurnResult):
        """Returns (handled, counts as a move, ending id)."""
        here = [a for a in self.world.actions if a.applies_in(self.current_room)]
        # Try an exact match first; only if nothing matches, ignore describing
        # words ("tie rope to the old willow" -> "tie rope to willow").
        candidates = ([a for a in here if a.matches(cmd)]
                      or [a for a in here if a.matches(cmd, loose=True)])
        live = []
        for action in candidates:
            if action.once and action.id in self.completed:
                if action.done:
                    result.say(action.done)
                    return True, True, None
                continue        # used up, and no 'done': as if it didn't exist
            live.append(action)
            if self.check(action.conditions):
                return True, True, self._run(action, cmd, result)
        for action in live:
            if action.fail:
                result.say(action.fail)
                return True, True, None
        return False, False, None

    def _run(self, action: Action, cmd: Command, result: TurnResult) -> str:
        result.say(action.message)
        for item_id, place in action.moves:
            destination = self.current_room if place == "here" else place
            if destination == "inventory":
                self._pick_up(item_id)
            else:
                self.item_locations[item_id] = destination
        self.flags.update(action.set_flags)
        self.flags.difference_update(action.clear_flags)
        self._award(f"action:{action.id}", action.score)
        self.completed.add(action.id)
        if action.go:
            self.current_room = action.go
            self._arrive(result)
        elif cmd.is_movement:
            self._walk(cmd.direction, result)
        return action.end

    # ==================================================================
    # Conditions and helpers
    # ==================================================================
    def check(self, conditions: list[Condition] | None) -> bool:
        return all(self._test(c) for c in conditions or [])

    def _test(self, c: Condition) -> bool:
        if c.kind == "has":
            value = self.item_locations.get(c.arg) == "inventory"
        elif c.kind == "here":
            value = self.is_present(c.arg)
        elif c.kind == "flag":
            value = c.arg in self.flags
        elif c.kind == "in":
            value = self.current_room == c.arg
        elif c.kind == "visited":
            value = c.arg in self.visited
        elif c.kind == "score":
            value = compare(self.score, c.op, c.number)
        else:
            value = compare(self.moves, c.op, c.number)
        return value != c.negated

    def is_present(self, item_id: str) -> bool:
        return self.item_locations.get(item_id) in ("inventory", self.current_room)

    def exits_text(self) -> str:
        """'Obvious exits: north, east, down.' Ways opened by actions aren't listed."""
        if not self.is_lit():
            return "It's too dark to see the way out."
        found = [d for d in DIRECTION_NAMES if d in self.room.exits]
        if not found:
            return "There are no obvious exits."
        return "Obvious exits: " + ", ".join(found) + "."

    def hint_text(self) -> str:
        """The room's hint: the first 'hint when' that's true, else the plain 'hint'."""
        hint = self._pick(self.room.hint_variants, self.room.hint)
        return hint or ("There's no hint for this spot. Try examining the things "
                        "around you, and type exits to see which ways you can go.")

    def is_lit(self) -> bool:
        if not self.room.dark:
            return True
        return any(item.light and self.is_present(item.id)
                   for item in self.world.items.values())

    def inventory(self) -> list[Item]:
        return [i for i in self.world.items.values()
                if self.item_locations[i.id] == "inventory"]

    def _pick_up(self, item_id: str) -> None:
        self.item_locations[item_id] = "inventory"
        self.handled.add(item_id)
        self._award(f"item:{item_id}", self.world.items[item_id].points)

    def here_text(self, item: Item) -> str:
        """The sentence for an item lying in the room."""
        if item.id in self.handled:
            if item.dropped:
                return item.dropped
            if item.name[:1].isupper():
                return f"{item.name} is here."
            article = "an" if item.name[:1].lower() in "aeiou" else "a"
            return f"There is {article} {item.name} here."
        return self._pick(item.here_variants, item.here)

    def _award(self, key: str, points: int) -> None:
        if points and key not in self.awarded:
            self.awarded.add(key)
            self.score += points

    def _pick(self, variants, plain: str) -> str:
        for conditions, text, _ in variants:
            if self.check(conditions):
                return text
        return plain

    # ==================================================================
    # Rooms and movement
    # ==================================================================
    def _arrive(self, result: TurnResult) -> None:
        """Describe the room the player has just entered."""
        first_time = self.current_room not in self.visited
        if first_time:
            self.visited.append(self.current_room)
            self._award(f"room:{self.current_room}", self.room.points)
        self._describe(result, full=first_time)

    def _describe(self, result: TurnResult, full: bool) -> None:
        room = self.room
        result.say(room.name, HEADING)
        if not self.is_lit():
            result.say(room.dark_text or DEFAULT_DARK_TEXT)
            return
        text = room.first if full else (room.again or room.first)
        extras = [t for conds, t, _ in room.extras if self.check(conds)]
        if extras:
            text = (text + " " if text else "") + " ".join(extras)
        result.say(text)
        for item in self.world.items.values():
            if self.item_locations[item.id] == room.id:
                result.say(self.here_text(item))

    def _walk(self, direction: str, result: TurnResult) -> None:
        exit_ = self.room.exits.get(direction)
        if not exit_:
            result.say("You can't go that way.")
            return
        self.current_room = exit_[0]
        self._arrive(result)

    # ==================================================================
    # Endings
    # ==================================================================
    def _check_endings(self, result: TurnResult) -> None:
        for ending in self.world.endings.values():
            if ending.conditions is not None and self.check(ending.conditions):
                self._finish(ending.id, result)
                return

    def _finish(self, ending_id: str, result: TurnResult) -> None:
        ending = self.world.endings[ending_id]
        self.ended = ending_id
        result.ending = ending
        result.say(ending.text, ENDING)
        result.say(f"You scored {self.score} out of {self.max_score} in "
                   f"{self.moves} move{'s' if self.moves != 1 else ''}.", ENDING)

    # ==================================================================
    # Built-in commands. Each returns True if the turn counts as a move.
    # ==================================================================
    def _builtin(self, cmd: Command, result: TurnResult) -> bool:
        verb = cmd.verb
        if verb not in self.world.known_verbs:
            item_ids = self.parser.lookup(verb)
            if item_ids:
                name = self.world.items[sorted(item_ids)[0]].name
                result.say(f"What do you want to do with the {name}?")
            else:
                result.say(f"I don't know the word \"{verb}\".")
            return False
        # Built-in commands never care about describing words: "take the
        # shiny key" is just "take key".
        cmd = cmd.plain()
        handler = getattr(self, f"_do_{verb}", None)
        if handler:
            return handler(cmd, result)
        return self._do_other(cmd, result)

    def _visible(self, noun: Noun, result: TurnResult) -> str | None:
        """The item this noun means, if the player can see it; else explain why not."""
        if noun.kind == "item":
            here = [i for i in noun.ids if self.is_present(i)]
            if here:
                item_id = here[0]
                if self.item_locations[item_id] != "inventory" and not self.is_lit():
                    result.say("It's too dark to see that.")
                    return None
                return item_id
        result.say(f"You don't see any \"{noun.word}\" here.")
        return None

    def _need_noun(self, cmd: Command, result: TurnResult) -> bool:
        if cmd.nouns:
            return True
        result.say(f"What do you want to {cmd.verb}?")
        return False

    def _do_go(self, cmd: Command, result: TurnResult) -> bool:
        if cmd.direction:
            self._walk(cmd.direction, result)
            return True
        if not cmd.nouns:
            result.say("Where do you want to go?")
            return False
        result.say("Which direction? (north, south, east, west, up, down, in or out)")
        return False

    def _do_look(self, cmd: Command, result: TurnResult) -> bool:
        self._describe(result, full=True)
        return True

    def _do_examine(self, cmd: Command, result: TurnResult) -> bool:
        if not self._need_noun(cmd, result):
            return False
        item_id = self._visible(cmd.nouns[0], result)
        if item_id:
            item = self.world.items[item_id]
            text = self._pick(item.examine_variants, item.examine)
            result.say(text or f"You see nothing special about the {item.name}.")
        return True

    def _do_take(self, cmd: Command, result: TurnResult) -> bool:
        if not self._need_noun(cmd, result):
            return False
        if cmd.nouns[0].kind == "word" and cmd.nouns[0].word in ("all", "everything"):
            return self._take_all(result)
        for noun in cmd.nouns:
            item_id = self._visible(noun, result)
            if not item_id:
                continue
            item = self.world.items[item_id]
            if self.item_locations[item_id] == "inventory":
                result.say(f"You already have the {item.name}.")
            elif not item.takeable:
                result.say(item.take_fail or "You can't take that.")
            else:
                self._pick_up(item_id)
                result.say("Taken.")
        return True

    def _take_all(self, result: TurnResult) -> bool:
        if not self.is_lit():
            result.say("It's too dark to find anything.")
            return True
        found = [i for i in self.world.items.values()
                 if self.item_locations[i.id] == self.current_room and i.takeable]
        if not found:
            result.say("There's nothing here to take.")
        for item in found:
            self._pick_up(item.id)
            result.say(f"{item.name}: Taken.")
        return True

    def _do_drop(self, cmd: Command, result: TurnResult) -> bool:
        if not self._need_noun(cmd, result):
            return False
        if cmd.nouns[0].kind == "word" and cmd.nouns[0].word in ("all", "everything"):
            held = self.inventory()
            if not held:
                result.say("You aren't carrying anything.")
            for item in held:
                self.item_locations[item.id] = self.current_room
                result.say(f"{item.name}: Dropped.")
            return True
        for noun in cmd.nouns:
            held = [i for i in noun.ids if self.item_locations.get(i) == "inventory"]
            if held:
                self.item_locations[held[0]] = self.current_room
                result.say("Dropped.")
            else:
                result.say(f"You aren't carrying any \"{noun.word}\".")
        return True

    def _do_inventory(self, cmd: Command, result: TurnResult) -> bool:
        held = self.inventory()
        if held:
            result.say("You are carrying:\n" + "\n".join(f"  {i.name}" for i in held))
        else:
            result.say("You are empty-handed.")
        return True

    def _do_wait(self, cmd: Command, result: TurnResult) -> bool:
        result.say("Time passes.")
        return True

    def _do_other(self, cmd: Command, result: TurnResult) -> bool:
        """Any understood verb that no action or built-in handles."""
        if not cmd.nouns:
            if cmd.verb in NO_NOUN_REPLIES:
                result.say(NO_NOUN_REPLIES[cmd.verb])
                return True
            return self._need_noun(cmd, result)
        for noun in cmd.nouns:
            if noun.kind == "direction":
                continue
            if not self._visible(noun, result):
                return True
        if cmd.verb in NOTHING_HAPPENS_VERBS:
            result.say("Nothing happens.")
        elif cmd.verb in NO_RESPONSE_VERBS:
            result.say("There's no response.")
        else:
            result.say(GENERIC_REPLIES[self.moves % len(GENERIC_REPLIES)])
        return True

    # ==================================================================
    # Saving and loading
    # ==================================================================
    def to_save(self, save_name: str) -> dict:
        w = self.world
        return {
            "format_version": SAVE_FORMAT_VERSION,
            "adventure_file": w.path.name if w.path else "",
            "adventure_title": w.title,
            "adventure_fingerprint": w.fingerprint,
            "save_name": save_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "current_room": self.current_room,
            "room_name": self.room.name,
            "visited_rooms": list(self.visited),
            "item_locations": dict(self.item_locations),
            "handled_items": sorted(self.handled),
            "flags": sorted(self.flags),
            "score": self.score,
            "awarded": sorted(self.awarded),
            "completed_actions": sorted(self.completed),
            "moves": self.moves,
            "ended": self.ended,
            "command_history": list(self.history),
            "transcript": list(self.transcript[-TRANSCRIPT_LINES:]),
        }

    @classmethod
    def from_save(cls, world: World, data: dict) -> tuple["Game", list[str]]:
        """Rebuild a game from save data. Returns (game, warnings)."""
        game = cls(world)
        warnings = []
        if data.get("adventure_fingerprint") != world.fingerprint:
            warnings.append("This adventure has been edited since you saved. "
                            "The save may not work correctly.")
        rooms, items = world.rooms, world.items
        room = data.get("current_room")
        game.current_room = room if room in rooms else world.game.start
        game.visited = [r for r in data.get("visited_rooms", []) if r in rooms]
        for item_id, place in data.get("item_locations", {}).items():
            if item_id in items and (place in rooms or place in ("inventory", "nowhere")):
                game.item_locations[item_id] = place
        if "handled_items" in data:
            game.handled = {i for i in data["handled_items"] if i in items}
        else:   # older saves: at least what's being carried has been handled
            game.handled = {i for i, place in game.item_locations.items()
                            if place == "inventory"}
        game.flags = set(data.get("flags", []))
        game.score = int(data.get("score", 0))
        game.awarded = set(data.get("awarded", []))
        game.completed = set(data.get("completed_actions", []))
        game.moves = int(data.get("moves", 0))
        game.ended = data.get("ended") if data.get("ended") in world.endings else None
        game.history = list(data.get("command_history", []))
        game.transcript = list(data.get("transcript", []))
        game.save_name = data.get("save_name")
        return game, warnings
