import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import paths


class UserDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_windows_uses_appdata(self):
        with mock.patch.object(sys, "platform", "win32"), \
                mock.patch.dict(os.environ, {"APPDATA": str(self.root)}):
            self.assertEqual(paths.user_data_dir(), self.root / "AdventureEngine")

    def test_linux_uses_xdg_data_home(self):
        with mock.patch.object(sys, "platform", "linux"), \
                mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root)}):
            self.assertEqual(paths.user_data_dir(), self.root / "adventure-engine")

    def test_saves_and_settings_are_not_next_to_the_program(self):
        with mock.patch("engine.paths.user_data_dir", return_value=self.root / "me"):
            self.assertEqual(paths.saves_dir(), self.root / "me" / "saves")
            self.assertEqual(paths.settings_file(), self.root / "me" / "settings.json")
            self.assertTrue((self.root / "me" / "saves").is_dir())

    def test_old_saves_are_copied_once(self):
        old, new = self.root / "old", self.root / "new"
        (old / "saves" / "yard").mkdir(parents=True)
        (old / "saves" / "yard" / "a.json").write_text("old a", encoding="utf-8")
        (old / "saves" / "yard" / "b.json").write_text("old b", encoding="utf-8")
        (old / "settings.json").write_text("{}", encoding="utf-8")
        (new / "saves" / "yard").mkdir(parents=True)
        (new / "saves" / "yard" / "b.json").write_text("new b", encoding="utf-8")
        paths.copy_old_data(old, new)
        self.assertEqual((new / "saves" / "yard" / "a.json").read_text(encoding="utf-8"), "old a")
        self.assertEqual((new / "saves" / "yard" / "b.json").read_text(encoding="utf-8"), "new b")
        self.assertTrue((new / "settings.json").is_file())
        self.assertTrue((old / "saves" / "yard" / "a.json").is_file())    # left in place


if __name__ == "__main__":
    unittest.main()
