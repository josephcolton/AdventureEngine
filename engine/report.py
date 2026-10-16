"""Collects the problems found while loading an adventure file.

Every message has a level (error, warning or note), an optional line number,
and plain-English wording written for someone who has never programmed.
"""

from __future__ import annotations

from dataclasses import dataclass

ERROR = "error"
WARNING = "warning"
NOTE = "note"

_LEVEL_ORDER = {ERROR: 0, WARNING: 1, NOTE: 2}
_HEADINGS = {ERROR: "Errors", WARNING: "Warnings", NOTE: "Notes"}


@dataclass
class Message:
    level: str
    line: int | None
    text: str

    def __str__(self) -> str:
        if self.line:
            return f"Line {self.line}: {self.text}"
        return self.text


class Report:
    """A list of messages, plus helpers for showing them to the author."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    def error(self, line: int | None, text: str) -> None:
        self.messages.append(Message(ERROR, line, text))

    def warning(self, line: int | None, text: str) -> None:
        self.messages.append(Message(WARNING, line, text))

    def note(self, line: int | None, text: str) -> None:
        self.messages.append(Message(NOTE, line, text))

    def _of_level(self, level: str) -> list[Message]:
        found = [m for m in self.messages if m.level == level]
        return sorted(found, key=lambda m: m.line or 0)

    @property
    def errors(self) -> list[Message]:
        return self._of_level(ERROR)

    @property
    def warnings(self) -> list[Message]:
        return self._of_level(WARNING)

    @property
    def notes(self) -> list[Message]:
        return self._of_level(NOTE)

    @property
    def has_errors(self) -> bool:
        return any(m.level == ERROR for m in self.messages)

    def summary(self) -> str:
        e, w = len(self.errors), len(self.warnings)
        if e:
            return (f"Found {e} error{'s' if e != 1 else ''} that must be fixed "
                    f"before the adventure can be played"
                    + (f", and {w} warning{'s' if w != 1 else ''}." if w else "."))
        if w:
            return (f"The adventure can be played, but there "
                    f"{'is' if w == 1 else 'are'} {w} warning{'s' if w != 1 else ''} "
                    f"worth a look.")
        return "Everything looks good!"

    def format(self) -> str:
        """The whole report as plain text, grouped by level."""
        parts = [self.summary()]
        for level in (ERROR, WARNING, NOTE):
            found = self._of_level(level)
            if found:
                parts.append("")
                parts.append(_HEADINGS[level] + ":")
                parts.extend("  " + str(m) for m in found)
        return "\n".join(parts)
