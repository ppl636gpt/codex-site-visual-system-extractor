from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from .cli_common import compact_trace, ensure_output_dir, write_json, write_markdown


def _flatten_tokens(node: Any, path: list[str], items: list[dict[str, Any]]) -> None:
    if isinstance(node, dict) and "$value" in node:
        items.append(
            {
                "tokenPath": ".".join(path),
                "value": node["$value"],
                "type": node.get("$type", "string"),
                "description": node.get("$description"),
            }
        )
        return
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if key.startswith("$"):
            continue
        _flatten_tokens(value, path + [key], items)


def _figma_type(token_type: str) -> str:
    mapping = {
        "color": "COLOR",
        "dimension": "FLOAT",
        "number": "FLOAT",
        "duration": "FLOAT",
        "fontFamily": "STRING",
        "fontWeight": "STRING",
        "typography": "STYLE",
        "shadow": "EFFECT",
        "border": "STYLE",
        "cubicBezier": "STRING",
    }
    return mapping.get(token_type, "STRING")


def _figma_collection(token_path: str) -> tuple[str, str]:
    if token_path.startswith("foundation."):
        return "Foundation", "Base"
    if token_path.startswith("semantic."):
        return "Semantic", "Default"
    if token_path.startswith("themes."):
        _, theme, *_ = token_path.split(".")
        return "Semantic", theme.capitalize()
    return "Components", "Documentation"


