


from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional


def build_payload(
    cursor_messages: List[Dict[str, Any]],
    chat_id: str,
    *,
    model: Optional[str] = None,
    message_id: Optional[str] = None,
    context: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """构建 Cursor /api/chat 请求体（AI SDK DefaultChatTransport 形态）。

    Args:
        cursor_messages: Cursor UIMessage 列表。
        chat_id: 会话 ID（``crypto.randomUUID()``）。
        model: 模型 ID（网关路由用，服务端可能忽略）。
        message_id: 可选触发消息 ID。
        context: 可选文档上下文块。

    Returns:
        请求体字典。
    """
    body: Dict[str, Any] = {
        "id": chat_id,
        "messages": cursor_messages,
        "trigger": "submit-message",
    }
    if model:
        body["model"] = model
    if message_id:
        body["messageId"] = message_id
    if context:
        body["context"] = context
    return body


def new_chat_id() -> str:
    """生成新的 chatId。"""
    return str(uuid.uuid4())


def new_message_id() -> str:
    """生成新的 messageId。"""
    return str(uuid.uuid4())

# =======================================================================
# 重导出 — 同包内协同模块的公共符号（保持外部 ``from .. import`` 路径稳定）
# =======================================================================

from .headers import (
    build_headers,
    build_resume_headers,
)

__all__ = [
    "build_headers",
    "build_resume_headers",
]
