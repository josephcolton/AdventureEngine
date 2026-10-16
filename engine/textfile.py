"""Reads the raw structure of an .adv file: sections, settings and text.

This module only knows about the *shape* of the file (headers, `key = value`,
indented continuation lines, comments). What the keys mean is decided later,
in loader.py.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .conditions import split_when
from .report import Report

SECTION_TYPES = ("game", "room", "item", "vocabulary", "action", "ending")
SECTIONS_WITH_ID = ("room", "item", "action", "ending")

# Settings whose value is text shown to the player. On these, a `#` is just a
# character; on every other setting, "  # ..." starts a trailing comment.
TEXT_KEYS = {
    "title", "author", "description", "intro", "name", "first", "again", "here",
    "examine", "take_fail", "dark_text", "message", "fail", "done", "text", "hint",
}

# Keys written as "<key> when <conditions> = <text>".
CONDITIONAL_KEYS = ("when", "here when", "examine when", "hint when")

_HEADER = re.compile(r"^\[\s*([A-Za-z_]+)\s*(?::\s*(.*?))?\s*\]$")
_SETTING = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
_VOCAB_SETTING = re.compile(r"^([^=]+?)\s*=\s*(.*)$")
_CONDITIONAL = re.compile(r"^(?:(here|examine|hint)\s+)?when\s+(?![\s=])(.*)$", re.IGNORECASE)
_TRAILING_COMMENT = re.compile(r"(?:[ \t]{2,}|\t)#")

PARAGRAPH = "\n\n"


@dataclass
class Entry:
    """One `key = value` setting, possibly continued over several lines."""
    key: str
    line: int
    is_text: bool
    condition_text: str | None = None    # only for conditional (`when`) lines
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_words(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def new_paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    @property
    def value(self) -> str:
        if self.is_text:
            return PARAGRAPH.join(" ".join(p) for p in self.paragraphs if p)
        return " ".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Section:
    kind: str           # game, room, item, vocabulary, action, ending
    name: str           # the id (or the phrase, for actions); "" if none
    line: int
    entries: list[Entry] = field(default_factory=list)

    def last(self, key: str) -> Entry | None:
        found = [e for e in self.entries if e.key == key]
        return found[-1] if found else None

    def value(self, key: str, default: str = "") -> str:
        entry = self.last(key)
        return entry.value if entry else default

    def all(self, key: str) -> list[Entry]:
        return [e for e in self.entries if e.key == key]

    @property
    def label(self) -> str:
        return f"[{self.kind}: {self.name}]" if self.name else f"[{self.kind}]"


def decode(data: bytes, report: Report) -> str:
    """Turn file bytes into text. Accepts UTF-8 with or without a BOM."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        report.warning(None, "This file isn't saved as UTF-8, so some special "
                       "characters may look wrong. In Notepad++ use "
                       "Encoding > Convert to UTF-8, then save.")
        return data.decode("cp1252", errors="replace")


def strip_trailing_comment(text: str) -> str:
    m = _TRAILING_COMMENT.search(text)
    return text[:m.start()] if m else text


def parse_text(text: str, report: Report) -> list[Section]:
    """Split the file into sections and settings, reporting shape problems."""
    sections: list[Section] = []
    section: Section | None = None
    entry: Entry | None = None
    discard = False          # swallowing the continuation lines of a bad line
    saw_blank = False
    complained_before_first = False

    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()

        if not stripped:
            saw_blank = True
            continue
        if stripped.startswith("#"):
            continue

        # --- an indented line continues the setting above it ---
        if raw[0] in " \t":
            if discard:
                continue
            if entry is None:
                report.error(number, "This line starts with a space, but there is no "
                             "setting above it for it to continue. If it is a new "
                             "setting, remove the space at the start of the line.")
                discard = True
                continue
            if entry.is_text:
                if stripped == "~":
                    entry.new_paragraph()
                else:
                    if saw_blank:
                        entry.new_paragraph()
                    entry.add_words(stripped)
            else:
                entry.add_words(strip_trailing_comment(stripped).strip())
            saw_blank = False
            continue

        saw_blank = False
        discard = False
        entry = None

        # --- a section header ---
        if stripped.startswith("["):
            header = strip_trailing_comment(stripped).strip()   # "[game]   # note" is fine
            section = _read_header(header, number, report)
            if section is not None:
                sections.append(section)
            else:
                discard = True
            continue

        if section is None:
            if not complained_before_first:
                report.error(number, "This line comes before the first section. "
                             "Every setting must belong to a section such as [game] "
                             "or [room: kitchen]. (Comments starting with # are fine.)")
                complained_before_first = True
            discard = True
            continue

        # --- a setting ---
        entry = _read_setting(section, stripped, number, report)
        if entry is None:
            discard = True
        else:
            section.entries.append(entry)

    return sections


def _read_header(stripped: str, number: int, report: Report) -> Section | None:
    m = _HEADER.match(stripped)
    if not m:
        report.error(number, "This looks like a section header, but it isn't written "
                     "correctly. Headers look like [game], [room: kitchen] or "
                     "[action: open the door].")
        return None
    kind = m.group(1).lower()
    name = (m.group(2) or "").strip()
    if kind not in SECTION_TYPES:
        guess = difflib.get_close_matches(kind, SECTION_TYPES, n=1)
        hint = f" Did you mean [{guess[0]}]?" if guess else ""
        report.error(number, f"[{kind}] isn't a kind of section I know. The kinds are: "
                     f"{', '.join(SECTION_TYPES)}.{hint}")
        return None
    if kind in SECTIONS_WITH_ID and not name:
        example = "open the door" if kind == "action" else "kitchen"
        report.error(number, f"A [{kind}] section needs a name after a colon, "
                     f"for example [{kind}: {example}].")
        return None
    if kind not in SECTIONS_WITH_ID and name:
        report.warning(number, f"[{kind}] sections don't have a name, so "
                       f"'{name}' will be ignored.")
        name = ""
    return Section(kind, name, number)


def _read_setting(section: Section, stripped: str, number: int,
                  report: Report) -> Entry | None:
    # Conditional lines: "when ... = text", "here when ... = text", ...
    m = _CONDITIONAL.match(stripped)
    if m and section.kind != "vocabulary":
        key = f"{m.group(1).lower()} when" if m.group(1) else "when"
        halves = split_when(m.group(2))
        if halves is None:
            report.error(number, "I couldn't read this 'when' line. It should look like: "
                         "when flag door_open = The door stands open. Check the spelling "
                         "of the condition and that there is an = before the text.")
            return None
        entry = Entry(key, number, is_text=True, condition_text=halves[0].strip())
        entry.add_words(halves[1].strip())
        return entry

    pattern = _VOCAB_SETTING if section.kind == "vocabulary" else _SETTING
    m = pattern.match(stripped)
    if not m:
        report.error(number, "This line doesn't look like a setting (name = value). "
                     "If it is part of the text above, start it with a space or tab.")
        return None
    key = " ".join(m.group(1).lower().split())
    is_text = key in TEXT_KEYS
    value = m.group(2).strip() if is_text else strip_trailing_comment(m.group(2)).strip()
    entry = Entry(key, number, is_text=is_text)
    entry.add_words(value)
    return entry
