from __future__ import annotations

import math
import re
from typing import Any

SUPPORTED_COMPONENTS = [
    "button",
    "input",
    "textarea",
    "select",
    "checkbox",
    "radio",
    "dropdown",
    "modal",
    "card",
    "tabs",
    "table",
    "badge",
    "chip",
    "tooltip",
    "navbar",
    "sidebar",
    "pagination",
    "toast",
    "accordion",
    "menu",
    "link",
    "breadcrumb",
    "form-group",
    "dialog",
]

TEXT_INPUT_TYPES = {
    "",
    "email",
    "number",
    "password",
    "search",
    "tel",
    "text",
    "url",
    "date",
    "datetime-local",
    "month",
    "time",
    "week",
}
BUTTON_INPUT_TYPES = {"button", "submit", "reset"}

KEYWORDS = {
    "button": {"btn", "button", "cta"},
    "input": {"input", "field", "control"},
    "textarea": {"textarea"},
    "select": {"select", "combobox", "picker"},
    "checkbox": {"checkbox", "switch", "toggle"},
    "radio": {"radio"},
    "dropdown": {"dropdown", "popover", "menu-trigger", "select"},
    "modal": {"modal", "drawer", "sheet", "overlay"},
    "card": {"card", "tile", "panel", "surface"},
    "tabs": {"tabs", "tablist", "segmented"},
    "table": {"table", "grid", "datagrid"},
    "badge": {"badge", "pill", "status"},
    "chip": {"chip", "tag", "token"},
    "tooltip": {"tooltip", "hint"},
    "navbar": {"navbar", "topbar", "header", "masthead"},
    "sidebar": {"sidebar", "sidenav", "drawer"},
    "pagination": {"pagination", "pager"},
    "toast": {"toast", "snackbar", "notice"},
    "accordion": {"accordion", "collapse", "disclosure"},
    "menu": {"menu", "menubar", "contextmenu"},
    "link": {"link"},
    "breadcrumb": {"breadcrumb", "crumb"},
    "form-group": {"form-group", "field-group", "input-group"},
    "dialog": {"dialog"},
}


def _token_pool(element: dict[str, Any]) -> set[str]:
    classes = [item.lower() for item in element.get("classes", []) if item]
    identifier = (element.get("id") or "").lower()
    role = (element.get("role") or "").lower()
    tag = (element.get("tag") or "").lower()
    input_type = (element.get("inputType") or "").lower()
    selector = (element.get("selector") or "").lower()
    pieces = classes + [identifier, role, tag, input_type, selector]
    return {token for piece in pieces for token in re.split(r"[^a-z0-9]+", piece) if token}


def _has_keyword(element: dict[str, Any], key: str) -> bool:
    tokens = _token_pool(element)
    return any(keyword in tokens for keyword in KEYWORDS.get(key, set()))


def _style(element: dict[str, Any], state: str = "base") -> dict[str, Any]:
    return element.get("states", {}).get(state, {}).get("style", {})


def _parse_px(value: Any) -> float | None:
    if value in (None, "", "auto", "normal"):
        return None
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)px\s*$", str(value))
    if not match:
        return None
    return float(match.group(1))


