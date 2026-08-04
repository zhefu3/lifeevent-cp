"""Shared helpers: config loading, deterministic RNG, JSON/JSONL IO, logging."""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def setup_logging(name: str = "lifeevent") -> logging.Logger:
    """Console logger with a stable format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config; default configs/config.yaml relative to project root."""
    cfg_path = Path(path) if path else PROJECT_ROOT / "configs" / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_rng(config: dict[str, Any]) -> np.random.Generator:
    """Single deterministic RNG derived from config seed."""
    return np.random.default_rng(int(config["random_seed"]))


def sha1_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(p, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def enabled_event_types(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Event-type registry filtered to enabled entries."""
    return {k: v for k, v in config["event_types"].items() if v.get("enabled", True)}


def profile_of(config: dict[str, Any], name: str) -> dict[str, Any]:
    if name not in config["profiles"]:
        raise KeyError(f"unknown profile: {name}")
    return config["profiles"][name]
