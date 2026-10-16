# Text Adventure Engine — Design Specification

## 1. Purpose

Build a desktop program that lets a non-programmer (the author's mother, a longtime Zork fan) **write** text adventures in a plain text file and **play** them in a simple window.

Design priorities, in order:

1. **The world file must be easy to read and write by hand** in Notepad++. Forgiving syntax, clear error messages with line numbers.
2. **The parser must feel natural.** "jump in the river", "wade into river" and "enter river" should all work from a single entry in the world file.
3. **Cross-platform.** Must run identically on Windows and Linux.
4. **No third-party dependencies.** Python standard library only.
5. **Open file formats.** World files are UTF-8 plain text; save files are JSON.

## 2. Technology

- **Language:** Python 3.10+.
- **GUI:** `tkinter` (ships with Python on Windows and most Linux distros).
- **Tests:** `unittest` (stdlib).
- **Paths:** use `pathlib` everywhere; never hard-code `/` or `\`.
- **Text encoding:** always read and write files as UTF-8 (`encoding="utf-8"`); tolerate a UTF-8 BOM (Notepad++ can add one).
- **Line endings:** accept both CRLF and LF.
- Launch with `python adventure.py`. Also provide `adventure.pyw` (a two-line wrapper that starts the same program) so that on Windows it can be double-clicked without opening a console window.
- Provide instructions (and a small build script) for building a Windows `.exe` with PyInstaller. This is the recommended way to hand the program to a non-programmer, but running from source must keep working without it.

## 3. Folder Layout

```
AdventureEngine/
├── adventure.py            # entry point
├── adventure.pyw           # same, without a console window (Windows double-click)
├── engine/                 # package: loader, parser, game state, validator
├── gui/                    # package: tkinter windows
├── adventures/             # the author drops .adv files here
│   ├── tutorial.adv        # sample adventure that exercises every feature
│   └── agnes_and_the_well.adv   # small example adventure (already present)
├── docs/
│   ├── text-adventure-engine-spec.md   # this document
│   ├── AUTHORING.md        # plain-language guide for writing adventures
│   └── notepadpp-adv.xml   # optional Notepad++ syntax-highlighting definition
└── tests/
```

The `adventures/` folder is located next to `adventure.py` (or next to the `.exe` when frozen). Create it if missing.

Saves and settings belong to each user, so they live in the user's data folder: `%APPDATA%\AdventureEngine` on Windows, `~/Library/Application Support/AdventureEngine` on macOS, `$XDG_DATA_HOME/adventure-engine` (default `~/.local/share/adventure-engine`) elsewhere. Inside it:

```
├── settings.json
└── saves/                  # created automatically
    └── <adventure-file-stem>/
        └── <save-name>.json
```

On startup, any `settings.json` and `saves/` left next to the program by older versions are copied into the user's folder (existing files there are never overwritten; the originals are left in place).

## 4. Program Flow and Window Layout

### 4.1 Start Screen

Shown when the program opens and when the player chooses **Change Adventure**.

- **Adventure dropdown:** lists every `.adv` file in `adventures/`, displayed by its `title` (from the `[game]` section), not its filename. Sorted alphabetically by title.
- Below the dropdown, show the selected adventure's **author** and **description**.
- **Buttons:** **Play**, **Check Adventure** (runs the validator and shows the report), **Refresh List** (rescan the folder), **Open Adventures Folder** (opens it in the OS file manager), **Quit**.
- If an adventure file has errors, still list it but mark it (for example `⚠ Haunted House`). Selecting it and pressing Play shows the error report instead of starting.
- Pressing **Play** on an adventure with no saves starts it immediately. If it has saves, the **Saved Game screen** is shown instead.

### 4.1a Saved Game Screen

- Shows the adventure's title and a list of its saves, newest first, each shown as `save name — date/time — room — score`. The newest is selected.
- **Buttons:** **Continue** (load the selected save; also Enter or double-click), **New Adventure** (start from the beginning), **Delete Save** (asks first; also the Delete key), **Back** (return to the start screen; also Escape).

### 4.2 Game Window

```
┌─────────────────────────────────────────────────────────┐
│ Game  View  Author  Help                    (menu bar)  │
├─────────────────────────────────────────────────────────┤
│ Muddy Riverbank              Score: 15 / 100  Moves: 42 │  status bar
├─────────────────────────────────────────────────────────┤
│                                                         │
│  (scrollable, read-only, word-wrapped story text)       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ > _                                       (input line)  │
└─────────────────────────────────────────────────────────┘
```

- **Status bar** (top): current room name on the left; score (`Score: X / MAX`) and move count on the right.
- **Story area:** read-only, word-wrapped, scrollable with mouse wheel and scrollbar; auto-scrolls to the bottom on new output. The player's typed commands are echoed in a distinct style (for example bold, prefixed with `>`).
- **Input line:** single line, keeps focus. **Enter** submits. **Up/Down arrows** cycle through command history.
- Window is resizable; the story area grows to fill it.

### 4.3 Menus

- **Game:** Save (Ctrl+S), Save As…, Load…, Restart, Change Adventure…, Quit.
- **View:** Larger Text (Ctrl+=), Smaller Text (Ctrl+-), Light/Dark theme. Remember font size and theme between sessions in a small JSON settings file in the user's data folder (section 3).
- **Author:** Check Adventure, Reload Adventure File (re-reads the `.adv` file and restarts, so the author can edit in Notepad++ and test quickly), Reload and Replay (re-reads the file, restarts, then silently re-runs every command typed so far this game, so the author lands back where she was; if a replayed command now leads to an ending, stop there), Show Flags & State (debug window), Go To Room… (debug teleport).
- **Help:** How to Play (list of commands), Get a Hint (same as typing `hint`), About.

### 4.4 Saving and Loading

- **Save:** if the current game was loaded from or previously saved to a file, overwrite it (no prompt needed). Otherwise behave like Save As.
- **Save As:** prompt for a save name (simple text dialog, not a raw file dialog). If the name exists, ask to confirm overwriting.
- **Load:** show the list of saves for the current adventure (same format as the start screen).
- Typing `save`, `load` or `restart` in the input line triggers the same actions.
- **Unsaved progress:** when quitting, restarting, loading or changing adventures with progress since the last save, ask "Save your progress first?" (Save / Don't Save / Cancel).
- **Save file format (JSON):**

```json
{
  "format_version": 1,
  "adventure_file": "riverbank.adv",
  "adventure_title": "The Riverbank",
  "adventure_fingerprint": "sha256 of the .adv file",
  "save_name": "before the cave",
  "saved_at": "2026-10-15T14:20:00",
  "current_room": "riverbank",
  "visited_rooms": ["riverbank", "forest_path"],
  "item_locations": {"rope": "inventory", "lantern": "cellar"},
  "handled_items": ["rope"],
  "flags": ["rope_tied"],
  "score": 15,
  "awarded": ["room:riverbank", "item:rope", "action:enter_river"],
  "completed_actions": ["enter_river"],
  "command_history": ["take rope", "n", "..."],
  "moves": 42,
  "transcript": ["...last ~200 lines of story text..."]
}
```

- On load, if the fingerprint differs from the current file, warn: "This adventure has been edited since you saved. The save may not work correctly." and load anyway, ignoring references to rooms/items that no longer exist (fall back to the start room if the current room is gone).
- Restore the recent transcript into the story area on load so the player sees where they were.
- Action keys in `awarded` and `completed_actions` are action ids (see `id` in 5.6).
- `command_history` holds every command typed this game (used by Reload and Replay).

## 5. The Adventure File Format (`.adv`)

INI-like, but parsed by our own code (do **not** use `configparser`; it can't handle the multi-line text and repeated keys we need).

### 5.1 General Syntax Rules

- A file is a series of **sections**. A section starts with a header in square brackets: `[room: kitchen]`.
- Inside a section, settings are `key = value`.
- **Long text:** any line that starts with a space or tab continues the previous value. Continuation lines are joined with single spaces (the window does the word-wrapping, so the author can break lines wherever she likes).
- **Paragraph break inside text:** either a continuation line containing only `~`, **or** one or more blank lines followed by another indented line. (Authors naturally press Enter twice for a new paragraph; that must just work.)
- **Blank lines** are otherwise ignored. A blank line does not by itself end a text value; the next *unindented* line does.
- **Comments:** lines whose first non-space character is `#` are ignored. A section header may also be followed by "  # ..." (`[game]   # exactly one`). On a **non-text** setting, a `#` preceded by at least two spaces starts a trailing comment (`max_score = 100   # optional`). On **text** settings a `#` is always shown as written. Text settings are: `title`, `author`, `description`, `intro`, `name`, `first`, `again`, `here`, `examine`, `take_fail`, `dark_text`, `message`, `fail`, `done`, `text`, `hint`, `dropped`, and the text part of any `when` line (5.3, 5.4).
- **Quotation marks** in text are ordinary characters (for dialogue) and are shown as written.
- Section types, IDs and keys are **case-insensitive**. IDs may contain letters, numbers and underscores; spaces in IDs are converted to underscores.
- Lists are comma-separated: `aliases = rope, coil, coil of rope`.
- **`points` and `score` are interchangeable** as key names everywhere (rooms, items, actions), so the author doesn't have to remember which one goes where.
- Unknown keys produce a **warning** (likely typo), not an error.
- A key that may only appear once (anything except `when` / `here when` / `examine when` / `hint when` lines and `also`) appearing twice in the same section is a **warning**; the last one is used.
- The same `[item: x]`, `[room: x]` or `[ending: x]` appearing twice is an error.
- **Indentation mistakes:** an unindented line that isn't a section header, comment, or `key = value` is an error, and the message must suggest the likely fix: *"Line 42 doesn't look like a setting. If it is part of the text above, start it with a space or tab."*

### 5.2 `[game]` — required, exactly one

```ini
[game]
title = The Riverbank
author = Mom
description = A short adventure about a swollen river and a lost locket.
start = riverbank
intro = It has rained for three days. Your grandmother's locket
    is somewhere down by the river, and you mean to find it.
max_score = 100     # optional; if omitted, computed automatically
```

If `max_score` is given and doesn't match the total points available, the validator warns.

### 5.3 `[room: id]`

```ini
[room: riverbank]
name = Muddy Riverbank
first = The river roars past, brown and swollen. A rowboat is
    tied to an old stump. A path climbs north into the woods,
    and a trapdoor in the mud leads down.
again = The river still roars. The rowboat bobs at its rope.
exits = north: forest_path, down: cellar
points = 5                # optional, awarded on first visit
dark = no                 # optional; see 5.7
when flag rope_tied = Your rope is knotted around the stump.
when not flag boat_gone = The rowboat tugs at its rope.
hint when has rope = That stump looks sturdy enough to tie something to.
hint = The river is too fast to swim. Perhaps there's another way.
```

| Key | Meaning |
|---|---|
| `name` | Shown in the status bar and as a heading when entering. |
| `first` | Description the first time the player enters. |
| `again` | Description on later visits. Optional; defaults to `first`. |
| `exits` | `direction: room_id` pairs. |
| `points` | Score for first visit. Optional. The start room's points (if any) are awarded when the game begins. |
| `dark` | `yes` means the player sees "It is pitch dark." unless a light source is present. Optional. |
| `when <conditions> = text` | Extra sentence appended to the description whenever the conditions are true. Any number allowed. |
| `hint` | Shown when the player types `hint` (or uses Help > Get a Hint) in this room. Optional. |
| `hint when <conditions> = text` | Conditional hint (same `when` reading rules). The first, in file order, whose conditions are true is used; otherwise the plain `hint`. If the room has neither, a generic "There's no hint for this spot..." message is shown. Any number allowed. |

`look` always shows the **full** description (`first`) plus extras; entering a visited room shows `again`.

**Reading `when` lines.** Conditions can themselves contain `=` (`when score = 50 = ...`, `when score >= 50 = ...`), so a `when` line is not split at the first `=`. Instead the loader reads one or more complete conditions (grammar in 5.6, comma-separated) after the word `when`; the `=` that follows the last complete condition separates the text. In regex terms: `^when\s+(COND(\s*,\s*COND)*)\s*=\s*(.*)$`, where `COND` is the condition pattern. If no complete condition can be read, report "Malformed condition" with the line number.

After the room text, the engine automatically lists visible items using each item's `here` text (see 5.4).

**Directions** and their built-in abbreviations: north/n, south/s, east/e, west/w, northeast/ne, northwest/nw, southeast/se, southwest/sw, up/u, down/d, in, out. Players may type `n`, `north`, `go north`, `walk n`, etc.

### 5.4 `[item: id]`

```ini
[item: rope]
name = coiled rope
aliases = rope, coil, coiled rope
location = riverbank        # a room id, "inventory", or "nowhere"
here = A coiled rope lies in the mud.
dropped = A coiled rope lies here.   # optional; see "Where it started" below
examine = Twenty feet of sturdy hemp, still damp.
take = yes                  # default yes; "no" for scenery/furniture
# take_fail is the message shown when take = no
take_fail = It's far too heavy to lift.
points = 5                  # optional, awarded the first time it reaches your inventory
light = no                  # "yes" makes it a light source (see dark rooms)
examine when flag rope_wet = The rope is soaked and heavy now.
```

- `location = nowhere` items don't exist yet; an action can bring them into play (see `move` in 5.6).
- **Scenery:** an item with `take = no` and no `here` text is invisible in the item list but can still be examined and used in actions. Use this for things mentioned in descriptions ("river", "stump").
- **Aliases:** the item's `name` and its id (with underscores turned into spaces) are always aliases automatically, in addition to any listed in `aliases`. Multi-word aliases are allowed. The parser matches the **longest** alias first.
- **Shared aliases are allowed.** Two items may both answer to "rope" (for example a coil of rope you carry and a rope tied to a well). See 6.1 step 5 for how the parser chooses.
- **Points** are awarded the first time the item enters the inventory by any means (`take` or an action's `move ... to inventory`).
- **Where it started:** `here` (and `here when`) describe the item where the author placed it, so they're only used until the item first enters the inventory (by `take` or an action's `move ... to inventory`). After that, the item is shown wherever it lies with its `dropped` text, or by default `There is a/an <name> here.` (`<name> is here.` when the name is capitalized). Items that start in the inventory count as already picked up. The set of picked-up items is kept in save files as `handled_items`; older saves without it treat only carried items as picked up.
- **Changing text:** `here` and `examine` may have conditional variants written `here when <conditions> = text` and `examine when <conditions> = text` (same `when` reading rules as 5.3). The first variant, in file order, whose conditions are true is used; otherwise the plain `here` / `examine` is used. Use this for characters whose appearance changes as the story moves along.

### 5.5 `[vocabulary]` — optional

The engine ships with a generous built-in synonym list (see 6.2). The author can add her own:

```ini
[vocabulary]
enter = wade, paddle, swim
tie = knot, fasten, lash
locket = pendant, necklace     # noun synonyms work too
```

Each line means "the word on the left also answers to the words on the right."

### 5.6 `[action: phrase]` — special commands

Actions are how the author makes anything special happen. The phrase is written the way a player might type it; the engine normalizes it exactly the way it normalizes player input (section 6), so `[action: jump in the river]` and `[action: enter river]` are equivalent.

```ini
[action: enter river]
where = riverbank
message = You wade in. The current snatches you off your feet
    and drags you down into darkness...
go = underwater_cave
score = 10

[action: tie rope to stump]
where = riverbank
if = has rope, not flag rope_tied
fail = You don't have anything to tie.
message = You knot the rope firmly around the stump.
move = rope to riverbank
set = rope_tied
score = 5
once = yes
done = The rope is already tied.

[action: go north]
where = riverbank
if = not flag fallen_tree
fail = A fallen tree blocks the path north.
```

| Key | Meaning |
|---|---|
| `id` | A name for this action, used in save files to remember `once` and scoring. Optional; see "Action ids" below. |
| `also` | Other phrases that trigger this same action, comma-separated (e.g. `also = go down, descend well`). Each is normalized like the main phrase. Optional. |
| `where` | Room id(s), comma-separated, or `anywhere`. Required. |
| `if` | Conditions, comma-separated; **all** must be true. Optional. |
| `fail` | Message when the conditions are false. If omitted, the engine falls through to normal handling (as if this action didn't exist). |
| `message` | Text shown when the action succeeds. |
| `go` | Move the player to this room (and describe it). |
| `score` | Points awarded — only the first time this action succeeds. |
| `set` / `clear` | Turn flags on or off (comma-separated). |
| `move` | `item to place` where place is a room id, `here`, `inventory` or `nowhere`. Several allowed, comma-separated. Use this to create, destroy, or swap items (e.g. `move = lamp to nowhere, lit_lamp to inventory`). |
| `end` | Trigger an ending by id (see 5.8). |
| `once` | `yes` = the action only works once; after that the `done` message is shown (or normal handling if no `done`). |

**What happens when an action runs.** When an action's phrase and `where` match:

1. If it is `once = yes` and has already succeeded: show `done` and end the turn, or, if there is no `done`, treat the action as if it didn't exist. This check comes **before** the `if` conditions, because those are often no longer true afterwards (after "tie rope to well", the player no longer `has rope`, but should see "The rope is already tied", not "You don't have anything to tie").
2. Otherwise, if its conditions pass, apply its effects in this order: show `message`; apply `move`; apply `set`, then `clear`; award `score` (first success only); mark it completed; then `go` (move the player and describe the new room, awarding that room's points); then `end`.
3. The turn is over; built-in handling does **not** also run. **One exception — movement overrides:** if the phrase is a plain movement (verb `go` plus only a direction, e.g. `go north`) and the action has no `go`, then after the effects above the player moves through the room's normal exit for that direction.

So an action on `go north` with `if` and `fail` acts as a locked or blocked door, and when its conditions pass the normal exit is used.

**Choosing among several actions.** The same phrase may appear in several `[action]` sections (e.g. different rooms or different conditions). The engine tries them in file order and uses the first whose `where` matches and whose conditions pass; if none pass, it shows the first matching `fail` message; if none have a `fail`, normal handling continues as if no action existed.

**Action ids.** Each action has an id used to remember `once` and awarded `score` in save files. If the author gives `id = ...`, that is used (must be unique; duplicates are an error). Otherwise the engine generates one from the main phrase's normalized form and the first `where` room, adding `#2`, `#3`, … for repeats in file order (e.g. `talk agnes@lane#2`). Generated ids can shift if the author reorders actions, which only matters for old saves (already covered by the fingerprint warning in 4.4).

**Conditions:**

| Condition | True when |
|---|---|
| `has item` | item is in inventory |
| `here item` | item is in the current room or inventory |
| `flag name` | flag is set |
| `in room` | player is in that room |
| `visited room` | player has been to that room |
| `score >= N` (also `>`, `<`, `<=`, `=`) | score comparison |
| `moves >= N` (same operators) | move-count comparison |
| `not <any of the above>` | negation |

Condition grammar (used by `if`, `when` lines and ending `when`): each condition is either `[not] (has|here|flag|in|visited) <id>` or `[not] (score|moves) (>=|<=|>|<|=) <number>`, case-insensitive, with any amount of space around operators.

Flags don't need to be declared; using a flag name creates it (the validator warns about flags that are checked but never set, which usually means a typo).

### 5.7 Darkness

A room with `dark = yes` shows only "It is pitch dark. You might be eaten by something." unless an item with `light = yes` is in the room or inventory. In the dark the player can still move and use actions, but the room's description and `when` extras aren't shown, and items in the room aren't listed and can't be taken or examined (items in the inventory still can). (A small nod to Zork's grue — the exact text can be overridden with `dark_text = ...` in the room.)

### 5.8 `[ending: id]` — wins and losses

```ini
[ending: found_locket]
type = win
when = has locket, in riverbank
text = You clasp the locket around your neck as the sun breaks
    through the clouds. Grandmother would be proud.

[ending: drowned]
type = lose
text = The water closes over your head. That was unwise.
```

- `type` is `win` or `lose`.
- `when` (optional) is checked after every turn that counts as a move; if true, the ending triggers.
- The final score shown includes any points awarded by the action that triggered the ending.
- Endings without `when` only trigger from an action's `end = id`.
- When an ending triggers: show its text, the final score (`You scored 85 out of 100 in 112 moves.`), and offer buttons **Restart**, **Load a Save**, **Choose Another Adventure**. The input line is disabled until one is chosen.

At least one `win` ending is required.

### 5.9 Complete Minimal Example

```ini
# The smallest possible adventure
[game]
title = The Locked Shed
author = Mom
start = yard
intro = You need a hammer from the shed.

[room: yard]
name = Back Yard
first = A tidy yard. A wooden shed stands to the east.
exits = east: shed

[room: shed]
name = Tool Shed
first = Dusty shelves line the walls.
exits = west: yard

[item: key]
name = brass key
aliases = key, brass key
location = yard
here = A brass key glints in the grass.
points = 10

[item: hammer]
name = hammer
location = shed
here = A hammer hangs on a hook.
points = 40

[action: go east]
where = yard
if = has key
fail = The shed door is locked.
message = You unlock the shed door and step inside.

[ending: done]
type = win
when = has hammer, in yard
text = Hammer in hand, you head back to the house. Well done!
```

## 6. The Command Parser

The **same normalization pipeline** is applied to player input and to every `[action: ...]` phrase in the file. Matching is then done on the normalized forms. This is what lets the author write one phrase and have many phrasings work.

### 6.1 Pipeline

1. **Split** into separate commands on `.`, `,`, `;`, and the word `then` ("take rope, then go north" is two commands). This happens before punctuation is removed. (Don't split on `and`; "take rope and pie" is out of scope for version 1.)
2. **Clean** each command: lowercase; delete apostrophes ("agnes's" → "agness"); replace every other character that isn't a letter, digit or underscore with a space (underscores are kept so an item id like `brass_key` stays one word); collapse runs of spaces; drop a leading "please". Then apply the author's `[vocabulary]` replacements (each word on the right is replaced by the word on the left). Item aliases and `[vocabulary]` words go through this same cleaning when the file is loaded, so they always line up with player input.
3. **Movement shortcuts:** if the whole command is a direction or its abbreviation (`n`, `north`, `in`, `up`…), or a movement verb (`go`, `walk`, `climb`, …) followed by only a direction, the result is `(go, [direction])` with the full direction name. Abbreviations are always expanded, so a player's `n` matches an author's `[action: go north]`.
4. Replace multi-word verb phrases using the synonym table, longest first ("climb into" → `enter`, "pick up" → `take`, "look at" → `examine`). Then replace remaining single-word verbs with their canonical verb.
5. **Context rules** (keep these in one clearly-commented place):
   - `climb` followed by a direction word becomes `go` ("climb down the well" → `(go, [down, well])`; "climb up" → `(go, [up])`).
   - `move` followed by a direction becomes `go`; otherwise it means `push` ("move the rock").
   - `look` with a noun means `examine`.
   - `enter` with no noun becomes `go in`; `exit` with no noun becomes `go out`. (This must not depend on the current room, because action phrases are normalized once, at load time.)
   - `leave` with a noun means `drop`; on its own it means `exit`.
6. **Resolve nouns:** match item aliases (longest first, including multi-word aliases and author noun synonyms) to items. An item id written exactly (e.g. `brass_key`) refers only to that item. Unmatched words stay as plain words (so scenery words in action phrases still match when no item is defined).
   - In **action phrases** (at load time), a word that is an alias of several items stands for **any** of them, so `[action: tie rope to well]` works with whichever rope the player means.
   - In **player input**, if several items share the alias, prefer those that are present (room or inventory). One present → that one. Several present → ask "Which do you mean…?" (6.3). None present → keep the word for the "You don't see any 'rope' here." message.
   - In player input, `it` / `them` / `him` / `her` mean the last item the player referred to.
7. Remove filler words: `the, a, an, some, of, to, into, in, on, onto, at, with, from, using, up, down` (multi-word aliases like "coil of rope" were already matched in step 6) — but never a direction that step 3 or 5 already turned into a noun of `go`, and only after step 4, so "pick up", "go in", "turn on" are already handled.
8. Result: `(verb, [noun1, noun2, ...])`.

**Matching player input to an action:** the verbs must be equal, and the nouns must be the **same set** regardless of order — no extra nouns, none missing. So `give the pie to agnes`, `offer agnes the apple pie` and `hand agnes pie` all match `[action: give pie to agnes]`, but `climb down the well with the rope` does not match `climb down the well` (the author can list it in `also` if she wants it).

**Describing words:** an unknown word (or an unbroken run of them) that comes directly before an item's name is a *describing word*, like "old" in "the old willow" or "big shiny" in "the big shiny key". The engine tries an exact match first, so an author who writes describing words into a phrase on purpose (`[action: polish dull key]`) still gets them honored. Only if no action matches exactly does it try again with describing words ignored on both sides. Built-in commands (6.3) always ignore describing words, so "take the shiny key" is just "take key". Unknown words anywhere else (not right before an item's name) are never ignored: "examine the lantren" still says "You don't see any 'lantren' here."

Example — all of these normalize to `(enter, [river])`:
`jump in the river`, `wade into river`, `get in river`, `go into the river`, `enter river`, `climb in river`.

### 6.2 Built-in Verb Synonyms (starting set — extend generously)

| Canonical | Synonyms |
|---|---|
| `go` | walk, run, move, head, travel, climb (when followed by a direction); `descend` = go down, `ascend` = go up |
| `enter` | go in, go into, get in, get into, jump in, jump into, climb in, climb into, step in, step into, wade in, dive in, hop in, crawl in, enter |
| `exit` | leave, get out, climb out, go out, step out |
| `take` | get, grab, pick up, carry, collect, snatch |
| `drop` | put down, discard, leave (with a noun), throw away |
| `examine` | x, look at, look in, look inside, look under, inspect, study, read, check, l at |
| `look` | l, look around |
| `inventory` | i, inv, items |
| `use` | apply, utilize |
| `put` | place, insert, set |
| `open` / `close` | — / shut |
| `push` / `pull` | press, shove / tug, yank |
| `talk` | talk to, speak to, speak with, chat with, greet, say hello to, ask |
| `give` | offer, hand, present |
| `light` | turn on, switch on, ignite |
| `show`, `tie`, `cut`, `eat`, `drink`, `climb`, `jump`, `swim`, `wait` (z), `again` (g) | add sensible synonyms |

Put the table in its own module/data file so it's easy to extend.

### 6.3 Turn Resolution Order

1. Empty input → do nothing.
2. Meta commands (`save`, `load`, `restart`, `score`, `exits`, `hint`, `help`, `quit`) — handled immediately, don't count as moves. A meta word only counts as a meta command when typed on its own, so `[action: save the cat]` still works. `exits` lists the current room's `exits` directions in standard order (`Obvious exits: north, east, down.`); ways opened only by actions aren't listed, and in an unlit dark room it says it's too dark to see the way out.
3. **Author actions** matching the current room (section 5.6).
4. Built-in commands: movement, `look`, `examine`, `take`, `take all`, `drop`, `drop all`, `inventory`, `wait`, `again`.
5. Nothing matched → a friendly, varied message ("I don't know how to do that.", "That doesn't seem to work.", "You can't do that here."). If the verb was understood but the noun wasn't, say so: "You don't see any 'lantren' here."
6. After any turn that counts as a move: increment moves, check `[ending]` conditions, update the status bar.

**What counts as a move:** any command whose verb was understood, even if it failed ("You can't go that way" still takes a turn, as in Zork). Meta commands, empty input, input with no recognizable verb, and the game asking a question back ("What do you want to take?", "Which do you mean…?") do not.

If the first word isn't a verb but is an item's name ("rope"), reply "What do you want to do with the coil of rope?" rather than "I don't know the word".

Built-in behavior notes:

- `take X` fails politely for items not present, `take = no` items (show `take_fail`), or items already held.
- `examine X` works for items in the room or inventory (including scenery); falls back to "You see nothing special about the X."
- `use X` / `use X with Y` / `put X in Y` with no matching action → "Nothing happens."
- `talk to X` / `give X to Y` / `show X to Y` with no matching action → "There's no response." (for a present item), or the usual "You don't see any…" if X isn't here.
- If a noun is ambiguous (two visible items share an alias), ask "Which do you mean, the brass key or the iron key?" and accept a one-word answer on the next line.
- `again`/`g` repeats the last command.

## 7. Validator ("Check Adventure")

Runs on load and from the Author menu / start screen. Produces a report of **errors** (game can't start), **warnings** (game runs, but something looks wrong) and **notes** (purely informational, such as one-way exits). Every message includes the **line number** and plain-English wording, written for a non-programmer.

Errors:
- Syntax problems: text before the first section, a line that isn't `key = value` (with the "did you forget to indent?" hint from 5.1), a section header with an unknown type.
- Missing `[game]`, missing `title` or `start`, `start` room doesn't exist.
- Duplicate room/item/ending ids, or duplicate action `id`s.
- Exit, `go`, `where`, `move`, `location` or `end` refers to a room/item/ending that doesn't exist. Suggest the closest existing id ("Did you mean 'kitchen'?") using `difflib`.
- Malformed condition.
- No `win` ending.

Warnings:
- Rooms that can't be reached from the start room (following exits and `go` actions).
- Items in `nowhere` that no action ever moves.
- Flags checked in conditions but never set (or set but never checked).
- Unknown keys (likely typos), and repeated single-use keys in one section.
- `max_score` doesn't match the computed total.
- Exits that are one-way (room A goes north to B, but B has no exit back) — reported as a **note**, since this is often intentional.
- An action phrase whose verb isn't a known verb (still works, but the author may want to add synonyms in `[vocabulary]`). A verb that appears on the left side of `[vocabulary]` counts as known.

## 8. Deliverables

1. The working program (`adventure.py`, `engine/`, `gui/`).
2. `adventures/tutorial.adv` — a small (6–10 rooms) but complete adventure that demonstrates **every** feature: first/again descriptions, `when` extras, all exit types, scenery, multi-word aliases, a locked door via action override, an item combination, a dark room and a light source, flags, `once`/`done`, scoring from rooms/items/actions, a lose ending and a win ending. Heavily commented so it doubles as a template.
3. `adventures/agnes_and_the_well.adv` — the four-room example adventure already in the `adventures/` folder. Keep it unchanged; it must load with **zero errors and zero warnings** (other than the informational one-way-exit note) and be winnable for 100/100. Add a unit test that plays it start to finish with the walkthrough in its header comment and also tries alternate phrasings: "speak with the old woman", "offer pie to agnes", "give agnes the pie", "knot rope to crank", "descend well", "climb rope" (at the bottom), and "examine rope" / "take rope" after the rope is tied (must describe the tied rope, not say it isn't there).
4. `docs/AUTHORING.md` — a friendly guide for the author, written for someone who has never programmed. Start with the minimal example (5.9), then introduce one feature at a time with short examples, and end with a cheat-sheet of every section, key and condition. Include a "Troubleshooting" section explaining common validator messages.
5. `docs/notepadpp-adv.xml` — a Notepad++ User Defined Language file that colors section headers, keys, comments and `~` paragraph breaks for `.adv` files, plus instructions in AUTHORING.md on how to import it.
6. `README.md` — how to install Python on Windows and Linux, how to run the program, and where to put adventure files.
7. Unit tests covering: file parsing (including continuation lines, blank-line paragraphs, `~`, comments on text vs. non-text keys, BOM, CRLF, `when` lines containing `=` in the condition), the normalization pipeline (especially the synonym examples in 6.1, context rules, and order-independent noun matching), shared-alias resolution, condition evaluation, action resolution order, effect order and fall-through, movement overrides, scoring awarded only once, save/load round-trip, Reload and Replay, and every validator check.

## 9. Out of Scope for Version 1 (possible later)

- A dedicated character system (conversation trees, characters that move around). In version 1, characters are scenery items (`take = no`) and conversations are `talk to` / `give` actions whose responses change with flags, as shown in `agnes_and_the_well.adv`.
- Containers holding items (boxes, bags) beyond what actions with `move` can simulate.
- Timed events / daemons.
- Sound or images.
- A graphical world editor.

## 10. Implementation Notes for Claude Code

- Keep the engine (parsing, state, rules) completely separate from the GUI so it can be tested without tkinter and could later get a terminal front end.
- Prefer clear, well-commented code over cleverness; the owner may want to read and modify it.
- Build in this order: file loader + validator → normalizer → game state and turn resolution (test with a simple text-mode loop) → tutorial adventure → GUI → save/load → docs.
- Test on both Windows and Linux path conventions (`pathlib`) and with files saved by Notepad++ in its default settings.
