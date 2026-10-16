"""Drives the real tkinter window without showing it (skipped if there's no display).

Dialogs are not opened here because they wait for a click; everything else is
exercised through the same methods the buttons and menus call.
"""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

from tests.test_tutorial import walkthrough_from_header


def type_line(screen, line: str) -> None:
    screen.entry.insert(0, line)
    screen._submit()


class GuiSmokeTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as problem:
            self.skipTest(f"no display: {problem}")
        self.root.withdraw()
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        saves_dir = tmp / "saves"
        saves_dir.mkdir()
        self.patches = [
            mock.patch("engine.paths.settings_file", return_value=tmp / "settings.json"),
            mock.patch("engine.paths.saves_dir", return_value=saves_dir),
        ]
        for p in self.patches:
            p.start()
        from gui.app import App
        from gui.settings import Settings
        self.app = App(self.root, Settings())

    def tearDown(self):
        for p in self.patches:
            p.stop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.tmp.cleanup()

    def start_tutorial(self):
        from gui.start_screen import StartScreen
        start = self.app.screen
        self.assertIsInstance(start, StartScreen)
        titles = list(start.adventure.cget("values"))
        self.assertIn("Grandma's Locket", titles)
        self.assertIn("Agnes and the Well", titles)
        start.adventure.current(titles.index("Grandma's Locket"))
        start._adventure_changed()
        start.play()            # no saves yet, so straight into the game
        return self.app.screen

    def story(self, screen) -> str:
        return screen.story.get("1.0", "end")

    def test_play_to_the_end(self):
        from gui.game_screen import GameScreen
        screen = self.start_tutorial()
        self.assertIsInstance(screen, GameScreen)
        self.assertIn("lazy summer afternoon", self.story(screen))
        self.assertEqual(screen.room_label.cget("text"), "Front Porch")
        for line in walkthrough_from_header():
            type_line(screen, line)
        self.assertIn("You have won", self.story(screen))
        self.assertIn("Score: 100 / 100", screen.score_label.cget("text"))
        self.assertTrue(screen.ending_row.winfo_manager())       # buttons shown
        self.assertFalse(screen.input_row.winfo_manager())       # input hidden
        screen.new_game()
        self.assertTrue(screen.input_row.winfo_manager())
        self.assertIn("Score: 0 / 100", screen.score_label.cget("text"))

    def test_history_arrows(self):
        screen = self.start_tutorial()
        type_line(screen, "look")
        type_line(screen, "inventory")
        screen._recall(-1)
        self.assertEqual(screen.entry.get(), "inventory")
        screen._recall(-1)
        self.assertEqual(screen.entry.get(), "look")
        screen._recall(+1)
        screen._recall(+1)
        self.assertEqual(screen.entry.get(), "")

    def test_save_and_load(self):
        from engine import Game, saves
        screen = self.start_tutorial()
        type_line(screen, "in")
        self.assertTrue(screen.game.unsaved)
        self.assertTrue(screen._write_save("in the kitchen"))
        self.assertFalse(screen.game.unsaved)
        self.assertTrue(screen.confirm_unsaved())        # nothing to ask about
        found = saves.list_saves(screen.world.path)
        self.assertEqual([s.name for s in found], ["in the kitchen"])
        type_line(screen, "out")
        game, warnings = Game.from_save(screen.world, saves.read_save(found[0].path))
        self.assertEqual(warnings, [])
        screen.use_game(game)
        self.assertEqual(screen.room_label.cget("text"), "Farmhouse Kitchen")
        self.assertIn("> in", self.story(screen))
        # now Play goes to the saved-game screen, which offers the save
        from gui.game_screen import GameScreen
        from gui.save_screen import SaveScreen
        screen.change_adventure()
        self.app.screen.play()
        picker = self.app.screen
        self.assertIsInstance(picker, SaveScreen)
        self.assertEqual(picker.list.size(), 1)
        self.assertIn("in the kitchen", picker.list.get(0))
        picker.back()
        self.app.screen.play()
        self.app.screen.play()          # Continue with the selected save
        screen = self.app.screen
        self.assertIsInstance(screen, GameScreen)
        self.assertEqual(screen.room_label.cget("text"), "Farmhouse Kitchen")
        screen.change_adventure()
        self.app.screen.play()
        self.app.screen.new_game()      # or start over
        self.assertEqual(self.app.screen.room_label.cget("text"), "Front Porch")

    def test_theme_and_font(self):
        screen = self.start_tutorial()
        self.app.theme_var.set("dark")
        self.app.apply_theme()
        self.assertEqual(screen.story.cget("background"), "#1f2023")
        size = self.app.fonts.story.cget("size")
        self.app.change_font(+2)
        self.assertEqual(self.app.fonts.story.cget("size"), size + 2)

    def test_author_tools(self):
        screen = self.start_tutorial()
        type_line(screen, "in")
        type_line(screen, "open drawer")
        screen.reload(replay=True)
        self.assertEqual(screen.game.current_room, "kitchen")
        self.assertEqual(screen.game.score, 5)
        self.assertIn("2 commands replayed", self.story(screen))
        screen.show_state()
        state = screen.state_text.get("1.0", "end")
        self.assertIn("drawer_open", state)
        screen.game.teleport("sandbar")
        screen.update_status()
        self.assertEqual(screen.room_label.cget("text"), "Sandbar")
        screen.reload()
        self.assertEqual(screen.game.current_room, "porch")


if __name__ == "__main__":
    unittest.main()
