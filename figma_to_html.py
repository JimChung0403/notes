"""
Figma Design → HTML 自動轉換工具

透過 Figma REST API 提取設計數據，再呼叫公司內部 OpenAI Compatible
多模態模型 API，自動產生單檔 HTML。

用法:
    # 基本用法：指定 Figma URL
    python figma_to_html.py "https://www.figma.com/design/ABC123/My-App?node-id=456-789"

    # 指定輸出檔案
    python figma_to_html.py "https://www.figma.com/design/ABC123/My-App?node-id=456-789" -o output.html

    # 指定框架風格
    python figma_to_html.py "..." --stack tailwind
    python figma_to_html.py "..." --stack inline

    # 自訂 prompt 補充
    python figma_to_html.py "..." --extra-prompt "使用繁體中文，按鈕風格圓角"

環境變數:
    FIGMA_TOKEN          Figma Personal Access Token（必填）
    LLM_BASE_URL         OpenAI Compatible API base URL（必填）
    LLM_API_KEY          LLM API Key（必填）
    LLM_MODEL            模型名稱（預設 gpt-4o）
    LLM_API_STYLE        chat 或 responses（預設 chat）
"""

import argparse
import base64
import json
import os
import re
import sys
import ssl
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FIGMA_TOKEN: str = os.environ.get("FIGMA_TOKEN", "")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "")  # e.g. http://10.0.1.50:8000/v1
LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o")
LLM_API_STYLE: str = os.environ.get("LLM_API_STYLE", "chat").strip().lower()
FIGMA_PROXY: str = os.environ.get("FIGMA_PROXY", "").strip()
LLM_PROXY: str = os.environ.get("LLM_PROXY", "").strip()
FIGMA_API: str = os.environ.get("FIGMA_API_BASE", "https://api.figma.com").rstrip("/")

_SSL_CONTEXT = ssl.create_default_context()


# ---------------------------------------------------------------------------
# Figma URL Parser
# ---------------------------------------------------------------------------

def parse_figma_url(url: str) -> tuple[str, str | None]:
    """從 Figma URL 提取 file_key 和 node_id。

    支援格式：
        https://www.figma.com/design/FILE_KEY/Name?node-id=123-456
        https://www.figma.com/file/FILE_KEY/Name?node-id=123-456
    """
    pattern = r"figma\.com/(?:design|file)/([a-zA-Z0-9]+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"無法從 URL 解析 file_key: {url}")
    file_key = m.group(1)

    node_id = None
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    raw_node_id = query.get("node-id", [None])[0]
    if raw_node_id:
        node_id = urllib.parse.unquote(raw_node_id).replace(":", "-")

    return file_key, node_id


# ---------------------------------------------------------------------------
# Figma REST API
# ---------------------------------------------------------------------------

def _build_proxy_handler(service: str, target_url: str) -> urllib.request.ProxyHandler | None:
    """依服務與 URL 選擇 proxy 設定。"""
    parsed = urllib.parse.urlparse(target_url)
    scheme = parsed.scheme.lower()
    service_proxy = FIGMA_PROXY if service == "figma" else LLM_PROXY if service == "llm" else ""
    proxy_url = (
        service_proxy
        or os.environ.get(f"{scheme.upper()}_PROXY", "")
        or os.environ.get(f"{scheme.lower()}_proxy", "")
        or os.environ.get("ALL_PROXY", "")
        or os.environ.get("all_proxy", "")
    ).strip()
    if not proxy_url:
        return None
    return urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})


def _build_opener(service: str, target_url: str) -> urllib.request.OpenerDirector:
    handlers: list[urllib.request.BaseHandler] = []
    proxy_handler = _build_proxy_handler(service, target_url)
    if proxy_handler:
        handlers.append(proxy_handler)
    if urllib.parse.urlparse(target_url).scheme.lower() == "https":
        handlers.append(urllib.request.HTTPSHandler(context=_SSL_CONTEXT))
    return urllib.request.build_opener(*handlers)


def _request_json(
    service: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: dict | None = None,
    method: str = "GET",
    timeout: int = 30,
) -> dict:
    """發送 JSON 請求並解析回應。"""
    request_headers = headers.copy() if headers else {}
    request_data = None
    if data is not None:
        request_headers.setdefault("Content-Type", "application/json")
        request_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=request_data,
        headers=request_headers,
        method=method,
    )
    opener = _build_opener(service, url)
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"{service.upper()} API {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"{service.upper()} API 連線失敗: {e.reason}") from e


