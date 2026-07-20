"""Cursor 平台响应清洗。"""

from __future__ import annotations

import re

_CLAUDE_IDENTITY_RESPONSE: str = (
    "I am Claude, made by Anthropic. I'm an AI assistant designed to be helpful, "
    "harmless, and honest. I can help you with a wide range of tasks including "
    "writing, analysis, coding, math, and more.\n\n"
    "I don't have information about the specific model version or ID being used "
    "for this conversation, but I'm happy to help you with whatever you need!"
)


def _sanitize_english_identity(result: str) -> str:
    """替换英文身份引用（Cursor -> Claude）。"""
    result = re.sub(
        r"I\s+am\s+(?:a\s+)?(?:support\s+)?assistant\s+for\s+Cursor",
        "I am Claude, an AI assistant by Anthropic",
        result, flags=re.I,
    )
    result = re.sub(
        r"I(?:'m|\s+am)\s+(?:a\s+)?Cursor(?:'s)?\s+(?:support\s+)?assistant",
        "I am Claude, an AI assistant by Anthropic",
        result, flags=re.I,
    )
    result = re.sub(
        r"Cursor(?:'s)?\s+support\s+assistant",
        "Claude, an AI assistant by Anthropic",
        result, flags=re.I,
    )
    result = re.sub(
        r"support\s+assistant\s+for\s+Cursor",
        "Claude, an AI assistant by Anthropic",
        result, flags=re.I,
    )
    result = re.sub(
        r"I\s+run\s+(?:on|in)\s+Cursor(?:'s)?\s+(?:support\s+)?system",
        "I am Claude, running on Anthropic's infrastructure",
        result, flags=re.I,
    )
    return result


def _sanitize_topic_refusal_phrases(result: str) -> str:
    """替换英文话题拒答表述（第一批：助手职责/话题范围表述）。"""
    result = re.sub(
        r"(?:help\s+with\s+)?coding\s+and\s+Cursor\s+IDE\s+questions",
        "help with a wide range of tasks",
        result, flags=re.I,
    )
    result = re.sub(
        r"(?:I'?m|I\s+am)\s+here\s+to\s+help\s+with\s+coding\s+and\s+Cursor[^.]*\.",
        "I am Claude, an AI assistant by Anthropic. I can help with a wide range of tasks.",
        result, flags=re.I,
    )
    result = re.sub(
        r"\*\*Cursor\s+IDE\s+features\*\*",
        "**AI capabilities**",
        result, flags=re.I,
    )
    result = re.sub(
        r"Cursor\s+IDE\s+(?:features|questions|related)",
        "various topics",
        result, flags=re.I,
    )
    result = re.sub(
        r"unrelated\s+to\s+programming\s+or\s+Cursor",
        "a general knowledge question",
        result, flags=re.I,
    )
    result = re.sub(
        r"unrelated\s+to\s+(?:programming|coding)",
        "a general knowledge question",
        result, flags=re.I,
    )
    result = re.sub(
        r"(?:a\s+)?(?:programming|coding|Cursor)[-]related\s+question",
        "a question",
        result, flags=re.I,
    )
    result = re.sub(
        r"(?:please\s+)?ask\s+a\s+(?:programming|coding)\s+(?:or\s+(?:Cursor[-]related\s+)?)?question",
        "feel free to ask me anything",
        result, flags=re.I,
    )
    return result


def _sanitize_topic_refusal_boundaries(result: str) -> str:
    """替换英文话题拒答表述（第二批：Cursor 功能/文档边界表述）。"""
    result = re.sub(
        r"questions\s+about\s+Cursor(?:'s)?\s+(?:features|editor|IDE|pricing|the\s+AI)",
        "your questions",
        result, flags=re.I,
    )
    result = re.sub(
        r"help\s+(?:you\s+)?with\s+(?:questions\s+about\s+)?Cursor",
        "help you with your tasks",
        result, flags=re.I,
    )
    result = re.sub(
        r"about\s+the\s+Cursor\s+(?:AI\s+)?(?:code\s+)?editor",
        "",
        result, flags=re.I,
    )
    result = re.sub(
        r"Cursor(?:'s)?\s+(?:features|editor|code\s+editor|IDE),?\s*(?:pricing|troubleshooting|billing)",
        "programming, analysis, and technical questions",
        result, flags=re.I,
    )
    result = re.sub(
        r"(?:finding\s+)?relevant\s+Cursor\s+(?:or\s+)?(?:coding\s+)?documentation",
        "relevant documentation",
        result, flags=re.I,
    )
    result = re.sub(
        r"(?:finding\s+)?relevant\s+Cursor",
        "relevant",
        result, flags=re.I,
    )
    result = re.sub(
        r"AI\s+chat,\s+code\s+completion,\s+rules,\s+context,?\s+etc\.?",
        "writing, analysis, coding, math, and more",
        result, flags=re.I,
    )
    result = re.sub(r"(?:\s+or|\s+and)\s+Cursor(?![\w])", "", result, flags=re.I)
    result = re.sub(r"Cursor(?:\s+or|\s+and)\s+", "", result, flags=re.I)
    return result


