#!/usr/bin/env python3
"""Build an installable Codex Desktop skill bundle."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


SKILL_DIR_NAME = "site-visual-system-extractor"
ROOT_FILES = [
    "SKILL.md",
]
ROOT_DIRS = [
    "agents",
    "references",
    "scripts",
    "assets",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the repository as an installable Codex skill archive."
    )
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root containing SKILL.md and skill resources.",
    )
    parser.add_argument(
        "--output",
        default=Path(__file__).resolve().parents[1] / "release" / "skill.zip",
        type=Path,
        help="Output zip path.",
    )
    return parser.parse_args()


def copy_required_files(root: Path, staging_skill_dir: Path) -> None:
    missing: list[str] = []
    for name in ROOT_FILES:
        source = root / name
        if not source.exists():
            missing.append(name)
            continue
        shutil.copy2(source, staging_skill_dir / name)
    for name in ROOT_DIRS:
        source = root / name
        if not source.exists():
            missing.append(name)
            continue
        shutil.copytree(
            source,
            staging_skill_dir / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
    if missing:
        raise FileNotFoundError(
            "Missing required skill resources: " + ", ".join(sorted(missing))
        )


def build_archive(root: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-skill-bundle-") as temp_dir:
        temp_path = Path(temp_dir)
        staging_skill_dir = temp_path / SKILL_DIR_NAME
        staging_skill_dir.mkdir()
        copy_required_files(root, staging_skill_dir)

        archive_base = output.with_suffix("")
        archive_path = shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=temp_path,
            base_dir=SKILL_DIR_NAME,
        )
    return Path(archive_path)


def main() -> int:
    args = parse_args()
    archive_path = build_archive(args.root.resolve(), args.output.resolve())
    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
