


from __future__ import annotations

# ── 服务端点 ────────────────────────────────────────────────────────────────────
BASE_URL: str = "https://cursor.com"
CHAT_PATH: str = "/api/chat"
DEPLOYMENT_ID: str = "dpl_2J8tisxS8XpA18cHKAudi6cggpWc"
MODELS_JS_URL: str = (
    "https://cursor.com/docs-static/_next/static/chunks/"
    "0z5v50kazv6pt.js?dpl={}".format(DEPLOYMENT_ID)
)
STREAM_RESUME_PATH: str = "/api/chat/{chat_id}/stream"

# ── 模型列表 ────────────────────────────────────────────────────────────────────
MODELS: list[str] = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-sonnet-4-thinking",
    "anthropic/claude-sonnet-4-6",
    "anthropic/claude-sonnet-4-6-thinking",
    "anthropic/claude-sonnet-4-6-long",
    "anthropic/claude-sonnet-4-5",
    "anthropic/claude-sonnet-4-5-thinking",
    "anthropic/claude-sonnet-4-5-long",
    "anthropic/claude-opus-4-6",
    "anthropic/claude-opus-4-6-thinking",
    "anthropic/claude-opus-4-5",
    "anthropic/claude-opus-4-5-thinking",
    "anthropic/claude-opus-4-6-fast",
    "anthropic/claude-opus-4-6-fast-thinking",
    "anthropic/claude-haiku-4-5",
    "anthropic/claude-sonnet-4-1m",
    "anthropic/claude-sonnet-4-1m-thinking",
    "google/gemini-3.1-pro",
    "google/gemini-3.1-long",
    "google/gemini-3-pro",
    "google/gemini-3-long",
    "google/gemini-3-flash",
    "google/gemini-3-pro-image-preview",
    "google/gemini-2.5-flash",
    "openai/gpt-5.1",
    "openai/gpt-5-codex",
    "openai/gpt-5-mini",
    "openai/gpt-5-fast",
    "openai/gpt-5.2",
    "openai/gpt-5.2-codex",
    "openai/gpt-5.4",
    "openai/gpt-5.4-fast",
    "openai/gpt-5.4-long",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.4-nano",
    "openai/gpt-5.3-codex",
    "openai/gpt-5.1-codex",
    "openai/gpt-5.1-codex-mini",
    "openai/gpt-5.1-codex-max",
    "xai/grok-4-20",
    "xai/grok-4-20-long",
    "moonshot/kimi-k2.5",
    "cursor/composer-1",
    "cursor/composer-1.5",
    "cursor/composer-2",
    "cursor/composer-2-fast",
]

# ── 能力字典 ────────────────────────────────────────────────────────────────────
CAPS: dict[str, bool] = {
    "chat": True,
    "completions": True,
    "thinking": True,
    "continuation": True,
}

# ── 模型获取 ────────────────────────────────────────────────────────────────────
FETCH_MODELS_ENABLED: bool = True
MODEL_FETCH_INTERVAL: int = 86400

# =======================================================================
# 重导出 — 同包内协同模块的公共符号（保持外部 ``from .. import`` 路径稳定）
# =======================================================================

from .headers import (
    build_headers,
    build_resume_headers,
)

from .payload import (
    build_payload,
    new_chat_id,
    new_message_id,
)

__all__ = [
    "build_headers",
    "build_resume_headers",
    "build_payload",
    "new_chat_id",
    "new_message_id",
]
