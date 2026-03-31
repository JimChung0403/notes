# Execution examples:
# python3 figma_prepare_llm_input.py "https://www.figma.com/design/FILE_KEY/Name?node-id=456-789"
# python3 figma_prepare_llm_input.py "https://www.figma.com/design/FILE_KEY/Name?node-id=456-789" -o figma_llm_input.json
# FIGMA_PROXY="http://proxy.company:8080" python3 figma_prepare_llm_input.py "https://www.figma.com/design/FILE_KEY/Name?node-id=456-789"

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


FIGMA_TOKEN = os.environ.get("FIGMA_TOKEN", "")
FIGMA_PROXY = os.environ.get("FIGMA_PROXY", "").strip()
FIGMA_API = os.environ.get("FIGMA_API_BASE", "https://api.figma.com").rstrip("/")

_SSL_CONTEXT = ssl.create_default_context()


def parse_figma_url(url: str) -> tuple[str, str | None]:
    pattern = r"figma\.com/(?:design|file)/([a-zA-Z0-9]+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Unable to parse file key from URL: {url}")

    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    raw_node_id = query.get("node-id", [None])[0]
    node_id = urllib.parse.unquote(raw_node_id).replace(":", "-") if raw_node_id else None
    return match.group(1), node_id


def build_proxy_handler(target_url: str) -> urllib.request.ProxyHandler | None:
    scheme = urllib.parse.urlparse(target_url).scheme.lower()
    proxy_url = (
        FIGMA_PROXY
        or os.environ.get(f"{scheme.upper()}_PROXY", "")
        or os.environ.get(f"{scheme.lower()}_proxy", "")
        or os.environ.get("ALL_PROXY", "")
        or os.environ.get("all_proxy", "")
    ).strip()
    if not proxy_url:
        return None
    return urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})


def build_opener(target_url: str) -> urllib.request.OpenerDirector:
    handlers: list[urllib.request.BaseHandler] = []
    proxy_handler = build_proxy_handler(target_url)
    if proxy_handler:
        handlers.append(proxy_handler)
    if urllib.parse.urlparse(target_url).scheme.lower() == "https":
        handlers.append(urllib.request.HTTPSHandler(context=_SSL_CONTEXT))
    return urllib.request.build_opener(*handlers)


def request_json(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, headers=headers or {})
    opener = build_opener(url)
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"Figma API {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Figma API connection failed: {exc.reason}") from exc


def normalize_node_ids(node_ids: str) -> str:
    parts = []
    for raw_part in node_ids.split(","):
        part = raw_part.strip()
        if part:
            parts.append(part.replace("-", ":"))
    if not parts:
        raise ValueError("node-id is empty")
    return ",".join(parts)


def figma_get(endpoint: str, params: dict[str, str] | None = None) -> dict:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{FIGMA_API}{endpoint}{query}"
    return request_json(url, headers={"X-Figma-Token": FIGMA_TOKEN})


def fetch_nodes(file_key: str, node_ids: str) -> dict:
    normalized_ids = normalize_node_ids(node_ids)
    print(f"[Figma] Fetch nodes: {normalized_ids}")
    return figma_get(f"/v1/files/{file_key}/nodes", {"ids": normalized_ids})


def fetch_variables(file_key: str) -> dict:
    print("[Figma] Fetch variables")
    try:
        return figma_get(f"/v1/files/{file_key}/variables/local")
    except RuntimeError as exc:
        print(f"[Figma] Variables unavailable: {exc}")
        return {}


def fetch_styles(file_key: str) -> dict:
    print("[Figma] Fetch styles")
    try:
        return figma_get(f"/v1/files/{file_key}/styles")
    except RuntimeError as exc:
        print(f"[Figma] Styles unavailable: {exc}")
        return {}