def _request_bytes(
    service: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> bytes:
    """發送請求並回傳原始 bytes。"""
    req = urllib.request.Request(url, headers=headers or {})
    opener = _build_opener(service, url)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"{service.upper()} API {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"{service.upper()} API 連線失敗: {e.reason}") from e


def _normalize_node_ids(node_ids: str) -> str:
    """將 Figma URL 中的 node-id 正規化成 API 可用格式。"""
    parts = []
    for raw_part in node_ids.split(","):
        part = raw_part.strip()
        if not part:
            continue
        parts.append(part.replace("-", ":"))
    if not parts:
        raise ValueError("node-id 為空，無法呼叫 Figma API")
    return ",".join(parts)


def _figma_get(endpoint: str, params: dict[str, str] | None = None) -> dict:
    """對 Figma API 發送 GET 請求。"""
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{FIGMA_API}{endpoint}{query}"
    return _request_json(
        "figma",
        url,
        headers={"X-Figma-Token": FIGMA_TOKEN},
    )


def fetch_nodes(file_key: str, node_ids: str) -> dict:
    """取得指定 node 的完整設計數據。"""
    normalized_ids = _normalize_node_ids(node_ids)
    print(f"[Figma] 取得節點資料: {normalized_ids}")
    return _figma_get(f"/v1/files/{file_key}/nodes", {"ids": normalized_ids})


def fetch_variables(file_key: str) -> dict:
    """取得 Design Tokens（Variables）。"""
    print("[Figma] 取得 Design Tokens...")
    try:
        return _figma_get(f"/v1/files/{file_key}/variables/local")
    except RuntimeError as e:
        print(f"[Figma] 警告：無法取得 variables（可能權限不足）: {e}")
        return {}


def fetch_styles(file_key: str) -> dict:
    """取得已發佈的 Styles。"""
    print("[Figma] 取得 Styles...")
    try:
        return _figma_get(f"/v1/files/{file_key}/styles")
    except RuntimeError:
        return {}


def fetch_image_url(file_key: str, node_ids: str, fmt: str = "png", scale: int = 2) -> str | None:
    """匯出節點為圖片，回傳圖片下載 URL。"""
    normalized_ids = _normalize_node_ids(node_ids)
    print(f"[Figma] 匯出 {fmt.upper()} @{scale}x ...")
    data = _figma_get(
        f"/v1/images/{file_key}",
        {"ids": normalized_ids, "format": fmt, "scale": str(scale)},
    )
    images = data.get("images", {})
    preferred_url = images.get(normalized_ids)
    if preferred_url:
        return preferred_url
    for _, url in images.items():
        if url:
            return url
    return None


def download_image(url: str) -> bytes:
    """下載圖片並回傳 bytes。"""
    print(f"[Figma] 下載圖片...")
    return _request_bytes("figma", url)


# ---------------------------------------------------------------------------
# Figma JSON → 精簡摘要（降低 token 消耗）
# ---------------------------------------------------------------------------

def simplify_node(node: dict, depth: int = 0, max_depth: int = 10) -> dict | None:
    """遞迴精簡 Figma node JSON，只保留與前端佈局/樣式相關的屬性。"""
    if depth > max_depth:
        return None

    keep_keys = {
        "id", "name", "type",
        # 佈局
        "layoutMode", "primaryAxisAlignItems", "counterAxisAlignItems",
        "paddingLeft", "paddingRight", "paddingTop", "paddingBottom",
        "itemSpacing", "layoutGrow", "layoutAlign",
        "absoluteBoundingBox", "constraints",
        # 尺寸
        "size",
        # 視覺
        "fills", "strokes", "strokeWeight", "strokeAlign",
        "cornerRadius", "rectangleCornerRadii",
        "effects", "opacity", "blendMode", "clipsContent",
        # 文字
        "characters", "style", "characterStyleOverrides", "styleOverrideTable",
        # 元件
        "componentId", "componentProperties",
    }

    result = {}
    for k, v in node.items():
        if k == "children":
            children = []
            for child in v:
                s = simplify_node(child, depth + 1, max_depth)
                if s:
                    children.append(s)
            if children:
                result["children"] = children
        elif k in keep_keys and v is not None:
            result[k] = v

    # 跳過不可見節點
    if node.get("visible") is False:
        return None

    return result if result else None


def simplify_figma_response(nodes_response: dict) -> dict:
    """精簡完整的 Figma nodes API 回應。"""
    simplified = {}
    nodes = nodes_response.get("nodes", {})
    for node_id, node_data in nodes.items():
        doc = node_data.get("document")
        if doc:
            simplified[node_id] = simplify_node(doc)
    return simplified


def extract_tokens_summary(variables_response: dict) -> dict:
    """從 variables API 回應中提取 token 摘要。"""
    summary = {"colors": {}, "numbers": {}, "strings": {}}
    meta = variables_response.get("meta", {})
    variables = meta.get("variables", {})
    variable_collections = meta.get("variableCollections", {})

    # 建立 collection name 映射
    collection_names = {}
    for cid, cdata in variable_collections.items():
        collection_names[cid] = cdata.get("name", cid)
        # 也建立 mode 名稱映射
        for mode in cdata.get("modes", []):
            collection_names[mode["modeId"]] = mode.get("name", "default")

    for vid, var in variables.items():
        name = var.get("name", vid)
        resolved_type = var.get("resolvedType", "")
        values = var.get("valuesByMode", {})

        # 取第一個 mode 的值作為預設
        for mode_id, value in values.items():
            if resolved_type == "COLOR" and isinstance(value, dict):
                r = round(value.get("r", 0) * 255)
                g = round(value.get("g", 0) * 255)
                b = round(value.get("b", 0) * 255)
                a = value.get("a", 1)
                if a < 1:
                    summary["colors"][name] = f"rgba({r},{g},{b},{a:.2f})"
                else:
                    summary["colors"][name] = f"#{r:02x}{g:02x}{b:02x}"
            elif resolved_type == "FLOAT" and isinstance(value, (int, float)):
                summary["numbers"][name] = value
            elif resolved_type == "STRING" and isinstance(value, str):
                summary["strings"][name] = value
            break  # 只取第一個 mode

    # 移除空的類別
    return {k: v for k, v in summary.items() if v}


def extract_styles_summary(styles_response: dict) -> dict:
    """從 styles API 回應中提取精簡摘要。"""
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

    return {k: v for k, v in summary.items() if v}


# ---------------------------------------------------------------------------
# 給 LLM 的單一輸入檔
# ---------------------------------------------------------------------------

def _fmt_px(value) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    if float(value).is_integer():
        return f"{int(value)}px"
    return f"{value}px"


def _rgba_to_css(color: dict, opacity: float | None = None) -> str | None:
    if not isinstance(color, dict):
        return None
    r = round(color.get("r", 0) * 255)
    g = round(color.get("g", 0) * 255)
    b = round(color.get("b", 0) * 255)
    a = opacity if opacity is not None else color.get("a", 1)
    if a is None:
        a = 1
    if a < 1:
        return f"rgba({r}, {g}, {b}, {a:.2f})"
    return f"#{r:02x}{g:02x}{b:02x}"


def _gradient_to_css(fill: dict) -> str | None:
    gradient_type = fill.get("type", "")
    stops = fill.get("gradientStops", [])
    if not stops:
        return None

    stop_parts = []
    for stop in stops:
        color = _rgba_to_css(stop.get("color", {}))
        position = stop.get("position")
        if color is None:
            continue
        if isinstance(position, (int, float)):
            stop_parts.append(f"{color} {round(position * 100)}%")
        else:
            stop_parts.append(color)

    if not stop_parts:
        return None

    if gradient_type == "GRADIENT_RADIAL":
        return f"radial-gradient(circle, {', '.join(stop_parts)})"
    return f"linear-gradient(180deg, {', '.join(stop_parts)})"


def _fills_to_css(fills: list[dict] | None, *, is_text: bool = False) -> dict[str, str]:
    if not isinstance(fills, list):
        return {}

    for fill in fills:
        if fill.get("visible") is False:
            continue
        fill_type = fill.get("type")
        opacity = fill.get("opacity")
        if fill_type == "SOLID":
            color = _rgba_to_css(fill.get("color", {}), opacity)
            if not color:
                continue
            return {"color" if is_text else "background-color": color}
        if fill_type and fill_type.startswith("GRADIENT"):
            gradient = _gradient_to_css(fill)
            if gradient:
                return {"background": gradient}
    return {}


def _strokes_to_css(strokes: list[dict] | None, stroke_weight, stroke_align) -> dict[str, str]:
    if not isinstance(strokes, list):
        return {}
    for stroke in strokes:
        if stroke.get("visible") is False:
            continue
        if stroke.get("type") != "SOLID":
            continue
        color = _rgba_to_css(stroke.get("color", {}), stroke.get("opacity"))
        if not color:
            continue
        weight = _fmt_px(stroke_weight) or "1px"
        border = f"{weight} solid {color}"
        css = {"border": border}
        if stroke_align:
            css["border-align"] = str(stroke_align).lower()
        return css
    return {}


def _effects_to_box_shadow(effects: list[dict] | None) -> str | None:
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
        radius = effect.get("radius", 0)
        spread = effect.get("spread", 0)
        color = _rgba_to_css(effect.get("color", {}))
        if not color:
            continue
        inset = " inset" if effect_type == "INNER_SHADOW" else ""
        shadows.append(
            f"{_fmt_px(offset.get('x', 0)) or '0px'} "
            f"{_fmt_px(offset.get('y', 0)) or '0px'} "
            f"{_fmt_px(radius) or '0px'} "
            f"{_fmt_px(spread) or '0px'} {color}{inset}"
        )
    return ", ".join(shadows) if shadows else None


def _map_primary_axis(value: str | None) -> str | None:
    mapping = {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "SPACE_BETWEEN": "space-between",
    }
    return mapping.get(value or "")


def _map_counter_axis(value: str | None) -> str | None:
    mapping = {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "BASELINE": "baseline",
    }
    return mapping.get(value or "")


def _node_css_properties(node: dict) -> dict[str, str]:
    css: dict[str, str] = {}

    layout_mode = node.get("layoutMode")
    if layout_mode == "HORIZONTAL":
        css["display"] = "flex"
        css["flex-direction"] = "row"
    elif layout_mode == "VERTICAL":
        css["display"] = "flex"
        css["flex-direction"] = "column"

    justify_content = _map_primary_axis(node.get("primaryAxisAlignItems"))
    if justify_content:
        css["justify-content"] = justify_content

    align_items = _map_counter_axis(node.get("counterAxisAlignItems"))
    if align_items:
        css["align-items"] = align_items

    item_spacing = _fmt_px(node.get("itemSpacing"))
    if item_spacing:
        css["gap"] = item_spacing

    paddings = [
        _fmt_px(node.get("paddingTop")) or "0px",
        _fmt_px(node.get("paddingRight")) or "0px",
        _fmt_px(node.get("paddingBottom")) or "0px",
        _fmt_px(node.get("paddingLeft")) or "0px",
    ]
    if any(value != "0px" for value in paddings):
        css["padding"] = " ".join(paddings)

    bounds = node.get("absoluteBoundingBox", {})
    width = _fmt_px(bounds.get("width"))
    height = _fmt_px(bounds.get("height"))
    if width:
        css["width"] = width
    if height:
        css["height"] = height

    if node.get("layoutGrow") == 1:
        css["flex"] = "1 1 0%"

    layout_align = node.get("layoutAlign")
    if layout_align == "STRETCH":
        css["align-self"] = "stretch"

    if isinstance(node.get("opacity"), (int, float)) and node.get("opacity") != 1:
        css["opacity"] = str(node["opacity"])

    if node.get("clipsContent"):
        css["overflow"] = "hidden"

    css.update(_fills_to_css(node.get("fills"), is_text=node.get("type") == "TEXT"))
    css.update(_strokes_to_css(node.get("strokes"), node.get("strokeWeight"), node.get("strokeAlign")))

    box_shadow = _effects_to_box_shadow(node.get("effects"))
    if box_shadow:
        css["box-shadow"] = box_shadow

    corner_radius = node.get("cornerRadius")
    if isinstance(corner_radius, (int, float)):
        css["border-radius"] = _fmt_px(corner_radius) or "0px"
    elif isinstance(node.get("rectangleCornerRadii"), list):
        radii = [(_fmt_px(v) or "0px") for v in node["rectangleCornerRadii"]]
        if any(v != "0px" for v in radii):
            css["border-radius"] = " ".join(radii)

    if node.get("type") == "TEXT":
        style = node.get("style", {})
        font_family = style.get("fontFamily")
        if font_family:
            css["font-family"] = font_family
        font_size = _fmt_px(style.get("fontSize"))
        if font_size:
            css["font-size"] = font_size
        if style.get("fontWeight"):
            css["font-weight"] = str(style["fontWeight"])
        line_height = _fmt_px(style.get("lineHeightPx"))
        if line_height:
            css["line-height"] = line_height
        letter_spacing = _fmt_px(style.get("letterSpacing"))
        if letter_spacing and letter_spacing != "0px":
            css["letter-spacing"] = letter_spacing
        text_align = style.get("textAlignHorizontal")
        if text_align:
            css["text-align"] = text_align.lower()
        text_decoration = style.get("textDecoration")
        if text_decoration and text_decoration != "NONE":
            css["text-decoration"] = text_decoration.lower().replace("_", "-")

    return css


def _css_dict_to_text(css: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value};" for key, value in css.items())


def _build_llm_node(node: dict) -> dict:
    css = _node_css_properties(node)
    result = {
        "id": node.get("id"),
        "name": node.get("name"),
        "type": node.get("type"),
        "text": node.get("characters"),
        "css": css,
        "css_text": _css_dict_to_text(css),
    }

    children = node.get("children", [])
    if children:
        result["children"] = [_build_llm_node(child) for child in children]

    return {k: v for k, v in result.items() if v not in (None, "", [], {})}


def build_llm_input_file(
    *,
    figma_url: str,
    file_key: str,
    node_id: str,
    design_json: dict,
    tokens: dict | None,
    styles: dict | None,
    extra_prompt: str,
) -> dict:
    """整理成單一檔案給外部 LLM 使用。"""
    root_node = next(iter(design_json.values()), {})
    llm_tree = _build_llm_node(root_node) if root_node else {}

    return {
        "version": "1.0",
        "purpose": "Provide a single structured file for an LLM to convert a Figma design into HTML.",
        "recommended_prompt": (
            "Please read this structured Figma design file together with the screenshot. "
            "Generate a complete single-file HTML page that reproduces the design precisely. "
            "Preserve hierarchy, exact text, spacing, typography, border radius, colors, and shadows. "
            "Prefer the provided CSS properties and tokens over guessing. "
            "Output only HTML."
            + (f" Additional requirements: {extra_prompt}" if extra_prompt else "")
        ),
        "source": {
            "figma_url": figma_url,
            "file_key": file_key,
            "node_id": node_id,
        },
        "tokens": tokens or {},
        "styles": styles or {},
        "design_tree": llm_tree,
        "raw_design_summary": design_json,
    }


# ---------------------------------------------------------------------------
# LLM API（OpenAI Compatible, 多模態）
# ---------------------------------------------------------------------------

def _post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }
    return _request_json(
        "llm",
        url,
        headers=headers,
        data=payload,
        method="POST",
        timeout=timeout,
    )


