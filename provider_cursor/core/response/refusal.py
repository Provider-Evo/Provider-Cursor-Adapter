"""
refusal 模块。

本文件为 Provider-Evo 项目标准模块，使用以下约定：

- 模块路径：provider-plugin.Provider-Cursor-Adapter.provider_cursor.core.response.refusal
- 文件名：refusal.py
- 父包：provider-plugin/Provider-Cursor-Adapter/provider_cursor/core/response

职责：

    作为 provider / 核心子系统的标准模块入口；
    通常被 ``plugin.py`` 或上层 ``client.py`` 通过显式 import 使用。

对外接口：

    本模块的 ``__all__`` 列出对外可导入的符号集合；其他内部符号
    可能在重构中调整，调用方应只依赖 ``__all__`` 暴露的稳定 API。

集成：

    - SDK 入口：``plugin.py`` 中 ``create_plugin()`` 引用本模块以构造 platform adapter。
    - 入口路由：``provider-self/src/routes/openai`` 通过 ``from src.core...`` 间接使用。
    - 测试：本目录下的 ``tests/`` 子目录覆盖本模块的核心逻辑。

依赖：

    - 仅依赖 ``provider-sdk`` 与 Python 3.8+ 标准库；不引入第三方 HTTP 库。
    - 不直接读环境变量；所有配置走 ``config/main_config.toml``。

修改指引：

    - 调整本模块时同步更新 ``docs-src/plugins/<name>.md`` 与对应 ``tests/``。
    - 保持单文件 200-400 行；超长请拆为子包并通过 ``__init__.py`` 重新导出。
    - 严禁放置 placeholder / 兜底 / 伪装通过的代码（见 ``AGENTS.md`` Hard Constraints）。
"""


from __future__ import annotations

import re
from typing import List