def simplify_node(node: dict, depth: int = 0, max_depth: int = 10) -> dict | None:
    if depth > max_depth:
        return None
    if node.get("visible") is False:
        return None

    keep_keys = {
        "id", "name", "type",
        "layoutMode", "primaryAxisAlignItems", "counterAxisAlignItems",
        "paddingLeft", "paddingRight", "paddingTop", "paddingBottom",
        "itemSpacing", "layoutGrow", "layoutAlign",
        "absoluteBoundingBox", "constraints",
        "fills", "strokes", "strokeWeight", "strokeAlign",
        "cornerRadius", "rectangleCornerRadii",
        "effects", "opacity", "blendMode", "clipsContent",
        "characters", "style", "characterStyleOverrides", "styleOverrideTable",
        "componentId", "componentProperties",
    }

    result = {}
    for key, value in node.items():
        if key == "children":
            children = []
            for child in value:
                simplified = simplify_node(child, depth + 1, max_depth)
                if simplified:
                    children.append(simplified)
            if children:
                result["children"] = children
        elif key in keep_keys and value is not None:
            result[key] = value
    return result if result else None


def simplify_figma_response(nodes_response: dict) -> dict:
    simplified = {}
    for node_id, node_data in nodes_response.get("nodes", {}).items():
        document = node_data.get("document")
        if document:
            simplified[node_id] = simplify_node(document)
    return simplified


def extract_tokens_summary(variables_response: dict) -> dict:
    summary = {"colors": {}, "numbers": {}, "strings": {}}
    meta = variables_response.get("meta", {})
    variables = meta.get("variables", {})

    for variable in variables.values():
        name = variable.get("name")
        resolved_type = variable.get("resolvedType")
        values = variable.get("valuesByMode", {})
        if not name or not values:
            continue
        first_value = next(iter(values.values()))

        if resolved_type == "COLOR" and isinstance(first_value, dict):
            summary["colors"][name] = rgba_to_css(first_value)
        elif resolved_type == "FLOAT" and isinstance(first_value, (int, float)):
            summary["numbers"][name] = first_value
        elif resolved_type == "STRING" and isinstance(first_value, str):
            summary["strings"][name] = first_value

    return {key: value for key, value in summary.items() if value}


def extract_styles_summary(styles_response: dict) -> dict:
    styles = styles_response.get("meta", {}).get("styles")
    if not isinstance(styles, list):
        styles = styles_response.get("styles", [])

    summary: dict[str, list[dict]] = {}
    for style in styles:
        style_type = style.get("style_type", "UNKNOWN")
        summary.setdefault(style_type, []).append({
            "key": style.get("key"),
            "name": style.get("name"),
            "description": style.get("description", ""),
        })
    return {key: value for key, value in summary.items() if value}


def fmt_px(value) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    if float(value).is_integer():
        return f"{int(value)}px"
    return f"{value}px"


def rgba_to_css(color: dict, opacity: float | None = None) -> str | None:
    if not isinstance(color, dict):
        return None
    red = round(color.get("r", 0) * 255)
    green = round(color.get("g", 0) * 255)
    blue = round(color.get("b", 0) * 255)
    alpha = opacity if opacity is not None else color.get("a", 1)
    if alpha is None:
        alpha = 1
    if alpha < 1:
        return f"rgba({red}, {green}, {blue}, {alpha:.2f})"
    return f"#{red:02x}{green:02x}{blue:02x}"


def gradient_to_css(fill: dict) -> str | None:
    stops = fill.get("gradientStops", [])
    if not stops:
        return None

    parts = []
    for stop in stops:
        color = rgba_to_css(stop.get("color", {}))
        position = stop.get("position")
        if not color:
            continue
        if isinstance(position, (int, float)):
            parts.append(f"{color} {round(position * 100)}%")
        else:
            parts.append(color)

    if not parts:
        return None

    if fill.get("type") == "GRADIENT_RADIAL":
        return f"radial-gradient(circle, {', '.join(parts)})"
    return f"linear-gradient(180deg, {', '.join(parts)})"


def fills_to_css(fills: list[dict] | None, is_text: bool) -> dict[str, str]:
    if not isinstance(fills, list):
        return {}
    for fill in fills:
        if fill.get("visible") is False:
            continue
        fill_type = fill.get("type")
        if fill_type == "SOLID":
            color = rgba_to_css(fill.get("color", {}), fill.get("opacity"))
            if color:
                return {"color" if is_text else "background-color": color}
        if fill_type and fill_type.startswith("GRADIENT"):
            gradient = gradient_to_css(fill)
            if gradient:
                return {"background": gradient}
    return {}


