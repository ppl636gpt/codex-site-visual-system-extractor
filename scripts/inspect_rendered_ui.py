#!/usr/bin/env python3
from visual_system_extractor.cli_common import build_root_parser, write_json
from visual_system_extractor.inspector import inspect_site


def main() -> int:
    parser = build_root_parser("Rendered UI inspection without token normalization.")
    args = parser.parse_args()
    inspection = inspect_site(
        source=args.source,
        pages=args.page,
        themes=args.theme,
        viewports=args.viewport,
        states=args.state,
        output_dir=args.output,
        wait_ms=args.wait_ms,
        max_elements=args.max_elements,
        max_state_probes=args.max_state_probes,
        keep_intermediate=True,
    )
    write_json(args.output / "inspection.raw.json", inspection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
