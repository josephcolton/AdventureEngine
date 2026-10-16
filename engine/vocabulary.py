"""The built-in word lists the parser uses.

To teach the game a new way of saying something, add it here. Each verb
below lists the other words and phrases that mean the same thing; phrases
can be several words long ("pick up"), and the longest match always wins.
"""

# Direction words and their abbreviations -> the full direction name.
DIRECTIONS = {
    "north": "north", "n": "north",
    "south": "south", "s": "south",
    "east": "east", "e": "east",
    "west": "west", "w": "west",
    "northeast": "northeast", "ne": "northeast",
    "northwest": "northwest", "nw": "northwest",
    "southeast": "southeast", "se": "southeast",
    "southwest": "southwest", "sw": "southwest",
    "up": "up", "u": "up",
    "down": "down", "d": "down",
    "in": "in", "inside": "in",
    "out": "out", "outside": "out",
}

DIRECTION_NAMES = ["north", "south", "east", "west", "northeast", "northwest",
                   "southeast", "southwest", "up", "down", "in", "out"]

# Commands about the program rather than the story. They only count as
# meta commands when typed on their own ("save", not "save the cat").
META_VERBS = {
    "save": ["save game"],
    "load": ["restore", "load game", "restore game"],
    "restart": ["restart game", "start over"],
    "quit": ["q", "quit game"],
    "score": [],
    "exits": [],
    "hint": ["hints", "clue", "clues"],
    "help": ["commands"],
}

# canonical verb -> other ways to say it
VERB_SYNONYMS = {
    "go": ["walk", "run", "head", "travel", "proceed", "stroll", "hike"],
    "enter": ["go in", "go into", "go inside", "get in", "get into", "jump in",
              "jump into", "climb in", "climb into", "step in", "step into",
              "wade in", "wade into", "dive in", "dive into", "hop in", "hop into",
              "crawl in", "crawl into", "walk into", "run into", "head into"],
    "exit": ["get out", "get out of", "climb out", "climb out of", "go out",
             "go out of", "step out", "step out of", "walk out", "crawl out"],
    "take": ["get", "grab", "pick up", "pick", "carry", "collect", "snatch",
             "acquire", "obtain", "hold"],
    "drop": ["put down", "set down", "discard", "throw away", "toss", "dump"],
    "examine": ["x", "look at", "look in", "look inside", "look into", "look under",
                "look behind", "look through", "l at", "inspect", "study", "read",
                "check", "describe", "observe", "search", "view", "watch"],
    "look": ["l", "look around", "glance", "glance around"],
    "inventory": ["i", "inv", "items", "invent"],
    "use": ["apply", "utilize", "operate"],
    "put": ["place", "insert", "set", "stick", "stuff", "lay"],
    "open": ["pry open"],
    "close": ["shut", "slam"],
    "unlock": [],
    "lock": [],
    "push": ["press", "shove", "poke", "prod"],
    "pull": ["tug", "yank", "drag"],
    "turn": ["rotate", "spin", "twist", "wind"],
    "talk": ["talk to", "talk with", "speak", "speak to", "speak with", "chat",
             "chat with", "chat to", "greet", "say hello to", "say hi to", "ask",
             "converse with", "hello", "hi"],
    "give": ["offer", "hand", "present", "donate"],
    "show": ["display", "reveal"],
    "tie": ["bind", "fasten", "knot", "attach", "lash", "secure"],
    "untie": ["unknot", "unfasten", "unbind", "detach"],
    "cut": ["slice", "chop", "saw", "slash", "sever", "trim"],
    "light": ["turn on", "switch on", "ignite", "kindle", "light up"],
    "extinguish": ["turn off", "switch off", "put out", "blow out", "snuff", "douse"],
    "eat": ["consume", "devour", "taste", "nibble", "munch", "bite"],
    "drink": ["sip", "swallow", "gulp", "quaff", "slurp"],
    "climb": ["scale", "clamber"],
    "jump": ["leap", "hop", "bound", "vault"],
    "swim": ["paddle", "bathe"],
    "wait": ["z", "rest", "pause", "linger"],
    "again": ["g", "repeat"],
    "break": ["smash", "shatter", "destroy"],
    "throw": ["hurl", "fling", "chuck"],
    "listen": ["hear", "listen to"],
    "smell": ["sniff"],
    "touch": ["feel", "pat", "stroke", "rub"],
    "dig": ["excavate", "shovel"],
    "fill": [],
    "empty": ["pour"],
    "wear": ["put on", "don"],
    "remove": ["take off", "doff"],
    "sit": ["sit down"],
    "sleep": ["nap", "doze"],
    "pray": [],
    "knock": ["knock on", "rap"],
    "kiss": [],
    "hug": ["embrace"],
    "wave": [],
    "sing": ["hum"],
    "yell": ["shout", "scream", "call"],
}

