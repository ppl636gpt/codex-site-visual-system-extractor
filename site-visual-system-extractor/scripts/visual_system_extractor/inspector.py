from __future__ import annotations

import copy
import json
import os
import socket
import threading
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from .cli_common import (
    DEFAULT_STATES,
    compact_trace,
    ensure_output_dir,
    is_url,
    normalize_pages,
    parse_states,
    parse_themes,
    parse_viewports,
    utc_now_iso,
    write_json,
)

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover - exercised in runtime environments without Playwright
    sync_playwright = None
    PlaywrightTimeoutError = RuntimeError
    PLAYWRIGHT_IMPORT_ERROR = exc
else:
    PLAYWRIGHT_IMPORT_ERROR = None

STYLE_PROPS = [
    "color",
    "backgroundColor",
    "backgroundImage",
    "borderTopColor",
    "borderTopWidth",
    "borderTopStyle",
    "borderRightColor",
    "borderRightWidth",
    "borderRightStyle",
    "borderBottomColor",
    "borderBottomWidth",
    "borderBottomStyle",
    "borderLeftColor",
    "borderLeftWidth",
    "borderLeftStyle",
    "borderRadius",
    "boxShadow",
    "opacity",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "lineHeight",
    "letterSpacing",
    "textTransform",
    "textDecorationLine",
    "textDecorationColor",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "marginTop",
    "marginRight",
    "marginBottom",
    "marginLeft",
    "width",
    "height",
    "minWidth",
    "minHeight",
    "maxWidth",
    "maxHeight",
    "gap",
    "rowGap",
    "columnGap",
    "outlineColor",
    "outlineStyle",
    "outlineWidth",
    "cursor",
    "transitionDuration",
    "transitionTimingFunction",
]
LAYOUT_PROPS = [
    "display",
    "position",
    "flexDirection",
    "justifyContent",
    "alignItems",
    "gridTemplateColumns",
    "gridTemplateRows",
    "gridAutoFlow",
]
SNAPSHOT_FUNCTION = """
(args) => {
  const styleProps = args.styleProps;
  const layoutProps = args.layoutProps;
  const maxElements = args.maxElements;
  const keywordPattern = /(btn|button|input|field|card|panel|modal|dialog|tab|table|badge|chip|navbar|sidebar|menu|dropdown|toast|tooltip|accordion|breadcrumb|pagination)/i;
  const interactiveRoles = new Set(["button", "link", "tab", "switch", "checkbox", "radio", "combobox", "menuitem"]);
  const structuralTags = new Set(["header", "nav", "main", "aside", "section", "article", "form", "table", "dialog", "footer"]);

  function visible(el) {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (!rect.width || !rect.height) return false;
    if (style.display === "none" || style.visibility === "hidden") return false;
    if (Number(style.opacity || "1") === 0) return false;
    return true;
  }

  function selectorFor(el) {
    const tag = el.tagName.toLowerCase();
    if (el.id) return `${tag}#${el.id}`;
    const classes = Array.from(el.classList).slice(0, 3).map((item) => `.${item}`).join("");
    let selector = `${tag}${classes}`;
    if (el.parentElement) {
      const siblings = Array.from(el.parentElement.children).filter((node) => node.tagName === el.tagName);
      if (siblings.length > 1) {
        selector += `:nth-of-type(${siblings.indexOf(el) + 1})`;
      }
    }
    return selector;
  }

  function domPath(el) {
    const parts = [];
    let current = el;
    while (current && current.nodeType === Node.ELEMENT_NODE && parts.length < 7) {
      parts.unshift(selectorFor(current));
      current = current.parentElement;
    }
    return parts.join(" > ");
  }

  function collectStyle(style) {
    const output = {};
    for (const prop of [...styleProps, ...layoutProps]) {
      const value = style[prop];
      if (value === undefined || value === null || value === "") continue;
      output[prop] = value;
    }
    return output;
  }

  function collectCustomProperties(style) {
    const result = {};
    for (let index = 0; index < style.length; index += 1) {
      const name = style[index];
      if (!name || !name.startsWith("--")) continue;
      const value = style.getPropertyValue(name).trim();
      if (!value) continue;
      result[name] = value;
    }
    return result;
  }

  function collectAttributes(el) {
    return {
      disabled: !!el.disabled || el.getAttribute("aria-disabled") === "true",
      checked: !!el.checked || el.getAttribute("aria-checked") === "true",
      selected: !!el.selected || el.getAttribute("aria-selected") === "true",
      expanded: el.getAttribute("aria-expanded") === "true",
      open: !!el.open || el.getAttribute("open") !== null,
      ariaModal: el.getAttribute("aria-modal") === "true",
      tabindex: el.getAttribute("tabindex"),
    };
  }

  function score(el, style, rect) {
    let current = 0;
    const reasons = [];
    const role = (el.getAttribute("role") || "").toLowerCase();
    const interactive = interactiveRoles.has(role) || ["a", "button", "input", "select", "textarea", "summary"].includes(el.tagName.toLowerCase());
    if (interactive) {
      current += 5;
      reasons.push("interactive");
    }
    const classBlob = `${el.className || ""} ${el.id || ""}`;
    if (keywordPattern.test(classBlob)) {
      current += 4;
      reasons.push("keyword");
    }
    if (style.backgroundColor !== "rgba(0, 0, 0, 0)" || style.boxShadow !== "none" || style.borderTopWidth !== "0px" || style.borderRadius !== "0px") {
      current += 3;
      reasons.push("styled-surface");
    }
    if (structuralTags.has(el.tagName.toLowerCase()) || style.display === "grid" || style.display === "flex") {
      current += 2;
      reasons.push("layout");
    }
    current += Math.min(rect.width * rect.height / 240000, 2.5);
    return { current, reasons, interactive };
  }

  function collectLayoutContainers() {
    return Array.from(document.querySelectorAll("body *"))
      .filter((el) => visible(el))
      .map((el) => {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const isContainer = style.display === "flex" || style.display === "grid" || ["header", "main", "nav", "aside", "section", "article", "form"].includes(el.tagName.toLowerCase());
        return {
          keep: isContainer && (rect.width * rect.height) > 4000,
          selector: selectorFor(el),
          domPath: domPath(el),
          tag: el.tagName.toLowerCase(),
          childCount: el.children.length,
          bounds: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
          style: collectStyle(style),
        };
      })
      .filter((item) => item.keep)
      .sort((a, b) => (b.bounds.width * b.bounds.height) - (a.bounds.width * a.bounds.height))
      .slice(0, 24)
      .map(({ keep, ...rest }) => rest);
  }

  function collectStylesheetSignals() {
    const customProperties = new Set();
    const mediaQueries = new Set();
    let accessibleSheets = 0;
    let blockedSheets = 0;

    function visitRules(rules) {
      for (const rule of rules) {
        if (rule.type === CSSRule.STYLE_RULE) {
          for (const name of rule.style) {
            if (name.startsWith("--")) customProperties.add(name);
          }
          continue;
        }
        if (rule.type === CSSRule.MEDIA_RULE) {
          mediaQueries.add(rule.media.mediaText);
          visitRules(rule.cssRules);
        }
      }
    }

    for (const sheet of Array.from(document.styleSheets)) {
      try {
        accessibleSheets += 1;
        visitRules(sheet.cssRules || []);
      } catch (error) {
        blockedSheets += 1;
      }
    }
    return {
      accessibleSheets,
      blockedSheets,
      customProperties: Array.from(customProperties).sort(),
      mediaQueries: Array.from(mediaQueries).sort(),
    };
  }

  const elements = Array.from(document.querySelectorAll("body *"))
    .filter((el) => visible(el))
    .map((el) => {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      const { current, reasons, interactive } = score(el, style, rect);
      return {
        el,
        current,
        reasons,
        interactive,
        rect,
        style,
      };
    })
    .filter((item) => item.current >= 3)
    .sort((a, b) => b.current - a.current)
    .slice(0, maxElements)
    .map((item, index) => {
      const extractId = `codex-${index + 1}`;
      item.el.setAttribute("data-codex-extract-id", extractId);
      return {
        extractId,
        selector: selectorFor(item.el),
        domPath: domPath(item.el),
        tag: item.el.tagName.toLowerCase(),
        role: item.el.getAttribute("role"),
        id: item.el.id || null,
        inputType: item.el.getAttribute("type"),
        classes: Array.from(item.el.classList).slice(0, 8),
        childCount: item.el.children.length,
        interactive: item.interactive,
        signals: item.reasons,
        bounds: {
          x: item.rect.x,
          y: item.rect.y,
          width: item.rect.width,
          height: item.rect.height,
        },
        computed: collectStyle(item.style),
        customProperties: collectCustomProperties(item.style),
        attributes: collectAttributes(item.el),
      };
    });

  const rootStyle = getComputedStyle(document.documentElement);
  const body = document.body || document.documentElement;
  const bodyStyle = getComputedStyle(body);
  return {
    document: {
      rootStyle: collectStyle(rootStyle),
      bodyStyle: collectStyle(bodyStyle),
      rootCssVariables: collectCustomProperties(rootStyle),
      bodyCssVariables: collectCustomProperties(bodyStyle),
      themeHints: {
        rootColorScheme: rootStyle.colorScheme || null,
        htmlClasses: Array.from(document.documentElement.classList).slice(0, 12),
        bodyClasses: Array.from(body.classList || []).slice(0, 12),
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
      },
      stylesheetSignals: collectStylesheetSignals(),
      layoutContainers: collectLayoutContainers(),
    },
    elements,
  };
}
"""
STATE_FUNCTION = """
(args) => {
  const el = document.querySelector(`[data-codex-extract-id="${args.extractId}"]`);
  if (!el) return null;
  const props = [...args.styleProps, ...args.layoutProps];
  const style = getComputedStyle(el);
  const output = {};
  for (const prop of props) {
    const value = style[prop];
    if (value === undefined || value === null || value === "") continue;
    output[prop] = value;
  }
  const customProperties = {};
  for (let index = 0; index < style.length; index += 1) {
    const name = style[index];
    if (!name || !name.startsWith("--")) continue;
    const value = style.getPropertyValue(name).trim();
    if (!value) continue;
    customProperties[name] = value;
  }
  return {
    style: output,
    customProperties,
    attributes: {
      disabled: !!el.disabled || el.getAttribute("aria-disabled") === "true",
      checked: !!el.checked || el.getAttribute("aria-checked") === "true",
      selected: !!el.selected || el.getAttribute("aria-selected") === "true",
      expanded: el.getAttribute("aria-expanded") === "true",
      open: !!el.open || el.getAttribute("open") !== null,
      ariaModal: el.getAttribute("aria-modal") === "true",
      tabindex: el.getAttribute("tabindex"),
    },
  };
}
"""


