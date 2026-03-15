from __future__ import annotations

import colorsys
import json
import math
import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from .cli_common import compact_trace, ensure_output_dir, write_json
from .detection import SUPPORTED_COMPONENTS, classify_component, infer_size_bucket, infer_variant, summarize_structure

COLOR_FIELDS = [
    "color",
    "backgroundColor",
    "borderTopColor",
    "borderRightColor",
    "borderBottomColor",
    "borderLeftColor",
    "outlineColor",
    "textDecorationColor",
]
SPACING_FIELDS = [
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "marginTop",
    "marginRight",
    "marginBottom",
    "marginLeft",
    "gap",
    "rowGap",
    "columnGap",
]
SIZING_FIELDS = ["width", "height", "minWidth", "minHeight", "maxWidth", "maxHeight", "borderTopWidth"]
TYPOGRAPHY_FIELDS = ["fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing", "textTransform"]
MOTION_FIELDS = ["transitionDuration", "transitionTimingFunction"]
ROLE_KEYWORDS = {
    "primary.default": {"primary", "brand", "cta", "action"},
    "secondary.default": {"secondary", "subtle"},
    "accent.default": {"accent", "highlight"},
    "background.canvas": {"background", "canvas", "page", "app-bg"},
    "surface.default": {"surface", "panel", "card", "container"},
    "text.default": {"text", "foreground", "copy", "fg"},
    "text.muted": {"muted", "subtle-text", "secondary-text"},
    "text.inverse": {"inverse", "on-primary", "on-dark"},
    "success.default": {"success", "positive", "valid"},
    "warning.default": {"warning", "caution"},
    "danger.default": {"danger", "error", "destructive", "critical"},
    "info.default": {"info", "notice"},
    "border.default": {"border", "stroke", "divider"},
    "overlay.scrim": {"overlay", "scrim", "backdrop"},
    "focus.ring": {"focus", "ring", "outline"},
}
STATUS_FAMILIES = {
    "success.default": {"green", "teal"},
    "warning.default": {"orange", "yellow"},
    "danger.default": {"red", "pink"},
    "info.default": {"blue", "cyan"},
}


def _trace(capture: dict[str, Any], element: dict[str, Any] | None, state: str, source_variable: str | None = None) -> dict[str, Any]:
    return {
        "page": capture.get("page"),
        "theme": capture.get("theme"),
        "viewport": capture.get("viewport", {}).get("name"),
        "selector": element.get("selector") if element else ":root",
        "state": state,
        "component": (element or {}).get("component", {}).get("type"),
        "sourceVariable": source_variable,
        "tag": (element or {}).get("tag"),
    }


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _parse_px(value: Any) -> float | None:
    if value in (None, "", "auto", "normal"):
        return None
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)px\s*$", str(value))
    if not match:
        return None
    return float(match.group(1))


def _px_label(value: str) -> str:
    number = _parse_px(value)
    if number is None:
        return str(value).replace(".", "-")
    rounded = round(number, 2)
    if rounded.is_integer():
        return str(int(rounded))
    return str(rounded).replace(".", "-")


def _is_transparent(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.replace(" ", "").lower()
    return normalized in {"transparent", "rgba(0,0,0,0)", "rgba(0,0,0,0.0)"}


def _canonicalize_color(value: str | None) -> str | None:
    if not value or value in {"initial", "inherit"}:
        return None
    normalized = value.strip()
    if _is_transparent(normalized):
        return None
    hex_match = re.match(r"^#([0-9a-fA-F]{3,8})$", normalized)
    if hex_match:
        hex_value = hex_match.group(1)
        if len(hex_value) == 3:
            return "#" + "".join(channel * 2 for channel in hex_value).upper()
        if len(hex_value) == 6:
            return "#" + hex_value.upper()
        if len(hex_value) == 8:
            rgb = "#" + hex_value[:6].upper()
            alpha = int(hex_value[6:], 16) / 255
            return f"rgba({int(hex_value[:2], 16)}, {int(hex_value[2:4], 16)}, {int(hex_value[4:6], 16)}, {alpha:.2f})"
    rgb_match = re.match(r"^rgba?\(([^)]+)\)$", normalized.replace(" / ", ","))
    if not rgb_match:
        return None
    parts = [chunk.strip() for chunk in rgb_match.group(1).split(",")]
    if len(parts) < 3:
        return None
    red = int(float(parts[0]))
    green = int(float(parts[1]))
    blue = int(float(parts[2]))
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    if alpha >= 0.995:
        return f"#{red:02X}{green:02X}{blue:02X}"
    return f"rgba({red}, {green}, {blue}, {alpha:.2f})"


def _color_rgba(value: str) -> tuple[int, int, int, float]:
    if value.startswith("#"):
        return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16), 1.0
    rgb_match = re.match(r"^rgba\((\d+), (\d+), (\d+), ([0-9.]+)\)$", value)
    if rgb_match:
        return (
            int(rgb_match.group(1)),
            int(rgb_match.group(2)),
            int(rgb_match.group(3)),
            float(rgb_match.group(4)),
        )
    raise ValueError(f"Unsupported color value: {value}")


def _color_family(value: str) -> str:
    red, green, blue, _ = _color_rgba(value)
    hue, saturation, _ = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    if saturation < 0.12:
        return "neutral"
    hue_degrees = hue * 360
    if hue_degrees < 15 or hue_degrees >= 345:
        return "red"
    if hue_degrees < 40:
        return "orange"
    if hue_degrees < 70:
        return "yellow"
    if hue_degrees < 150:
        return "green"
    if hue_degrees < 180:
        return "teal"
    if hue_degrees < 210:
        return "cyan"
    if hue_degrees < 250:
        return "blue"
    if hue_degrees < 285:
        return "indigo"
    if hue_degrees < 320:
        return "purple"
    return "pink"