def _build_variable_entries(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for root_name in ("foundation", "semantic", "themes"):
        _flatten_tokens(normalized[root_name], [root_name], items)
    variables: list[dict[str, Any]] = []
    for item in items:
        collection, mode = _figma_collection(item["tokenPath"])
        variables.append(
            {
                "tokenPath": item["tokenPath"],
                "figmaName": item["tokenPath"].replace(".", "/"),
                "figmaCollection": collection,
                "figmaMode": mode,
                "figmaType": _figma_type(item["type"]),
                "sourceValue": item["value"],
                "description": item["description"],
            }
        )
    return variables


def _iter_component_entries(components: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for component_name, component_body in components.items():
        for variant, variant_body in component_body.get("variants", {}).items():
            for size, size_body in variant_body.get("sizes", {}).items():
                for theme, theme_body in size_body.get("themes", {}).items():
                    entries.append(
                        {
                            "component": component_name,
                            "variant": variant,
                            "size": size,
                            "theme": theme,
                            "states": sorted(theme_body.get("states", {}).keys()),
                            "usedTokenRefs": theme_body.get("$extensions", {}).get("codex", {}).get("usedTokenRefs", []),
                            "whereFound": theme_body.get("$extensions", {}).get("codex", {}).get("whereFound", []),
                            "structure": theme_body.get("$extensions", {}).get("codex", {}).get("structure"),
                            "confidence": theme_body.get("$extensions", {}).get("codex", {}).get("confidence"),
                        }
                    )
    return entries


def _build_figma_mapping(normalized: dict[str, Any]) -> dict[str, Any]:
    component_entries = _iter_component_entries(normalized["components"])
    theme_modes = sorted(normalized["themes"].keys())
    return {
        "collections": [
            {"name": "Foundation", "modes": ["Base"], "sourceRoots": ["foundation"]},
            {"name": "Semantic", "modes": ["Default", *[theme.capitalize() for theme in theme_modes]], "sourceRoots": ["semantic", "themes"]},
            {"name": "Components", "modes": ["Documentation"], "sourceRoots": ["components"]},
        ],
        "variables": _build_variable_entries(normalized),
        "componentMappings": [
            {
                "component": entry["component"],
                "suggestedFigmaName": entry["component"].replace("-", " ").title(),
                "properties": {
                    "Вариант": entry["variant"],
                    "Размер": entry["size"],
                    "Тема": entry["theme"],
                    "Состояние": entry["states"],
                },
                "documentationNotes": {
                    "используемыеТокены": entry["usedTokenRefs"],
                    "гдеНайдено": entry["whereFound"],
                    "структура": entry["structure"],
                    "confidence": entry["confidence"],
                },
            }
            for entry in component_entries
        ],
        "notes": [
            "Сопоставь foundation tokens с Figma Variables в коллекции Foundation.",
            "Сопоставь semantic tokens с коллекцией Semantic, а темы с Figma modes.",
            "Используй component mappings как документацию для свойств, вариантов и состояний компонентов.",
        ],
    }


def _render_components_summary(components: dict[str, Any]) -> str:
    lines = ["# Сводка по компонентам", ""]
    entries = _iter_component_entries(components)
    if not entries:
        lines.append("Переиспользуемые семейства компонентов с достаточной confidence не обнаружены.")
        return "\n".join(lines)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[entry["component"]].append(entry)

    for component_name, items in sorted(grouped.items()):
        lines.append(f"## {component_name}")
        lines.append("")
        for entry in sorted(items, key=lambda item: (item["variant"], item["size"], item["theme"])):
            lines.append(f"### {entry['variant']} / {entry['size']} / {entry['theme']}")
            lines.append(f"- Где найдено: {', '.join(entry['whereFound']) or 'n/a'}")
            lines.append(f"- Состояния: {', '.join(entry['states']) or 'base'}")
            lines.append(f"- Токены: {', '.join(entry['usedTokenRefs']) or 'остались raw values'}")
            lines.append(f"- Структура: {entry['structure'] or 'не классифицирована'}")
            reuse = "высокая" if (entry["confidence"] or 0) >= 0.8 else "средняя" if (entry["confidence"] or 0) >= 0.6 else "низкая"
            lines.append(f"- Переиспользуемость: {reuse}")
            lines.append(f"- Confidence: {entry['confidence'] or 0:.2f}")
            lines.append("")
    return "\n".join(lines)


def _palette_summary(foundation: dict[str, Any]) -> list[str]:
    colors = foundation.get("colors", {}).get("palette", {})
    summary: list[str] = []
    for family, scales in sorted(colors.items()):
        summary.append(f"- {family}: {len(scales)} tokens")
    return summary or ["- No palette tokens emitted"]


def _scale_summary(group: dict[str, Any]) -> str:
    values = []
    for token in group.values():
        if isinstance(token, dict) and "$value" in token:
            raw_value = token["$value"]
            if isinstance(raw_value, dict):
                values.append("/".join(str(part) for part in raw_value.keys()))
            else:
                values.append(str(raw_value))
    return ", ".join(values) if values else "не обнаружено"


def _token_names(group: dict[str, Any]) -> str:
    return ", ".join(group.keys()) if group else "не обнаружено"


def _layout_observations(inspection: dict[str, Any]) -> list[str]:
    media_queries: Counter[str] = Counter()
    display_modes: Counter[str] = Counter()
    grid_patterns: Counter[str] = Counter()
    for capture in inspection.get("captures", []):
        if capture.get("loadError"):
            continue
        for media_query in capture.get("document", {}).get("stylesheetSignals", {}).get("mediaQueries", []):
            media_queries[media_query] += 1
        for container in capture.get("document", {}).get("layoutContainers", []):
            style = container.get("style", {})
            display = style.get("display")
            if display:
                display_modes[display] += 1
            columns = style.get("gridTemplateColumns")
            if columns and columns != "none":
                grid_patterns[columns] += 1
    observations = []
    if media_queries:
        observations.append(f"- Media queries observed: {', '.join(query for query, _ in media_queries.most_common(6))}")
    if display_modes:
        observations.append(f"- Dominant layout modes: {', '.join(f'{mode} ({count})' for mode, count in display_modes.most_common(4))}")
    if grid_patterns:
        observations.append(f"- Grid patterns: {', '.join(pattern for pattern, _ in grid_patterns.most_common(4))}")
    return observations or ["- Доказательства по layout ограничились inline и surface-элементами."]


def _theme_model(inspection: dict[str, Any], normalized: dict[str, Any]) -> list[str]:
    themes = sorted(normalized["themes"].keys())
    lines = [f"- Извлечённые темы: {', '.join(themes)}"]
    theme_hints: Counter[str] = Counter()
    for capture in inspection.get("captures", []):
        hints = capture.get("document", {}).get("themeHints", {})
        for class_name in hints.get("htmlClasses", []) + hints.get("bodyClasses", []):
            lowered = class_name.lower()
            if "theme" in lowered or "dark" in lowered or "light" in lowered:
                theme_hints[lowered] += 1
    if theme_hints:
        lines.append(f"- Theme hint classes: {', '.join(name for name, _ in theme_hints.most_common(6))}")
    return lines


def _repeated_patterns(normalized: dict[str, Any]) -> list[str]:
    entries = _iter_component_entries(normalized["components"])
    component_counts: Counter[str] = Counter(entry["component"] for entry in entries)
    if not component_counts:
        return ["- Повторяющиеся component patterns выше порога confidence не обнаружены."]
    return [f"- {component}: {count} групп variant/theme" for component, count in component_counts.most_common(8)]


def _inconsistencies(normalized: dict[str, Any]) -> list[str]:
    foundation = normalized["foundation"]
    spacing_count = len(foundation.get("spacing", {}))
    radius_count = len(foundation.get("radii", {}))
    shadow_count = len(foundation.get("shadows", {}))
    notes = []
    if spacing_count > 14:
        notes.append(f"- Spacing scale слишком широкая ({spacing_count} значений); ручная консолидация может улучшить переиспользование.")
    if radius_count > 7:
        notes.append(f"- Radius scale содержит {radius_count} значений; проверь, можно ли объединить почти одинаковые токены.")
    if shadow_count > 6:
        notes.append(f"- Shadow scale содержит {shadow_count} значений; проверь, можно ли упростить уровни elevation.")
    if not notes:
        notes.append("- Существенных несогласованностей scale в извлечённой выборке не обнаружено.")
    return notes


def _confidence_lines(normalized: dict[str, Any]) -> list[str]:
    confidence_values: list[float] = []
    for root_name in ("foundation", "semantic", "themes"):
        items: list[dict[str, Any]] = []
        _flatten_tokens(normalized[root_name], [root_name], items)
        for item in items:
            pass
    for component_entry in _iter_component_entries(normalized["components"]):
        if component_entry["confidence"] is not None:
            confidence_values.append(component_entry["confidence"])
    if confidence_values:
        return [f"- Средняя confidence переиспользуемых компонентов: {mean(confidence_values):.2f}"]
    return ["- Не удалось вычислить confidence компонентов по текущей выборке."]


def _limitations(inspection: dict[str, Any]) -> list[str]:
    lines = []
    warnings = [warning for warning in inspection.get("warnings", []) if warning]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings[:8])
    errors = [capture for capture in inspection.get("captures", []) if capture.get("loadError")]
    if errors:
        lines.extend(f"- Не удалось загрузить {capture['page']} ({capture['theme']}/{capture['viewport']['name']}): {capture['loadError']}" for capture in errors[:6])
    if not lines:
        lines.append("- Существенных сбоев извлечения не зафиксировано.")
    return lines


def _reliability_breakdown(normalized: dict[str, Any]) -> list[str]:
    reliable = 0
    heuristic = 0

    def walk(node: Any) -> None:
        nonlocal reliable, heuristic
        if isinstance(node, dict) and "$value" in node:
            confidence = node.get("$extensions", {}).get("codex", {}).get("confidence", 0.0)
            if confidence >= 0.85:
                reliable += 1
            elif confidence < 0.6:
                heuristic += 1
            return
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key.startswith("$"):
                continue
            walk(value)

    for root_name in ("foundation", "semantic", "themes"):
        walk(normalized[root_name])
    return [
        f"- Надёжные токены (confidence >= 0.85): {reliable}",
        f"- Эвристические токены (confidence < 0.60): {heuristic}",
    ]


def _render_design_audit(inspection: dict[str, Any], normalized: dict[str, Any]) -> str:
    foundation = normalized["foundation"]
    lines = ["# Аудит дизайн-системы", ""]
    lines.append("## Сводка по палитре")
    lines.extend(_palette_summary(foundation))
    lines.append("")
    lines.append("## Типографическая шкала")
    lines.append(f"- Font families: {_scale_summary(foundation.get('typography', {}).get('family', {}))}")
    lines.append(f"- Font sizes: {_scale_summary(foundation.get('typography', {}).get('size', {}))}")
    lines.append(f"- Typography styles: {_token_names(foundation.get('typography', {}).get('style', {}))}")
    lines.append("")
    lines.append("## Шкала отступов")
    lines.append(f"- {_scale_summary(foundation.get('spacing', {}))}")
    lines.append("")
    lines.append("## Шкала радиусов")
    lines.append(f"- {_scale_summary(foundation.get('radii', {}))}")
    lines.append("")
    lines.append("## Шкала теней")
    lines.append(f"- {_scale_summary(foundation.get('shadows', {}))}")
    lines.append("")
    lines.append("## Наблюдения по layout")
    lines.extend(_layout_observations(inspection))
    lines.append("")
    lines.append("## Модель тем")
    lines.extend(_theme_model(inspection, normalized))
    lines.append("")
    lines.append("## Повторяющиеся UI-паттерны")
    lines.extend(_repeated_patterns(normalized))
    lines.append("")
    lines.append("## Несогласованности")
    lines.extend(_inconsistencies(normalized))
    lines.append("")
    lines.append("## Заметки по confidence")
    lines.extend(_confidence_lines(normalized))
    lines.extend(_reliability_breakdown(normalized))
    lines.append("")
    lines.append("## Ограничения")
    lines.extend(_limitations(inspection))
    return "\n".join(lines)


def build_figma_outputs(inspection: dict[str, Any], normalized: dict[str, Any], output_dir: str | Any) -> None:
    output = ensure_output_dir(output_dir)
    write_json(output / "figma-mapping.json", _build_figma_mapping(normalized))
    write_markdown(output / "components-summary.md", _render_components_summary(normalized["components"]))
    write_markdown(output / "design-audit.md", _render_design_audit(inspection, normalized))
