"""Turns a command like "jump in the river" into (enter, [river]).

The *same* steps are used for what the player types and for every
[action: ...] phrase in the adventure file. Matching is done on the results,
which is why one action phrase covers many ways of saying it. See section 6
of docs/text-adventure-engine-spec.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Callable, Iterable

from .vocabulary import (DIRECTIONS, FILLER_WORDS, PRONOUNS, VERB_EXPANSIONS,
                         build_verb_table)

_SPLIT = re.compile(r"[.,;]|\bthen\b", re.IGNORECASE)


@dataclass(frozen=True)
class Noun:
    kind: str                       # "item", "word" or "direction"
    word: str                       # the words as typed, for messages
    ids: frozenset = frozenset()    # for items: which item(s) this could be
    ambiguous: bool = False         # several of those items are right here
    describing: bool = False        # an unknown word just before an item's name,
                                    # like "old" in "the old willow"

    def same_as(self, other: "Noun") -> bool:
        """Does this noun (from an action phrase) match `other` (from the player)?"""
        if self.kind != other.kind:
            return False
        if self.kind == "item":
            return bool(self.ids & other.ids)
        return self.word == other.word


@dataclass(frozen=True)
class Command:
    verb: str
    nouns: tuple
    text: str = ""                  # the original words, for messages

    @property
    def is_movement(self) -> bool:
        """A plain movement: go + a direction and nothing else."""
        return (self.verb == "go" and len(self.nouns) == 1
                and self.nouns[0].kind == "direction")

    @property
    def direction(self) -> str | None:
        for noun in self.nouns:
            if noun.kind == "direction":
                return noun.word
        return None

    @property
    def form(self) -> str:
        """A short readable form such as 'give pie agnes'."""
        return " ".join([self.verb] + [n.word for n in self.nouns])

    def matches(self, other: "Command", loose: bool = False) -> bool:
        """Same verb and the same set of nouns, in any order.

        With loose=True, describing words on both sides are ignored, so
        "tie rope to the old willow" matches "tie rope to willow".
        """
        mine, theirs = (self.plain(), other.plain()) if loose else (self, other)
        return mine.verb == theirs.verb and nouns_match(mine.nouns, theirs.nouns)

    def plain(self) -> "Command":
        """This command without its describing words."""
        return Command(self.verb, tuple(n for n in self.nouns if not n.describing), self.text)

    def with_noun(self, index: int, noun: Noun) -> "Command":
        nouns = list(self.nouns)
        nouns[index] = noun
        return Command(self.verb, tuple(nouns), self.text)


def nouns_match(wanted: Iterable[Noun], given: Iterable[Noun]) -> bool:
    """True if every noun pairs up with exactly one other, ignoring order."""
    wanted, given = list(wanted), list(given)
    if len(wanted) != len(given):
        return False

    def pair(i: int, used: set[int]) -> bool:
        if i == len(wanted):
            return True
        for j, noun in enumerate(given):
            if j not in used and wanted[i].same_as(noun) and pair(i + 1, used | {j}):
                return True
        return False

    return pair(0, set())


def split_commands(text: str) -> list[str]:
    """'take rope, then go north' -> ['take rope', 'go north']"""
    return [part.strip() for part in _SPLIT.split(text) if part.strip()]


def clean(text: str) -> list[str]:
    """Lowercase, drop apostrophes, turn other punctuation into spaces, split.

    Underscores are kept so an item id like brass_key stays one word.
    """
    text = text.lower().replace("'", "").replace("’", "")
    text = "".join(c if c.isalnum() or c == "_" else " " for c in text)
    return text.split()


class Normalizer:
    def __init__(self, item_aliases: dict[str, Iterable[str]],
                 vocabulary: Iterable[tuple[str, str]] = ()):
        """
        item_aliases: item id -> its aliases (name, id and listed aliases).
        vocabulary:   (word, other_word) pairs from [vocabulary]: other_word
                      is replaced by word before anything else happens.
        """
        self.verbs = build_verb_table()
        self.max_verb_len = max(len(k) for k in self.verbs)

        self.replacements: dict[tuple[str, ...], tuple[str, ...]] = {}
        for word, other in vocabulary:
            src, dst = tuple(clean(other)), tuple(clean(word))
            if src and dst:
                self.replacements[src] = dst
        self.max_replace_len = max((len(k) for k in self.replacements), default=0)

        self.aliases: dict[tuple[str, ...], set[str]] = {}
        for item_id, aliases in item_aliases.items():
            for alias in aliases:
                key = tuple(self._replace(clean(alias)))
                if key:
                    self.aliases.setdefault(key, set()).add(item_id)
        self.max_alias_len = max((len(k) for k in self.aliases), default=0)

    # ------------------------------------------------------------------
    def parse(self, text: str,
              present: Callable[[str], bool] | None = None,
              last_item: str | None = None) -> Command | None:
        """Normalize one command.

        For player input pass `present` (is this item here?) so that shared
        aliases pick the item in front of the player, and `last_item` so
        "it" works. For action phrases leave both out.
        """
        tokens = clean(text)
        if tokens and tokens[0] == "please":
            tokens = tokens[1:]
        tokens = self._replace(tokens)
        if not tokens:
            return None

        # Step 3: a bare direction ("n", "up") is a movement.
        if len(tokens) == 1 and tokens[0] in DIRECTIONS:
            return Command("go", (Noun("direction", DIRECTIONS[tokens[0]]),), text)

        # Step 4: the verb, longest phrase first.
        verb, rest = self._split_verb(tokens)

        # Step 5: words whose meaning depends on what follows.
        if verb in ("climb", "move") and rest and rest[0] in DIRECTIONS:
            verb = "go"
        elif verb == "move":
            verb = "push"
        elif verb == "leave":
            verb = "drop" if rest else "exit"

        nouns: list[Noun] = []
        if verb == "go" and rest and rest[0] in DIRECTIONS:
            nouns.append(Noun("direction", DIRECTIONS[rest[0]]))
            rest = rest[1:]

        # Steps 6 and 7: items, then drop filler words.
        nouns.extend(self._nouns(rest, present, last_item))

        if verb in ("enter", "exit") and not nouns:
            nouns = [Noun("direction", "in" if verb == "enter" else "out")]
            verb = "go"
        if verb == "look" and nouns:
            verb = "examine"
        return Command(verb, tuple(nouns), text)

    def item_noun(self, word: str, ids: set[str],
                  present: Callable[[str], bool] | None) -> Noun:
        """Choose among items that share an alias."""
        if present is None or len(ids) == 1:
            return Noun("item", word, frozenset(ids))
        here = {i for i in ids if present(i)}
        if len(here) == 1:
            return Noun("item", word, frozenset(here))
        if len(here) > 1:
            return Noun("item", word, frozenset(here), ambiguous=True)
        return Noun("item", word, frozenset(ids))

    def lookup(self, text: str) -> set[str]:
        """Which items does this whole phrase name? (Used for "which one?" answers.)"""
        return set(self.aliases.get(tuple(self._replace(clean(text))), set()))

    # ------------------------------------------------------------------
    def _replace(self, tokens: list[str]) -> list[str]:
        """Apply the author's [vocabulary] word replacements."""
        if not self.replacements:
            return list(tokens)
        out: list[str] = []
        i = 0
        while i < len(tokens):
            for n in range(min(self.max_replace_len, len(tokens) - i), 0, -1):
                key = tuple(tokens[i:i + n])
                if key in self.replacements:
                    out.extend(self.replacements[key])
                    i += n
                    break
            else:
                out.append(tokens[i])
                i += 1
        return out

    def _split_verb(self, tokens: list[str]) -> tuple[str, list[str]]:
        for n in range(min(self.max_verb_len, len(tokens)), 0, -1):
            canonical = self.verbs.get(tuple(tokens[:n]))
            if canonical:
                rest = list(tokens[n:])
                if canonical in VERB_EXPANSIONS:
                    canonical, direction = VERB_EXPANSIONS[canonical]
                    rest.insert(0, direction)
                return canonical, rest
        return tokens[0], list(tokens[1:])

    def _nouns(self, words: list[str], present, last_item) -> list[Noun]:
        nouns: list[Noun] = []
        i = 0
        while i < len(words):
            for n in range(min(self.max_alias_len, len(words) - i), 0, -1):
                key = tuple(words[i:i + n])
                if key in self.aliases:
                    nouns.append(self.item_noun(" ".join(key), self.aliases[key], present))
                    i += n
                    break
            else:
                word = words[i]
                i += 1
                if word in PRONOUNS and last_item and present is not None:
                    nouns.append(Noun("item", word, frozenset({last_item})))
                elif word not in FILLER_WORDS:
                    nouns.append(Noun("word", word))
        return mark_describing(nouns)


def mark_describing(nouns: list[Noun]) -> list[Noun]:
    """Mark unknown words that come right before an item's name.

    In "the big old willow", if only "willow" is a known name, "big" and
    "old" are describing words. Working backwards from each item, every
    unknown word in an unbroken run before it is marked.
    """
    marked = list(nouns)
    for i in range(len(marked) - 2, -1, -1):
        after = marked[i + 1]
        if marked[i].kind == "word" and (after.kind == "item" or after.describing):
            marked[i] = replace(marked[i], describing=True)
    return marked