def _luminance(value: str) -> float:
    red, green, blue, alpha = _color_rgba(value)
    if alpha == 0:
        return 1.0

    def channel(component: int) -> float:
        normalized = component / 255
        if normalized <= 0.03928:
            return normalized / 12.92
        return ((normalized + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _with_alpha(value: str, alpha: float) -> str:
    red, green, blue, _ = _color_rgba(value)
    return f"rgba({red}, {green}, {blue}, {alpha:.2f})"


def _normalize_duration(value: str | None) -> str | None:
    if not value:
        return None
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        return None
    first = values[0]
    if first.endswith("ms"):
        return first
    if first.endswith("s"):
        try:
            milliseconds = float(first[:-1]) * 1000
            return f"{int(round(milliseconds))}ms"
        except ValueError:
            return None
    return None


def _alias_or_raw(path: str | None, raw_value: Any) -> Any:
    return f"{{{path}}}" if path else raw_value


def _meaningful_shadow(value: str) -> bool:
    normalized = value.replace(" ", "").lower()
    return normalized not in {"", "none", "rgba(0,0,0,0)0px0px0px0px"}


def _register(bucket: dict[str, Any], key: str, value: Any, trace: dict[str, Any], *, source_variable: str | None = None, hint: str | None = None) -> None:
    entry = bucket.setdefault(
        key,
        {
            "value": value,
            "count": 0,
            "trace": [],
            "sourceVariables": Counter(),
            "hints": Counter(),
        },
    )
    entry["count"] += 1
    if len(entry["trace"]) < 8:
        entry["trace"].append(trace)
    if source_variable:
        entry["sourceVariables"][source_variable] += 1
    if hint:
        entry["hints"][hint] += 1


def _most_common(counter: Counter[str]) -> str | None:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def _make_token(value: Any, token_type: str, entry: dict[str, Any], description: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    token = {
        "$value": value,
        "$type": token_type,
        "$extensions": {
            "codex": {
                "confidence": round(min(0.99, 0.82 + min(entry["count"], 12) * 0.012), 2),
                "observationCount": entry["count"],
                "trace": compact_trace(entry["trace"]),
            }
        },
    }
    if entry["sourceVariables"]:
        token["$extensions"]["codex"]["sourceVariables"] = [name for name, _ in entry["sourceVariables"].most_common(4)]
    if description:
        token["$description"] = description
    if extra:
        token["$extensions"]["codex"].update(extra)
    return token


def _set_nested(root: dict[str, Any], path: list[str], value: Any) -> None:
    cursor = root
    for segment in path[:-1]:
        cursor = cursor.setdefault(segment, {})
    cursor[path[-1]] = value


def _flatten_token_paths(root_name: str, tree: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}

    def walk(node: Any, path: list[str]) -> None:
        if isinstance(node, dict) and "$value" in node:
            lookup[str(node["$value"])] = ".".join(path)
            return
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key.startswith("$"):
                continue
            walk(value, path + [key])

    walk(tree, [root_name])
    return lookup


def _foundation_dimension_lookup(foundation: dict[str, Any], key_path: list[str], token_prefix: str, values: list[tuple[str, dict[str, Any]]], type_name: str) -> tuple[dict[str, Any], dict[str, str]]:
    group: dict[str, Any] = {}
    lookup: dict[str, str] = {}
    for value, entry in values:
        token_name = f"{token_prefix}-{_px_label(value)}"
        group[token_name] = _make_token(value, type_name, entry)
        lookup[value] = ".".join(["foundation", *key_path, token_name])
    return group, lookup


def _font_family_category(value: str) -> str:
    normalized = value.lower()
    if "mono" in normalized or "code" in normalized:
        return "mono"
    if "serif" in normalized or any(item in normalized for item in ["georgia", "merriweather", "times"]):
        return "serif"
    if any(item in normalized for item in ["display", "headline", "grotesk"]):
        return "display"
    return "sans"


def _clean_font_family(value: str) -> str:
    return value.split(",")[0].strip().strip("'\"")


def _infer_text_style_role(trace: dict[str, Any], style: dict[str, Any]) -> str:
    tag = (trace.get("tag") or "").lower()
    component = (trace.get("component") or "").lower()
    size = _parse_px(style.get("fontSize")) or 0.0
    if component in {"button", "badge", "chip", "tabs", "menu", "navbar"}:
        return "label"
    if tag in {"h1", "h2"} or size >= 32:
        return "display"
    if tag in {"h3", "h4", "h5"} or size >= 24:
        return "heading"
    if size <= 12:
        return "caption"
    return "body"


def _collect_foundation_observations(inspection: dict[str, Any]) -> dict[str, Any]:
    observations = {
        "colors": {},
        "fontFamily": {},
        "fontSize": {},
        "fontWeight": {},
        "lineHeight": {},
        "letterSpacing": {},
        "typographyStyle": {},
        "spacing": {},
        "sizing": {},
        "radii": {},
        "shadows": {},
        "borders": {},
        "opacity": {},
        "duration": {},
        "easing": {},
    }

    for capture in inspection.get("captures", []):
        if capture.get("loadError"):
            continue

        document = capture.get("document", {})
        for selector_name, style in (("html", document.get("rootStyle", {})), ("body", document.get("bodyStyle", {}))):
            trace = _trace(capture, None, "base")
            trace["selector"] = selector_name
            for field in COLOR_FIELDS:
                color = _canonicalize_color(style.get(field))
                if color:
                    _register(observations["colors"], color, color, trace)
            for field in TYPOGRAPHY_FIELDS:
                value = _normalize_whitespace(str(style.get(field)))
                if not value or value == "normal":
                    continue
                target = {
                    "fontFamily": "fontFamily",
                    "fontSize": "fontSize",
                    "fontWeight": "fontWeight",
                    "lineHeight": "lineHeight",
                    "letterSpacing": "letterSpacing",
                }.get(field)
                if target:
                    _register(observations[target], value, value, trace)

        for variable_source, variables in (("root", document.get("rootCssVariables", {})), ("body", document.get("bodyCssVariables", {}))):
            for name, value in variables.items():
                trace = _trace(capture, None, "base", source_variable=name)
                trace["selector"] = variable_source
                color = _canonicalize_color(value)
                if color:
                    _register(observations["colors"], color, color, trace, source_variable=name)
                length = _parse_px(value)
                if length is not None:
                    if "radius" in name:
                        _register(observations["radii"], value, value, trace, source_variable=name)
                    elif "space" in name or "gap" in name or "padding" in name or "margin" in name:
                        _register(observations["spacing"], value, value, trace, source_variable=name)
                    else:
                        _register(observations["sizing"], value, value, trace, source_variable=name)

        for element in capture.get("elements", []):
            component = classify_component(element)
            element["component"] = component
            for state_name, state in element.get("states", {}).items():
                style = state.get("style", {})
                trace = _trace(capture, element, state_name)
                trace["component"] = component["type"]
                for field in COLOR_FIELDS:
                    color = _canonicalize_color(style.get(field))
                    if color:
                        _register(observations["colors"], color, color, trace)
                for field in TYPOGRAPHY_FIELDS:
                    value = _normalize_whitespace(str(style.get(field)))
                    if not value or value == "normal":
                        continue
                    target = {
                        "fontFamily": "fontFamily",
                        "fontSize": "fontSize",
                        "fontWeight": "fontWeight",
                        "lineHeight": "lineHeight",
                        "letterSpacing": "letterSpacing",
                    }.get(field)
                    if target:
                        _register(observations[target], value, value, trace)
                typography_value = {
                    "fontFamily": style.get("fontFamily"),
                    "fontSize": style.get("fontSize"),
                    "fontWeight": style.get("fontWeight"),
                    "lineHeight": style.get("lineHeight"),
                    "letterSpacing": style.get("letterSpacing") or "0px",
                    "textTransform": style.get("textTransform") or "none",
                }
                if typography_value["fontFamily"] and typography_value["fontSize"]:
                    key = json.dumps(typography_value, sort_keys=True)
                    _register(
                        observations["typographyStyle"],
                        key,
                        typography_value,
                        trace,
                        hint=_infer_text_style_role(trace, style),
                    )
                for field in SPACING_FIELDS:
                    value = style.get(field)
                    numeric = _parse_px(value)
                    if numeric is not None and 0 <= numeric <= 96:
                        _register(observations["spacing"], value, value, trace)
                for field in SIZING_FIELDS:
                    value = style.get(field)
                    numeric = _parse_px(value)
                    if numeric is not None and 0 <= numeric <= 640:
                        _register(observations["sizing"], value, value, trace)
                radius = style.get("borderRadius")
                if _parse_px(radius) is not None:
                    _register(observations["radii"], radius, radius, trace)
                shadow = _normalize_whitespace(str(style.get("boxShadow") or ""))
                if _meaningful_shadow(shadow):
                    _register(observations["shadows"], shadow, shadow, trace)
                opacity = style.get("opacity")
                try:
                    normalized_opacity = f"{float(opacity):.2f}"
                except (TypeError, ValueError):
                    normalized_opacity = None
                if normalized_opacity is not None:
                    _register(observations["opacity"], normalized_opacity, normalized_opacity, trace)
                duration = _normalize_duration(style.get("transitionDuration"))
                if duration and duration != "0ms":
                    _register(observations["duration"], duration, duration, trace)
                easing = _normalize_whitespace(str(style.get("transitionTimingFunction") or ""))
                if easing and easing != "ease":
                    _register(observations["easing"], easing, easing, trace)

                border_color = _canonicalize_color(style.get("borderTopColor"))
                border_width = style.get("borderTopWidth")
                border_style = style.get("borderTopStyle")
                if border_color and _parse_px(border_width) not in (None, 0.0) and border_style not in {"none", ""}:
                    border_value = {
                        "color": border_color,
                        "width": border_width,
                        "style": border_style,
                    }
                    _register(observations["borders"], json.dumps(border_value, sort_keys=True), border_value, trace)

                for variable_name, variable_value in state.get("customProperties", {}).items():
                    color = _canonicalize_color(variable_value)
                    if color:
                        _register(observations["colors"], color, color, trace, source_variable=variable_name)
                    if _parse_px(variable_value) is not None:
                        if "radius" in variable_name:
                            _register(observations["radii"], variable_value, variable_value, trace, source_variable=variable_name)
                        elif "space" in variable_name or "gap" in variable_name:
                            _register(observations["spacing"], variable_value, variable_value, trace, source_variable=variable_name)
                        else:
                            _register(observations["sizing"], variable_value, variable_value, trace, source_variable=variable_name)

    return observations


def _build_foundation_tokens(observations: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    foundation = {
        "colors": {"palette": {}},
        "typography": {"family": {}, "size": {}, "weight": {}, "lineHeight": {}, "letterSpacing": {}, "style": {}},
        "spacing": {},
        "sizing": {},
        "radii": {},
        "shadows": {},
        "borders": {},
        "opacity": {},
        "motion": {"duration": {}, "easing": {}},
    }
    lookup: dict[str, dict[str, str]] = {
        "color": {},
        "fontFamily": {},
        "fontSize": {},
        "fontWeight": {},
        "lineHeight": {},
        "letterSpacing": {},
        "spacing": {},
        "sizing": {},
        "radii": {},
        "shadow": {},
        "border": {},
        "opacity": {},
        "duration": {},
        "easing": {},
    }

    family_groups: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for color, entry in observations["colors"].items():
        family_groups[_color_family(color)].append((color, entry))
    scale_labels = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"]
    for family, items in sorted(family_groups.items()):
        sorted_items = sorted(items, key=lambda item: _luminance(item[0]), reverse=True)
        foundation["colors"]["palette"][family] = {}
        for index, (color, entry) in enumerate(sorted_items):
            scale = scale_labels[index] if index < len(scale_labels) else f"x{index + 1}"
            foundation["colors"]["palette"][family][scale] = _make_token(color, "color", entry)
            lookup["color"][color] = f"foundation.colors.palette.{family}.{scale}"

    family_counters: Counter[str] = Counter()
    for value, entry in sorted(observations["fontFamily"].items(), key=lambda item: (-item[1]["count"], item[0])):
        category = _font_family_category(value)
        family_counters[category] += 1
        token_name = f"{category}-{family_counters[category]:02d}"
        foundation["typography"]["family"][token_name] = _make_token(value, "fontFamily", entry, description=_clean_font_family(value))
        lookup["fontFamily"][value] = f"foundation.typography.family.{token_name}"

    for value, entry in sorted(observations["fontSize"].items(), key=lambda item: (_parse_px(item[0]) or 0, item[0])):
        token_name = f"size-{_px_label(value)}"
        foundation["typography"]["size"][token_name] = _make_token(value, "dimension", entry)
        lookup["fontSize"][value] = f"foundation.typography.size.{token_name}"

    weight_labels = {"300": "light", "400": "regular", "500": "medium", "600": "semibold", "700": "bold"}
    for value, entry in sorted(observations["fontWeight"].items(), key=lambda item: (float(item[0]), item[0])):
        token_name = weight_labels.get(value, f"weight-{value}")
        foundation["typography"]["weight"][token_name] = _make_token(value, "fontWeight", entry)
        lookup["fontWeight"][value] = f"foundation.typography.weight.{token_name}"

    for value, entry in sorted(observations["lineHeight"].items(), key=lambda item: (_parse_px(item[0]) or 0, item[0])):
        token_name = f"line-{_px_label(value)}"
        foundation["typography"]["lineHeight"][token_name] = _make_token(value, "dimension", entry)
        lookup["lineHeight"][value] = f"foundation.typography.lineHeight.{token_name}"

    for value, entry in sorted(observations["letterSpacing"].items(), key=lambda item: (_parse_px(item[0]) or 0, item[0])):
        token_name = f"tracking-{_px_label(value)}"
        foundation["typography"]["letterSpacing"][token_name] = _make_token(value, "dimension", entry)
        lookup["letterSpacing"][value] = f"foundation.typography.letterSpacing.{token_name}"

    style_counters: Counter[str] = Counter()
    for _, entry in sorted(observations["typographyStyle"].items(), key=lambda item: (-item[1]["count"], item[0])):
        hint = _most_common(entry["hints"]) or "body"
        size_bucket = _px_label(entry["value"]["fontSize"])
        style_counters[hint] += 1
        token_name = f"{hint}-{size_bucket}-{style_counters[hint]:02d}"
        composite_value = {
            "fontFamily": _alias_or_raw(lookup["fontFamily"].get(entry["value"]["fontFamily"]), entry["value"]["fontFamily"]),
            "fontSize": _alias_or_raw(lookup["fontSize"].get(entry["value"]["fontSize"]), entry["value"]["fontSize"]),
            "fontWeight": _alias_or_raw(lookup["fontWeight"].get(entry["value"]["fontWeight"]), entry["value"]["fontWeight"]),
            "lineHeight": _alias_or_raw(lookup["lineHeight"].get(entry["value"]["lineHeight"]), entry["value"]["lineHeight"]),
            "letterSpacing": _alias_or_raw(lookup["letterSpacing"].get(entry["value"]["letterSpacing"]), entry["value"]["letterSpacing"]),
            "textTransform": entry["value"]["textTransform"],
        }
        foundation["typography"]["style"][token_name] = _make_token(composite_value, "typography", entry)

    for group_name, observation_name, prefix, token_type in (
        ("spacing", "spacing", "space", "dimension"),
        ("sizing", "sizing", "size", "dimension"),
        ("radii", "radii", "radius", "dimension"),
    ):
        values = sorted(observations[observation_name].items(), key=lambda item: (_parse_px(item[0]) or 0, item[0]))
        for value, entry in values:
            token_name = f"{prefix}-{_px_label(value)}"
            foundation[group_name][token_name] = _make_token(value, token_type, entry)
            lookup[group_name if group_name != "radii" else "radii"][value] = f"foundation.{group_name}.{token_name}"

    for index, (shadow, entry) in enumerate(sorted(observations["shadows"].items(), key=lambda item: (-item[1]["count"], item[0])), start=1):
        token_name = f"shadow-{index}"
        foundation["shadows"][token_name] = _make_token(shadow, "shadow", entry)
        lookup["shadow"][shadow] = f"foundation.shadows.{token_name}"

    for index, (_, entry) in enumerate(sorted(observations["borders"].items(), key=lambda item: (-item[1]["count"], item[0])), start=1):
        token_name = f"border-{index}"
        border_value = entry["value"].copy()
        color_path = lookup["color"].get(border_value["color"])
        border_value["color"] = f"{{{color_path}}}" if color_path else border_value["color"]
        sizing_path = lookup["sizing"].get(border_value["width"])
        border_value["width"] = f"{{{sizing_path}}}" if sizing_path else border_value["width"]
        foundation["borders"][token_name] = _make_token(border_value, "border", entry)
        lookup["border"][json.dumps(entry["value"], sort_keys=True)] = f"foundation.borders.{token_name}"

    for value, entry in sorted(observations["opacity"].items(), key=lambda item: (float(item[0]), item[0])):
        token_name = f"opacity-{int(round(float(value) * 100))}"
        foundation["opacity"][token_name] = _make_token(value, "number", entry)
        lookup["opacity"][value] = f"foundation.opacity.{token_name}"

    for value, entry in sorted(observations["duration"].items(), key=lambda item: (_parse_px(item[0].replace("ms", "px")) or 0, item[0])):
        token_name = f"duration-{value.replace('ms', '')}"
        foundation["motion"]["duration"][token_name] = _make_token(value, "duration", entry)
        lookup["duration"][value] = f"foundation.motion.duration.{token_name}"

    for index, (value, entry) in enumerate(sorted(observations["easing"].items(), key=lambda item: (-item[1]["count"], item[0])), start=1):
        token_name = f"easing-{index}"
        foundation["motion"]["easing"][token_name] = _make_token(value, "cubicBezier", entry)
        lookup["easing"][value] = f"foundation.motion.easing.{token_name}"

    return foundation, lookup


def _variable_candidates(captures: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    keywords = ROLE_KEYWORDS.get(role, set())
    results: list[dict[str, Any]] = []
    for capture in captures:
        document = capture.get("document", {})
        sources = [
            ("html", document.get("rootCssVariables", {})),
            ("body", document.get("bodyCssVariables", {})),
        ]
        for element in capture.get("elements", []):
            for state_name, state in element.get("states", {}).items():
                sources.append((element.get("selector", "element"), state.get("customProperties", {})))
        for selector, values in sources:
            for variable_name, raw_value in values.items():
                normalized_name = variable_name.lower()
                if not any(keyword in normalized_name for keyword in keywords):
                    continue
                color = _canonicalize_color(raw_value)
                if not color:
                    continue
                results.append(
                    {
                        "value": color,
                        "confidence": 0.94,
                        "reason": f"CSS variable hint: {variable_name}",
                        "trace": [{"page": capture["page"], "theme": capture["theme"], "viewport": capture["viewport"]["name"], "selector": selector, "state": "base", "component": None, "sourceVariable": variable_name}],
                    }
                )
    return results


def _status_hint(element: dict[str, Any]) -> str | None:
    blob = " ".join([*(element.get("classes", []) or []), str(element.get("id") or "")]).lower()
    for role, keywords in {
        "success.default": {"success", "positive", "valid"},
        "warning.default": {"warning", "caution"},
        "danger.default": {"danger", "error", "destructive"},
        "info.default": {"info", "notice"},
    }.items():
        if any(keyword in blob for keyword in keywords):
            return role
    return None


def _saturated_palette(foundation: dict[str, Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for family, scales in foundation["colors"]["palette"].items():
        for scale, token in scales.items():
            items.append((family, token["$value"]))
    return items


def _aggregate_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    grouped: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        value = candidate["value"]
        entry = grouped.setdefault(value, {"score": 0.0, "trace": [], "reasons": [], "count": 0})
        entry["score"] += candidate["confidence"]
        entry["count"] += 1
        entry["trace"].extend(candidate["trace"])
        entry["reasons"].append(candidate["reason"])
    value, entry = max(grouped.items(), key=lambda item: (item[1]["score"], item[1]["count"]))
    confidence = min(0.99, 0.45 + entry["score"] / max(entry["count"], 1) * 0.5)
    return {
        "value": value,
        "confidence": round(confidence, 2),
        "trace": compact_trace(entry["trace"]),
        "reason": "; ".join(dict.fromkeys(entry["reasons"]))[:180],
        "observationCount": entry["count"],
    }


def _semantic_fallback(role: str, foundation: dict[str, Any], primary_value: str | None = None) -> dict[str, Any] | None:
    palette = _saturated_palette(foundation)
    if role in {"background.canvas", "surface.default", "surface.raised", "text.default", "text.muted", "text.inverse", "border.default", "border.subtle", "border.strong"}:
        neutral_values = [value for family, value in palette if family == "neutral"]
        if not neutral_values:
            return None
        if role == "background.canvas":
            return {"value": neutral_values[0], "confidence": 0.42, "trace": [], "reason": "neutral fallback", "observationCount": 0}
        if role == "surface.default":
            return {"value": neutral_values[min(1, len(neutral_values) - 1)], "confidence": 0.4, "trace": [], "reason": "neutral surface fallback", "observationCount": 0}
        if role == "surface.raised":
            return {"value": neutral_values[min(2, len(neutral_values) - 1)], "confidence": 0.38, "trace": [], "reason": "raised surface fallback", "observationCount": 0}
        if role == "text.default":
            return {"value": neutral_values[-1], "confidence": 0.42, "trace": [], "reason": "text fallback", "observationCount": 0}
        if role == "text.muted":
            return {"value": neutral_values[max(len(neutral_values) - 3, 0)], "confidence": 0.36, "trace": [], "reason": "muted text fallback", "observationCount": 0}
        if role == "text.inverse":
            return {"value": neutral_values[0], "confidence": 0.36, "trace": [], "reason": "inverse text fallback", "observationCount": 0}
        if role == "border.default":
            return {"value": neutral_values[min(2, len(neutral_values) - 1)], "confidence": 0.34, "trace": [], "reason": "border fallback", "observationCount": 0}
        if role == "border.subtle":
            return {"value": neutral_values[min(1, len(neutral_values) - 1)], "confidence": 0.34, "trace": [], "reason": "subtle border fallback", "observationCount": 0}
        if role == "border.strong":
            return {"value": neutral_values[max(len(neutral_values) - 3, 0)], "confidence": 0.34, "trace": [], "reason": "strong border fallback", "observationCount": 0}

    if role == "focus.ring" and primary_value:
        return {"value": _with_alpha(primary_value, 0.4), "confidence": 0.35, "trace": [], "reason": "derived from primary", "observationCount": 0}
    if role == "overlay.scrim" and primary_value:
        return {"value": "rgba(0, 0, 0, 0.56)", "confidence": 0.35, "trace": [], "reason": "overlay fallback", "observationCount": 0}

    family_preferences = STATUS_FAMILIES.get(role)
    if family_preferences:
        for family, value in palette:
            if family in family_preferences:
                return {"value": value, "confidence": 0.39, "trace": [], "reason": f"{family} palette fallback", "observationCount": 0}
    if role in {"primary.default", "secondary.default", "accent.default"}:
        saturated = [value for family, value in palette if family != "neutral"]
        if saturated:
            index = {"primary.default": 0, "secondary.default": min(1, len(saturated) - 1), "accent.default": min(2, len(saturated) - 1)}[role]
            return {"value": saturated[index], "confidence": 0.39, "trace": [], "reason": "palette fallback", "observationCount": 0}
    return None


def _role_token(candidate: dict[str, Any], foundation_lookup: dict[str, dict[str, str]]) -> dict[str, Any]:
    path = foundation_lookup["color"].get(candidate["value"])
    value = f"{{{path}}}" if path else candidate["value"]
    return {
        "$value": value,
        "$type": "color",
        "$description": candidate.get("reason"),
        "$extensions": {
            "codex": {
                "confidence": candidate.get("confidence", 0.4),
                "observationCount": candidate.get("observationCount", 0),
                "trace": compact_trace(candidate.get("trace", [])),
                "heuristic": candidate.get("confidence", 0.0) < 0.6,
            }
        },
    }


def _build_semantic_tokens(inspection: dict[str, Any], foundation: dict[str, Any], foundation_lookup: dict[str, dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[str]], dict[str, dict[str, list[str]]]]:
    theme_names = []
    for capture in inspection.get("captures", []):
        if capture.get("loadError"):
            continue
        if capture["theme"] not in theme_names:
            theme_names.append(capture["theme"])
    if not theme_names:
        theme_names = ["auto"]

    theme_roles: dict[str, dict[str, dict[str, Any]]] = {}
    base_theme = "light" if "light" in theme_names else ("auto" if "auto" in theme_names else theme_names[0])

    for theme in theme_names:
        captures = [capture for capture in inspection.get("captures", []) if capture.get("theme") == theme and not capture.get("loadError")]
        candidates: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for role in ROLE_KEYWORDS:
            candidates[role].extend(_variable_candidates(captures, role))

        for capture in captures:
            document = capture.get("document", {})
            document_background = _canonicalize_color(document.get("bodyStyle", {}).get("backgroundColor")) or _canonicalize_color(document.get("rootStyle", {}).get("backgroundColor"))
            if document_background:
                candidates["background.canvas"].append({"value": document_background, "confidence": 0.95, "reason": "document background", "trace": [_trace(capture, None, "base")], "observationCount": 1})
            document_text = _canonicalize_color(document.get("bodyStyle", {}).get("color")) or _canonicalize_color(document.get("rootStyle", {}).get("color"))
            if document_text:
                candidates["text.default"].append({"value": document_text, "confidence": 0.93, "reason": "document text color", "trace": [_trace(capture, None, "base")], "observationCount": 1})

            for element in capture.get("elements", []):
                component = element.get("component") or classify_component(element)
                element["component"] = component
                base_style = element.get("states", {}).get("base", {}).get("style", {})
                variant = infer_variant(component["type"], element, base_style)
                base_trace = _trace(capture, element, "base")
                background = _canonicalize_color(base_style.get("backgroundColor"))
                foreground = _canonicalize_color(base_style.get("color"))
                border = _canonicalize_color(base_style.get("borderTopColor"))
                if component["type"] in {"card", "modal", "dialog", "dropdown", "menu", "input", "textarea", "select", "sidebar", "navbar"} and background:
                    role = "surface.raised" if component["type"] in {"modal", "dialog", "dropdown", "menu"} or base_style.get("boxShadow") not in {"none", "", None} else "surface.default"
                    candidates[role].append({"value": background, "confidence": 0.88, "reason": f"{component['type']} surface", "trace": [base_trace], "observationCount": 1})
                if component["type"] in {"button", "badge", "chip"} and background:
                    role = "primary.default" if variant in {"solid", "soft", "pill"} else "secondary.default"
                    confidence = 0.86 if role == "primary.default" else 0.74
                    candidates[role].append({"value": background, "confidence": confidence, "reason": f"{component['type']} {variant} background", "trace": [base_trace], "observationCount": 1})
                    if foreground:
                        candidates["text.inverse"].append({"value": foreground, "confidence": 0.8, "reason": f"{component['type']} foreground", "trace": [base_trace], "observationCount": 1})
                if component["type"] == "link" and foreground:
                    candidates["accent.default"].append({"value": foreground, "confidence": 0.72, "reason": "link foreground", "trace": [base_trace], "observationCount": 1})
                    candidates["text.link"].append({"value": foreground, "confidence": 0.76, "reason": "link foreground", "trace": [base_trace], "observationCount": 1})
                if border:
                    candidates["border.default"].append({"value": border, "confidence": 0.8, "reason": "component border", "trace": [base_trace], "observationCount": 1})
                status_role = _status_hint(element)
                if status_role and (background or foreground or border):
                    status_value = background or foreground or border
                    candidates[status_role].append({"value": status_value, "confidence": 0.84, "reason": f"{status_role} class hint", "trace": [base_trace], "observationCount": 1})
                if "focus" in element.get("states", {}):
                    focus_style = element["states"]["focus"]["style"]
                    focus_color = _canonicalize_color(focus_style.get("outlineColor")) or _canonicalize_color(focus_style.get("boxShadow"))
                    if focus_color:
                        candidates["focus.ring"].append({"value": focus_color, "confidence": 0.82, "reason": "observed focus state", "trace": [_trace(capture, element, "focus")], "observationCount": 1})
                if component["type"] in {"modal", "dialog"}:
                    for state_name, state in element.get("states", {}).items():
                        overlay_color = _canonicalize_color(state.get("style", {}).get("backgroundColor"))
                        if overlay_color and overlay_color.startswith("rgba"):
                            candidates["overlay.scrim"].append({"value": overlay_color, "confidence": 0.62, "reason": "modal translucent surface", "trace": [_trace(capture, element, state_name)], "observationCount": 1})

        theme_roles[theme] = {}
        primary_candidate = _aggregate_candidates(candidates["primary.default"])
        role_order = [
            "background.canvas",
            "surface.default",
            "surface.raised",
            "text.default",
            "text.muted",
            "text.inverse",
            "text.link",
            "primary.default",
            "secondary.default",
            "accent.default",
            "success.default",
            "warning.default",
            "danger.default",
            "info.default",
            "border.default",
            "border.subtle",
            "border.strong",
            "overlay.scrim",
            "focus.ring",
        ]
        for role in role_order:
            candidate = _aggregate_candidates(candidates[role])
            if candidate is None:
                candidate = _semantic_fallback(role, foundation, primary_value=primary_candidate["value"] if primary_candidate else None)
            if candidate is None:
                continue
            theme_roles[theme][role] = candidate

    semantic: dict[str, Any] = {"colors": {}}
    themes: dict[str, Any] = {}
    semantic_lookup: dict[str, list[str]] = {}
    theme_lookup: dict[str, dict[str, list[str]]] = {}

    for theme, roles in theme_roles.items():
        theme_tree = {"semantic": {"colors": {}}}
        theme_lookup[theme] = {}
        for role, candidate in roles.items():
            token = _role_token(candidate, foundation_lookup)
            path = ["semantic", "colors", *role.split(".")]
            _set_nested(theme_tree, path, token)
            theme_lookup[theme].setdefault(candidate["value"], [])
            alias_path = f"themes.{theme}.semantic.colors.{role}"
            if alias_path not in theme_lookup[theme][candidate["value"]]:
                theme_lookup[theme][candidate["value"]].append(alias_path)
        themes[theme] = theme_tree

    for role, candidate in theme_roles.get(base_theme, {}).items():
        token = _role_token(candidate, foundation_lookup)
        _set_nested(semantic, ["colors", *role.split(".")], token)
        semantic_lookup.setdefault(candidate["value"], [])
        alias_path = f"semantic.colors.{role}"
        if alias_path not in semantic_lookup[candidate["value"]]:
            semantic_lookup[candidate["value"]].append(alias_path)

    return semantic, themes, semantic_lookup, theme_lookup


def _component_style_map(style: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    for prop in ("backgroundColor", "color", "borderRadius", "boxShadow", "fontFamily", "fontSize", "fontWeight", "lineHeight", "opacity", "height", "minHeight", "gap", "outlineColor", "outlineWidth", "textDecorationLine"):
        value = style.get(prop)
        if value not in (None, "", "none"):
            output[prop] = value

    border_color = _canonicalize_color(style.get("borderTopColor"))
    if border_color:
        output["borderColor"] = border_color
    border_width = style.get("borderTopWidth")
    if _parse_px(border_width) not in (None, 0.0):
        output["borderWidth"] = border_width
    border_style = style.get("borderTopStyle")
    if border_style not in (None, "", "none"):
        output["borderStyle"] = border_style

    padding_left = style.get("paddingLeft")
    padding_right = style.get("paddingRight")
    padding_top = style.get("paddingTop")
    padding_bottom = style.get("paddingBottom")
    if padding_left and padding_left == padding_right:
        output["paddingX"] = padding_left
    else:
        if padding_left:
            output["paddingLeft"] = padding_left
        if padding_right:
            output["paddingRight"] = padding_right
    if padding_top and padding_top == padding_bottom:
        output["paddingY"] = padding_top
    else:
        if padding_top:
            output["paddingTop"] = padding_top
        if padding_bottom:
            output["paddingBottom"] = padding_bottom
    return output


def _alias_dimension(prop: str, value: str, foundation_lookup: dict[str, dict[str, str]]) -> str | None:
    if prop in {"paddingX", "paddingY", "paddingLeft", "paddingRight", "paddingTop", "paddingBottom", "gap"}:
        return foundation_lookup["spacing"].get(value)
    if prop in {"borderRadius"}:
        return foundation_lookup["radii"].get(value)
    if prop in {"height", "minHeight", "borderWidth", "outlineWidth"}:
        return foundation_lookup["sizing"].get(value) or foundation_lookup["spacing"].get(value)
    if prop in {"fontSize"}:
        return foundation_lookup["fontSize"].get(value)
    if prop in {"lineHeight"}:
        return foundation_lookup["lineHeight"].get(value)
    return foundation_lookup["sizing"].get(value)


def _component_prop_type(prop: str) -> str:
    if prop in {"backgroundColor", "color", "borderColor", "outlineColor"}:
        return "color"
    if prop in {"boxShadow"}:
        return "shadow"
    if prop in {"fontFamily"}:
        return "fontFamily"
    if prop in {"fontWeight"}:
        return "fontWeight"
    if prop in {"opacity"}:
        return "number"
    if prop in {"borderStyle", "textDecorationLine"}:
        return "string"
    return "dimension"


def _preferred_color_alias(prop: str, value: str, theme: str, foundation_lookup: dict[str, dict[str, str]], semantic_lookup: dict[str, list[str]], theme_lookup: dict[str, dict[str, list[str]]]) -> str | None:
    preferred_keywords = {
        "backgroundColor": ("primary", "secondary", "accent", "surface", "background"),
        "color": ("text", "success", "warning", "danger", "info", "accent", "primary"),
        "borderColor": ("border", "secondary", "surface"),
        "outlineColor": ("focus", "primary", "accent"),
    }
    candidates = [*theme_lookup.get(theme, {}).get(value, []), *semantic_lookup.get(value, [])]
    for keyword in preferred_keywords.get(prop, ()):
        for candidate in candidates:
            if f".{keyword}." in candidate or candidate.endswith(f".{keyword}"):
                return candidate
    if candidates:
        return candidates[0]
    return foundation_lookup["color"].get(value)


def _component_value_token(prop: str, value: str, theme: str, foundation_lookup: dict[str, dict[str, str]], semantic_lookup: dict[str, list[str]], theme_lookup: dict[str, dict[str, list[str]]]) -> tuple[dict[str, Any], str | None]:
    alias_path = None
    if prop in {"backgroundColor", "color", "borderColor", "outlineColor"}:
        alias_path = _preferred_color_alias(prop, value, theme, foundation_lookup, semantic_lookup, theme_lookup)
    elif prop == "boxShadow":
        alias_path = foundation_lookup["shadow"].get(value)
    elif prop == "fontFamily":
        alias_path = foundation_lookup["fontFamily"].get(value)
    elif prop == "fontWeight":
        alias_path = foundation_lookup["fontWeight"].get(value)
    elif prop == "opacity":
        alias_path = foundation_lookup["opacity"].get(f"{float(value):.2f}")
    else:
        alias_path = _alias_dimension(prop, value, foundation_lookup)

    token_value = f"{{{alias_path}}}" if alias_path else value
    token = {"$value": token_value, "$type": _component_prop_type(prop)}
    return token, alias_path


def _build_component_tokens(inspection: dict[str, Any], foundation_lookup: dict[str, dict[str, str]], semantic_lookup: dict[str, list[str]], theme_lookup: dict[str, dict[str, list[str]]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for capture in inspection.get("captures", []):
        if capture.get("loadError"):
            continue
        theme = capture.get("theme", "auto")
        for element in capture.get("elements", []):
            component = element.get("component") or classify_component(element)
            element["component"] = component
            component_type = component["type"]
            if component_type not in SUPPORTED_COMPONENTS:
                continue
            base_style = element.get("states", {}).get("base", {}).get("style", {})
            variant = infer_variant(component_type, element, base_style)
            size = infer_size_bucket(base_style)
            key = (component_type, variant, size, theme)
            bucket = groups.setdefault(
                key,
                {
                    "states": defaultdict(lambda: defaultdict(Counter)),
                    "trace": [],
                    "confidence": [],
                    "pages": Counter(),
                    "structures": Counter(),
                    "usedRefs": set(),
                },
            )
            bucket["confidence"].append(component["confidence"])
            bucket["pages"][capture["page"]] += 1
            bucket["structures"][summarize_structure(element)] += 1
            bucket["trace"].append(_trace(capture, element, "base"))
            for state_name, state in element.get("states", {}).items():
                style_map = _component_style_map(state.get("style", {}))
                for prop, value in style_map.items():
                    if prop in {"backgroundColor", "color", "borderColor", "outlineColor"}:
                        normalized = _canonicalize_color(value)
                        if not normalized:
                            continue
                        value = normalized
                    bucket["states"][state_name][prop][value] += 1

    components: dict[str, Any] = {}
    for (component_type, variant, size, theme), bucket in sorted(groups.items()):
        states_out: dict[str, Any] = {}
        used_refs: set[str] = set()
        for state_name, props in bucket["states"].items():
            state_out: dict[str, Any] = {}
            for prop, counter in props.items():
                value = counter.most_common(1)[0][0]
                token, alias_path = _component_value_token(prop, value, theme, foundation_lookup, semantic_lookup, theme_lookup)
                state_out[prop] = token
                if alias_path:
                    used_refs.add(alias_path)
            states_out[state_name] = state_out
        entry = {
            "states": states_out,
            "$extensions": {
                "codex": {
                    "confidence": round(mean(bucket["confidence"]), 2) if bucket["confidence"] else 0.5,
                    "observationCount": len(bucket["trace"]),
                    "whereFound": list(bucket["pages"].keys()),
                    "usedTokenRefs": sorted(used_refs),
                    "structure": bucket["structures"].most_common(1)[0][0] if bucket["structures"] else "structure not classified",
                    "trace": compact_trace(bucket["trace"]),
                }
            },
        }
        components.setdefault(component_type, {}).setdefault("variants", {}).setdefault(variant, {}).setdefault("sizes", {}).setdefault(size, {}).setdefault("themes", {})[theme] = entry
    return components


def normalize_inspection(inspection: dict[str, Any], output_dir: str | Any) -> dict[str, Any]:
    observations = _collect_foundation_observations(inspection)
    foundation, foundation_lookup = _build_foundation_tokens(observations)
    semantic, themes, semantic_lookup, theme_lookup = _build_semantic_tokens(inspection, foundation, foundation_lookup)
    components = _build_component_tokens(inspection, foundation_lookup, semantic_lookup, theme_lookup)

    output = ensure_output_dir(output_dir)
    write_json(output / "tokens.foundation.json", {"foundation": foundation})
    write_json(output / "tokens.semantic.json", {"semantic": semantic})
    write_json(output / "tokens.components.json", {"components": components})
    write_json(output / "tokens.themes.json", {"themes": themes})

    return {
        "foundation": foundation,
        "semantic": semantic,
        "components": components,
        "themes": themes,
    }
