"""Keeps docs/AUTHORING.md honest: its examples must work with the real engine."""

import re
import unittest
import xml.etree.ElementTree as ET

from engine import Game, load_text
from tests.helpers import ROOT, run

GUIDE = (ROOT / "docs" / "AUTHORING.md").read_text(encoding="utf-8")
BLOCKS = re.findall(r"```ini\n(.*?)```", GUIDE, re.S)

# Messages about the *shape* of the text. Example snippets mention rooms and
# items that aren't defined in the snippet, so reference errors are expected;
# these kinds of problems are not.
SHAPE_PROBLEMS = ("doesn't look like a setting", "starts with a space",
                  "comes before the first section", "isn't a kind of section",
                  "isn't a setting I know", "Malformed condition",
                  "couldn't read this 'when' line", "should be yes or no",
                  "should be a whole number", "should look like",
                  "isn't written correctly", "needs a name after a colon")


def github_anchor(heading: str) -> str:
    slug = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return slug.replace(" ", "-")


class AuthoringGuideTests(unittest.TestCase):
    def test_there_are_plenty_of_examples(self):
        self.assertGreater(len(BLOCKS), 20)

    def test_every_example_is_written_correctly(self):
        for block in BLOCKS:
            with self.subTest(block=block[:60]):
                text = block if "[" in block else "[vocabulary]\n" + block
                world = load_text(text)
                problems = [str(m) for m in world.report.messages
                            if any(p in m.text for p in SHAPE_PROBLEMS)]
                self.assertEqual(problems, [])

    def test_first_adventure_works_as_described(self):
        world = load_text(BLOCKS[0])
        self.assertEqual(world.report.errors + world.report.warnings, [])
        game = Game(world)
        game.start()
        self.assertEqual(run(game, "east"), "The shed door is locked.")
        run(game, "take key")
        self.assertIn("Tool Shed", run(game, "east"))
        run(game, "take hammer")
        self.assertIn("Well done!", run(game, "west"))
        self.assertEqual(game.score, 50)

    def test_contents_links_point_at_real_headings(self):
        anchors = {github_anchor(h) for h in re.findall(r"^#{2,3} (.+)$", GUIDE, re.M)}
        links = re.findall(r"\]\(#([^)]+)\)", GUIDE)
        self.assertGreater(len(links), 20)
        for link in links:
            self.assertIn(link, anchors)

    def test_known_words_list_matches_the_engine(self):
        from engine.vocabulary import VERB_SYNONYMS
        listed = re.search(r"Words the game already knows.*?> (.*?)\n", GUIDE, re.S).group(1)
        self.assertEqual({w.strip() for w in listed.split(",")}, set(VERB_SYNONYMS))


class OtherDocsTests(unittest.TestCase):
    def test_notepadpp_file_is_valid(self):
        tree = ET.parse(ROOT / "docs" / "notepadpp-adv.xml")
        lang = tree.getroot().find("UserLang")
        self.assertEqual(lang.get("ext"), "adv")

    def test_readme_links_and_images_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(((?:docs|adventures)/[^)#]+)\)", readme):
            self.assertTrue((ROOT / target).exists(), target)


if __name__ == "__main__":
    unittest.main()
