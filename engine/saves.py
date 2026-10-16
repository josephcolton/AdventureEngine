"""Save files: one JSON file per save, in saves/<adventure-file-stem>/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import paths


@dataclass
class SaveInfo:
    name: str
    path: Path
    saved_at: str
    room_name: str
    score: int
    max_score: int | None = None

    @property
    def label(self) -> str:
        """'before the cave — 15 Oct 2026 2:20 PM — Muddy Riverbank — 15'"""
        try:
            when = datetime.fromisoformat(self.saved_at)
            stamp = f"{when.day} {when:%b %Y} {when:%I:%M %p}".replace(" 0", " ")
        except ValueError:
            stamp = self.saved_at
        score = f"{self.score} / {self.max_score}" if self.max_score else str(self.score)
        return f"{self.name} — {stamp} — {self.room_name} — {score}"


def folder_for(adventure_path: Path, saves_root: Path | None = None) -> Path:
    return (saves_root or paths.saves_dir()) / Path(adventure_path).stem


def file_name(save_name: str) -> str:
    """A safe file name for any save name the player types."""
    safe = re.sub(r"[^A-Za-z0-9 _-]+", "_", save_name).strip(" .") or "save"
    return safe[:80] + ".json"


def save_path(adventure_path: Path, save_name: str,
              saves_root: Path | None = None) -> Path:
    return folder_for(adventure_path, saves_root) / file_name(save_name)


def write_save(adventure_path: Path, data: dict,
               saves_root: Path | None = None) -> Path:
    path = save_path(adventure_path, data["save_name"], saves_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)          # never leave a half-written save behind
    return path


def read_save(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def list_saves(adventure_path: Path, max_score: int | None = None,
               saves_root: Path | None = None) -> list[SaveInfo]:
    """Saves for one adventure, newest first. Unreadable files are skipped."""
    folder = folder_for(adventure_path, saves_root)
    found = []
    if folder.is_dir():
        for path in folder.glob("*.json"):
            try:
                data = read_save(path)
                found.append(SaveInfo(
                    name=str(data.get("save_name", path.stem)), path=path,
                    saved_at=str(data.get("saved_at", "")),
                    room_name=str(data.get("room_name", data.get("current_room", ""))),
                    score=int(data.get("score", 0)), max_score=max_score))
            except (OSError, ValueError, TypeError):
                continue
    found.sort(key=lambda s: s.saved_at, reverse=True)
    return found
