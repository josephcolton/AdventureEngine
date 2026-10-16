import tempfile
import unittest
from pathlib import Path

from engine import Game, saves
from tests.helpers import BASIC, game_from, run


class SaveFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.adv = Path("yard.adv")

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_list_read(self):
        game = game_from(BASIC)
        run(game, "take key")
        first = game.to_save("before the shed")
        first["saved_at"] = "2026-10-15T10:00:00"
        saves.write_save(self.adv, first, self.root)
        run(game, "e")
        second = game.to_save("in the shed?")
        second["saved_at"] = "2026-10-15T11:00:00"
        path = saves.write_save(self.adv, second, self.root)

        found = saves.list_saves(self.adv, 51, self.root)
        self.assertEqual([s.name for s in found], ["in the shed?", "before the shed"])
        self.assertIn("Tool Shed", found[0].label)
        self.assertIn("11 / 51", found[0].label)
        self.assertEqual(path.parent.name, "yard")

        loaded, _ = Game.from_save(game.world, saves.read_save(found[1].path))
        self.assertEqual(loaded.current_room, "yard")

    def test_overwrite_same_name(self):
        game = game_from(BASIC)
        saves.write_save(self.adv, game.to_save("a"), self.root)
        saves.write_save(self.adv, game.to_save("a"), self.root)
        self.assertEqual(len(saves.list_saves(self.adv, saves_root=self.root)), 1)

    def test_unreadable_save_is_skipped(self):
        folder = saves.folder_for(self.adv, self.root)
        folder.mkdir(parents=True)
        (folder / "junk.json").write_text("not json", encoding="utf-8")
        self.assertEqual(saves.list_saves(self.adv, saves_root=self.root), [])


if __name__ == "__main__":
    unittest.main()
