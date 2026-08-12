"""Config loading: sources registry, scoring weights, overrides."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import yaml


class Config:
    def __init__(self, root: Path):
        self.root = root
        self.sources_file = root / "config" / "sources.yaml"
        self.scoring_file = root / "config" / "scoring.yaml"
        self.overrides_dir = root / "config" / "overrides"

    def load_sources(self) -> list:
        if not self.sources_file.exists():
            return []
        with open(self.sources_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("sources", []) if isinstance(data, dict) else (data or [])

    def load_scoring(self) -> dict:
        if not self.scoring_file.exists():
            return {}
        with open(self.scoring_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_overrides(self) -> dict:
        result = {}
        if not self.overrides_dir.exists():
            return result
        for name in ("merge.yaml", "split.yaml", "hide.yaml", "source-trust.yaml"):
            p = self.overrides_dir / name
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    result[name.replace(".yaml", "")] = yaml.safe_load(f) or {}
        return result
