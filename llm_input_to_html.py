# Execution examples:
# python3 llm_input_to_html.py
# python3 llm_input_to_html.py --input figma_llm_input.json --image ./component.png -o output.html
# LLM_BASE_URL="http://internal-llm/v1" LLM_API_KEY="xxx" LLM_MODEL="qwen3.5" python3 llm_input_to_html.py --image ./component.png
# LLM_API_STYLE="responses" python3 llm_input_to_html.py --input figma_llm_input.json --image ./component.png

import argparse
import base64
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5")
LLM_API_STYLE = os.environ.get("LLM_API_STYLE", "chat").strip().lower()
LLM_PROXY = os.environ.get("LLM_PROXY", "").strip()

_SSL_CONTEXT = ssl.create_default_context()


SYSTEM_PROMPT_INLINE = """You are a senior frontend engineer using Qwen 3.5 style instruction following.

Task:
- Convert the provided structured Figma JSON and optional screenshot into a complete single-file HTML document.

Priority:
1. Use the JSON file as the source of truth for structure, exact text, CSS, spacing, sizing, typography, colors, radius, borders, and shadows.
2. Use the screenshot only to resolve visual ambiguity, not to override explicit JSON values.

Rules:
- Output a complete HTML file only.
- Do not wrap the answer in markdown fences.
- Use inline CSS inside a single <style> block in <head>.
- Preserve node hierarchy from design_tree.
- Preserve text exactly as provided.
- Prefer css and css_text values already provided in the JSON.
- Use tokens when they are useful, but do not invent a design system that is not present.
- Recreate layout with flexbox/grid as needed.
- Keep the result visually close to the design and reasonably responsive.
- If some visual asset is unclear or missing, use a simple placeholder element and keep layout intact.
"""

SYSTEM_PROMPT_TAILWIND = """You are a senior frontend engineer using Qwen 3.5 style instruction following.

Task:
- Convert the provided structured Figma JSON and optional screenshot into a complete single-file HTML document.

Priority:
1. Use the JSON file as the source of truth for structure, exact text, CSS, spacing, sizing, typography, colors, radius, borders, and shadows.
2. Use the screenshot only to resolve visual ambiguity, not to override explicit JSON values.

Rules:
- Output a complete HTML file only.
- Do not wrap the answer in markdown fences.
- Use Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
- Preserve node hierarchy from design_tree.
- Preserve text exactly as provided.
- Prefer css and css_text values already provided in the JSON.
- Use tokens when they are useful, but do not invent a design system that is not present.
- Keep the result visually close to the design and reasonably responsive.
- If some visual asset is unclear or missing, use a simple placeholder element and keep layout intact.
"""


def build_proxy_handler(target_url: str) -> urllib.request.ProxyHandler | None:
    scheme = urllib.parse.urlparse(target_url).scheme.lower()
    proxy_url = (
        LLM_PROXY
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


def request_json(url: str, payload: dict, timeout: int = 120) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    opener = build_opener(url)
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"LLM API {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM API connection failed: {exc.reason}") from exc


def image_to_data_uri(path: Path) -> str:
    mime = "image/png"
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def build_user_content(llm_input: dict, image_path: Path | None, extra_prompt: str) -> list[dict]:
    content: list[dict] = []

    if image_path:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": image_to_data_uri(image_path),
                "detail": "high",
            },
        })
        content.append({
            "type": "text",
            "text": "The image above is the screenshot reference for the design.\n\n",
        })

    recommended_prompt = llm_input.get("recommended_prompt", "")
    if recommended_prompt:
        content.append({
            "type": "text",
            "text": f"Reference instruction from design file:\n{recommended_prompt}\n\n",
        })

    design_str = json.dumps(llm_input, ensure_ascii=False, indent=2)
    if len(design_str) > 120000:
        design_str = design_str[:120000] + "\n... (truncated)"

    content.append({
        "type": "text",
        "text": (
            "Structured Figma design file:\n\n"
            f"```json\n{design_str}\n```\n\n"
        ),
    })

    if extra_prompt:
        content.append({
            "type": "text",
            "text": f"Additional requirements:\n{extra_prompt}\n\n",
        })

    content.append({
        "type": "text",
        "text": "Generate the final HTML now.",
    })
    return content


