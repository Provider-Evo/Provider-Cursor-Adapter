


from __future__ import annotations

from typing import Dict, Optional


def build_headers(
    *,
    x_is_human: str = "",
    cookie: str = "",
    chat_path: str = "/api/chat",
    method: str = "POST",
) -> Dict[str, str]:
    """构建文档站 /api/chat 请求头（含 Bot 防护三元组）。

    Args:
        x_is_human: ``x-is-human`` Bot challenge JSON 字符串。
        cookie: 可选会话 Cookie。
        chat_path: ``x-path`` 值。
        method: ``x-method`` 值。

    Returns:
        请求头字典。
    """
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "sec-ch-ua-platform": '"Windows"',
        "x-path": chat_path,
        "sec-ch-ua": (
            '"Chromium";v="131","Not_A Brand";v="24","Google Chrome";v="131"'
        ),
        "x-method": method,
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "origin": "https://cursor.com",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://cursor.com/cn/docs",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "priority": "u=1,i",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "x-is-human": x_is_human or "",
    }
    cookie_value = (cookie or "").strip()
    if cookie_value:
        headers["Cookie"] = cookie_value
    return headers


def build_resume_headers(
    *,
    x_is_human: str = "",
    cookie: str = "",
    chat_id: str,
) -> Dict[str, str]:
    """构建 GET /api/chat/{chatId}/stream 请求头。"""
    return build_headers(
        x_is_human=x_is_human,
        cookie=cookie,
        chat_path="/api/chat/{}/stream".format(chat_id),
        method="GET",
    )

# =======================================================================
# 重导出 — 同包内协同模块的公共符号（保持外部 ``from .. import`` 路径稳定）
# =======================================================================

from .payload import (
    build_payload,
    new_chat_id,
    new_message_id,
)

__all__ = [
    "build_payload",
    "new_chat_id",
    "new_message_id",
]