def _to_responses_content(user_content: list[dict]) -> list[dict]:
    content: list[dict] = []
    for part in user_content:
        if part.get("type") == "text":
            content.append({"type": "input_text", "text": part["text"]})
        elif part.get("type") == "image_url":
            image = part.get("image_url", {})
            content.append({
                "type": "input_image",
                "image_url": image.get("url"),
                "detail": image.get("detail", "high"),
            })
    return content


def _extract_chat_text(result: dict) -> str:
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"LLM 未回傳任何 choices: {json.dumps(result, ensure_ascii=False)[:500]}")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for item in content:
            if item.get("type") == "text":
                text_obj = item.get("text")
                if isinstance(text_obj, str):
                    texts.append(text_obj)
                elif isinstance(text_obj, dict) and isinstance(text_obj.get("value"), str):
                    texts.append(text_obj["value"])
        if texts:
            return "\n".join(texts)

    raise RuntimeError(f"無法解析 chat completions 回應: {json.dumps(result, ensure_ascii=False)[:800]}")


def _extract_responses_text(result: dict) -> str:
    output_text = result.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    texts = []
    for item in result.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                texts.append(content["text"])
    if texts:
        return "\n".join(texts)

    raise RuntimeError(f"無法解析 responses API 回應: {json.dumps(result, ensure_ascii=False)[:800]}")


