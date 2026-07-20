"""Cursor 平台 HTTP 客户端协调器。"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiohttp

from src.core.dispatch.cand import Candidate, make_id
from src.foundation.logger import get_logger

from ..consts import BASE_URL, CHAT_PATH, MODELS_JS_URL, STREAM_RESUME_PATH
from ..headers import build_headers, build_resume_headers
from ..payload import build_payload, new_chat_id, new_message_id
from ..response.convo import build_cursor_messages
from ..response.saniti import sanitize_response
from .client_helpers import (
    auth_from_candidate,
    classify_attempt_item,
    collect_stream_chunks,
    finalize_attempt,
    iter_response_chunks,
    parse_models_from_js,
)

logger = get_logger(__name__)

MAX_RETRIES: int = 2
MAX_REFUSAL_RETRIES: int = 1


class CursorClient:
    """Cursor 文档站 /api/chat 客户端。

    拒答重试的重述前缀处理、models.js 解析、SSE 流迭代等纯函数拆分至
    ``client_helpers.py``。
    """

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._models: List[str] = []
        self._candidates: List[Candidate] = []
        self._api_keys: List[str] = []
        self._x_is_human: str = ""
        self._session_cookie: str = ""

    async def init_immediate(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        from pathlib import Path
        from src.foundation.config.reader import get_config_reader
        from ...accounts import API_KEYS, SESSION_COOKIE, X_IS_HUMAN

        plugin_dir = Path(__file__).resolve().parents[3]
        reader = get_config_reader()
        config, _schema, _raw = reader.get_plugin_config(plugin_dir)
        self._x_is_human = str(config.get("x_is_human") or X_IS_HUMAN or "")
        self._session_cookie = str(config.get("session_cookie") or SESSION_COOKIE or "")

        self._api_keys = [k for k in API_KEYS if isinstance(k, str) and k.strip()]
        self._rebuild_candidates()
        logger.info("cursor 客户端初始化完成，凭证数量: {}".format(len(self._api_keys)))

    async def background_setup(self) -> None:
        try:
            models = await self.fetch_remote_models()
            if models:
                logger.info("cursor 后台首次模型拉取成功，共 %d 个", len(models))
        except Exception as exc:
            logger.warning("cursor 后台首次模型拉取失败: %s", exc)

    async def fetch_remote_models(self) -> List[str]:
        if self._session is None:
            return []
        async with self._session.get(
            MODELS_JS_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
            },
            ssl=False,
            timeout=aiohttp.ClientTimeout(connect=10, total=30),
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    "cursor 获取模型 JS 失败: HTTP {}".format(resp.status)
                )
            text = await resp.text()
        return parse_models_from_js(text)

    def update_models(self, models: List[str]) -> None:
        self._models = list(models)
        for cand in self._candidates:
            cand.models = list(models)

    def _build_candidate(self, key: str) -> Candidate:
        from ..consts import CAPS

        return Candidate(
            id=make_id("cursor", "cursor_browser"),
            platform="cursor",
            resource_id="cursor_browser",
            models=list(self._models),
            context_length=None,
            meta={
                "api_key": key,
                "x_is_human": self._x_is_human,
                "session_cookie": self._session_cookie,
                "chat_id": new_chat_id(),
            },
            **CAPS,
        )

    def _rebuild_candidates(self) -> None:
        self._candidates = [self._build_candidate(key) for key in self._api_keys]

    def _chat_id_for(self, candidate: Candidate) -> str:
        chat_id = str(candidate.meta.get("chat_id") or "").strip()
        if not chat_id:
            chat_id = new_chat_id()
            candidate.meta["chat_id"] = chat_id
        return chat_id

    async def candidates(self) -> List[Candidate]:
        return list(self._candidates)

    async def ensure_candidates(self, count: int) -> int:
        return len(self._candidates)

    async def _complete_attempt(
        self,
        candidate: Candidate,
        cursor_messages: List[Dict[str, Any]],
        model: str,
        stream: bool,
        attempt: int,
    ) -> AsyncGenerator[Union[str, Dict[str, Any], Tuple[bool, Any]], None]:
        """执行一次补全尝试，边界情况通过 (False, ...) 标记信号回传给调用方。

        Yields:
            正常文本/思考/usage 片段直接产出；当需要重试时最终产出
            ``(False, new_messages)`` 表示应以新消息重试；当正常结束时
            产出 ``(True, None)``。
        """
        raw_text = ""
        raw_thinking = ""
        usage_data: Optional[Dict[str, Any]] = None

        chunk_iterator = self._post_chat_stream(candidate, cursor_messages, model)
        async for chunk in collect_stream_chunks(chunk_iterator, stream):
            if isinstance(chunk, dict) and "__collected__" in chunk:
                raw_text, raw_thinking, usage_data = chunk["__collected__"]
            else:
                yield chunk

        full_text = sanitize_response(raw_text)
        thinking_text = raw_thinking.strip()

        async for item in finalize_attempt(
            cursor_messages, stream, attempt, full_text, thinking_text, usage_data,
            MAX_REFUSAL_RETRIES,
        ):
            yield item

    async def _run_attempt(
        self,
        candidate: Candidate,
        cursor_messages: List[Dict[str, Any]],
        model: str,
        stream: bool,
        attempt: int,
    ) -> AsyncGenerator[Union[str, Dict[str, Any], Tuple[bool, Any]], None]:
        """执行单次尝试，直接转发内容片段，并在结尾产出重试/结束信号。"""
        retry_messages: Optional[List[Dict[str, Any]]] = None
        finished = False

        async for item in self._complete_attempt(
            candidate, cursor_messages, model, stream, attempt
        ):
            is_signal, item_finished, payload = classify_attempt_item(item)
            if not is_signal:
                yield payload
                continue
            finished = item_finished
            if not finished:
                retry_messages = payload
            break

        yield (finished, retry_messages)

    async def complete(
        self,
        candidate: Candidate,
        messages: List[Dict[str, Any]],
        model: str,
        stream: bool,
        *,
        thinking: bool = False,
        search: bool = False,
        **kw: Any,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        del thinking, search, kw
        cursor_messages = build_cursor_messages(messages)
        last_exc: Optional[Exception] = None

        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                await asyncio.sleep(1.0 * (2 ** (attempt - 1)))
            try:
                finished, retry_messages = True, None
                async for item in self._run_attempt(
                    candidate, cursor_messages, model, stream, attempt
                ):
                    if isinstance(item, tuple):
                        finished, retry_messages = item
                    else:
                        yield item
                if finished:
                    return
                cursor_messages = retry_messages
                last_exc = RuntimeError("refusal_detected")

            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "cursor 请求失败（%d/%d）: %s",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    exc,
                )

        if last_exc is not None:
            raise last_exc

    async def resume_stream(
        self,
        candidate: Candidate,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """GET /api/chat/{chatId}/stream 恢复中断流。"""
        if self._session is None:
            return
        chat_id = self._chat_id_for(candidate)
        x_is_human, cookie = auth_from_candidate(candidate)
        headers = build_resume_headers(
            x_is_human=x_is_human,
            cookie=cookie,
            chat_id=chat_id,
        )
        url = "{}{}".format(BASE_URL, STREAM_RESUME_PATH.format(chat_id=chat_id))
        async with self._session.get(
            url,
            headers=headers,
            ssl=False,
            timeout=aiohttp.ClientTimeout(connect=30, total=300),
        ) as resp:
            if resp.status == 204:
                return
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(
                    "cursor resume HTTP {}: {}".format(resp.status, body[:200])
                )
            async for chunk in iter_response_chunks(resp):
                yield chunk

    async def _post_chat_stream(
        self,
        candidate: Candidate,
        cursor_messages: List[Dict[str, Any]],
        model: str,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        if self._session is None:
            raise RuntimeError("cursor 客户端未初始化")

        chat_id = self._chat_id_for(candidate)
        x_is_human, cookie = auth_from_candidate(candidate)
        headers = build_headers(x_is_human=x_is_human, cookie=cookie)
        payload = build_payload(
            cursor_messages,
            chat_id,
            model=model,
            message_id=new_message_id(),
        )
        url = "{}{}".format(BASE_URL, CHAT_PATH)

        async with self._session.post(
            url,
            json=payload,
            headers=headers,
            ssl=False,
            timeout=aiohttp.ClientTimeout(connect=30, total=300),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(
                    "cursor HTTP {}: {}".format(resp.status, body[:300])
                )
            async for chunk in iter_response_chunks(resp):
                yield chunk

    async def close(self) -> None:
        return