def _is_transparent(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.replace(" ", "").lower()
    return normalized in {"transparent", "rgba(0,0,0,0)", "rgba(0,0,0,0.0)"}


def _has_border(style: dict[str, Any]) -> bool:
    width = _parse_px(style.get("borderTopWidth")) or 0.0
    border_style = (style.get("borderTopStyle") or "").lower()
    border_color = style.get("borderTopColor")
    return width > 0 and border_style not in {"none", ""} and not _is_transparent(border_color)


def _has_fill(style: dict[str, Any]) -> bool:
    return not _is_transparent(style.get("backgroundColor"))


def _has_shadow(style: dict[str, Any]) -> bool:
    value = (style.get("boxShadow") or "").strip().lower()
    return value not in {"", "none"}


def _radius(style: dict[str, Any]) -> float:
    return _parse_px(style.get("borderRadius")) or 0.0


def _height(style: dict[str, Any]) -> float:
    return _parse_px(style.get("height")) or _parse_px(style.get("minHeight")) or 0.0


def _area(element: dict[str, Any]) -> float:
    bounds = element.get("bounds", {})
    return float(bounds.get("width", 0)) * float(bounds.get("height", 0))


def classify_component(element: dict[str, Any]) -> dict[str, Any]:
    tag = (element.get("tag") or "").lower()
    role = (element.get("role") or "").lower()
    input_type = (element.get("inputType") or "").lower()
    state_style = _style(element)
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}

    def add(name: str, score: float, reason: str) -> None:
        if score <= scores.get(name, 0.0):
            return
        scores[name] = score
        reasons.setdefault(name, []).append(reason)

    if tag == "button":
        add("button", 0.98, "button tag")
    if input_type in BUTTON_INPUT_TYPES:
        add("button", 0.93, f"input[{input_type}]")
    if role == "button":
        add("button", 0.9, "ARIA role=button")
    if _has_keyword(element, "button"):
        add("button", 0.75, "button keyword")

    if tag == "input" and input_type in TEXT_INPUT_TYPES:
        add("input", 0.97, f"text-like input[{input_type or 'text'}]")
    if _has_keyword(element, "input") and tag in {"div", "label", "span"}:
        add("form-group", 0.55, "field wrapper keyword")

    if tag == "textarea":
        add("textarea", 0.98, "textarea tag")
    if tag == "select" or role in {"combobox", "listbox"}:
        add("select", 0.96, "select or combobox role")

    if tag == "input" and input_type == "checkbox":
        add("checkbox", 0.98, "checkbox input")
    if role in {"checkbox", "switch"}:
        add("checkbox", 0.94, f"ARIA role={role}")

    if tag == "input" and input_type == "radio":
        add("radio", 0.98, "radio input")
    if role == "radio":
        add("radio", 0.94, "ARIA role=radio")

    if tag == "dialog" or role == "dialog":
        add("dialog", 0.98, "dialog element or role")
    if element.get("states", {}).get("base", {}).get("attributes", {}).get("ariaModal"):
        add("modal", 0.95, "aria-modal=true")
    if _has_keyword(element, "modal"):
        add("modal", 0.75, "modal keyword")

    if tag in {"nav", "header"}:
        add("navbar", 0.78, f"{tag} tag")
    if tag == "aside":
        add("sidebar", 0.88, "aside tag")
    if _has_keyword(element, "navbar"):
        add("navbar", 0.86, "navbar keyword")
    if _has_keyword(element, "sidebar"):
        add("sidebar", 0.86, "sidebar keyword")

    if role in {"tab", "tablist", "tabpanel"} or _has_keyword(element, "tabs"):
        add("tabs", 0.9, "tab role or keyword")
    if tag == "table" or role in {"table", "grid"}:
        add("table", 0.96, "table tag or role")

    if role == "tooltip" or _has_keyword(element, "tooltip"):
        add("tooltip", 0.94, "tooltip role or keyword")
    if role in {"menu", "menubar", "menuitem"} or _has_keyword(element, "menu"):
        add("menu", 0.92, "menu role or keyword")
    if _has_keyword(element, "dropdown"):
        add("dropdown", 0.8, "dropdown keyword")
    if role in {"alert", "status"} or _has_keyword(element, "toast"):
        add("toast", 0.92, "toast role or keyword")
    if tag in {"details", "summary"} or _has_keyword(element, "accordion"):
        add("accordion", 0.92, "accordion pattern")

    if tag == "a":
        add("link", 0.95, "anchor tag")
    if _has_keyword(element, "breadcrumb"):
        add("breadcrumb", 0.84, "breadcrumb keyword")
    if _has_keyword(element, "pagination"):
        add("pagination", 0.84, "pagination keyword")

    if _has_keyword(element, "badge"):
        add("badge", 0.85, "badge keyword")
    if _has_keyword(element, "chip"):
        add("chip", 0.85, "chip keyword")

    height = _height(state_style)
    radius = _radius(state_style)
    area = _area(element)
    if area > 900 and (_has_fill(state_style) or _has_border(state_style) or _has_shadow(state_style)):
        add("card", 0.62, "surface-like container")
    if tag in {"article", "section"} and area > 2000:
        add("card", 0.64, f"{tag} surface container")
    if tag == "form":
        add("form-group", 0.72, "form tag")

    if height and height < 40 and radius >= max(height / 2 - 2, 8) and _has_fill(state_style):
        add("badge", 0.65, "compact pill surface")
        add("chip", 0.63, "compact pill surface")

    if not scores:
        return {"type": "unknown", "confidence": 0.0, "reasons": []}

    component_type, score = max(scores.items(), key=lambda item: item[1])
    confidence = round(max(0.35, min(0.99, score)), 2)
    return {"type": component_type, "confidence": confidence, "reasons": reasons.get(component_type, [])[:4]}