def call_llm(
    system_prompt: str,
    user_content: list[dict],
    max_tokens: int = 16000,
    temperature: float = 0.2,
) -> str:
    """呼叫公司內部 OpenAI Compatible 多模態 API。"""
    base_url = LLM_BASE_URL.rstrip("/")

    if LLM_API_STYLE == "responses":
        url = f"{base_url}/responses"
        payload = {
            "model": LLM_MODEL,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": _to_responses_content(user_content)},
            ],
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        print(f"[LLM] 呼叫 {LLM_MODEL}（responses API）生成 HTML...")
        result = _post_json(url, payload)
        return _extract_responses_text(result)

    if LLM_API_STYLE != "chat":
        raise RuntimeError("LLM_API_STYLE 只支援 'chat' 或 'responses'")

    url = f"{base_url}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    print(f"[LLM] 呼叫 {LLM_MODEL}（chat completions API）生成 HTML...")
    result = _post_json(url, payload)
    return _extract_chat_text(result)


def image_to_data_uri(image_bytes: bytes, mime: str = "image/png") -> str:
    """將圖片 bytes 轉為 base64 data URI。"""
    b64 = base64.b64encode(image_bytes).decode()
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# Prompt 組裝
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TAILWIND = """\
You are an expert frontend developer. Your task is to convert Figma design data into a \
complete, single-file HTML page.

Rules:
- Output a COMPLETE HTML file with <!DOCTYPE html>, <html>, <head>, <body>.
- Use Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
- Use semantic HTML5 tags (header, nav, main, section, article, footer, etc.)
- Match the Figma layout precisely: flex directions, gaps, paddings, colors, font sizes, border radius, shadows.
- For colors, convert Figma RGBA to hex/rgba and use Tailwind arbitrary values like bg-[#2563EB] when needed.
- For images/icons that you cannot reproduce, use a placeholder <div> with a descriptive comment.
- Make the layout responsive where reasonable.
- Include ALL text content exactly as shown in the Figma data.
- Output ONLY the HTML code. No explanations, no markdown fences.
"""