def to_responses_content(user_content: list[dict]) -> list[dict]:
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


def extract_chat_text(result: dict) -> str:
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"No choices returned: {json.dumps(result, ensure_ascii=False)[:600]}")

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

    raise RuntimeError(f"Unable to parse chat response: {json.dumps(result, ensure_ascii=False)[:800]}")


def extract_responses_text(result: dict) -> str:
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

    raise RuntimeError(f"Unable to parse responses output: {json.dumps(result, ensure_ascii=False)[:800]}")


def call_chat_completions(system_prompt: str, user_content: list[dict], max_tokens: int, temperature: float) -> str:
    base_url = LLM_BASE_URL.rstrip("/")
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    result = request_json(f"{base_url}/chat/completions", payload)
    return extract_chat_text(result)


def call_responses(system_prompt: str, user_content: list[dict], max_tokens: int, temperature: float) -> str:
    base_url = LLM_BASE_URL.rstrip("/")
    payload = {
        "model": LLM_MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": to_responses_content(user_content)},
        ],
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }
    result = request_json(f"{base_url}/responses", payload)
    return extract_responses_text(result)


def call_llm(system_prompt: str, user_content: list[dict], max_tokens: int, temperature: float) -> str:
    if LLM_API_STYLE == "chat":
        return call_chat_completions(system_prompt, user_content, max_tokens, temperature)
    if LLM_API_STYLE == "responses":
        return call_responses(system_prompt, user_content, max_tokens, temperature)
    raise RuntimeError("LLM_API_STYLE must be 'chat' or 'responses'")


def extract_html(response_text: str) -> str:
    match = re.search(r"```html\s*\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"```\s*\n(.*?)```", response_text, re.DOTALL)
    if match:
        block = match.group(1).strip()
        if block.startswith("<!DOCTYPE") or block.startswith("<html"):
            return block

    stripped = response_text.strip()
    if stripped.startswith("<!DOCTYPE") or stripped.startswith("<html"):
        return stripped
    return stripped


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML from a prepared Figma LLM input JSON file.")
    parser.add_argument("--input", default="figma_llm_input.json", help="Prepared JSON path")
    parser.add_argument("--image", default="", help="Optional screenshot path")
    parser.add_argument("-o", "--output", default="output.html", help="Output HTML path")
    parser.add_argument("--stack", choices=["inline", "tailwind"], default="inline", help="HTML styling mode")
    parser.add_argument("--extra-prompt", default="", help="Additional generation requirements")
    parser.add_argument("--max-tokens", type=int, default=16000, help="Max output tokens")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    args = parser.parse_args()

    if not LLM_BASE_URL:
        print("[Error] LLM_BASE_URL is required", file=sys.stderr)
        sys.exit(1)
    if not LLM_API_KEY:
        print("[Error] LLM_API_KEY is required", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[Error] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    image_path = Path(args.image) if args.image else None
    if image_path and not image_path.exists():
        print(f"[Error] Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as file:
        llm_input = json.load(file)

    system_prompt = SYSTEM_PROMPT_INLINE if args.stack == "inline" else SYSTEM_PROMPT_TAILWIND
    user_content = build_user_content(llm_input, image_path, args.extra_prompt)

    print(f"[Info] Input:     {input_path}")
    if image_path:
        print(f"[Info] Image:     {image_path}")
    print(f"[Info] Output:    {args.output}")
    print(f"[Info] Model:     {LLM_MODEL}")
    print(f"[Info] API Style: {LLM_API_STYLE}")
    if LLM_PROXY:
        print(f"[Info] Proxy:     {LLM_PROXY}")

    html = extract_html(call_llm(system_prompt, user_content, args.max_tokens, args.temperature))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)

    print(f"[Done] Wrote {output_path}")


if __name__ == "__main__":
    main()