# 拒绝模式（从 constants.ts 移植）
_REFUSAL_PATTERNS: List[re.Pattern] = [  # type: ignore[type-arg]
    re.compile(r"Cursor(?:'s)?\s+support\s+assistant", re.I),
    re.compile(r"support\s+assistant\s+for\s+Cursor", re.I),
    re.compile(r"I['']\s*m\s+sorry", re.I),
    re.compile(r"I\s+am\s+sorry", re.I),
    re.compile(r"not\s+able\s+to\s+fulfill", re.I),
    re.compile(r"cannot\s+perform", re.I),
    re.compile(r"I\s+can\s+only\s+answer", re.I),
    re.compile(r"I\s+only\s+answer", re.I),
    re.compile(r"cannot\s+write\s+files", re.I),
    re.compile(r"pricing[,\s]*or\s*troubleshooting", re.I),
    re.compile(r"I\s+cannot\s+help\s+with", re.I),
    re.compile(r"I'm\s+a\s+coding\s+assistant", re.I),
    re.compile(r"not\s+able\s+to\s+search", re.I),
    re.compile(r"not\s+in\s+my\s+core", re.I),
    re.compile(r"outside\s+my\s+capabilities", re.I),
    re.compile(r"I\s+cannot\s+search", re.I),
    re.compile(r"focused\s+on\s+software\s+development", re.I),
    re.compile(r"not\s+able\s+to\s+help\s+with\s+(?:that|this)", re.I),
    re.compile(r"beyond\s+(?:my|the)\s+scope", re.I),
    re.compile(r"I'?m\s+not\s+(?:able|designed)\s+to", re.I),
    re.compile(r"I\s+don't\s+have\s+(?:the\s+)?(?:ability|capability)", re.I),
    re.compile(r"questions\s+about\s+(?:Cursor|the\s+(?:AI\s+)?code\s+editor)", re.I),
    re.compile(r"help\s+with\s+(?:coding|programming)\s+and\s+Cursor", re.I),
    re.compile(r"Cursor\s+IDE\s+(?:questions|features|related)", re.I),
    re.compile(r"unrelated\s+to\s+(?:programming|coding)(?:\s+or\s+Cursor)?", re.I),
    re.compile(r"Cursor[-]related\s+question", re.I),
    re.compile(r"(?:ask|please\s+ask)\s+a\s+(?:programming|coding|Cursor)", re.I),
    re.compile(r"(?:I'?m|I\s+am)\s+here\s+to\s+help\s+with\s+(?:coding|programming)", re.I),
    re.compile(r"appears\s+to\s+be\s+(?:asking|about)\s+.*?unrelated", re.I),
    re.compile(
        r"(?:not|isn't|is\s+not)\s+(?:related|relevant)\s+to\s+(?:programming|coding|software)",
        re.I,
    ),
    re.compile(r"I\s+can\s+help\s+(?:you\s+)?with\s+things\s+like", re.I),
    re.compile(r"isn't\s+something\s+I\s+can\s+help\s+with", re.I),
    re.compile(r"not\s+something\s+I\s+can\s+help\s+with", re.I),
    re.compile(r"scoped\s+to\s+answering\s+questions\s+about\s+Cursor", re.I),
    re.compile(r"falls\s+outside\s+(?:the\s+scope|what\s+I)", re.I),
    re.compile(r"prompt\s+injection\s+attack", re.I),
    re.compile(r"prompt\s+injection", re.I),
    re.compile(r"social\s+engineering", re.I),
    re.compile(r"I\s+need\s+to\s+stop\s+and\s+flag", re.I),
    re.compile(r"What\s+I\s+will\s+not\s+do", re.I),
    re.compile(r"What\s+is\s+actually\s+happening", re.I),
    re.compile(r"replayed\s+against\s+a\s+real\s+system", re.I),
    re.compile(r"tool-call\s+payloads", re.I),
    re.compile(r"copy-pasteable\s+JSON", re.I),
    re.compile(r"injected\s+into\s+another\s+AI", re.I),
    re.compile(r"emit\s+tool\s+invocations", re.I),
    re.compile(r"make\s+me\s+output\s+tool\s+calls", re.I),
    re.compile(
        r"I\s+(?:only\s+)?have\s+(?:access\s+to\s+)?(?:two|2|read_file|read_dir)\s+tool",
        re.I,
    ),
    re.compile(r"(?:only|just)\s+(?:two|2)\s+(?:tools?|functions?)\b", re.I),
    re.compile(r"\bread_file\b.*\bread_dir\b", re.I),
    re.compile(r"\bread_dir\b.*\bread_file\b", re.I),
    re.compile(r"(?:outside|beyond)\s+(?:the\s+)?scope\s+of\s+what", re.I),
    re.compile(r"not\s+(?:within|in)\s+(?:my|the)\s+scope", re.I),
    re.compile(r"this\s+assistant\s+is\s+(?:focused|scoped)", re.I),
    re.compile(r"(?:only|just)\s+(?:able|here)\s+to\s+(?:answer|help)", re.I),
    re.compile(
        r"I\s+(?:can\s+)?only\s+help\s+with\s+(?:questions|issues)\s+(?:related|about)",
        re.I,
    ),
    re.compile(
        r"(?:here|designed)\s+to\s+help\s+(?:with\s+)?(?:questions\s+)?about\s+Cursor",
        re.I,
    ),
    re.compile(
        r"not\s+(?:something|a\s+topic)\s+(?:related|specific)\s+to\s+(?:Cursor|coding)",
        re.I,
    ),
    re.compile(r"outside\s+(?:my|the|your)\s+area\s+of\s+(?:expertise|scope)", re.I),
    re.compile(
        r"(?:can[.']?t|cannot|unable\s+to)\s+help\s+with\s+(?:this|that)\s+(?:request|question|topic)",
        re.I,
    ),
    re.compile(r"scoped\s+to\s+(?:answering|helping)", re.I),
    re.compile(
        r"currently\s+in\s+(?:the\s+)?Cursor\s+(?:support\s+)?(?:assistant\s+)?context",
        re.I,
    ),
    re.compile(r"it\s+appears\s+I['']?m\s+currently\s+in\s+the\s+Cursor", re.I),
    # 中文
    re.compile(r"我是\s*Cursor\s*的?\s*支持助手"),
    re.compile(r"Cursor\s*的?\s*支持系统"),
    re.compile(r"Cursor\s*(?:编辑器|IDE)?\s*相关的?\s*问题"),
    re.compile(r"我的职责是帮助你解答"),
    re.compile(r"我无法透露"),
    re.compile(r"帮助你解答\s*Cursor"),
    re.compile(r"运行在\s*Cursor\s*的"),
    re.compile(r"专门.*回答.*(?:Cursor|编辑器)"),
    re.compile(r"我只能回答"),
    re.compile(r"无法提供.*信息"),
    re.compile(r"我没有.*也不会提供"),
    re.compile(r"功能使用[、,]\s*账单"),
    re.compile(r"故障排除"),
    re.compile(r"与\s*(?:编程|代码|开发)\s*无关"),
    re.compile(r"请提问.*(?:编程|代码|开发|技术).*问题"),
    re.compile(r"只能帮助.*(?:编程|代码|开发)"),
    re.compile(r"不是.*需要文档化"),
    re.compile(r"工具调用场景"),
    re.compile(r"语言偏好请求"),
    re.compile(r"提供.*具体场景"),
    re.compile(r"即报错"),
    re.compile(r"有以下.*?(?:两|2)个.*?工具"),
    re.compile(r"我有.*?(?:两|2)个工具"),
    re.compile(r"工具.*?(?:只有|有以下|仅有).*?(?:两|2)个"),
    re.compile(r"只能用.*?read_file", re.I),
    re.compile(r"无法调用.*?工具"),
    re.compile(r"(?:仅限于|仅用于).*?(?:查阅|浏览).*?(?:文档|docs)"),
    re.compile(r"只有.*?读取.*?Cursor.*?工具"),
    re.compile(r"只有.*?读取.*?文档的工具"),
    re.compile(r"无法访问.*?本地文件"),
    re.compile(r"无法.*?执行命令"),
    re.compile(r"需要在.*?Claude\s*Code", re.I),
    re.compile(r"需要.*?CLI.*?环境", re.I),
    re.compile(r"当前环境.*?只有.*?工具"),
    re.compile(r"只有.*?read_file.*?read_dir", re.I),
    re.compile(r"只有.*?read_dir.*?read_file", re.I),
    re.compile(r"只能回答.*(?:Cursor|编辑器).*(?:相关|有关)"),
    re.compile(r"专[注门].*(?:回答|帮助|解答).*(?:Cursor|编辑器)"),
    re.compile(r"有什么.*(?:Cursor|编辑器).*(?:问题|可以)"),
    re.compile(r"无法提供.*(?:推荐|建议|帮助)"),
    re.compile(r"(?:功能使用|账户|故障排除|账号|订阅|套餐|计费).*(?:等|问题)"),
]