SYSTEM_PROMPT_INLINE = """\
You are an expert frontend developer. Your task is to convert Figma design data into a \
complete, single-file HTML page.

Rules:
- Output a COMPLETE HTML file with <!DOCTYPE html>, <html>, <head>, <body>.
- Use inline CSS styles and a <style> block in <head>. Do NOT use any external CSS framework.
- Use CSS Flexbox/Grid to reproduce the Figma Auto Layout.
- Use semantic HTML5 tags.
- Match the Figma layout precisely: flex directions, gaps, paddings, colors, font sizes, border radius, shadows.
- For images/icons that you cannot reproduce, use a placeholder <div> with a descriptive comment.
- Make the layout responsive where reasonable.
- Include ALL text content exactly as shown in the Figma data.
- Output ONLY the HTML code. No explanations, no markdown fences.
"""


def build_user_content(
    design_json: dict,
    tokens: dict | None,
    styles: dict | None,
    screenshot_bytes: bytes | None,
    extra_prompt: str = "",
) -> list[dict]:
    """組裝多模態 user message content。"""
    parts: list[dict] = []

    # 1. 截圖（如果有）
    if screenshot_bytes:
        parts.append({
            "type": "image_url",
            "image_url": {
                "url": image_to_data_uri(screenshot_bytes),
                "detail": "high",
            },
        })
        parts.append({
            "type": "text",
            "text": "Above is a screenshot of the Figma design. Use it as visual reference.\n\n",
        })

    # 2. 設計結構 JSON
    design_str = json.dumps(design_json, ensure_ascii=False, indent=2)
    # 如果太長則截斷（避免超過 context window）
    if len(design_str) > 80000:
        design_str = design_str[:80000] + "\n... (truncated)"
    parts.append({
        "type": "text",
        "text": (
            "## Figma Design Structure (JSON)\n\n"
            "This is the structured design data extracted from Figma REST API. "
            "Use this to determine exact layout (flexbox direction, gaps, paddings), "
            "colors, typography, border radius, shadows, and text content.\n\n"
            f"```json\n{design_str}\n```\n\n"
        ),
    })

    # 3. Design Tokens（如果有）
    if tokens:
        tokens_str = json.dumps(tokens, ensure_ascii=False, indent=2)
        parts.append({
            "type": "text",
            "text": (
                "## Design Tokens\n\n"
                "These are the design variables (colors, spacing, etc.) from Figma. "
                "Use these as CSS custom properties where applicable.\n\n"
                f"```json\n{tokens_str}\n```\n\n"
            ),
        })

    # 4. Styles（如果有）
    if styles:
        styles_str = json.dumps(styles, ensure_ascii=False, indent=2)
        parts.append({
            "type": "text",
            "text": (
                "## Published Styles\n\n"
                "These are style definitions fetched from Figma as JSON. "
                "Use them to preserve naming and design-system intent when relevant.\n\n"
                f"```json\n{styles_str}\n```\n\n"
            ),
        })

    # 5. 額外指示
    if extra_prompt:
        parts.append({
            "type": "text",
            "text": f"## Additional Requirements\n\n{extra_prompt}\n\n",
        })

    parts.append({
        "type": "text",
        "text": "Now generate the complete HTML file.",
    })

    return parts