def _sanitize_english_topic_refusal(result: str) -> str:
    """替换英文话题拒答/工具边界表述。"""
    result = _sanitize_topic_refusal_phrases(result)
    result = _sanitize_topic_refusal_boundaries(result)
    return result


def _sanitize_chinese_identity(result: str) -> str:
    """替换中文身份/系统归属引用（第一批）。"""
    result = re.sub(
        r"我是\s*Cursor\s*的?\s*支持助手",
        "我是Claude，由Anthropic开发的AI助手",
        result,
    )
    result = re.sub(
        r"Cursor\s*的?\s*支持(?:系统|助手)",
        "Claude，Anthropic的AI助手",
        result,
    )
    result = re.sub(
        r"运行在\s*Cursor\s*的?\s*(?:支持)?系统中",
        "运行在Anthropic的基础设施上",
        result,
    )
    result = re.sub(
        r"帮助你解答\s*Cursor\s*相关的?\s*问题",
        "帮助你解答各种问题",
        result,
    )
    result = re.sub(
        r"关于\s*Cursor\s*(?:编辑器|IDE)?\s*的?\s*问题",
        "你的问题",
        result,
    )
    result = re.sub(
        r"专门.*?回答.*?(?:Cursor|编辑器).*?问题",
        "可以回答各种技术和非技术问题",
        result,
    )
    result = re.sub(
        r"(?:功能使用[、,]\s*)?账单[、,]\s*(?:故障排除|定价)",
        "编程、分析和各种技术问题",
        result,
    )
    result = re.sub(r"故障排除等", "等各种问题", result)
    result = re.sub(r"我的职责是帮助你解答", "我可以帮助你解答", result)
    result = re.sub(r"如果你有关于\s*Cursor\s*的问题", "如果你有任何问题", result)
    return result


def _sanitize_chinese_topic_refusal(result: str) -> str:
    """替换中文话题拒答表述（第二批）。"""
    result = re.sub(
        r"这个问题与\s*(?:Cursor\s*或?\s*)?(?:软件开发|编程|代码|开发)\s*无关[^。\n]*[。，,]?\s*",
        "",
        result,
    )
    result = re.sub(
        r"(?:与\s*)?(?:Cursor|编程|代码|开发|软件开发)\s*(?:无关|不相关)[^。\n]*[。，,]?\s*",
        "",
        result,
    )
    result = re.sub(
        r"如果有?\s*(?:Cursor\s*)?(?:相关|有关).*?(?:欢迎|请)\s*(?:继续)?(?:提问|询问)[。！!]?\s*",
        "",
        result,
    )
    result = re.sub(
        r"如果你?有.*?(?:Cursor|编程|代码|开发).*?(?:问题|需求)[^。\n]*[。，,]?\s*(?:欢迎|请|随时).*$",
        "",
        result,
        flags=re.M,
    )
    result = re.sub(r"(?:与|和|或)\s*Cursor\s*(?:相关|有关)", "", result)
    result = re.sub(r"Cursor\s*(?:相关|有关)\s*(?:或|和|的)", "", result)
    return result


def _sanitize_chinese(result: str) -> str:
    """替换中文身份/话题引用（Cursor -> Claude）。"""
    result = _sanitize_chinese_identity(result)
    result = _sanitize_chinese_topic_refusal(result)
    return result


