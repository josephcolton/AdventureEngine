import unittest

from engine.conditions import ConditionError, parse_conditions, split_when
from tests.helpers import BASIC, game_from


class ConditionParsingTests(unittest.TestCase):
    def test_kinds(self):
        conds = parse_conditions("has rope, not flag Tied, score >= 10, moves<5, "
                                 "in kitchen, visited cellar, here lamp")
        self.assertEqual([c.kind for c in conds],
                         ["has", "flag", "score", "moves", "in", "visited", "here"])
        self.assertTrue(conds[1].negated)
        self.assertEqual(conds[1].arg, "tied")
        self.assertEqual((conds[2].op, conds[2].number), (">=", 10))

    def test_bad_condition(self):
        with self.assertRaises(ConditionError):
            parse_conditions("holding rope")

    def test_split_when(self):
        self.assertEqual(split_when("score = 50 = Half!"), ("score = 50", "Half!"))
        self.assertIsNone(split_when("banana = text"))


class ConditionEvaluationTests(unittest.TestCase):
    def test_evaluation(self):
        game = game_from(BASIC)
        check = lambda text: game.check(parse_conditions(text))
        self.assertTrue(check("in yard, visited yard, here key, not has key"))
        self.assertTrue(check("score = 1, moves = 0"))
        game.command("take key")
        self.assertTrue(check("has key, score > 10, moves >= 1, not visited shed"))
        game.flags.add("x")
        self.assertTrue(check("flag x"))
        self.assertFalse(check("not flag x"))


if __name__ == "__main__":
    unittest.main()
