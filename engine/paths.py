"""Where the program keeps adventures, saves and settings.

Adventures live next to adventure.py (or next to the .exe when the program
has been bundled with PyInstaller), so authors can find and edit them.

Saves and settings belong to each person who uses the computer, so they go
in that user's own data folder:

    Windows   %APPDATA%\\AdventureEngine
    macOS     ~/Library/Application Support/AdventureEngine
    Linux     $XDG_DATA_HOME/adventure-engine  (usually ~/.local/share/...)
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "AdventureEngine"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):          # running as a PyInstaller .exe
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """This user's own folder for saves and settings (not created here)."""
    home = Path.home()
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        return Path(base) / APP_NAME if base else home / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base) if base else home / ".local" / "share") / "adventure-engine"


def adventures_dir(base: Path | None = None) -> Path:
    folder = (base or app_dir()) / "adventures"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def saves_dir(base: Path | None = None) -> Path:
    folder = (base or user_data_dir()) / "saves"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def settings_file(base: Path | None = None) -> Path:
    folder = base or user_data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"


def copy_old_data(old: Path | None = None, new: Path | None = None) -> None:
    """Older versions kept saves/ and settings.json next to the program.

    Copy them into the user's data folder so nobody loses a game. Anything
    already in the new place wins, and the old files are left where they are.
    """
    old = old or app_dir()
    new = new or user_data_dir()
    try:
        old_settings = old / "settings.json"
        if old_settings.is_file() and not (new / "settings.json").exists():
            new.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_settings, new / "settings.json")
        old_saves = old / "saves"
        if old_saves.is_dir():
            for source in old_saves.rglob("*.json"):
                target = new / "saves" / source.relative_to(old_saves)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    except OSError:
        pass        # a failed copy is never fatal; the old files are still there