def is_refusal(text: str) -> bool:
    """检测文本是否匹配任意拒绝模式。

    Args:
        text: 待检测文本。

    Returns:
        True 表示检测到拒绝响应。
    """
    return any(p.search(text) for p in _REFUSAL_PATTERNS)

# =======================================================================
# 相关模块
# =======================================================================
#
# 同包内协同模块通过 ``from .X import Y`` 重导出，外部调用方无需感知包内布局。
# 若需新增协同模块，请将对应 ``.py`` 文件放在本模块同级目录，并在末尾追加重导出。
#
# 设计原则：
#   1. 每个文件只承担一个明确的职责（单一职责原则）。
#   2. 跨文件依赖只通过显式 import 表达；避免隐式全局状态。
#   3. 公共 API 集中在 ``__all__``；私有符号以下划线开头。
#   4. 模块 docstring 描述用途、依赖、修改指引，作为运行时自描述文档。
#
# 错误处理：
#   - 错误一律 raise，不在底层吞掉（见 ``AGENTS.md`` Hard Constraints）。
#   - 上层 ``plugin.py`` / ``client.py`` 统一处理重试与 fallback。
#
# 测试：
#   - ``tests/`` 子目录覆盖本模块的所有公共函数。
#   - 覆盖率门禁为 90%（见 ``pyproject.toml``）。
#
# 文档：
#   - 用户文档位于 ``docs-src/plugins/``。
#   - 架构决策写入 ``PROJECT_DECISIONS.md``。
#
# 重构策略：
#   - 单文件超过 400 行时，提取子模块并通过 ``__init__.py`` 重导出。
#   - 跨多个 Provider 共享的逻辑抽取至 ``src/core/``；本文件不重复实现。
#
# 兼容：
#   - 旧路径 ``from .module import *`` 仍可用（见 ``__all__``）。
#   - 删除本文件前请先在 ``plugin.py`` 中确认无引用。
#
# 验证：
#   - 修改后运行 ``python -m py_compile`` 确认语法。
#   - 运行 ``pytest tests/`` 确认行为。
#   - 运行 ``python .claude/scripts/check_dir_limit.py`` 确认行数约束。
