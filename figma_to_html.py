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

FIGMA_API = "https://api.figma.com"


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
    node_match = re.search(r"node-id=([0-9]+-[0-9]+)", url)
    if node_match:
        node_id = node_match.group(1)

    return file_key, node_id


# ---------------------------------------------------------------------------
# Figma REST API
# ---------------------------------------------------------------------------

def _figma_get(endpoint: str) -> dict:
    """對 Figma API 發送 GET 請求。"""
    proxies = {
        "http": "zzz",
        "https": "zzz",
    }
    response = requests.get(
        f"{FIGMA_API}{endpoint}", 
        headers={"X-Figma-Token": FIGMA_TOKEN},
        proxies=proxies,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    
    url = f"{FIGMA_API}{endpoint}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": FIGMA_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"Figma API {e.code}: {body}") from e


def fetch_nodes(file_key: str, node_ids: str) -> dict:
    """取得指定 node 的完整設計數據。"""
    print(f"[Figma] 取得節點資料: {node_ids}")
    return _figma_get(f"/v1/files/{file_key}/nodes?ids={node_ids}")


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
    print(f"[Figma] 匯出 {fmt.upper()} @{scale}x ...")
    data = _figma_get(
        f"/v1/images/{file_key}?ids={node_ids}&format={fmt}&scale={scale}"
    )
    images = data.get("images", {})
    # node_ids 格式 "123-456" 但 API 回傳 key 可能是 "123:456"
    for key, url in images.items():
        if url:
            return url
    return None


def download_image(url: str) -> bytes:
    """下載圖片並回傳 bytes。"""
    print(f"[Figma] 下載圖片...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


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


# ---------------------------------------------------------------------------
# LLM API（OpenAI Compatible, 多模態）
# ---------------------------------------------------------------------------

def _post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"LLM API {e.code}: {body}") from e


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

    # 4. 額外指示
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
  export LLM_BASE_URL="http://10.0.1.50:8000/v1"
  export LLM_API_KEY="your-api-key"
  export LLM_MODEL="gpt-4o"
  export LLM_API_STYLE="chat"

使用範例:
  python figma_to_html.py "https://www.figma.com/design/ABC123/App?node-id=456-789"
  python figma_to_html.py "..." -o card.html --stack tailwind
  python figma_to_html.py "..." --extra-prompt "使用繁體中文"
  python figma_to_html.py "..." --no-screenshot
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
    parser.add_argument("--save-json", action="store_true", help="同時儲存提取的 Figma JSON 到 output 同目錄")
    parser.add_argument("--max-tokens", type=int, default=16000, help="LLM 最大生成 token 數（預設 16000）")
    parser.add_argument("--llm-api-style", choices=["chat", "responses"], default=LLM_API_STYLE,
                        help="OpenAI Compatible API 類型：chat 或 responses（預設取自 LLM_API_STYLE 或 chat）")

    args = parser.parse_args()

    # --- 檢查環境變數 ---
    errors = []
    if not FIGMA_TOKEN:
        errors.append("FIGMA_TOKEN 未設定。請執行: export FIGMA_TOKEN='figd_xxxxx'")
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
    print()

    # --- Step 1: Figma REST API 提取設計數據 ---
    nodes_resp = fetch_nodes(file_key, node_id)
    design_json = simplify_figma_response(nodes_resp)

    # --- Step 2: 提取 Design Tokens ---
    tokens = None
    if not args.no_tokens:
        variables_resp = fetch_variables(file_key)
        if variables_resp:
            tokens = extract_tokens_summary(variables_resp)
            if tokens:
                print(f"[Figma] 取得 {sum(len(v) for v in tokens.values())} 個 tokens")

    # --- Step 3: 匯出截圖 ---
    screenshot_bytes = None
    if not args.no_screenshot:
        img_url = fetch_image_url(file_key, node_id, fmt="png", scale=2)
        if img_url:
            screenshot_bytes = download_image(img_url)
            print(f"[Figma] 截圖大小: {len(screenshot_bytes) / 1024:.0f} KB")

    # --- Step 3.5: 儲存中間檔案（可選）---
    if args.save_json:
        out_dir = Path(args.output).parent
        with open(out_dir / "figma_design.json", "w", encoding="utf-8") as f:
            json.dump(design_json, f, ensure_ascii=False, indent=2)
        if tokens:
            with open(out_dir / "figma_tokens.json", "w", encoding="utf-8") as f:
                json.dump(tokens, f, ensure_ascii=False, indent=2)
        if screenshot_bytes:
            with open(out_dir / "figma_screenshot.png", "wb") as f:
                f.write(screenshot_bytes)
        print(f"[Info] 中間檔案已儲存到 {out_dir}/")

    # --- Step 4: 呼叫 LLM 生成 HTML ---
    system_prompt = SYSTEM_PROMPT_TAILWIND if args.stack == "tailwind" else SYSTEM_PROMPT_INLINE
    user_content = build_user_content(design_json, tokens, screenshot_bytes, args.extra_prompt)

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