@dataclass
class ResolvedSource:
    source: str
    base_url: str
    default_page: str
    source_type: str
    cleanup: callable | None = None


class SilentSpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str | None = None, spa_fallback: str | None = None, **kwargs: Any) -> None:
        self.spa_fallback = spa_fallback
        super().__init__(*args, directory=directory, **kwargs)

    def send_head(self):  # type: ignore[override]
        path_only = self.path.split("?", 1)[0].split("#", 1)[0]
        resolved = self.translate_path(path_only)
        if os.path.exists(resolved):
            return super().send_head()
        if self.spa_fallback:
            fallback_path = os.path.join(self.directory or "", self.spa_fallback)
            if os.path.exists(fallback_path):
                self.path = f"/{self.spa_fallback}"
        return super().send_head()

    def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - quiet server
        return


def _get_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_local_server(root: Path, spa_fallback: str | None) -> tuple[str, callable]:
    port = _get_open_port()
    handler = partial(SilentSpaHandler, directory=str(root), spa_fallback=spa_fallback)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}/"

    def cleanup() -> None:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    return base_url, cleanup


def resolve_source(source: str) -> ResolvedSource:
    if is_url(source):
        parsed = urlparse(source)
        base_url = f"{parsed.scheme}://{parsed.netloc}/"
        default_page = parsed.path or "/"
        if parsed.query:
            default_page = f"{default_page}?{parsed.query}"
        return ResolvedSource(source=source, base_url=base_url, default_page=default_page, source_type="url")

    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Source path not found: {path}")

    if path.is_file():
        base_url, cleanup = _start_local_server(path.parent, "index.html" if (path.parent / "index.html").exists() else None)
        return ResolvedSource(
            source=str(path),
            base_url=base_url,
            default_page=f"/{path.name}",
            source_type="local_file",
            cleanup=cleanup,
        )

    spa_fallback = "index.html" if (path / "index.html").exists() else None
    base_url, cleanup = _start_local_server(path, spa_fallback)
    return ResolvedSource(
        source=str(path),
        base_url=base_url,
        default_page="/",
        source_type="local_dir",
        cleanup=cleanup,
    )


