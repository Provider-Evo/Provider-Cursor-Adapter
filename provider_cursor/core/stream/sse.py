


from __future__ import annotations

import json
from typing import Any, Dict, Optional, Union

ParsedChunk = Union[str, Dict[str, Any]]


def _raise_stream_error(obj: Dict[str, Any]) -> None:
    """从 ``error`` chunk 中提取消息并抛出 ``ValueError``。"""
    err = obj.get("error")
    if isinstance(err, dict):
        message = err.get("message") or err.get("text") or str(err)
    else:
        message = str(err)
    raise ValueError("Cursor stream error: {}".format(message))


def _parse_finish_usage(obj: Dict[str, Any]) -> Optional[ParsedChunk]:
    """从 ``finish`` chunk 的 ``messageMetadata.usage`` 中提取 usage 信息。"""
    meta = obj.get("messageMetadata")
    if not isinstance(meta, dict) or not meta.get("usage"):
        return None
    usage = meta["usage"]
    if not isinstance(usage, dict):
        return None
    return {
        "usage": {
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
            "total_tokens": usage.get("totalTokens"),
        }
    }


def _parse_delta_chunk(obj: Dict[str, Any], event_type: str) -> Optional[ParsedChunk]:
    """处理 ``text-delta`` / ``reasoning-delta`` 两类增量 chunk。"""
    delta = obj.get("delta", "")
    if not isinstance(delta, str) or not delta:
        return None
    if event_type == "text-delta":
        return delta
    return {"thinking": delta}


def parse_sse_line(data_str: str) -> Optional[ParsedChunk]:
    """解析 SSE ``data:`` 行中的 UI message stream chunk。

    支持 AI SDK 6.x chunk 类型（``0o78f7f7aglud.js`` schema ``hL``）：
    ``text-delta``、``reasoning-delta``、``finish``、``error``。

    Args:
        data_str: ``data:`` 前缀之后的字符串。

    Returns:
        str 文本片段、dict（thinking/usage）或 None（跳过）。
    """
    if not data_str or data_str == "[DONE]":
        return None

    try:
        obj = json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(obj, dict):
        return None

    if "error" in obj:
        _raise_stream_error(obj)

    event_type = str(obj.get("type") or "")

    if event_type in ("text-delta", "reasoning-delta"):
        return _parse_delta_chunk(obj, event_type)

    if event_type == "finish":
        return _parse_finish_usage(obj)

    return None
