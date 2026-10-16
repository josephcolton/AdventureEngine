import unittest

from engine.normalizer import Normalizer, split_commands

ITEMS = {
    "river": ["river"],
    "rope": ["rope", "coil", "coil of rope"],
    "tied_rope": ["rope", "tied rope"],
    "agnes": ["agnes", "old woman", "woman"],
    "pie": ["pie", "apple pie"],
    "well": ["well", "crank"],
}


def form(cmd):
    """(verb, sorted noun descriptions) for easy comparison."""
    nouns = []
    for n in cmd.nouns:
        nouns.append(",".join(sorted(n.ids)) if n.kind == "item" else n.word)
    return cmd.verb, nouns


class NormalizerTests(unittest.TestCase):
    def setUp(self):
        self.norm = Normalizer(ITEMS, [("tie", "knot"), ("enter", "wade")])

    def parse(self, text, **kw):
        return self.norm.parse(text, **kw)

    def test_enter_river_examples(self):
        for text in ["jump in the river", "wade into river", "get in river",
                     "go into the river", "enter river", "climb in river",
                     "Jump into the River!"]:
            with self.subTest(text=text):
                self.assertEqual(form(self.parse(text)), ("enter", ["river"]))

    def test_directions(self):
        for text in ["n", "north", "go north", "walk n", "go n"]:
            with self.subTest(text=text):
                self.assertEqual(form(self.parse(text)), ("go", ["north"]))
                self.assertTrue(self.parse(text).is_movement)

    def test_bare_enter_and_exit_are_directions(self):
        self.assertEqual(form(self.parse("go in")), ("go", ["in"]))
        self.assertEqual(form(self.parse("enter")), ("go", ["in"]))
        self.assertEqual(form(self.parse("get out")), ("go", ["out"]))
        self.assertEqual(form(self.parse("leave")), ("go", ["out"]))

    def test_context_verbs(self):
        self.assertEqual(form(self.parse("climb down the well")), ("go", ["down", "well"]))
        self.assertEqual(form(self.parse("climb up")), ("go", ["up"]))
        self.assertEqual(form(self.parse("climb rope")),
                         ("climb", ["rope,tied_rope"]))
        self.assertEqual(form(self.parse("leave the pie")), ("drop", ["pie"]))
        self.assertEqual(form(self.parse("move pie")), ("push", ["pie"]))
        self.assertEqual(form(self.parse("move north")), ("go", ["north"]))
        self.assertEqual(form(self.parse("descend well")), ("go", ["down", "well"]))

    def test_multiword_verbs(self):
        self.assertEqual(form(self.parse("pick up the pie")), ("take", ["pie"]))
        self.assertEqual(form(self.parse("look at agnes")), ("examine", ["agnes"]))
        self.assertEqual(form(self.parse("speak with the old woman")),
                         ("talk", ["agnes"]))
        self.assertEqual(form(self.parse("l")), ("look", []))
        self.assertEqual(form(self.parse("x pie")), ("examine", ["pie"]))

    def test_author_vocabulary(self):
        self.assertEqual(form(self.parse("knot rope to crank")),
                         ("tie", ["rope,tied_rope", "well"]))

    def test_longest_alias_wins(self):
        cmd = self.parse("take the coil of rope")
        self.assertEqual(form(cmd), ("take", ["rope"]))
        self.assertEqual(cmd.nouns[0].word, "coil of rope")

    def test_unknown_words_stay(self):
        self.assertEqual(form(self.parse("examine the lantren")),
                         ("examine", ["lantren"]))

    def test_unknown_verb_kept(self):
        self.assertEqual(form(self.parse("xyzzy")), ("xyzzy", []))

    def test_noun_order_does_not_matter(self):
        a = self.parse("give pie to agnes")
        for text in ["give agnes the pie", "offer the apple pie to the old woman",
                     "hand agnes pie"]:
            with self.subTest(text=text):
                self.assertTrue(a.matches(self.parse(text)))

    def test_extra_nouns_do_not_match(self):
        a = self.parse("climb down the well")
        self.assertFalse(a.matches(self.parse("climb down the well with the rope")))

    def test_shared_alias_in_phrase_matches_either(self):
        phrase = self.parse("tie rope to well")
        player = self.parse("tie rope to crank", present=lambda i: i == "tied_rope")
        self.assertEqual(form(player), ("tie", ["tied_rope", "well"]))
        self.assertTrue(phrase.matches(player))

    def test_shared_alias_ambiguous_when_both_present(self):
        cmd = self.parse("take rope", present=lambda i: i in ("rope", "tied_rope"))
        self.assertTrue(cmd.nouns[0].ambiguous)

    def test_item_id_written_exactly(self):
        self.assertEqual(form(self.parse("take tied_rope")), ("take", ["tied_rope"]))

    def test_pronoun(self):
        cmd = self.parse("eat it", present=lambda i: True, last_item="pie")
        self.assertEqual(form(cmd), ("eat", ["pie"]))

    def test_describing_words_are_marked(self):
        cmd = self.parse("tie the rope to the big old well")
        self.assertEqual([(n.word, n.describing) for n in cmd.nouns],
                         [("rope", False), ("big", True), ("old", True), ("well", False)])
        # unknown words that aren't right before a thing's name are not describing
        cmd = self.parse("examine the lantren")
        self.assertFalse(cmd.nouns[0].describing)
        cmd = self.parse("give pie happily")
        self.assertFalse(cmd.nouns[1].describing)

    def test_loose_matching_ignores_describing_words(self):
        phrase = self.parse("tie rope to well")
        player = self.parse("tie the frayed rope to the big old well")
        self.assertFalse(phrase.matches(player))
        self.assertTrue(phrase.matches(player, loose=True))
        # describing words in the author's phrase are ignored too
        self.assertTrue(self.parse("tie rope to old well").matches(phrase, loose=True))
        # but a genuinely different noun still doesn't match
        self.assertFalse(phrase.matches(self.parse("tie rope to fence"), loose=True))

    def test_split_commands(self):
        self.assertEqual(split_commands("take rope then go north. look; wait, i"),
                         ["take rope", "go north", "look", "wait", "i"])

    def test_apostrophes(self):
        norm = Normalizer({"hat": ["agnes's hat"]})
        self.assertEqual(form(norm.parse("take Agnes's hat")), ("take", ["hat"]))
        self.assertEqual(form(norm.parse("take agness hat")), ("take", ["hat"]))


if __name__ == "__main__":
    unittest.main()
