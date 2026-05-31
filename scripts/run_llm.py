"""
（可选）直接调用 LLM API 跑结构化。
- 优先 Anthropic Claude（ANTHROPIC_API_KEY）
- 其次 OpenAI（OPENAI_API_KEY）
- 都没有则提示用户走"投喂包"模式
"""
import os
import sys


def call_anthropic(prompt: str, model: str = "claude-3-5-sonnet-latest") -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": model,
                "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"]
    except Exception as e:
        print(f"[anthropic] 调用失败：{e}", file=sys.stderr)
        return None


def call_openai(prompt: str, model: str = "gpt-4o-mini") -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[openai] 调用失败：{e}", file=sys.stderr)
        return None


def run_llm(prompt: str) -> tuple[str | None, str]:
    """
    尝试用任意可用的 LLM 跑 prompt。
    返回 (结果文本, 提供方名称)。失败返回 (None, "none")。
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        result = call_anthropic(prompt)
        if result:
            return result, "claude"
    if os.getenv("OPENAI_API_KEY"):
        result = call_openai(prompt)
        if result:
            return result, "openai"
    return None, "none"


def is_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