def strokes_to_css(strokes: list[dict] | None, stroke_weight, stroke_align) -> dict[str, str]:
    if not isinstance(strokes, list):
        return {}
    for stroke in strokes:
        if stroke.get("visible") is False or stroke.get("type") != "SOLID":
            continue
        color = rgba_to_css(stroke.get("color", {}), stroke.get("opacity"))
        if not color:
            continue
        result = {"border": f"{fmt_px(stroke_weight) or '1px'} solid {color}"}
        if stroke_align:
            result["border-align"] = str(stroke_align).lower()
        return result
    return {}


def effects_to_box_shadow(effects: list[dict] | None) -> str | None:
    if not isinstance(effects, list):
        return None
    shadows = []
    for effect in effects:
        if effect.get("visible") is False:
            continue
        effect_type = effect.get("type")
        if effect_type not in {"DROP_SHADOW", "INNER_SHADOW"}:
            continue
        offset = effect.get("offset", {})
        color = rgba_to_css(effect.get("color", {}))
        if not color:
            continue
        inset = " inset" if effect_type == "INNER_SHADOW" else ""
        shadows.append(
            f"{fmt_px(offset.get('x', 0)) or '0px'} "
            f"{fmt_px(offset.get('y', 0)) or '0px'} "
            f"{fmt_px(effect.get('radius', 0)) or '0px'} "
            f"{fmt_px(effect.get('spread', 0)) or '0px'} {color}{inset}"
        )
    return ", ".join(shadows) if shadows else None


def map_primary_axis(value: str | None) -> str | None:
    return {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "SPACE_BETWEEN": "space-between",
    }.get(value or "")


def map_counter_axis(value: str | None) -> str | None:
    return {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "BASELINE": "baseline",
    }.get(value or "")


def node_css_properties(node: dict) -> dict[str, str]:
    css: dict[str, str] = {}
    layout_mode = node.get("layoutMode")
    if layout_mode == "HORIZONTAL":
        css["display"] = "flex"
        css["flex-direction"] = "row"
    elif layout_mode == "VERTICAL":
        css["display"] = "flex"
        css["flex-direction"] = "column"

    justify_content = map_primary_axis(node.get("primaryAxisAlignItems"))
    if justify_content:
        css["justify-content"] = justify_content
    align_items = map_counter_axis(node.get("counterAxisAlignItems"))
    if align_items:
        css["align-items"] = align_items

    gap = fmt_px(node.get("itemSpacing"))
    if gap:
        css["gap"] = gap

    paddings = [
        fmt_px(node.get("paddingTop")) or "0px",
        fmt_px(node.get("paddingRight")) or "0px",
        fmt_px(node.get("paddingBottom")) or "0px",
        fmt_px(node.get("paddingLeft")) or "0px",
    ]
    if any(value != "0px" for value in paddings):
        css["padding"] = " ".join(paddings)

    bounds = node.get("absoluteBoundingBox", {})
    width = fmt_px(bounds.get("width"))
    height = fmt_px(bounds.get("height"))
    if width:
        css["width"] = width
    if height:
        css["height"] = height

    if node.get("layoutGrow") == 1:
        css["flex"] = "1 1 0%"
    if node.get("layoutAlign") == "STRETCH":
        css["align-self"] = "stretch"
    if isinstance(node.get("opacity"), (int, float)) and node.get("opacity") != 1:
        css["opacity"] = str(node["opacity"])
    if node.get("clipsContent"):
        css["overflow"] = "hidden"

    css.update(fills_to_css(node.get("fills"), is_text=node.get("type") == "TEXT"))
    css.update(strokes_to_css(node.get("strokes"), node.get("strokeWeight"), node.get("strokeAlign")))

    box_shadow = effects_to_box_shadow(node.get("effects"))
    if box_shadow:
        css["box-shadow"] = box_shadow

    corner_radius = node.get("cornerRadius")
    if isinstance(corner_radius, (int, float)):
        css["border-radius"] = fmt_px(corner_radius) or "0px"
    elif isinstance(node.get("rectangleCornerRadii"), list):
        radii = [(fmt_px(value) or "0px") for value in node["rectangleCornerRadii"]]
        if any(value != "0px" for value in radii):
            css["border-radius"] = " ".join(radii)

    if node.get("type") == "TEXT":
        style = node.get("style", {})
        if style.get("fontFamily"):
            css["font-family"] = style["fontFamily"]
        if style.get("fontSize"):
            css["font-size"] = fmt_px(style["fontSize"]) or ""
        if style.get("fontWeight"):
            css["font-weight"] = str(style["fontWeight"])
        if style.get("lineHeightPx"):
            css["line-height"] = fmt_px(style["lineHeightPx"]) or ""
        letter_spacing = fmt_px(style.get("letterSpacing"))
        if letter_spacing and letter_spacing != "0px":
            css["letter-spacing"] = letter_spacing
        if style.get("textAlignHorizontal"):
            css["text-align"] = style["textAlignHorizontal"].lower()
        if style.get("textDecoration") and style.get("textDecoration") != "NONE":
            css["text-decoration"] = style["textDecoration"].lower().replace("_", "-")

    return {key: value for key, value in css.items() if value}


