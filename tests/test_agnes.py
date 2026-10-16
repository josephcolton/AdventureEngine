"""Plays adventures/agnes_and_the_well.adv from start to finish."""

import unittest

from engine import Game, load_adventure
from tests.helpers import ADVENTURES, run

WALKTHROUGH = ["take pie", "east", "talk to agnes", "give pie to agnes", "north",
               "tie rope to well", "climb down the well", "take ring", "up",
               "south", "give ring to agnes"]


class AgnesTests(unittest.TestCase):
    def setUp(self):
        self.world = load_adventure(ADVENTURES / "agnes_and_the_well.adv")
        self.game = Game(self.world)
        self.game.start()

    def test_loads_cleanly(self):
        self.assertEqual(self.world.report.errors, [])
        self.assertEqual(self.world.report.warnings, [])
        self.assertEqual(self.world.max_score, 100)

    def test_walkthrough_wins_100(self):
        result = None
        for command in WALKTHROUGH:
            self.assertIsNone(self.game.ended, f"ended early before '{command}'")
            result = self.game.command(command)
        self.assertEqual(self.game.ended, "ring_home")
        self.assertEqual(result.ending.type, "win")
        self.assertEqual(self.game.score, 100)
        self.assertIn("You scored 100 out of 100", result.text)

    def test_alternate_phrasings(self):
        g = self.game
        run(g, "pick up the apple pie", "e")
        self.assertIn("Hello, dear", run(g, "speak with the old woman"))
        self.assertIn("Oh, my favorite", run(g, "give agnes the pie"))
        self.assertIn("much happier", run(g, "examine agnes"))
        self.assertIn("Walter tried", run(g, "chat with agnes"))
        run(g, "n")
        self.assertIn("without a rope", run(g, "descend well"))
        self.assertIn("knot the rope", run(g, "knot rope to crank"))
        self.assertIn("already tied", run(g, "tie rope to well"))
        self.assertIn("knotted tightly", run(g, "examine rope"))
        self.assertIn("tied to the crank", run(g, "take rope"))
        self.assertIn("A rope hangs from the crank", run(g, "look"))
        self.assertIn("Bottom of the Well", run(g, "descend well"))
        self.assertIn("only way back up", run(g, "take rope"))
        run(g, "take ring")
        self.assertIn("haul yourself back up", run(g, "climb rope"))
        self.assertEqual(g.current_room, "well_yard")
        run(g, "climb down rope", "climb up")
        self.assertEqual(g.current_room, "well_yard")
        run(g, "s")
        self.assertIn("It still fits", run(g, "offer the ring to the old woman"))
        self.assertEqual(g.score, 100)

    def test_other_ways_down_and_up(self):
        g = self.game
        run(g, "take pie", "e", "give pie to agnes", "n", "tie rope to well")
        for down in ["go down", "enter well", "go down well", "climb down the well"]:
            with self.subTest(down=down):
                run(g, down)
                self.assertEqual(g.current_room, "well_bottom")
                run(g, "u")
                self.assertEqual(g.current_room, "well_yard")

    def test_describing_words(self):
        g = self.game
        run(g, "take the warm pie", "e")
        self.assertIn("Oh, my favorite", run(g, "give the warm apple pie to dear old agnes"))
        run(g, "n")
        self.assertIn("knot the rope", run(g, "tie the frayed rope to the rusty crank"))

    def test_give_without_pie(self):
        self.assertIn("You don't have anything she'd want",
                      run(self.game, "e", "give pie to agnes"))


if __name__ == "__main__":
    unittest.main()
