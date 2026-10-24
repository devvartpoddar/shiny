"""The house theme: _brand.yml at the repo root, or an app's own beside its
app.py when it has one."""
from __future__ import annotations

import inspect
from functools import lru_cache
from pathlib import Path

import yaml
from shiny import ui

ROOT = Path(__file__).resolve().parent.parent


def _brand_path(start: Path | None) -> Path:
    here = start or ROOT
    for d in (here, *here.parents):
        if (d / "_brand.yml").is_file():
            return d / "_brand.yml"
        if d == ROOT:
            break
    return ROOT / "_brand.yml"


def _caller_dir() -> Path | None:
    for f in inspect.stack()[2:]:
        p = Path(f.filename)
        if p.name == "app.py":
            return p.parent
    return None


@lru_cache(maxsize=8)
def brand(path: str | None = None) -> dict:
    """The brand file as a dict (colors, fonts) — for charts and custom CSS."""
    p = Path(path) if path else _brand_path(_caller_dir())
    with p.open() as fh:
        return yaml.safe_load(fh) or {}


def theme(path: str | None = None) -> ui.Theme:
    """The Shiny theme built from the brand file. Pass to ui.page_opts(theme=...)."""
    p = Path(path) if path else _brand_path(_caller_dir())
    return ui.Theme.from_brand(p)


def palette() -> dict[str, str]:
    b = brand()
    return dict((b.get("color") or {}).get("palette") or {})
