"""Conditions such as "has rope", "not flag door_open" or "score >= 50".

Conditions appear in `if = ...`, in ending `when = ...`, and in conditional
text lines like `when flag rope_tied = A rope hangs here.`
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# One condition, as a regular expression. Used both to read single
# conditions and to find where the conditions end on a `when` line.
COND_PATTERN = (
    r"(?:not\s+)?"
    r"(?:(?:has|here|flag|in|visited)\s+[A-Za-z0-9_]+"
    r"|(?:score|moves)\s*(?:>=|<=|>|<|=)\s*\d+)"
)

_ONE_COND = re.compile(
    r"\s*(?P<neg>not\s+)?"
    r"(?:(?P<kind>has|here|flag|in|visited)\s+(?P<arg>[A-Za-z0-9_]+)"
    r"|(?P<counter>score|moves)\s*(?P<op>>=|<=|>|<|=)\s*(?P<num>\d+))\s*",
    re.IGNORECASE,
)

# "<conditions> = <text>" -- the text starts after the `=` that follows the
# last complete condition, so `score = 50 = Well done!` splits correctly.
_WHEN_LINE = re.compile(
    rf"^\s*({COND_PATTERN}(?:\s*,\s*{COND_PATTERN})*)\s*=\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)


class ConditionError(ValueError):
    """Raised when a condition can't be understood."""


@dataclass(frozen=True)
class Condition:
    negated: bool
    kind: str            # has, here, flag, in, visited, score, moves
    arg: str = ""        # item/room/flag id for the word kinds
    op: str = ""         # comparison operator for score/moves
    number: int = 0
    text: str = ""       # as written, for messages

    @property
    def refers_to_item(self) -> bool:
        return self.kind in ("has", "here")

    @property
    def refers_to_room(self) -> bool:
        return self.kind in ("in", "visited")


def parse_condition(text: str) -> Condition:
    m = _ONE_COND.fullmatch(text)
    if not m:
        raise ConditionError(
            f"I don't understand the condition '{text.strip()}'. Conditions look "
            f"like: has rope, here lamp, flag door_open, in kitchen, visited cellar, "
            f"score >= 50, moves < 100 -- with 'not' in front to reverse them.")
    negated = bool(m.group("neg"))
    if m.group("kind"):
        return Condition(negated, m.group("kind").lower(), arg=m.group("arg").lower(),
                         text=text.strip())
    return Condition(negated, m.group("counter").lower(), op=m.group("op"),
                     number=int(m.group("num")), text=text.strip())


def parse_conditions(text: str) -> list[Condition]:
    """Read a comma-separated list of conditions (all must be true)."""
    if not text.strip():
        return []
    return [parse_condition(part) for part in text.split(",")]


def split_when(text: str) -> tuple[str, str] | None:
    """Split "<conditions> = <text>" into its two halves, or None if malformed."""
    m = _WHEN_LINE.match(text)
    if not m:
        return None
    return m.group(1), m.group(2)


def compare(left: int, op: str, right: int) -> bool:
    return {
        ">=": left >= right, "<=": left <= right,
        ">": left > right, "<": left < right, "=": left == right,
    }[op]
