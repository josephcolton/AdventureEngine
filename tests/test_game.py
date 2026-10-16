import unittest

from engine import Game
from tests.helpers import BASIC, game_from, run


class MovementAndLookingTests(unittest.TestCase):
    def setUp(self):
        self.game = game_from(BASIC)

    def test_start_awards_start_room_points(self):
        self.assertEqual(self.game.score, 1)
        self.assertEqual(self.game.visited, ["yard"])

    def test_cant_go_that_way(self):
        self.assertEqual(run(self.game, "w"), "You can't go that way.")
        self.assertEqual(self.game.moves, 1)       # a failed move still counts

    def test_first_then_again(self):
        run(self.game, "take key", "e")
        self.assertIn("The yard.", run(self.game, "w"))
        self.assertIn("A tidy yard", run(self.game, "look"))

    def test_dark_room(self):
        text = run(self.game, "n")
        self.assertIn("pitch dark", text)
        self.assertNotIn("hammer", text)
        self.assertIn("too dark", run(self.game, "take hammer"))
        run(self.game, "s", "take key", "e", "take lamp", "w")
        text = run(self.game, "n")
        self.assertIn("Damp stone walls", text)
        self.assertIn("A hammer lies", text)

    def test_exits(self):
        self.assertEqual(run(self.game, "exits"), "Obvious exits: north, east.")
        self.assertEqual(self.game.moves, 0)       # just information, like score
        run(self.game, "take key", "e")
        self.assertEqual(run(self.game, "exits"), "Obvious exits: west.")
        run(self.game, "w", "n")
        self.assertEqual(run(self.game, "exits"), "It's too dark to see the way out.")

    def test_unknown_word_does_not_count(self):
        self.assertIn("don't know the word", run(self.game, "xyzzy"))
        self.assertEqual(self.game.moves, 0)

    def test_noun_not_here(self):
        self.assertEqual(run(self.game, "examine lantren"),
                         "You don't see any \"lantren\" here.")

    def test_examine_fallback(self):
        self.assertEqual(run(self.game, "x key"), "You see nothing special about the brass key.")

    def test_builtins_ignore_describing_words(self):
        self.assertEqual(run(self.game, "examine the shiny key"),
                         "You see nothing special about the brass key.")
        self.assertEqual(run(self.game, "take the small shiny key"), "Taken.")
        self.assertEqual(run(self.game, "drop the shiny key"), "Dropped.")
        # an unknown word on its own is still reported
        self.assertEqual(run(self.game, "take the lantren"),
                         "You don't see any \"lantren\" here.")

    def test_several_commands_and_again(self):
        run(self.game, "take key, then e")
        self.assertEqual(self.game.current_room, "shed")
        run(self.game, "w", "g")
        self.assertEqual(self.game.current_room, "yard")   # "g" repeated "w": no exit west


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.game = game_from(BASIC)

    def test_locked_door_override(self):
        self.assertEqual(run(self.game, "e"), "The shed door is locked.")
        self.assertEqual(self.game.current_room, "yard")
        run(self.game, "take key")
        text = run(self.game, "go east")
        self.assertIn("You unlock the shed door.", text)
        self.assertEqual(self.game.current_room, "shed")

    def test_actions_ignore_describing_words_only_when_needed(self):
        game = game_from(BASIC + """
[action: polish key]
where = yard
message = It shines.

[action: polish dull key]
where = yard
message = Now it isn't dull any more.
""")
        self.assertEqual(run(game, "polish the old brass key"), "It shines.")
        # an exact match (with the describing word) wins over the loose one
        self.assertEqual(run(game, "polish dull key"), "Now it isn't dull any more.")

    def test_first_passing_action_wins_and_fall_through(self):
        game = game_from(BASIC + """
[action: wave]
where = yard
if = flag a
message = First.

[action: wave]
where = yard
message = Second.

[action: sing]
where = yard
if = flag never
""")
        self.assertEqual(run(game, "wave"), "Second.")
        game.flags.add("a")
        self.assertEqual(run(game, "wave"), "First.")
        # conditions false and no fail: built-in handling as if no action existed
        self.assertEqual(run(game, "sing"), "You hum a little tune to yourself.")

    def test_once_done_and_scoring_once(self):
        game = game_from(BASIC + """
[action: pray]
where = anywhere
message = A warm feeling.
score = 5
once = yes
done = Nothing more happens.

[action: dance]
where = anywhere
message = You dance.
score = 3
""")
        run(game, "pray")
        self.assertEqual(game.score, 6)
        self.assertEqual(run(game, "pray"), "Nothing more happens.")
        run(game, "dance", "dance")
        self.assertEqual(game.score, 9)

    def test_effect_order_and_move(self):
        game = game_from(BASIC + """
[item: gem]
name = gem
location = nowhere
points = 7

[action: dig]
where = yard
message = You dig.
move = gem to inventory, key to nowhere
set = dug
score = 2
go = shed
""")
        text = run(game, "dig")
        self.assertTrue(text.startswith("You dig.\nTool Shed"))
        self.assertEqual(game.item_locations["gem"], "inventory")
        self.assertEqual(game.item_locations["key"], "nowhere")
        self.assertIn("dug", game.flags)
        self.assertEqual(game.score, 1 + 7 + 2)

    def test_action_end_and_final_score(self):
        game = game_from(BASIC + """
[action: jump]
where = yard
score = 4
end = done
""")
        result = game.command("jump")
        self.assertIsNotNone(result.ending)
        self.assertIn("You scored 5 out of", result.text)
        self.assertIn("game is over", run(game, "look"))

    def test_when_ending(self):
        run(self.game, "take key", "e", "take lamp", "w", "n", "take hammer")
        result = self.game.command("s")
        self.assertEqual(result.ending.id, "done")
        self.assertIn("Well done!", result.text)

    def test_which_do_you_mean(self):
        run(self.game, "take key", "e")
        self.assertIn("Which do you mean", run(self.game, "drop key", "x key"))
        self.assertEqual(run(self.game, "iron"), "You see nothing special about the iron key.")


class SaveStateTests(unittest.TestCase):
    def test_round_trip(self):
        game = game_from(BASIC)
        run(game, "take key", "e", "take lamp")
        data = game.to_save("test")
        loaded, warnings = Game.from_save(game.world, data)
        self.assertEqual(warnings, [])
        for attr in ("current_room", "visited", "item_locations", "flags", "score",
                     "awarded", "completed", "moves", "history"):
            self.assertEqual(getattr(loaded, attr), getattr(game, attr), attr)
        # points already awarded are not given again
        run(loaded, "drop key", "take key")
        self.assertEqual(loaded.score, game.score)

    def test_edited_adventure_warns_and_tolerates_missing_things(self):
        game = game_from(BASIC)
        data = game.to_save("x")
        data["adventure_fingerprint"] = "different"
        data["current_room"] = "gone"
        data["item_locations"]["ghost"] = "yard"
        loaded, warnings = Game.from_save(game.world, data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(loaded.current_room, "yard")
        self.assertNotIn("ghost", loaded.item_locations)

    def test_replay(self):
        game = game_from(BASIC)
        run(game, "take key", "save", "e", "xyzzy")
        self.assertEqual(game.history, ["take key", "e", "xyzzy"])
        fresh = Game(game.world)
        fresh.start()
        fresh.replay(game.history)
        self.assertEqual(fresh.current_room, "shed")
        self.assertEqual(fresh.score, game.score)


if __name__ == "__main__":
    unittest.main()
