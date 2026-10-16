# How to Write Your Own Text Adventure

Welcome! This guide shows you how to write your own adventure game, one small step at a time.

You don't need to know anything about programming. An adventure is just a plain text file that you write in Notepad++. You describe your rooms, the things in them, and what happens when the player does something special. The game takes care of everything else.

Take it slowly. Try each example as you go. You can't break anything, and the game will tell you if something needs fixing.

---

## What's in This Guide

1. [Getting Started](#getting-started)
2. [Your First Adventure](#your-first-adventure)
3. [The Writing Rules](#the-writing-rules)
4. [Rooms](#rooms)
5. [Things the Player Can Pick Up](#things-the-player-can-pick-up)
6. [Scenery](#scenery)
7. [Special Commands](#special-commands)
8. [Conditions: "Only If..."](#conditions-only-if)
9. [Flags: Remembering What Happened](#flags-remembering-what-happened)
10. [Making Things Appear and Disappear](#making-things-appear-and-disappear)
11. [Locked Doors](#locked-doors)
12. [Things That Only Happen Once](#things-that-only-happen-once)
13. [Characters and Conversations](#characters-and-conversations)
14. [Descriptions That Change](#descriptions-that-change)
15. [Dark Rooms and Lamps](#dark-rooms-and-lamps)
16. [Points and Scoring](#points-and-scoring)
17. [Winning and Losing](#winning-and-losing)
18. [Teaching the Game New Words](#teaching-the-game-new-words)
19. [Testing Your Adventure](#testing-your-adventure)
20. [Helpful Tips](#helpful-tips)
21. [When Something Goes Wrong](#when-something-goes-wrong)
22. [Cheat Sheet](#cheat-sheet)
23. [Colors in Notepad++](#colors-in-notepad)

---

## Getting Started

### Where adventure files go

Every adventure is a file whose name ends in **.adv**, kept in the **adventures** folder inside the program's folder.

The easy way to find that folder: start the game and click **Open Adventures Folder** on the first screen.

There are two adventures in there already:

- **tutorial.adv** (called *Grandma's Locket*) uses every feature in this guide. It's full of notes explaining how it works. It makes a good model to copy from.
- **agnes_and_the_well.adv** is a very short adventure, only four rooms.

Open them in Notepad++ and have a look. It's a good way to learn.

### Making a new adventure

1. Open Notepad++.
2. Choose **File > New**.
3. Type your adventure (start with the example in the next section).
4. Choose **File > Save As...** and save it in the **adventures** folder. Give it a name that ends in **.adv**, such as `haunted_house.adv`.

### Trying it out

1. Start the game (or click **Refresh List** if it's already open).
2. Pick your adventure from the list.
3. Click **Check Adventure**. It will tell you about any mistakes and which line they're on.
4. Click **Play**.

When you change your file, save it in Notepad++, then use **Author > Reload Adventure File** in the game to see your changes. You don't need to close the game.

---

## Your First Adventure

Here is the smallest possible adventure. Copy it into Notepad++ and save it as `locked_shed.adv` in the adventures folder.

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

Play it! Try typing `east` before you have the key, then `take key`, then `east` again.

Here is what each part does:

- `[game]` holds the adventure's title, your name, which room the player starts in (`start = yard`), and the opening words (`intro`).
- `[room: yard]` and `[room: shed]` are the two places. `exits` says which way the player can go.
- `[item: key]` and `[item: hammer]` are things the player can pick up. `location` says where each one starts.
- `[action: go east]` is a special command. It stops the player going east until they have the key.
- `[ending: done]` is how the player wins: by carrying the hammer back to the yard.

The rest of this guide explains each part in more detail.

---

## The Writing Rules

There are only a few rules to remember.

### Sections

A file is made of **sections**. Each section starts with a heading in square brackets:

```ini
[room: kitchen]
```

The word before the colon says what kind of section it is (`room`, `item`, `action` and so on). The word after the colon is its **short name**.

### Short names

Short names are how you refer to rooms and things elsewhere in the file. The player never sees them.

- Use letters, numbers and the underscore `_` (no spaces). For example: `kitchen`, `front_porch`, `brass_key`.
- If you do type a space, the game quietly turns it into an underscore.
- Capital letters don't matter. `Kitchen` and `kitchen` are the same.

### Settings

Inside a section, each line is a **setting**: a word, an equals sign, and a value.

```ini
name = Farmhouse Kitchen
points = 5
```

### Long text

To make text longer, keep going on the next line. **Start each extra line with a space or a tab.**

```ini
first = The kitchen smells of fresh bread. A big pine table
    stands in the middle of the room, and a door leads out
    to the porch.
```

You can break the lines wherever you like. The game joins them up and wraps the text to fit the window.

> **Important:** if you forget the space at the start of an extra line, the game thinks it's a new setting and gets confused. **Check Adventure** will point to the line and remind you.

### New paragraphs

To start a new paragraph inside long text, leave a blank line, then carry on (still with a space at the start):

```ini
intro = It has rained for three days.

    Your grandmother's locket is somewhere down by the river.
```

You can also put a line with just a `~` on it. It does the same thing:

```ini
intro = It has rained for three days.
    ~
    Your grandmother's locket is somewhere down by the river.
```

### Notes to yourself (comments)

Any line that starts with `#` is a note for you. The game ignores it.

```ini
# Remember to add a key for the attic later!
```

Put notes on a line of their own.

### Quotation marks

Use ordinary quotation marks for people talking. They show up exactly as you type them.

```ini
message = "Hello, dear," Agnes says.
```

---

## Rooms

```ini
[room: riverbank]
name = Muddy Riverbank
first = The river roars past, brown and swollen. A path climbs
    north into the woods.
again = The muddy riverbank. The woods are north.
exits = north: forest_path, down: cellar
points = 5
```

| Setting | What it does |
|---|---|
| `name` | The room's name. It's shown at the top of the window and as a heading. |
| `first` | The full description, shown the first time the player arrives (and whenever they type `look`). |
| `again` | A shorter description for later visits. You can leave this out, and the game will use `first` every time. |
| `exits` | The ways out. Write a direction, a colon, then the short name of the room it leads to. Separate them with commas. |
| `points` | Points the player gets the first time they come here. You can leave this out. |

### Directions

These are the directions you can use in `exits`:

`north`, `south`, `east`, `west`, `northeast`, `northwest`, `southeast`, `southwest`, `up`, `down`, `in`, `out`

Players can type them in full or in short (`n`, `s`, `e`, `w`, `ne`, `nw`, `se`, `sw`, `u`, `d`). They can also say `go north`, `walk north` or `climb up`. You don't have to do anything for that to work.

> **Remember:** exits only go one way. If the kitchen has `north: hall`, the hall needs `south: kitchen` so the player can get back.

---

## Things the Player Can Pick Up

```ini
[item: rope]
name = coil of rope
aliases = rope, coil, hemp rope
location = riverbank
here = A coil of rope lies in the mud.
examine = Twenty feet of sturdy hemp, still damp.
points = 5
```

| Setting | What it does |
|---|---|
| `name` | What the game calls it, as in "You are carrying: coil of rope". |
| `aliases` | Other words the player might use for it, separated by commas. The name and the short name always work, so you don't need to repeat them. |
| `location` | Where it starts: a room's short name, `inventory` (the player starts out carrying it), or `nowhere` (it isn't in the game yet; see [Making Things Appear and Disappear](#making-things-appear-and-disappear)). |
| `here` | The sentence shown in the room description while it's lying there. |
| `examine` | What the player sees when they type `examine rope` or `look at rope`. |
| `points` | Points the player gets the first time they have it. You can leave this out. |

The game already knows how to `take`, `drop` and `examine` things, and how to list what the player is carrying (`inventory`). You don't have to write any of that.

### Aliases with more than one word

Aliases can be several words long:

```ini
aliases = rope, coil, coil of rope, old rope
```

---

## Scenery

Scenery is anything the player can look at but can't carry, such as a tree, a river, a fireplace or a painting.

```ini
[item: willow]
name = willow tree
aliases = willow, tree, old willow, roots
location = riverbank
examine = The old willow's roots grip the bank like fingers.
take = no
take_fail = The willow has stood here for a hundred years.
```

- `take = no` means it can't be picked up.
- `take_fail` is what the game says when the player tries.
- Leave out `here`. The room's description already mentions the willow, so it doesn't need its own sentence.

> **Tip:** Every time you mention something interesting in a description, make it scenery so the player can look at it. Players love to `examine` everything!

---

## Special Commands

Special commands (called **actions**) are where the fun happens. An action says: *"When the player types this, in this room, do this."*

```ini
[action: ring the bell]
where = chapel
message = The bell rings out across the valley. Somewhere far
    off, a dog starts barking.
```

The words after `action:` are the command. **Write it the way a player would say it.** The game understands lots of other ways of saying the same thing. For example, this one action:

```ini
[action: enter river]
where = riverbank
message = You wade in. The water is freezing!
```

...also works when the player types `jump in the river`, `wade into river`, `get in the river`, `go into the river` or `climb in river`.

The order of the words doesn't matter either. `[action: give pie to agnes]` also works for `give agnes the pie` and `offer the pie to Agnes`.

Players often add describing words, like `give the warm pie to dear old Agnes`. The game quietly skips any word it doesn't know when it comes just before the name of a thing, so that works too.

### More ways of saying it: `also`

If you think of other ways a player might say something, list them with `also`:

```ini
[action: climb down the well]
also = go down, enter well, descend well, climb down rope
where = well_yard
message = You climb down into the cool darkness...
go = well_bottom
```

### Which rooms: `where`

`where` is required. It can be:

- one room: `where = kitchen`
- several rooms: `where = riverbank, sandbar`
- every room: `where = anywhere`

### What an action can do

| Setting | What it does |
|---|---|
| `message` | Shows some text. |
| `go` | Moves the player to another room (and describes it). |
| `move` | Moves things around. See [Making Things Appear and Disappear](#making-things-appear-and-disappear). |
| `set` / `clear` | Turns flags on or off. See [Flags](#flags-remembering-what-happened). |
| `score` | Gives the player points. They only get them once, however many times they do it. |
| `end` | Ends the game. See [Winning and Losing](#winning-and-losing). |

---

## Conditions: "Only If..."

Often an action should only work in certain situations. Use `if` for that, and `fail` for what to say when it doesn't work:

```ini
[action: tie rope to well]
where = well_yard
if = has rope
fail = You don't have anything to tie.
message = You knot the rope firmly around the crank.
```

Here are all the conditions you can use:

| Condition | It's true when... |
|---|---|
| `has rope` | the player is carrying the rope |
| `here rope` | the rope is in this room, or the player is carrying it |
| `flag door_open` | an action has turned on the flag `door_open` |
| `in kitchen` | the player is in the kitchen |
| `visited cellar` | the player has been to the cellar at some point |
| `score >= 50` | the score is 50 or more (you can also use `>`, `<`, `<=` and `=`) |
| `moves < 100` | fewer than 100 turns have passed (same choices as for score) |

Put `not` in front of any of these to turn it around: `not has rope`, `not flag door_open`, `not visited cellar`.

To require several things at once, separate them with commas. **All** of them must be true:

```ini
if = has lamp, has matches, not flag lamp_lit
```

> **What if there's no `fail`?** If the conditions aren't true and there's no `fail` line, the game carries on as if your action wasn't there. That's useful sometimes, as you'll see below.

---

## Flags: Remembering What Happened

A **flag** is like a light switch. It's either on or off. Use flags to remember that something has happened.

Turn a flag on with `set`, and off with `clear`:

```ini
[action: open window]
where = bedroom
if = not flag window_open
fail = It's already open.
message = You push the window open. A cool breeze blows in.
set = window_open

[action: close window]
where = bedroom
if = flag window_open
fail = It's already closed.
message = You pull the window shut.
clear = window_open
```

You can name a flag anything you like (no spaces). You don't need to set them up in advance; just start using them.

Then check the flag in other places with `flag window_open` or `not flag window_open`.

---

## Making Things Appear and Disappear

Use `move` to put a thing somewhere else. Write the thing's short name, the word `to`, then where it should go:

| Where | Meaning |
|---|---|
| a room's short name | put it in that room |
| `here` | put it in the room the player is in |
| `inventory` | put it in the player's hands |
| `nowhere` | take it out of the game |

### Things that appear

A thing whose `location` is `nowhere` isn't in the game at the start. An action can bring it in:

```ini
[item: matches]
name = box of matches
aliases = matches, match
location = nowhere
here = A box of matches sits in the open drawer.

[action: open drawer]
where = kitchen
message = You pull open the drawer. Inside is a box of matches.
move = matches to here
```

### Swapping one thing for another

To change a thing (an unlit lamp becoming a lit lamp, say), make two items and swap them. You can move several things at once by separating them with commas:

```ini
[item: lamp]
name = oil lamp
aliases = lamp, lantern
location = kitchen
here = An old oil lamp hangs on a hook.
examine = It's full of oil, but it isn't lit.

[item: lit_lamp]
name = lit oil lamp
aliases = lamp, lantern
location = nowhere
here = A lit oil lamp glows here.
examine = The little flame burns steady and bright.
light = yes

[action: light lamp with matches]
also = light lamp
where = anywhere
if = has lamp, has matches
fail = You'll need the lamp and something to light it with.
message = The lamp flickers, then glows warm and bright.
move = lamp to nowhere, lit_lamp to inventory
```

Notice that both lamps answer to "lamp". That's fine. The game always picks the one that's actually in front of the player.

---

## Locked Doors

Your actions are checked **before** the game's normal commands. That means you can change what an ordinary command like `go east` does.

```ini
[action: go east]
where = garden
if = has key
fail = The shed door is locked.
message = You unlock the shed door with the key.
```

Without the key, the player sees "The shed door is locked." and stays put. With the key, they see the message **and then walk through the exit as normal**. You don't need a `go` line, because the room's own exit is used.

If you'd rather the message only appears the first time, use a flag and two actions:

```ini
[action: go east]
where = garden
if = flag shed_unlocked

[action: go east]
where = garden
if = has key
fail = The shed door is locked.
message = You unlock the shed door with the key.
set = shed_unlocked
```

The first action lets the player straight through once the shed is unlocked. The second does the unlocking. (When there are several actions for the same command, the game tries them in order. There's more about this under [Characters and Conversations](#characters-and-conversations).)

---

## Things That Only Happen Once

Add `once = yes` to make an action work only one time. Use `done` for what to say if the player tries again:

```ini
[action: tie rope to well]
where = well_yard
if = has rope
fail = You don't have anything to tie.
message = You knot the rope firmly around the crank.
move = rope to nowhere
set = rope_tied
score = 10
once = yes
done = The rope is already tied securely.
```

If you leave out `done`, then after the first time the game acts as if the action isn't there.

---

## Characters and Conversations

A character is simply scenery that the player can talk to:

```ini
[item: agnes]
name = Agnes
aliases = old woman, woman, neighbor
location = lane
here = Old Agnes sits on the bench, fanning herself.
examine = Agnes has lived in the village longer than anyone.
take = no
take_fail = Agnes would not appreciate that one bit.
```

To make a conversation that changes as the story goes on, write **several actions with the same command**. The game tries them **from top to bottom** and uses the **first one whose `if` is true**. So put the most particular ones first and the plain, everyday one last:

```ini
[action: talk to agnes]
where = lane
if = flag ring_returned
message = Agnes just smiles and turns the ring on her finger.

[action: talk to agnes]
where = lane
if = flag fed_agnes
message = "That well swallowed my wedding ring," Agnes says.

[action: talk to agnes]
where = lane
message = "Hello, dear," Agnes says. "I'm ever so hungry."
```

Players can say `talk to agnes`, `speak with the old woman`, `chat with Agnes`, `greet agnes` or `ask agnes`. They all work.

Giving a character something works the same way:

```ini
[action: give pie to agnes]
where = lane
if = has pie
fail = You don't have anything she'd want.
message = Agnes's face lights up. "Oh, my favorite!"
move = pie to nowhere, rope to inventory
set = fed_agnes
score = 15
once = yes
```

---

## Descriptions That Change

### Extra sentences in a room

A `when` line adds a sentence to a room's description, but only while its condition is true. You can have as many as you like:

```ini
[room: well_yard]
name = The Old Well
first = Tall grass surrounds a round stone well.
exits = south: lane
when flag rope_tied = A rope hangs from the crank, down into the dark.
when moves >= 50 = The afternoon shadows are growing long.
```

The pattern is: `when`, then the condition, then `=`, then the sentence.

### Things that look different

For items, use `here when` and `examine when` in the same way. The game uses the first one whose condition is true. If none of them are true, it uses the plain `here` or `examine`:

```ini
[item: agnes]
name = Agnes
location = lane
here = Old Agnes sits on the bench, fanning herself.
examine = Her eyes are kind, but she looks a little sad today.
examine when flag fed_agnes = Agnes looks much happier now.
take = no
```

---

## Dark Rooms and Lamps

Put `dark = yes` in a room to make it dark:

```ini
[room: cellar]
name = Root Cellar
first = Shelves of jars line the cool stone walls.
exits = up: kitchen
dark = yes
dark_text = It is pitch dark. You can smell damp earth.
```

In a dark room the player only sees the `dark_text`, unless they're carrying something with `light = yes` (or one is lying in the room). They can still walk around, but they can't see or pick up anything in the room.

`dark_text` is optional. If you leave it out, the player sees: *"It is pitch dark. You might be eaten by something."*

To make a light, give an item `light = yes`:

```ini
[item: lantern]
name = brass lantern
location = hall
here = A brass lantern stands by the door.
light = yes
```

---

## Points and Scoring

Players get points in three ways, and only ever once for each:

- **Visiting a room for the first time:** `points = 5` in the room
- **Getting hold of a thing for the first time:** `points = 10` in the item
- **Doing a special action for the first time:** `score = 15` in the action

(`points` and `score` mean exactly the same thing. Use whichever you like.)

The game adds up all the points for you and shows them at the top of the window, as in "Score: 15 / 100".

If you'd like, you can write the total in the `[game]` section yourself:

```ini
max_score = 100
```

If it doesn't match the real total, **Check Adventure** will let you know.

---

## Winning and Losing

Every adventure needs at least one **winning** ending. You can also have losing ones.

```ini
[ending: found_locket]
type = win
when = has locket, in riverbank
text = You clasp the locket around your neck as the sun breaks
    through the clouds. Grandmother would be proud.
    ~
    *** You have won ***

[ending: drowned]
type = lose
text = The water closes over your head. That was unwise.
```

- `type` is `win` or `lose`.
- `when` is checked after every turn. As soon as it's true, the game ends.
- An ending without `when` only happens when an action says so with `end`:

```ini
[action: jump in the river]
where = riverbank
message = You leap into the swirling brown water...
end = drowned
```

When the game ends, the player sees your text and their final score, then buttons to play again, load a saved game, or pick another adventure.

---

## Teaching the Game New Words

The game already knows hundreds of words. If you'd like it to know more, add a `[vocabulary]` section.

Each line means: *"the word on the left also answers to the words on the right."*

```ini
[vocabulary]
tie = knot, fasten, lash
locket = pendant, necklace
whistle = toot
```

- `tie = knot, fasten, lash` means `knot rope to post` now works anywhere `tie rope to post` does.
- `locket = pendant, necklace` means players can say `take the necklace`.
- `whistle = toot` teaches the game a brand-new word. `whistle` isn't a word the game knew before, so listing it here also stops **Check Adventure** from warning you about it.

### Words the game already knows

You never need to teach it these. They already come with lots of other ways of saying them:

> go, enter, exit, take, drop, examine, look, inventory, use, put, open, close, unlock, lock, push, pull, turn, talk, give, show, tie, untie, cut, light, extinguish, eat, drink, climb, jump, swim, wait, again, break, throw, listen, smell, touch, dig, fill, empty, wear, remove, sit, sleep, pray, knock, kiss, hug, wave, sing, yell

For example, `take` also understands `get`, `grab`, `pick up` and `carry`, and `examine` also understands `look at`, `x`, `inspect`, `read` and `check`.

---

## Testing Your Adventure

The **Author** menu (at the top of the game window) has tools to help you test.

| Menu item | What it does |
|---|---|
| **Check Adventure** | Looks through your file for mistakes. See [When Something Goes Wrong](#when-something-goes-wrong). |
| **Reload Adventure File** | Reads your file again and starts from the beginning. Use this after saving changes in Notepad++. |
| **Reload and Replay** | Reads your file again, then quietly repeats everything you've typed so far, so you end up right back where you were. This is a great time-saver! |
| **Show Flags & State** | Opens a small window showing the score, which flags are on, what the player is carrying and where everything is. It updates as you play. |
| **Go To Room...** | Jumps straight to any room. Handy for testing the end of a long adventure. (It doesn't give you that room's points.) |

### A good way to work

1. Keep Notepad++ and the game open side by side.
2. Write a little, then save.
3. In the game, choose **Author > Reload and Replay**.
4. Try out what you just wrote.
5. Repeat!

> **About saved games:** if you change an adventure after saving a game, the game will warn you when you load that save. It will still try its best to load it.

---

## Helpful Tips

**Give things all the names you use for them.** If your description says "an old willow tree", players might call it the `willow`, the `tree` or the `willow tree`, so give it all three as aliases. Describing words are taken care of for you: as long as "willow" is an alias, `tie rope to the old willow` and `tie rope to the gnarled willow` both work. But if "tree" isn't an alias, `tie rope to the tree` won't find your action.

**Make scenery for everything you describe.** If a room mentions a fireplace, players will type `examine fireplace`.

**Write actions the way a player would type them.** `[action: tie rope to willow]` is better than `[action: rope willow]`.

**Use `also` generously.** If you can think of another way to say it, add it.

**Start small.** Get two or three rooms working, then add more.

**Copy from the tutorial.** `tutorial.adv` has an example of everything. Find the part that does what you want, copy it, and change the words.

**Play your adventure all the way through** before you share it, and ask someone else to try it. They'll type things you never thought of!

---

## When Something Goes Wrong

**Check Adventure** lists three kinds of messages:

- **Errors** must be fixed before the adventure can be played.
- **Warnings** won't stop the game, but something probably isn't right.
- **Notes** are just for your information.

Each message tells you the **line number**. In Notepad++, press **Ctrl+G** and type the number to jump straight to that line.

Here are the messages you're most likely to see, and what to do about them.

### "This line doesn't look like a setting"

> *This line doesn't look like a setting (name = value). If it is part of the text above, start it with a space or tab.*

This almost always means you forgot the space at the start of an extra line of text. Put a space or a tab at the start of the line.

### "This line starts with a space, but there is no setting above it"

A line starts with a space, but there's nothing above it for it to continue. Usually it comes straight after a `[section]` heading. Take the space away.

### "...refers to a room called '...', but there is no such room"

> *The 'north' exit from room 'hall' refers to a room called 'kichen', but there is no such room. Did you mean 'kitchen'?*

There's a spelling mistake in a room's short name. The game will often guess what you meant. The same goes for things ("refers to an item called...") and endings.

### "Malformed condition"

The game didn't understand something in an `if` or `when` line. Check the spelling against the list in [Conditions](#conditions-only-if). A common slip is `have rope` instead of `has rope`.

### "I couldn't read this 'when' line"

A `when` line should look like this: `when flag door_open = The door stands open.` Check that the condition is spelled correctly and that there's an `=` before the sentence.

### "There is no winning ending"

Every adventure needs at least one `[ending: ...]` with `type = win`.

### "...isn't a setting I know"

> *'nmae' isn't a setting I know in a [room] section, so it will be ignored. Did you mean 'name'?*

There's a spelling mistake in a setting's name. Check the [Cheat Sheet](#cheat-sheet) for the right spelling.

### "The flag '...' is checked but never set"

You check a flag in an `if` or `when` line, but no action ever turns it on, so it will always be off. Usually this is a spelling difference, such as `door_open` in one place and `dooropen` in another.

### "The flag '...' is set but never checked"

An action turns a flag on, but nothing ever looks at it. Again, often a spelling difference.

### "Room '...' can't be reached"

There's no exit or action that leads to this room, so the player can never get there. Add an exit, or an action with `go`.

### "Item '...' starts 'nowhere' and no action ever moves it into the game"

This thing has `location = nowhere`, but no action ever brings it in with `move`. Check the spelling in your `move` line.

### "The phrase '...' starts with '...', which isn't a word the game already knows"

The command will still work if the player types exactly those words. But the game doesn't know any other ways of saying it. To fix this, add the word to [vocabulary](#teaching-the-game-new-words), perhaps with some other ways of saying it.

### "max_score is ..., but the points available add up to ..."

The `max_score` you wrote doesn't match the real total. The simplest fix is to delete the `max_score` line and let the game add it up for you.

### "This file isn't saved as UTF-8"

In Notepad++, choose **Encoding > Convert to UTF-8**, then save.

### Note: "...but there is no exit back"

Room A leads to room B, but B doesn't lead back. That's fine if you meant it (a slide you can't climb back up, for example). Otherwise add the missing exit.

---

## Cheat Sheet

### The sections

```ini
[game]                # exactly one, usually at the top
[room: short_name]    # one for each place
[item: short_name]    # one for each thing, scenery or character
[action: command]     # special commands
[ending: short_name]  # wins and losses
[vocabulary]          # extra words (optional)
```

### `[game]`

| Setting | Needed? | Example |
|---|---|---|
| `title` | yes | `title = The Riverbank` |
| `start` | yes | `start = riverbank` |
| `author` | no | `author = Mom` |
| `description` | no | `description = A short adventure about a lost locket.` |
| `intro` | no | `intro = It has rained for three days.` |
| `max_score` | no | `max_score = 100` |

### `[room: ...]`

| Setting | Example |
|---|---|
| `name` | `name = Muddy Riverbank` |
| `first` | `first = The river roars past.` |
| `again` | `again = The riverbank.` |
| `exits` | `exits = north: woods, down: cellar` |
| `points` | `points = 5` |
| `dark` | `dark = yes` |
| `dark_text` | `dark_text = You can't see a thing.` |
| `when` | `when flag rope_tied = A rope hangs here.` |

### `[item: ...]`

| Setting | Example |
|---|---|
| `name` | `name = coil of rope` |
| `aliases` | `aliases = rope, coil` |
| `location` | `location = riverbank` (or `inventory`, or `nowhere`) |
| `here` | `here = A coil of rope lies here.` |
| `examine` | `examine = Twenty feet of sturdy rope.` |
| `take` | `take = no` (for scenery) |
| `take_fail` | `take_fail = It's too heavy.` |
| `points` | `points = 5` |
| `light` | `light = yes` |
| `here when` | `here when flag tied = The rope is tied to the post.` |
| `examine when` | `examine when flag wet = The rope is soaking wet.` |

### `[action: ...]`

| Setting | Example |
|---|---|
| `where` (needed) | `where = kitchen` or `where = hall, stairs` or `where = anywhere` |
| `also` | `also = go down, descend` |
| `if` | `if = has key, not flag door_open` |
| `fail` | `fail = The door is locked.` |
| `message` | `message = The door swings open.` |
| `go` | `go = cellar` |
| `move` | `move = lamp to nowhere, lit_lamp to inventory` |
| `set` | `set = door_open` |
| `clear` | `clear = door_open` |
| `score` | `score = 10` |
| `once` | `once = yes` |
| `done` | `done = You already did that.` |
| `end` | `end = drowned` |
| `id` | `id = open_the_door` (optional; a name used in saved games) |

### `[ending: ...]`

| Setting | Example |
|---|---|
| `type` (needed) | `type = win` or `type = lose` |
| `when` | `when = has locket, in riverbank` |
| `text` | `text = You have won!` |

### `[vocabulary]`

```ini
tie = knot, fasten
locket = pendant, necklace
```

### Conditions

```
has ITEM          here ITEM          flag NAME
in ROOM           visited ROOM
score >= 50       moves < 100        (also >, <, <=, =)
not ...           (in front of any of these)
```

Separate several conditions with commas. All of them must be true.

### Directions

```
north   south   east   west   northeast   northwest
southeast   southwest   up   down   in   out
```

### Places for `move`

```
a room's short name     here     inventory     nowhere
```

### Yes and no

For settings like `take`, `dark`, `light` and `once`, you can write `yes` or `no`.

---

## Colors in Notepad++

Notepad++ can color your adventure files, so section headings, notes and `=` signs stand out. You only need to set this up once.

1. In Notepad++, open the **Language** menu.
2. Choose **User Defined Language**, then **Define your language...**
3. In the window that opens, click **Import...**
4. Find the program's **docs** folder and choose **notepadpp-adv.xml**.
5. Close that window, then close and reopen Notepad++.

From then on, any file ending in **.adv** will be colored automatically:

- `[section headings]` in **bold brown**
- `# notes` in green
- `=` and `~` in blue

If **.adv** files don't change color, open one, then choose **Language > Adventure** from the menu.
