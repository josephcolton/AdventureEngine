import unittest

from tests.helpers import BASIC, world_from

GOOD = BASIC


def messages(text, level="errors"):
    world = world_from(text)
    return [m.text for m in getattr(world.report, level)]


def has(found, fragment):
    return any(fragment in m for m in found)


class ValidatorErrorTests(unittest.TestCase):
    def test_basic_is_clean(self):
        world = world_from(GOOD)
        self.assertEqual(world.report.errors, [])
        self.assertEqual(world.report.warnings, [])

    def test_missing_game(self):
        self.assertTrue(has(messages("[room: a]\nfirst = x\n"), "no [game] section"))

    def test_missing_title_and_start(self):
        found = messages("[game]\nauthor = me\n")
        self.assertTrue(has(found, "needs a title"))
        self.assertTrue(has(found, "needs a start room"))

    def test_start_room_missing_with_suggestion(self):
        found = messages(GOOD.replace("start = yard", "start = yrd"))
        self.assertTrue(has(found, "Did you mean 'yard'"))

    def test_duplicate_ids(self):
        found = messages(GOOD + "\n[room: yard]\nfirst = again\n")
        self.assertTrue(has(found, "two rooms called 'yard'"))
        found = messages(GOOD + "\n[item: lamp]\nlocation = yard\n")
        self.assertTrue(has(found, "two items called 'lamp'"))
        found = messages(GOOD + "\n[ending: done]\ntype = lose\n")
        self.assertTrue(has(found, "two endings called 'done'"))
        found = messages(GOOD + "\n[action: a]\nid = x\nwhere = yard\n"
                         "[action: b]\nid = x\nwhere = yard\n")
        self.assertTrue(has(found, "Two actions use the id 'x'"))

    def test_bad_references(self):
        found = messages(GOOD.replace("east: shed", "east: shedd"))
        self.assertTrue(has(found, "'shedd'"))
        found = messages(GOOD + """
[action: zap]
where = yrd
go = celar
move = lamb to here
end = finished
if = has kee
""")
        for fragment in ["'yrd'", "'celar'", "'lamb'", "'finished'", "'kee'"]:
            self.assertTrue(has(found, fragment), fragment)

    def test_bad_location(self):
        self.assertTrue(has(messages(GOOD.replace("location = shed", "location = shd")),
                            "Did you mean 'shed'"))

    def test_malformed_condition(self):
        self.assertTrue(has(messages(GOOD.replace("if = has key", "if = holding key")),
                            "Malformed condition"))

    def test_no_win(self):
        self.assertTrue(has(messages(GOOD.replace("type = win", "type = lose")),
                            "no winning ending"))

    def test_bad_values(self):
        found = messages(GOOD.replace("points = 40", "points = lots")
                         .replace("light = yes", "light = maybe"))
        self.assertTrue(has(found, "whole number"))
        self.assertTrue(has(found, "yes or no"))

    def test_bad_exit_direction(self):
        self.assertTrue(has(messages(GOOD.replace("east: shed", "eest: shed")),
                            "isn't a direction"))

    def test_action_needs_where(self):
        self.assertTrue(has(messages(GOOD + "\n[action: wave]\nmessage = hi\n"),
                            "needs a 'where'"))


class ValidatorWarningTests(unittest.TestCase):
    def test_unreachable_room(self):
        found = messages(GOOD + "\n[room: attic]\nfirst = Dusty.\n", "warnings")
        self.assertTrue(has(found, "'attic' can't be reached"))

    def test_go_action_makes_room_reachable(self):
        found = messages(GOOD + "\n[room: attic]\nfirst = Dusty.\n"
                         "[action: climb ladder]\nwhere = shed\ngo = attic\n", "warnings")
        self.assertFalse(has(found, "can't be reached"))

    def test_item_never_appears(self):
        found = messages(GOOD + "\n[item: ghost]\nlocation = nowhere\n", "warnings")
        self.assertTrue(has(found, "'ghost' starts 'nowhere'"))

    def test_flags(self):
        found = messages(GOOD + "\n[action: wave]\nwhere = yard\nif = flag opn\n"
                         "[action: open door]\nwhere = yard\nset = open\n", "warnings")
        self.assertTrue(has(found, "'opn' is checked but never set"))
        self.assertTrue(has(found, "'open' is set but never checked"))

    def test_unknown_key_and_repeats(self):
        found = messages(GOOD.replace("name = lamp", "nmae = lamp\nlight = no"), "warnings")
        self.assertTrue(has(found, "Did you mean 'name'"))
        self.assertTrue(has(found, "'light' appears 2 times"))

    def test_max_score_mismatch(self):
        found = messages(GOOD.replace("start = yard", "start = yard\nmax_score = 99"),
                         "warnings")
        self.assertTrue(has(found, "add up to 51"))

    def test_unknown_verb(self):
        found = messages(GOOD + "\n[action: xyzzy]\nwhere = yard\nmessage = Poof.\n",
                         "warnings")
        self.assertTrue(has(found, "'xyzzy'"))

    def test_one_way_exit_is_a_note(self):
        found = messages(GOOD.replace("exits = south: yard", ""), "notes")
        self.assertTrue(has(found, "no way back"))

    def test_go_action_counts_as_a_way_back(self):
        text = GOOD.replace("exits = south: yard", "") + (
            "\n[action: climb up]\nwhere = cellar\ngo = yard\n")
        self.assertFalse(has(messages(text, "notes"), "no way back"))

    def test_points_and_score_interchangeable(self):
        world = world_from(GOOD.replace("points = 40", "score = 40"))
        self.assertEqual(world.items["hammer"].points, 40)


if __name__ == "__main__":
    unittest.main()