# Single words that stand for a verb *and* a direction.
VERB_EXPANSIONS = {
    "descend": ("go", "down"),
    "ascend": ("go", "up"),
}

# Words whose meaning depends on what follows (see normalizer.py):
#   climb + direction -> go,  move + direction -> go (otherwise push),
#   leave + noun -> drop (otherwise exit).
CONTEXT_VERBS = {"climb", "move", "leave"}

# Little words that are dropped after verbs and item names have been found.
FILLER_WORDS = {
    "the", "a", "an", "some", "of", "to", "into", "in", "on", "onto", "at",
    "with", "from", "using", "up", "down", "about", "for",
}

# Words that mean "the last thing you mentioned".
PRONOUNS = {"it", "them", "him", "her"}

# Verbs that make sense with no noun at all, with the reply to give when no
# author action handles them.
NO_NOUN_REPLIES = {
    "jump": "You jump on the spot. Nothing much happens.",
    "swim": "There's nowhere to swim here.",
    "listen": "You hear nothing unusual.",
    "smell": "You smell nothing unusual.",
    "sleep": "This is no time for a nap.",
    "sing": "You hum a little tune to yourself.",
    "pray": "You say a quiet prayer. You feel a little better.",
    "yell": "Nobody answers.",
    "wave": "You wave. Nobody waves back.",
    "sit": "You sit for a moment, then get back up.",
    "dig": "You scrape at the ground, but find nothing.",
    "knock": "Nobody answers.",
}

# Replies when a verb is understood but no author action handles it.
NOTHING_HAPPENS_VERBS = {"use", "put", "push", "pull", "turn", "touch"}
NO_RESPONSE_VERBS = {"talk", "give", "show", "kiss", "hug"}
GENERIC_REPLIES = [
    "I don't know how to do that.",
    "That doesn't seem to work.",
    "You can't do that here.",
]

DEFAULT_DARK_TEXT = "It is pitch dark. You might be eaten by something."

HELP_TEXT = """Type what you want to do in plain words, then press Enter.

Moving around:  north, south, east, west (or n, s, e, w), up, down, in, out
Looking:        look (or l), examine the lamp (or x lamp)
Things:         take the rope, drop the rope, take all, inventory (or i)
Doing:          open, push, pull, give, talk to, tie, climb, eat ... try anything!
Other:          wait (or z), again (or g) to repeat, score, exits
Stuck?          hint

You can type several commands at once: take the rope, then go north.
The game also understands: save, load, restart, quit."""


def build_verb_table() -> dict[tuple[str, ...], str]:
    """Map every verb phrase (as a tuple of words) to its canonical verb."""
    table: dict[tuple[str, ...], str] = {}
    for groups in (VERB_SYNONYMS, META_VERBS):
        for canonical, synonyms in groups.items():
            table[(canonical,)] = canonical
            for phrase in synonyms:
                table[tuple(phrase.split())] = canonical
    for word in VERB_EXPANSIONS:
        table[(word,)] = word
    return table


KNOWN_VERBS = (set(VERB_SYNONYMS) | set(META_VERBS) | CONTEXT_VERBS
               | {verb for verb, _ in VERB_EXPANSIONS.values()})
