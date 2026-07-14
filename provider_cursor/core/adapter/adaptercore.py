"""Cursor 平台适配器实现。

包含 :class:`CursorAdapter` 的完整业务逻辑，
经由 :mod:`src.platforms.cursor.util` 的 ``__getattr__`` 延迟加载。
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp

from src.core.dispatch.candidate import Candidate
from src.core.utils.compat.models_cache import ModelsCache
from src.foundation.logger import get_logger
from provider_sdk.extensions.platform.adapter import PlatformAdapter

from ..constants import CAPS, MODELS, FETCH_MODELS_ENABLED, MODEL_FETCH_INTERVAL
from .client import CursorClient

logger = get_logger(__name__)


class CursorAdapter(PlatformAdapter):
    """Cursor 平台适配器。

    将 Provider-V2 通用接口映射到 Cursor /api/chat SSE 端点。
    内置拒绝检测、响应清洗、thinking 提取、认知重构重试逻辑。
    模型列表通过 ModelsCache 管理，后台每24小时周期刷新。
    """

    def __init__(self) -> None:
        """初始化适配器实例。"""
        self._client: Any = None
        self._models: List[str] = []
        self._cache: Optional[ModelsCache] = None
        self._refresh_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
        self._model_fetch_interval: int = 86400

    @property
    def name(self) -> str:
        """返回平台小写标识。

        Returns:
            平台标识字符串。
        """
        return "cursor"

    @property
    def supported_models(self) -> List[str]:
        """返回当前支持的模型列表。

        Returns:
            模型 ID 列表。
        """
        return list(self._models)

    @property
    def default_capabilities(self) -> Dict[str, bool]:
        """返回平台默认能力字典。

        Returns:
            能力名称到布尔值的映射。
        """
        return dict(CAPS)

    async def init(self, session: aiohttp.ClientSession) -> None:
        """初始化适配器——立即注册，后台完善。

        先以硬编码数据注册到 registry，后台 Task 执行模型刷新等耗时操作。

        Args:
            session: 共享的 aiohttp 会话。
        """
        self._client = CursorClient()
        await self._client.init_immediate(session)

        self._models = list(MODELS)
        self._model_fetch_interval: int = MODEL_FETCH_INTERVAL

        self._cache = ModelsCache(
            platform="cursor",
            fallback_models=MODELS,
            fetch_enabled=FETCH_MODELS_ENABLED,
        )
        cached = await self._cache.load()
        if cached:
            self._models = cached
            self._client.update_models(self._models)

        self._refresh_task = asyncio.ensure_future(self._background_init())

    async def _background_init(self) -> None:
        """后台初始化：完成耗时操作后持续刷新。
        """
        try:
            await self._client.background_setup()
        except Exception as exc:
            logger.warning("cursor 后台初始化失败: %s", exc)

        if self._cache is not None:
            asyncio.ensure_future(
                self._cache.start_refresh_loop(
                    fetch_fn=self.fetch_remote_models,
                    interval=self._model_fetch_interval,
                    on_update=self._on_models_updated,
                )
            )

    async def _on_models_updated(self, models: List[str]) -> None:
        """模型列表更新回调。

        Args:
            models: 新的模型列表。
        """
        self._models = models
        if self._client is not None:
            self._client.update_models(models)
        logger.info("cursor 模型列表已更新: %d 个", len(models))

    async def fetch_remote_models(self) -> List[str]:
        """拉取远程模型列表，从 cursor.com JS 静态资源解析。

        Returns:
            模型 ID 列表。
        """
        if self._client is None:
            return list(MODELS)
        try:
            return await self._client.fetch_remote_models()
        except Exception as exc:
            logger.warning("cursor 远程模型拉取失败: %s", exc)
            return list(MODELS)

    async def candidates(self) -> List[Candidate]:
        """返回当前可用候选项。

        Returns:
            候选项列表。
        """
        if self._client is None:
            return []
        return await self._client.candidates()

    async def ensure_candidates(self, count: int) -> int:
        """确保候选项数量。

        Args:
            count: 期望的候选项数量。

        Returns:
            实际可用候选项数量。
        """
        if self._client is None:
            return 0
        return await self._client.ensure_candidates(count)

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
        """执行聊天补全，委托给 client。

        Args:
            candidate: 候选项（含 meta 信息）。
            messages: 标准消息列表（OpenAI/Anthropic 格式）。
            model: 模型名。
            stream: 是否流式。
            thinking: 是否启用 thinking 提取。
            search: 是否启用搜索（不支持，忽略）。
            **kw: 其他参数。

        Yields:
            str 文本片段 或 dict（thinking/usage）。
        """
        async for chunk in self._client.complete(
            candidate, messages, model, stream,
            thinking=thinking, search=search, **kw,
        ):
            yield chunk

    async def resume_stream(
        self,
        candidate: Candidate,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """恢复 GET /api/chat/{chatId}/stream 流。"""
        if self._client is None:
            return
        async for chunk in self._client.resume_stream(candidate):
            yield chunk

    async def close(self) -> None:
        """关闭适配器，停止后台刷新任务，释放资源。
        """
        if self._refresh_task is not None and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                logger.debug("cursor refresh task cancelled")
        if self._client is not None:
            await self._client.close()


Adapter = CursorAdapter
