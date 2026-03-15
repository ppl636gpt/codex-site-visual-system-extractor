from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_VIEWPORTS = (
    ("mobile", 390, 844),
    ("tablet", 834, 1194),
    ("desktop", 1440, 1024),
)
DEFAULT_THEMES = ["auto"]
DEFAULT_STATES = ["hover", "focus", "active"]


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "item"


def ensure_output_dir(path: Path | str) -> Path:
    output = Path(path).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def parse_viewports(values: Iterable[str] | None) -> list[Viewport]:
    if not values:
        return [Viewport(name, width, height) for name, width, height in DEFAULT_VIEWPORTS]

    parsed: list[Viewport] = []
    for index, raw in enumerate(values, start=1):
        if "=" in raw:
            name, dims = raw.split("=", 1)
        else:
            name = f"vp-{index}"
            dims = raw
        match = re.match(r"^\s*(\d+)x(\d+)\s*$", dims)
        if not match:
            raise ValueError(f"Invalid viewport '{raw}'. Use name=WIDTHxHEIGHT or WIDTHxHEIGHT.")
        parsed.append(Viewport(name.strip() or f"vp-{index}", int(match.group(1)), int(match.group(2))))
    return parsed


def parse_themes(values: Iterable[str] | None) -> list[str]:
    themes = [value.strip().lower() for value in values or DEFAULT_THEMES if value.strip()]
    allowed = {"auto", "light", "dark"}
    invalid = sorted(set(themes) - allowed)
    if invalid:
        raise ValueError(f"Invalid theme values: {', '.join(invalid)}")
    ordered: list[str] = []
    for theme in themes:
        if theme not in ordered:
            ordered.append(theme)
    return ordered or DEFAULT_THEMES.copy()


def parse_states(values: Iterable[str] | None) -> list[str]:
    states = [value.strip().lower() for value in values or DEFAULT_STATES if value.strip()]
    allowed = {"hover", "focus", "active"}
    invalid = sorted(set(states) - allowed)
    if invalid:
        raise ValueError(f"Invalid interactive states: {', '.join(invalid)}")
    ordered: list[str] = []
    for state in states:
        if state not in ordered:
            ordered.append(state)
    return ordered


def normalize_pages(values: Iterable[str] | None) -> list[str]:
    pages = [value.strip() for value in values or [] if value.strip()]
    if not pages:
        return ["/"]
    ordered: list[str] = []
    for page in pages:
        if page not in ordered:
            ordered.append(page)
    return ordered


def compact_trace(trace: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    return trace[:limit]


def write_json(path: Path | str, data: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text())


def write_markdown(path: Path | str, text: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text.rstrip() + "\n")


def build_root_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--source", required=True, help="Remote URL, local HTML file, or local site directory.")
    parser.add_argument("--page", action="append", default=[], help="Relative or absolute page path to inspect.")
    parser.add_argument("--theme", action="append", default=[], help="Theme mode: auto, light, dark.")
    parser.add_argument(
        "--viewport",
        action="append",
        default=[],
        help="Viewport in name=WIDTHxHEIGHT form. Repeat as needed.",
    )
    parser.add_argument("--state", action="append", default=[], help="Interactive state to probe: hover, focus, active.")
    parser.add_argument("--output", required=True, type=Path, help="Directory for generated outputs.")
    parser.add_argument("--wait-ms", type=int, default=1200, help="Additional settle delay after network idle.")
    parser.add_argument("--max-elements", type=int, default=180, help="Maximum visible elements to sample per capture.")
    parser.add_argument(
        "--max-state-probes",
        type=int,
        default=36,
        help="Maximum interactive elements to probe for hover/focus/active states per capture.",
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Write inspection.raw.json in addition to normalized outputs.",
    )
    return parser


def build_normalize_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize a raw inspection into token JSON files.")
    parser.add_argument("--inspection", required=True, help="Path to inspection.raw.json.")
    parser.add_argument("--output", required=True, type=Path, help="Directory for normalized token outputs.")
    return parser


def build_figma_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Figma mapping and markdown reports from extracted tokens.")
    parser.add_argument("--inspection", required=True, help="Path to inspection.raw.json.")
    parser.add_argument("--tokens-dir", required=True, type=Path, help="Directory containing the token JSON files.")
    parser.add_argument("--output", required=True, type=Path, help="Directory for figma-mapping and reports.")
    return parser
