from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from relay.schemas import Skill


class SkillLoader:
    """Loads skills from project, user, global, and built-in layers.

    Earlier layers win when two skills share the same id. This gives project
    skills the highest priority while still allowing a useful built-in baseline.
    """

    def __init__(
        self,
        project_root: Path,
        user_home: Path | None = None,
        global_dir: Path | None = None,
        builtin_dir: Path | None = None,
    ) -> None:
        self.project_root = project_root
        self.user_home = user_home or Path.home()
        self.global_dir = global_dir or Path(os.getenv("RELAY_GLOBAL_SKILLS", "/etc/relay/skills"))
        self.builtin_dir = builtin_dir or Path(__file__).resolve().parents[1] / "builtin_skills"

    def layers(self) -> list[tuple[str, Path]]:
        return [
            ("project", self.project_root / ".relay" / "skills"),
            ("user", self.user_home / ".relay" / "skills"),
            ("global", self.global_dir),
            ("builtin", self.builtin_dir),
        ]

    def load(self) -> list[Skill]:
        loaded: dict[str, Skill] = {}
        for source, directory in self.layers():
            for skill in self._load_dir(source, directory):
                loaded.setdefault(skill.id, skill)
        return list(loaded.values())

    def match(self, domain: str) -> list[Skill]:
        domain = domain.lower()
        return [skill for skill in self.load() if domain in {item.lower() for item in skill.domains}]

    def _load_dir(self, source: str, directory: Path) -> Iterable[Skill]:
        if not directory.exists():
            return []
        skills: list[Skill] = []
        for path in sorted(directory.glob("*.skill.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            skills.append(Skill(**data, source=source, path=str(path)))
        return skills