def _capture_trace(page_path: str, theme: str, viewport_name: str, element: dict[str, Any], state: str) -> dict[str, Any]:
    return {
        "page": page_path,
        "theme": theme,
        "viewport": viewport_name,
        "selector": element.get("selector"),
        "state": state,
        "component": None,
        "sourceVariable": None,
        "tag": element.get("tag"),
    }


def _make_state_payload(page, extract_id: str) -> dict[str, Any] | None:
    return page.evaluate(
        STATE_FUNCTION,
        {"extractId": extract_id, "styleProps": STYLE_PROPS, "layoutProps": LAYOUT_PROPS},
    )


def _state_changed(base: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if not candidate:
        return False
    return json.dumps(base, sort_keys=True) != json.dumps(candidate, sort_keys=True)


def _assign_existing_states(element: dict[str, Any]) -> None:
    base_state = copy.deepcopy(element["states"]["base"])
    attributes = base_state.get("attributes", {})
    if attributes.get("disabled"):
        element["states"]["disabled"] = copy.deepcopy(base_state)
    if attributes.get("checked"):
        element["states"]["checked"] = copy.deepcopy(base_state)
    if attributes.get("selected"):
        element["states"]["selected"] = copy.deepcopy(base_state)
    if attributes.get("expanded") or attributes.get("open"):
        element["states"]["open"] = copy.deepcopy(base_state)


def _prepare_elements(raw_elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for item in raw_elements:
        state = {
            "style": item.pop("computed"),
            "customProperties": item.pop("customProperties"),
            "attributes": item.pop("attributes"),
        }
        item["states"] = {"base": state}
        _assign_existing_states(item)
        prepared.append(item)
    return prepared


def _interactive_candidates(elements: list[dict[str, Any]], max_state_probes: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_signatures: set[tuple[Any, ...]] = set()
    for element in elements:
        if not element.get("interactive"):
            continue
        base = element["states"]["base"]["style"]
        signature = (
            element.get("tag"),
            element.get("role"),
            base.get("backgroundColor"),
            base.get("color"),
            base.get("borderTopColor"),
            base.get("borderRadius"),
            base.get("height"),
        )
        if signature in seen_signatures:
            continue
        selected.append(element)
        seen_signatures.add(signature)
        if len(selected) >= max_state_probes:
            break
    return selected


def _clear_transient_state(page) -> None:
    page.mouse.move(1, 1)
    page.evaluate("() => { if (document.activeElement && document.activeElement.blur) { document.activeElement.blur(); } }")


def _probe_states(page, elements: list[dict[str, Any]], states: list[str], max_state_probes: int) -> list[str]:
    warnings: list[str] = []
    if not states:
        return warnings

    for element in _interactive_candidates(elements, max_state_probes):
        selector = f'[data-codex-extract-id="{element["extractId"]}"]'
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed(timeout=1500)
        except Exception:
            continue

        base_payload = element["states"]["base"]
        for state_name in states:
            try:
                if state_name == "hover":
                    locator.hover(timeout=1500, force=True)
                elif state_name == "focus":
                    locator.focus(timeout=1500)
                elif state_name == "active":
                    box = locator.bounding_box(timeout=1500)
                    if not box:
                        continue
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    page.mouse.down()
                else:
                    continue

                payload = _make_state_payload(page, element["extractId"])
                if payload and _state_changed(base_payload, payload):
                    element["states"][state_name] = payload
            except Exception as exc:
                warnings.append(f"State '{state_name}' failed for {element.get('selector')}: {exc}")
            finally:
                if state_name == "active":
                    try:
                        page.mouse.up()
                    except Exception:
                        pass
                _clear_transient_state(page)
    return warnings


def _build_target_url(base_url: str, page_path: str) -> str:
    if is_url(page_path):
        return page_path
    return urljoin(base_url, page_path)


def _capture_page(page, resolved: ResolvedSource, page_path: str, theme: str, viewport: dict[str, Any], states: list[str], wait_ms: int, max_elements: int, max_state_probes: int) -> dict[str, Any]:
    capture: dict[str, Any] = {
        "page": page_path,
        "resolvedUrl": _build_target_url(resolved.base_url, page_path),
        "theme": theme,
        "viewport": viewport,
        "warnings": [],
    }
    try:
        page.goto(capture["resolvedUrl"], wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except PlaywrightTimeoutError:
            capture["warnings"].append("networkidle timeout; continued after settle delay")
        page.wait_for_timeout(wait_ms)
        page.evaluate("() => new Promise((resolve) => requestAnimationFrame(() => resolve(true)))")
    except Exception as exc:
        capture["loadError"] = str(exc)
        return capture

    snapshot = page.evaluate(
        SNAPSHOT_FUNCTION,
        {"styleProps": STYLE_PROPS, "layoutProps": LAYOUT_PROPS, "maxElements": max_elements},
    )
    capture["document"] = snapshot["document"]
    capture["elements"] = _prepare_elements(snapshot["elements"])
    capture["warnings"].extend(_probe_states(page, capture["elements"], states, max_state_probes))
    return capture


def inspect_site(
    source: str,
    pages: list[str] | None,
    themes: list[str] | None,
    viewports: list[str] | None,
    states: list[str] | None,
    output_dir: Path | str,
    wait_ms: int,
    max_elements: int,
    max_state_probes: int,
    keep_intermediate: bool,
) -> dict[str, Any]:
    if sync_playwright is None:
        raise SystemExit(
            "Playwright is required. Run `python3 -m pip install -r scripts/requirements.txt` "
            "and `python3 -m playwright install chromium` before retrying."
        ) from PLAYWRIGHT_IMPORT_ERROR

    resolved = resolve_source(source)
    normalized_pages = normalize_pages(pages)
    if normalized_pages == ["/"] and resolved.default_page != "/":
        normalized_pages = [resolved.default_page]

    normalized_themes = parse_themes(themes)
    normalized_states = parse_states(states)
    normalized_viewports = [item.to_dict() for item in parse_viewports(viewports)]
    output = ensure_output_dir(output_dir)

    inspection: dict[str, Any] = {
        "meta": {
            "generatedAt": utc_now_iso(),
            "source": source,
            "resolvedSource": resolved.base_url,
            "sourceType": resolved.source_type,
            "pages": normalized_pages,
            "themes": normalized_themes,
            "viewports": normalized_viewports,
            "interactiveStates": normalized_states or DEFAULT_STATES,
            "waitMs": wait_ms,
            "maxElements": max_elements,
            "maxStateProbes": max_state_probes,
        },
        "captures": [],
        "warnings": [],
    }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for theme in normalized_themes:
                    for viewport in normalized_viewports:
                        context = browser.new_context(
                            color_scheme=None if theme == "auto" else theme,
                            viewport={"width": viewport["width"], "height": viewport["height"]},
                        )
                        try:
                            for page_path in normalized_pages:
                                page = context.new_page()
                                try:
                                    capture = _capture_page(
                                        page,
                                        resolved,
                                        page_path,
                                        theme,
                                        viewport,
                                        normalized_states,
                                        wait_ms,
                                        max_elements,
                                        max_state_probes,
                                    )
                                    inspection["captures"].append(capture)
                                    inspection["warnings"].extend(capture.get("warnings", []))
                                finally:
                                    page.close()
                        finally:
                            context.close()
            finally:
                browser.close()
    finally:
        if resolved.cleanup:
            resolved.cleanup()

    if keep_intermediate:
        write_json(output / "inspection.raw.json", inspection)
    return inspection
