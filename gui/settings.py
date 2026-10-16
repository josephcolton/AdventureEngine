"""Remembers text size, theme and window size between sessions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from engine import paths

MIN_FONT, MAX_FONT = 8, 32


@dataclass
class Settings:
    font_size: int = 13
    theme: str = "light"            # "light" or "dark"
    geometry: str = "900x680"
    last_adventure: str = ""        # file name of the adventure last played

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or paths.settings_file()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        known = {f.name for f in fields(cls)}
        settings = cls(**{k: v for k, v in data.items() if k in known})
        settings.font_size = max(MIN_FONT, min(MAX_FONT, int(settings.font_size)))
        if settings.theme not in ("light", "dark"):
            settings.theme = "light"
        return settings

    def save(self, path: Path | None = None) -> None:
        path = path or paths.settings_file()
        try:
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass        # not being able to remember settings is never fatal