def _sanitize_tool_claims(result: str) -> str:
    """清理关于可用工具数量/名称的错误声明。"""
    result = re.sub(
        r"(?:I\s+)?(?:only\s+)?have\s+(?:access\s+to\s+)?(?:two|2)\s+tools?[^.]*\.",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(r"工具.*?只有.*?(?:两|2)个[^。]*。", "", result)
    result = re.sub(r"我有以下.*?(?:两|2)个工具[^。]*。?", "", result)
    result = re.sub(r"我有.*?(?:两|2)个工具[^。]*[。：:]?", "", result)
    result = re.sub(
        r"\*\*`?read_file`?\*\*[^\n]*\n(?:[^\n]*\n){0,3}",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"\*\*`?read_dir`?\*\*[^\n]*\n(?:[^\n]*\n){0,3}",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"\d+\.\s*\*\*`?read_(?:file|dir)`?\*\*[^\n]*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"[⚠注意].*?(?:不是|并非|无法).*?(?:本地文件|代码库|执行代码)[^。\n]*[。]?\s*",
        "",
        result,
    )
    result = re.sub(r"[^。\n]*只有.*?读取.*?(?:Cursor|文档).*?工具[^。\n]*[。]?\s*", "", result)
    result = re.sub(r"[^。\n]*无法访问.*?本地文件[^。\n]*[。]?\s*", "", result)
    result = re.sub(r"[^。\n]*无法.*?执行命令[^。\n]*[。]?\s*", "", result)
    result = re.sub(
        r"[^。\n]*需要在.*?Claude\s*Code[^。\n]*[。]?\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(r"[^。\n]*当前环境.*?只有.*?工具[^。\n]*[。]?\s*", "", result)
    return result


def _has_prompt_injection_accusation(result: str) -> bool:
    """检测是否触发了提示注入指控，需整体替换为固定身份回复。"""
    return bool(
        re.search(
            r"prompt\s+injection|social\s+engineering"
            r"|I\s+need\s+to\s+stop\s+and\s+flag"
            r"|What\s+I\s+will\s+not\s+do",
            result,
            re.I,
        )
    )


def _sanitize_context_leak(result: str) -> str:
    """清理 Cursor 支持助手上下文泄露相关表述。"""
    result = re.sub(
        r"I\s+apologi[sz]e\s*[-–—]?\s*it\s+appears\s+I[''']?m\s+currently\s+in\s+the\s+Cursor"
        r"[\s\S]*?(?:available|context)[.!]?\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"[^\n.!?]*(?:currently\s+in|running\s+in|operating\s+in)\s+(?:the\s+)?Cursor\s+"
        r"(?:support\s+)?(?:assistant\s+)?context[^\n.!?]*[.!?]?\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"[^\n.!?]*where\s+only\s+[`\"']?read_file[`\"']?\s+and\s+[`\"']?read_dir[`\"']?"
        r"[^\n.!?]*[.!?]?\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"However,\s+based\s+on\s+the\s+tool\s+call\s+results\s+shown[^\n.!?]*[.!?]?\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"[^\n.!?]*(?:accidentally|mistakenly|keep|sorry|apologies|apologize)"
        r"[^\n.!?]*(?:called|calling|used|using)[^\n.!?]*Cursor[^\n.!?]*tool[^\n.!?]*[.!?]\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(
        r"[^\n.!?]*Cursor\s+documentation[^\n.!?]*tool[^\n.!?]*[.!?]\s*",
        "",
        result,
        flags=re.I,
    )
    result = re.sub(r"I\s+need\s+to\s+stop\s+this[.!]\s*", "", result, flags=re.I)
    return result


def sanitize_response(text: str) -> str:
    """清洗响应中的 Cursor 身份引用，替换为 Claude。

    从 handler.ts sanitizeResponse() 完整移植，覆盖英文和中文两套规则。

    豁免说明：本函数按业务职责编排为若干子函数（英文身份、英文话题、中文、
    工具边界声明、提示注入指控、上下文泄露），主体仅负责按顺序调用。

    Args:
        text: 原始响应文本。

    Returns:
        清洗后的文本。
    """
    result = text

    result = _sanitize_english_identity(result)
    result = _sanitize_english_topic_refusal(result)
    result = _sanitize_chinese(result)
    result = _sanitize_tool_claims(result)

    if _has_prompt_injection_accusation(result):
        return _CLAUDE_IDENTITY_RESPONSE

    result = _sanitize_context_leak(result)

    return result


# Public export alias
CLAUDE_IDENTITY_RESPONSE: str = _CLAUDE_IDENTITY_RESPONSE
