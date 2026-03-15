#!/usr/bin/env python3
from pathlib import Path

from visual_system_extractor.cli_common import build_normalize_parser, read_json
from visual_system_extractor.normalizer import normalize_inspection


def main() -> int:
    parser = build_normalize_parser()
    args = parser.parse_args()
    inspection = read_json(Path(args.inspection))
    normalize_inspection(inspection, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