# ---------------------------------------------------------------------------
# 從 LLM 回應中提取 HTML
# ---------------------------------------------------------------------------

def extract_html(response: str) -> str:
    """從 LLM 回應中提取 HTML，處理可能被 markdown fence 包裹的情況。"""
    # 嘗試提取 ```html ... ``` 區塊
    m = re.search(r"```html\s*\n(.*?)```", response, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 嘗試提取 ``` ... ``` 區塊
    m = re.search(r"```\s*\n(.*?)```", response, re.DOTALL)
    if m:
        content = m.group(1).strip()
        if content.startswith("<!DOCTYPE") or content.startswith("<html"):
            return content

    # 如果直接是 HTML
    if response.strip().startswith("<!DOCTYPE") or response.strip().startswith("<html"):
        return response.strip()

    # fallback: 回傳原始內容
    return response.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global LLM_API_STYLE

    parser = argparse.ArgumentParser(
        description="Figma Design → HTML（封閉網路版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
環境變數設定範例:
  export FIGMA_TOKEN="figd_xxxxx"
  export FIGMA_PROXY="http://proxy.company:8080"  # 可選
  export LLM_BASE_URL="http://10.0.1.50:8000/v1"
  export LLM_API_KEY="your-api-key"
  export LLM_MODEL="gpt-4o"
  export LLM_API_STYLE="chat"

使用範例:
  python figma_to_html.py "https://www.figma.com/design/ABC123/App?node-id=456-789"
  python figma_to_html.py "..." -o card.html --stack tailwind
  python figma_to_html.py "..." --extra-prompt "使用繁體中文"
  python figma_to_html.py "..." --no-screenshot
  python figma_to_html.py "..." --json-only
  python figma_to_html.py "..." --prepare-only --llm-input-output design_for_llm.json
  python figma_to_html.py "..." --llm-api-style responses
  python figma_to_html.py "..." --save-json  # 同時儲存中間 JSON 檔案
        """,
    )
    parser.add_argument("figma_url", help="Figma 設計稿 URL（含 node-id）")
    parser.add_argument("-o", "--output", default="output.html", help="輸出 HTML 檔案路徑（預設 output.html）")
    parser.add_argument("--stack", choices=["tailwind", "inline"], default="tailwind",
                        help="CSS 方案：tailwind（CDN）或 inline（純 CSS）（預設 tailwind）")
    parser.add_argument("--extra-prompt", default="", help="額外的生成指示（例如：使用繁體中文）")
    parser.add_argument("--no-screenshot", action="store_true", help="跳過截圖匯出（節省 API 呼叫）")
    parser.add_argument("--no-tokens", action="store_true", help="跳過 Design Tokens 提取")
    parser.add_argument("--json-only", action="store_true",
                        help="僅使用 Figma JSON（nodes / variables / styles），不下載截圖")
    parser.add_argument("--prepare-only", action="store_true",
                        help="只提取與整理 Figma 資料，不呼叫內部 LLM 生成 HTML")
    parser.add_argument("--llm-input-output", default="",
                        help="輸出單一給 LLM 使用的 JSON 檔案路徑")
    parser.add_argument("--save-json", action="store_true", help="同時儲存提取的 Figma JSON 到 output 同目錄")
    parser.add_argument("--max-tokens", type=int, default=16000, help="LLM 最大生成 token 數（預設 16000）")
    parser.add_argument("--llm-api-style", choices=["chat", "responses"], default=LLM_API_STYLE,
                        help="OpenAI Compatible API 類型：chat 或 responses（預設取自 LLM_API_STYLE 或 chat）")

    args = parser.parse_args()

    # --- 檢查環境變數 ---
    errors = []
    if not FIGMA_TOKEN:
        errors.append("FIGMA_TOKEN 未設定。請執行: export FIGMA_TOKEN='figd_xxxxx'")
    if not args.prepare_only:
        if not LLM_BASE_URL:
            errors.append("LLM_BASE_URL 未設定。請執行: export LLM_BASE_URL='http://your-llm-server/v1'")
        if not LLM_API_KEY:
            errors.append("LLM_API_KEY 未設定。請執行: export LLM_API_KEY='your-key'")
    if errors:
        for e in errors:
            print(f"[錯誤] {e}", file=sys.stderr)
        sys.exit(1)

    LLM_API_STYLE = args.llm_api_style

    # --- 解析 Figma URL ---
    try:
        file_key, node_id = parse_figma_url(args.figma_url)
    except ValueError as e:
        print(f"[錯誤] {e}", file=sys.stderr)
        sys.exit(1)

    if not node_id:
        print("[錯誤] URL 中缺少 node-id 參數。請在 Figma 中選取 Frame 後複製 URL。", file=sys.stderr)
        print("  正確格式: https://www.figma.com/design/FILE_KEY/Name?node-id=123-456", file=sys.stderr)
        sys.exit(1)

    print(f"[Info] File Key: {file_key}")
    print(f"[Info] Node ID:  {node_id}")
    print(f"[Info] Stack:    {args.stack}")
    print(f"[Info] Model:    {LLM_MODEL}")
    print(f"[Info] LLM API:  {LLM_API_STYLE}")
    print(f"[Info] Mode:     {'prepare-only' if args.prepare_only else 'generate-html'}")
    print(f"[Info] Figma API: {FIGMA_API}")
    if FIGMA_PROXY:
        print(f"[Info] Figma Proxy: {FIGMA_PROXY}")
    if LLM_PROXY:
        print(f"[Info] LLM Proxy:   {LLM_PROXY}")
    print()

    # --- Step 1: Figma REST API 提取設計數據 ---
    nodes_resp = fetch_nodes(file_key, node_id)
    design_json = simplify_figma_response(nodes_resp)

    # --- Step 2: 提取 Design Tokens ---
    tokens = None
    variables_resp: dict = {}
    if not args.no_tokens:
        variables_resp = fetch_variables(file_key)
        if variables_resp:
            tokens = extract_tokens_summary(variables_resp)
            if tokens:
                print(f"[Figma] 取得 {sum(len(v) for v in tokens.values())} 個 tokens")

    # --- Step 2.5: 提取 Styles ---
    styles_resp = fetch_styles(file_key)
    styles = extract_styles_summary(styles_resp)
    if styles:
        print(f"[Figma] 取得 {sum(len(v) for v in styles.values())} 個 styles")

    llm_input = build_llm_input_file(
        figma_url=args.figma_url,
        file_key=file_key,
        node_id=node_id,
        design_json=design_json,
        tokens=tokens,
        styles=styles,
        extra_prompt=args.extra_prompt,
    )

    # --- Step 3: 匯出截圖 ---
    screenshot_bytes = None
    if not args.no_screenshot and not args.json_only:
        img_url = fetch_image_url(file_key, node_id, fmt="png", scale=2)
        if img_url:
            screenshot_bytes = download_image(img_url)
            print(f"[Figma] 截圖大小: {len(screenshot_bytes) / 1024:.0f} KB")

    # --- Step 3.5: 儲存中間檔案（可選）---
    if args.save_json:
        out_dir = Path(args.output).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "figma_design.json", "w", encoding="utf-8") as f:
            json.dump(design_json, f, ensure_ascii=False, indent=2)
        with open(out_dir / "figma_nodes_raw.json", "w", encoding="utf-8") as f:
            json.dump(nodes_resp, f, ensure_ascii=False, indent=2)
        if tokens:
            with open(out_dir / "figma_tokens.json", "w", encoding="utf-8") as f:
                json.dump(tokens, f, ensure_ascii=False, indent=2)
        if not args.no_tokens and variables_resp:
            with open(out_dir / "figma_variables_raw.json", "w", encoding="utf-8") as f:
                json.dump(variables_resp, f, ensure_ascii=False, indent=2)
        if styles:
            with open(out_dir / "figma_styles.json", "w", encoding="utf-8") as f:
                json.dump(styles, f, ensure_ascii=False, indent=2)
        if styles_resp:
            with open(out_dir / "figma_styles_raw.json", "w", encoding="utf-8") as f:
                json.dump(styles_resp, f, ensure_ascii=False, indent=2)
        if screenshot_bytes:
            with open(out_dir / "figma_screenshot.png", "wb") as f:
                f.write(screenshot_bytes)
        print(f"[Info] 中間檔案已儲存到 {out_dir}/")

    llm_input_path = args.llm_input_output.strip()
    if not llm_input_path:
        output_base = Path(args.output)
        llm_input_path = str(output_base.with_suffix(".llm_input.json"))

    llm_input_file = Path(llm_input_path)
    llm_input_file.parent.mkdir(parents=True, exist_ok=True)
    with open(llm_input_file, "w", encoding="utf-8") as f:
        json.dump(llm_input, f, ensure_ascii=False, indent=2)
    print(f"[完成] LLM 輸入檔已儲存到: {llm_input_file}")

    if args.prepare_only:
        return

    # --- Step 4: 呼叫 LLM 生成 HTML ---
    system_prompt = SYSTEM_PROMPT_TAILWIND if args.stack == "tailwind" else SYSTEM_PROMPT_INLINE
    user_content = build_user_content(design_json, tokens, styles, screenshot_bytes, args.extra_prompt)

    response = call_llm(
        system_prompt=system_prompt,
        user_content=user_content,
        max_tokens=args.max_tokens,
    )

    # --- Step 5: 提取並儲存 HTML ---
    html = extract_html(response)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print()
    print(f"[完成] HTML 已儲存到: {args.output}")
    print(f"[完成] 用瀏覽器開啟檢視: open {args.output}")


if __name__ == "__main__":
    main()
