from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST_FILE = ".gp-config.json"


@dataclass
class RepoManifest:
    work_id_prefix: str
    required_reviewers: int = 2
    service: str = ""
    pre_push_commands: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, start: Path | None = None) -> "RepoManifest":
        path = cls._find(start or Path.cwd())
        raw = json.loads(path.read_text())
        return cls(
            work_id_prefix=raw["workIdPrefix"],
            required_reviewers=raw.get("requiredReviewers", 2),
            service=raw.get("service", ""),
            pre_push_commands=raw.get("prePushCommands", []),
        )

    @staticmethod
    def _find(start: Path) -> Path:
        for directory in [start, *start.parents]:
            candidate = directory / MANIFEST_FILE
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"{MANIFEST_FILE} not found. Run 'gp init' to initialize this repository."
        )

    def write(self, path: Path) -> None:
        data = {
            "workIdPrefix": self.work_id_prefix,
            "requiredReviewers": self.required_reviewers,
            "service": self.service,
            "prePushCommands": self.pre_push_commands,
        }
        path.write_text(json.dumps(data, indent=2) + "\n")
