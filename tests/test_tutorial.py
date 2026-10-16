"""Plays adventures/tutorial.adv and checks each feature it demonstrates."""

import re
import unittest

from engine import Game, load_adventure
from tests.helpers import ADVENTURES, run

PATH = ADVENTURES / "tutorial.adv"


def walkthrough_from_header() -> list[str]:
    """The commands listed under HOW TO WIN in the file's header comment."""
    text = PATH.read_text(encoding="utf-8-sig")
    block = re.search(r"HOW TO WIN.*?\n(.*?)\n#\s*\n#\s*HOW TO LOSE", text, re.S).group(1)
    words = " ".join(line.lstrip("#").strip() for line in block.splitlines())
    return [c.strip() for c in words.split(",") if c.strip()]


class TutorialTests(unittest.TestCase):
    def setUp(self):
        self.world = load_adventure(PATH)
        self.game = Game(self.world)
        self.game.start()

    def test_loads_with_nothing_to_report(self):
        self.assertEqual(self.world.report.messages, [], self.world.report.format())
        self.assertEqual(self.world.total_points, 100)
        self.assertGreaterEqual(len(self.world.rooms), 6)
        self.assertLessEqual(len(self.world.rooms), 10)

    def test_uses_every_direction(self):
        used = {d for room in self.world.rooms.values() for d in room.exits}
        self.assertEqual(used, {"north", "south", "east", "west", "northeast",
                                "northwest", "southeast", "southwest", "up", "down",
                                "in", "out"})

    def test_header_walkthrough_wins_100(self):
        commands = walkthrough_from_header()
        self.assertGreater(len(commands), 20)
        result = None
        for command in commands:
            self.assertIsNone(self.game.ended, f"ended early before '{command}'")
            result = self.game.command(command)
        self.assertEqual(self.game.ended, "locket_home")
        self.assertEqual(result.ending.type, "win")
        self.assertEqual(self.game.score, 100)

    def test_lose_ending(self):
        result = None
        for command in ["s", "se", "jump in the river"]:
            result = self.game.command(command)
        self.assertEqual(result.ending.type, "lose")
        self.assertIn("You scored 0 out of 100", result.text)

    def test_dark_cellar_and_lamp(self):
        g = self.game
        self.assertIn("pitch dark", run(g, "in", "take lamp", "d"))
        self.assertIn("too dark", run(g, "take key"))
        self.assertIn("holding both", run(g, "u", "light lamp"))
        run(g, "open drawer", "take matches")
        self.assertIn("glows warm", run(g, "strike a match"))       # vocabulary verb
        self.assertIn("already burning", run(g, "light lamp"))       # once / done
        self.assertIn("iron key", run(g, "d"))
        self.assertEqual(g.inventory()[0].id, "lit_lamp")
        self.assertIn("flame burns", run(g, "examine lamp"))       # shared alias

    def test_drawer_once_without_done_falls_through(self):
        g = self.game
        run(g, "in")
        self.assertIn("box of matches", run(g, "open drawer"))
        self.assertIn("sits in the\nopen drawer".replace("\n", " "), run(g, "look"))
        self.assertEqual(run(g, "open drawer"), "It's already open.")
        self.assertEqual(run(g, "close drawer"), "You slide the drawer shut.")
        self.assertIn("closed", run(g, "x drawer"))
        self.assertEqual(run(g, "open drawer"), "You open the drawer.")
        self.assertEqual(g.score, 5)
        run(g, "take matches", "out")
        self.assertIn("A box of matches lies here.", run(g, "drop matches", "look"))

    def test_locked_shed(self):
        g = self.game
        self.assertIn("sturdy padlock", run(g, "s", "e"))
        self.assertIn("need a key", run(g, "unlock shed"))
        g.item_locations["key"] = "inventory"
        self.assertIn("swing the shed door open", run(g, "unlock the door"))
        self.assertEqual(g.current_room, "garden")
        self.assertEqual(run(g, "open shed"), "It's already unlocked.")
        self.assertIn("Garden Shed", run(g, "e"))
        self.assertIn("door stands open", run(g, "w"))
        self.assertEqual(g.score, 5)

    def test_grandma_conversation_changes(self):
        g = self.game
        self.assertIn("lost my locket", run(g, "talk to grandma"))
        g.visited.append("riverbank")
        self.assertIn("tie a rope", run(g, "speak with gran"))
        self.assertIn("muddy shoes", run(g, "look"))
        g.visited.append("sandbar")
        g.item_locations["trowel"] = "inventory"
        self.assertIn("found my trowel", run(g, "talk to granny"))
        self.assertIn("Planning some digging", run(g, "examine grandma"))

    def test_rope_and_sandbar(self):
        g = self.game
        g.item_locations["rope"] = "inventory"
        run(g, "s", "se")
        self.assertIn("too steep", run(g, "climb down rope"))
        run(g, "knot rope to the gnarled willow")      # "gnarled" is a describing word
        self.assertIn("leave it tied", run(g, "take rope"))
        self.assertIn("Sandbar", run(g, "d"))
        self.assertIn("something to\ndig".replace("\n", " "), run(g, "dig"))
        g.item_locations["trowel"] = "inventory"
        self.assertIn("up comes", run(g, "dig in the sand with the trowel"))
        self.assertIn("Taken.", run(g, "take the necklace"))       # noun vocabulary
        self.assertIn("Muddy Riverbank", run(g, "climb up the bank"))

    def test_extras_on_moves_and_score(self):
        g = self.game
        self.assertNotIn("shadows", run(g, "look"))
        g.moves, g.score = 50, 50
        text = run(g, "look")
        self.assertIn("shadows are growing long", text)
        self.assertIn("kettle", text)

    def test_apple_and_tree(self):
        g = self.game
        self.assertIn("haul yourself up", run(g, "s", "sw", "climb the apple tree"))
        self.assertIn("magpie", run(g, "look"))
        self.assertIn("crisp", run(g, "eat the apple"))
        self.assertIn("don't have an apple", run(g, "eat apple"))
        self.assertIn("cheerful tune", run(g, "toot"))


if __name__ == "__main__":
    unittest.main()
