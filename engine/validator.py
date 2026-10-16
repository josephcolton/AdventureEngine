"""Checks an adventure for mistakes ("Check Adventure").

Errors stop the game from starting; warnings point at things that look
wrong but don't stop play; notes are purely informational.
"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from .vocabulary import KNOWN_VERBS, META_VERBS

if TYPE_CHECKING:
    from .model import World

PLACES = ("inventory", "nowhere")


def _hint(name: str, choices) -> str:
    guess = difflib.get_close_matches(name, sorted(choices), n=1, cutoff=0.6)
    return f" Did you mean '{guess[0]}'?" if guess else ""


def validate(world: "World") -> None:
    report = world.report
    rooms, items, endings = world.rooms, world.items, world.endings

    def room_exists(room_id: str, line, what: str) -> bool:
        if room_id in rooms:
            return True
        report.error(line, f"{what} refers to a room called '{room_id}', but there is "
                     f"no such room.{_hint(room_id, rooms)}")
        return False

    def item_exists(item_id: str, line, what: str) -> bool:
        if item_id in items:
            return True
        report.error(line, f"{what} refers to an item called '{item_id}', but there is "
                     f"no such item.{_hint(item_id, items)}")
        return False

    # --- the [game] section ---
    start = world.game.start
    if start and start not in rooms:
        report.error(world.game.lines.get("start"), f"The start room '{start}' doesn't "
                     f"exist.{_hint(start, rooms)}")
    if world.game.max_score is not None and world.game.max_score != world.total_points:
        report.warning(world.game.lines.get("max_score"),
                       f"max_score is {world.game.max_score}, but the points available "
                       f"in the adventure add up to {world.total_points}. You can delete "
                       f"the max_score line and the game will work it out for you.")

    # --- rooms and exits ---
    for room in rooms.values():
        for direction, (target, line) in room.exits.items():
            room_exists(target, line, f"The '{direction}' exit from room '{room.id}'")

    # --- items ---
    for item in items.values():
        loc = item.location
        if loc not in PLACES and loc not in rooms:
            room_exists(loc, item.lines.get("location", item.line),
                        f"The location of item '{item.id}'")

    # --- actions ---
    # A verb the author lists on the left of [vocabulary] counts as known:
    # she has already given it other ways of saying it.
    declared = {word.split()[0].lower() for word, _, _ in world.vocabulary if word.split()}
    for action in world.actions:
        label = f"[action: {action.phrase}]"
        lines = action.lines
        for room_id in action.where or []:
            room_exists(room_id, lines.get("where", action.line), f"The 'where' of {label}")
        if action.go:
            room_exists(action.go, lines.get("go"), f"The 'go' of {label}")
        for item_id, place in action.moves:
            item_exists(item_id, lines.get("move"), f"The 'move' of {label}")
            if place not in PLACES + ("here",) and place not in rooms:
                room_exists(place, lines.get("move"), f"The 'move' of {label}")
        if action.end and action.end not in endings:
            report.error(lines.get("end"), f"The 'end' of {label} refers to an ending "
                         f"called '{action.end}', but there is no such ending."
                         f"{_hint(action.end, endings)}")
        for command in action.commands:
            if command.verb not in KNOWN_VERBS and command.verb not in declared:
                report.warning(action.line, f"The phrase '{command.text}' starts with "
                               f"'{command.verb}', which isn't a word the game already "
                               f"knows. It will still work when typed that way, but you "
                               f"may want to add other ways of saying it in [vocabulary].")
            elif command.verb in META_VERBS and not command.nouns:
                report.warning(action.line, f"'{command.text}' is a built-in command "
                               f"(like save or quit), so this action can never happen.")

    # --- conditions everywhere ---
    from .model import all_conditions
    checked_flags: dict[str, int] = {}
    for cond, line in all_conditions(world):
        if cond.refers_to_item:
            item_exists(cond.arg, line, f"The condition '{cond.text}'")
        elif cond.refers_to_room:
            room_exists(cond.arg, line, f"The condition '{cond.text}'")
        elif cond.kind == "flag":
            checked_flags.setdefault(cond.arg, line)

    set_flags: dict[str, int] = {}
    for action in world.actions:
        for flag in action.set_flags:
            set_flags.setdefault(flag, action.lines.get("set", action.line))
    for flag, line in checked_flags.items():
        if flag not in set_flags:
            report.warning(line, f"The flag '{flag}' is checked but never set by any "
                           f"action, so it will always be off. Is it misspelled?"
                           f"{_hint(flag, set_flags)}")
    for flag, line in set_flags.items():
        if flag not in checked_flags:
            report.warning(line, f"The flag '{flag}' is set but never checked anywhere. "
                           f"Is it misspelled?{_hint(flag, checked_flags)}")

    # --- endings ---
    if not any(e.type == "win" for e in endings.values()):
        report.error(None, "There is no winning ending. Add an [ending: ...] section "
                     "with 'type = win'.")

    # --- items that never appear ---
    brought_in = {item_id for a in world.actions for item_id, place in a.moves
                  if place != "nowhere"}
    for item in items.values():
        if item.location == "nowhere" and item.id not in brought_in:
            report.warning(item.line, f"Item '{item.id}' starts 'nowhere' and no action "
                           f"ever moves it into the game, so the player can never see it.")

    # --- rooms the player can't reach ---
    if start in rooms:
        reached = {start}
        frontier = [start]
        anywhere_goes = [a.go for a in world.actions if a.where is None and a.go]
        for target in anywhere_goes:
            if target in rooms and target not in reached:
                reached.add(target)
                frontier.append(target)
        while frontier:
            room_id = frontier.pop()
            targets = [t for t, _ in rooms[room_id].exits.values()]
            targets += [a.go for a in world.actions
                        if a.go and a.where and room_id in a.where]
            for target in targets:
                if target in rooms and target not in reached:
                    reached.add(target)
                    frontier.append(target)
        for room in rooms.values():
            if room.id not in reached:
                report.warning(room.line, f"Room '{room.id}' can't be reached from the "
                               f"start room by any exit or 'go' action.")

    # --- one-way exits (informational) ---
    # A way back can be an exit or an action with 'go' (like climbing down a
    # rope), so only rooms with neither are mentioned.
    for room in rooms.values():
        for direction, (target, line) in room.exits.items():
            if target in rooms and target != room.id:
                back = [t for t, _ in rooms[target].exits.values()]
                back += [a.go for a in world.actions if a.go and a.applies_in(target)]
                if room.id not in back:
                    report.note(line, f"The '{direction}' exit from '{room.id}' leads to "
                                f"'{target}', but there is no way back: '{target}' has no "
                                f"exit to '{room.id}', and no action there has "
                                f"'go = {room.id}'. That's fine if you meant it.")
