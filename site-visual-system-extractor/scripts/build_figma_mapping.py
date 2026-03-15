#!/usr/bin/env python3
from pathlib import Path

from visual_system_extractor.cli_common import build_figma_parser, read_json
from visual_system_extractor.figma_export import build_figma_outputs


def main() -> int:
    parser = build_figma_parser()
    args = parser.parse_args()
    inspection = read_json(Path(args.inspection))
    normalized = {
        "foundation": read_json(args.tokens_dir / "tokens.foundation.json")["foundation"],
        "semantic": read_json(args.tokens_dir / "tokens.semantic.json")["semantic"],
        "components": read_json(args.tokens_dir / "tokens.components.json")["components"],
        "themes": read_json(args.tokens_dir / "tokens.themes.json")["themes"],
    }
    build_figma_outputs(inspection, normalized, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
