#!/usr/bin/env python3
from visual_system_extractor.cli_common import build_root_parser
from visual_system_extractor.figma_export import build_figma_outputs
from visual_system_extractor.inspector import inspect_site
from visual_system_extractor.normalizer import normalize_inspection


def main() -> int:
    parser = build_root_parser("End-to-end visual system extraction for a site or app.")
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
        keep_intermediate=args.keep_intermediate,
    )
    normalized = normalize_inspection(inspection, args.output)
    build_figma_outputs(inspection, normalized, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
