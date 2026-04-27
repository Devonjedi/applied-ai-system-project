from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "song_catalog.csv"


@dataclass(frozen=True)
class Song:
    title: str
    artist: str
    genre: str
    energy: int
    mood: str
    tags: tuple[str, ...]
    scene: str
    description: str

    def searchable_text(self) -> str:
        parts = [
            self.title,
            self.artist,
            self.genre,
            self.mood,
            self.scene,
            self.description,
            *self.tags,
        ]
        return " ".join(part.lower() for part in parts if part)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "energy": self.energy,
            "mood": self.mood,
            "tags": ", ".join(self.tags),
            "scene": self.scene,
            "description": self.description,
        }


def load_catalog(path: Path | str = DEFAULT_CATALOG_PATH) -> list[Song]:
    catalog_path = Path(path)
    songs: list[Song] = []

    with catalog_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            songs.append(
                Song(
                    title=row["title"].strip(),
                    artist=row["artist"].strip(),
                    genre=row["genre"].strip().lower(),
                    energy=int(row["energy"]),
                    mood=row["mood"].strip().lower(),
                    tags=tuple(_split_tags(row["tags"])),
                    scene=row["scene"].strip().lower(),
                    description=row["description"].strip(),
                )
            )

    return songs


def available_genres(songs: Iterable[Song]) -> list[str]:
    return sorted({song.genre for song in songs})


def _split_tags(raw_tags: str) -> list[str]:
    return [tag.strip().lower() for tag in raw_tags.split("|") if tag.strip()]