def infer_size_bucket(style: dict[str, Any]) -> str:
    height = _height(style)
    font_size = _parse_px(style.get("fontSize")) or 0.0
    reference = max(height, font_size * 2)
    if reference >= 52:
        return "xl"
    if reference >= 44:
        return "lg"
    if reference >= 34:
        return "md"
    if reference >= 24:
        return "sm"
    return "xs"


def infer_variant(component_type: str, element: dict[str, Any], style: dict[str, Any]) -> str:
    fill = _has_fill(style)
    border = _has_border(style)
    shadow = _has_shadow(style)
    radius = _radius(style)
    display = (style.get("display") or "").lower()
    text_decoration = (style.get("textDecorationLine") or "").lower()

    if component_type in {"button", "badge", "chip"}:
        if fill and not border:
            return "solid"
        if border and not fill:
            return "outline"
        if fill and border:
            return "soft"
        if radius >= 999 or (height := _height(style)) and radius >= math.floor(height / 2):
            return "pill"
        return "ghost"

    if component_type in {"input", "textarea", "select"}:
        if border and fill:
            return "filled"
        if border:
            return "outline"
        return "underlined"

    if component_type in {"modal", "dialog", "dropdown", "menu", "toast", "card"}:
        if shadow:
            return "elevated"
        if border:
            return "outlined"
        return "flat"

    if component_type == "tabs":
        attributes = element.get("states", {}).get("base", {}).get("attributes", {})
        if attributes.get("selected"):
            return "selected"
        return "tab"

    if component_type in {"navbar", "menu"}:
        if display in {"flex", "inline-flex"} and style.get("flexDirection") == "column":
            return "vertical"
        return "horizontal"

    if component_type == "sidebar":
        return "vertical"

    if component_type == "table":
        if border:
            return "bordered"
        return "plain"

    if component_type == "link":
        if "underline" in text_decoration:
            return "underlined"
        if fill or border:
            return "button-link"
        return "text"

    if component_type == "accordion":
        attributes = element.get("states", {}).get("base", {}).get("attributes", {})
        if attributes.get("expanded"):
            return "open"
        return "closed"

    if component_type == "pagination":
        return "standard"

    if component_type == "breadcrumb":
        return "trail"

    if component_type == "form-group":
        return "field"

    return "default"


def summarize_structure(element: dict[str, Any]) -> str:
    style = _style(element)
    parts: list[str] = []
    tag = element.get("tag")
    if tag:
        parts.append(tag)
    display = style.get("display")
    if display:
        parts.append(display)
    child_count = element.get("childCount")
    if isinstance(child_count, int):
        parts.append(f"{child_count} дочерних элементов")
    if style.get("gridTemplateColumns") and style.get("gridTemplateColumns") != "none":
        parts.append("grid")
    if style.get("flexDirection"):
        parts.append(f"flex-{style['flexDirection']}")
    return ", ".join(parts) or "структура не классифицирована"


def state_names(element: dict[str, Any]) -> list[str]:
    return sorted(element.get("states", {}).keys())