def css_dict_to_text(css: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value};" for key, value in css.items())


def build_llm_node(node: dict) -> dict:
    css = node_css_properties(node)
    result = {
        "id": node.get("id"),
        "name": node.get("name"),
        "type": node.get("type"),
        "text": node.get("characters"),
        "css": css,
        "css_text": css_dict_to_text(css),
    }

    if node.get("children"):
        result["children"] = [build_llm_node(child) for child in node["children"]]

    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def build_llm_input(figma_url: str, file_key: str, node_id: str, design_json: dict, tokens: dict, styles: dict) -> dict:
    root = next(iter(design_json.values()), {})
    return {
        "version": "1.0",
        "recommended_prompt": (
            "Read this JSON file together with the screenshot. Generate a complete single-file HTML page. "
            "Use the JSON as the source of truth and the screenshot only for visual confirmation. "
            "Preserve hierarchy, exact text, spacing, typography, colors, radius, border, and shadows. "
            "Prefer the provided css and tokens over guessing. Output only HTML."
        ),
        "source": {
            "figma_url": figma_url,
            "file_key": file_key,
            "node_id": node_id,
        },
        "tokens": tokens or {},
        "styles": styles or {},
        "design_tree": build_llm_node(root) if root else {},
        "raw_design_summary": design_json,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare one JSON file for an LLM from a Figma URL.")
    parser.add_argument("figma_url", help="Figma URL containing node-id")
    parser.add_argument("-o", "--output", default="figma_llm_input.json", help="Output JSON path")
    parser.add_argument("--no-tokens", action="store_true", help="Skip variables")
    args = parser.parse_args()

    if not FIGMA_TOKEN:
        print("[Error] FIGMA_TOKEN is required", file=sys.stderr)
        sys.exit(1)

    try:
        file_key, node_id = parse_figma_url(args.figma_url)
    except ValueError as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        sys.exit(1)

    if not node_id:
        print("[Error] node-id is missing in Figma URL", file=sys.stderr)
        sys.exit(1)

    print(f"[Info] File Key:   {file_key}")
    print(f"[Info] Node ID:    {node_id}")
    print(f"[Info] Figma API:  {FIGMA_API}")
    if FIGMA_PROXY:
        print(f"[Info] Proxy:      {FIGMA_PROXY}")

    nodes_response = fetch_nodes(file_key, node_id)
    design_json = simplify_figma_response(nodes_response)

    tokens = {}
    if not args.no_tokens:
        tokens = extract_tokens_summary(fetch_variables(file_key))

    styles = extract_styles_summary(fetch_styles(file_key))

    llm_input = build_llm_input(args.figma_url, file_key, node_id, design_json, tokens, styles)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(llm_input, file, ensure_ascii=False, indent=2)

    print(f"[Done] Wrote {output_path}")


if __name__ == "__main__":
    main()
