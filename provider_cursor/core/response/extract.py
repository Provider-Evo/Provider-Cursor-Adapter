"""Cursor 平台数据提取工具。"""

from __future__ import annotations

from typing import Dict, List, Optional


class _ScanState:
    """顶层扫描过程中的可变状态（字符串/深度追踪）。"""

    __slots__ = ("in_string", "escape", "quote", "depth_curly", "depth_square")

    def __init__(self) -> None:
        self.in_string = False
        self.escape = False
        self.quote: Optional[str] = None
        self.depth_curly = 0
        self.depth_square = 0


def _advance_in_string(ch: str, state: _ScanState) -> None:
    """在字符串内部处理转义与引号闭合，更新 state。"""
    if state.escape:
        state.escape = False
    elif ch == "\\":
        state.escape = True
    elif ch == state.quote:
        state.in_string = False
        state.quote = None


def _advance_balanced_array(
    ch: str,
    state: _ScanState,
    depth: int,
) -> "tuple[int, bool]":
    """扫描数组配平中的单字符，返回 (新 depth, 是否已闭合)。"""
    if state.in_string:
        _advance_in_string(ch, state)
        return depth, False
    if ch in ("'", '"'):
        state.in_string = True
        state.quote = ch
        return depth, False
    if ch == "[":
        return depth + 1, False
    if ch != "]":
        return depth, False
    new_depth = depth - 1
    return new_depth, new_depth == 0


def extract_balanced_array(text: str, start_index: int) -> str:
    """从指定位置提取平衡的数组文本（处理嵌套和字符串内的括号）。

    Args:
        text: 源文本。
        start_index: '[' 的起始位置。

    Returns:
        包含首尾括号的完整数组文本。

    Raises:
        ValueError: 位置不是 '[' 或数组未闭合。
    """
    if start_index >= len(text) or text[start_index] != "[":
        raise ValueError("位置 {} 不是 '['".format(start_index))

    i = start_index
    depth = 0
    state = _ScanState()

    while i < len(text):
        depth, closed = _advance_balanced_array(text[i], state, depth)
        if closed:
            return text[start_index:i + 1]
        i += 1

    raise ValueError("数组未闭合")


def _split_object_at_curly(
    ch: str,
    state: _ScanState,
    obj_start: Optional[int],
    i: int,
    array_text: str,
    objs: List[str],
) -> Optional[int]:
    """处理 ``{``/``}`` 深度，闭合时追加对象片段。"""
    if ch == "{":
        if state.depth_curly == 0:
            obj_start = i
        state.depth_curly += 1
        return obj_start
    if ch != "}":
        return obj_start
    state.depth_curly -= 1
    if state.depth_curly == 0 and obj_start is not None:
        objs.append(array_text[obj_start:i + 1])
        return None
    return obj_start


def split_top_level_objects(array_text: str) -> List[str]:
    """将数组文本拆分为顶层对象字符串列表。

    Args:
        array_text: 形如 '[{...},{...}]' 的文本。

    Returns:
        顶层对象字符串列表。

    Raises:
        ValueError: 输入不是合法数组文本。
    """
    if not array_text or array_text[0] != "[" or array_text[-1] != "]":
        raise ValueError("不是合法数组文本")

    objs: List[str] = []
    i = 1
    n = len(array_text)
    state = _ScanState()
    obj_start: Optional[int] = None

    while i < n - 1:
        ch = array_text[i]
        if state.in_string:
            _advance_in_string(ch, state)
        elif ch in ("'", '"'):
            state.in_string = True
            state.quote = ch
        else:
            obj_start = _split_object_at_curly(ch, state, obj_start, i, array_text, objs)
        i += 1

    return objs


def _skip_ws(text: str, i: int, n: int) -> int:
    """跳过 \\t\\r\\n 空白字符，返回新位置。"""
    while i < n and text[i] in "\t\r\n":
        i += 1
    return i


def _parse_quoted_string(text: str, i: int, n: int, quote_ch: str) -> "tuple[str, int]":
    """解析从 i（指向引号后第一个字符）开始的带引号字符串。

    Returns:
        (字符串内容, 结束后的位置)。若未闭合，位置停在 n。
    """
    buf: List[str] = []
    escape = False
    while i < n:
        c = text[i]
        if escape:
            buf.append(c)
            escape = False
        elif c == "\\":
            escape = True
        elif c == quote_ch:
            i += 1
            break
        else:
            buf.append(c)
        i += 1
    return "".join(buf), i


def _advance_balanced_char(
    c: str,
    state: _ScanState,
    open_ch: str,
    close_ch: str,
    depth: int,
) -> int:
    """处理配平扫描中的单个字符，返回更新后的 depth。"""
    if state.in_string:
        _advance_in_string(c, state)
        return depth
    if c in ("'", '"'):
        state.in_string = True
        state.quote = c
        return depth
    if c == open_ch:
        return depth + 1
    if c == close_ch:
        return depth - 1
    return depth


def _parse_balanced(text: str, start: int, n: int, open_ch: str, close_ch: str) -> int:
    """从 start（指向 open_ch）开始扫描配平括号，返回闭合括号后的位置。"""
    depth = 1
    i = start + 1
    state = _ScanState()
    while i < n and depth > 0:
        depth = _advance_balanced_char(text[i], state, open_ch, close_ch, depth)
        i += 1
    return i


def _parse_key(obj_text: str, i: int, n: int) -> "tuple[Optional[str], int]":
    """解析字段名（带引号或裸标识符），返回 (key 或 None, 新位置)。"""
    ch = obj_text[i]
    if ch in ("'", '"'):
        key, j = _parse_quoted_string(obj_text, i + 1, n, ch)
        if j >= n:
            return None, n
        return key, j

    j = i
    while j < n and (obj_text[j].isalnum() or obj_text[j] in "_$."):
        j += 1
    if j == i:
        return None, i + 1
    return obj_text[i:j], j


def _parse_value(obj_text: str, i: int, n: int) -> "tuple[str, int]":
    """解析字段值（字符串/对象/数组/裸值），返回 (原始字符串值, 新位置)。"""
    ch = obj_text[i]
    if ch in ("'", '"'):
        value, j = _parse_quoted_string(obj_text, i + 1, n, ch)
        return value, j
    if ch == "{":
        j = _parse_balanced(obj_text, i, n, "{", "}")
        return obj_text[i:j], j
    if ch == "[":
        j = _parse_balanced(obj_text, i, n, "[", "]")
        return obj_text[i:j], j

    start = i
    while i < n and obj_text[i] not in ",}":
        i += 1
    return obj_text[start:i].strip(), i


def _consume_field(obj_text: str, i: int, n: int, result: Dict[str, str]) -> int:
    """解析一个 "key:value" 字段并写入 result，返回解析后的新位置。"""
    key, i = _parse_key(obj_text, i, n)
    if key is None:
        return i

    i = _skip_ws(obj_text, i, n)
    if i >= n or obj_text[i] != ":":
        return i
    i += 1
    i = _skip_ws(obj_text, i, n)
    if i >= n:
        return n

    value, i = _parse_value(obj_text, i, n)
    result[key] = value
    return i


def _advance_depth(ch: str, state: _ScanState) -> bool:
    """处理括号深度追踪，命中括号字符时返回 True。"""
    if ch in ("'", '"'):
        state.in_string = True
        state.quote = ch
        return True
    if ch == "{":
        state.depth_curly += 1
        return True
    if ch == "}":
        state.depth_curly -= 1
        return True
    if ch == "[":
        state.depth_square += 1
        return True
    if ch == "]":
        state.depth_square -= 1
        return True
    return False


def parse_top_level_fields(obj_text: str) -> Dict[str, str]:
    """只解析对象第一层字段，返回字段名到原始字符串值的映射。

    Args:
        obj_text: 形如 '{key:"val",...}' 的对象文本。

    Returns:
        字段名到原始字符串值的字典。
    """
    result: Dict[str, str] = {}
    i = 1
    n = len(obj_text)
    state = _ScanState()

    while i < n - 1:
        ch = obj_text[i]
        if state.in_string:
            _advance_in_string(ch, state)
            i += 1
            continue

        if _advance_depth(ch, state):
            i += 1
            continue

        if state.depth_curly == 0 and state.depth_square == 0:
            if ch in "\t\r\n,":
                i += 1
                continue
            i = _consume_field(obj_text, i, n, result)
            continue

        i += 1

    return result


def extract_id_from_subrows(subrows_text: str) -> List[str]:
    """从 subRows 数组文本中提取所有子项 id。

    Args:
        subrows_text: 形如 '[{"id":"..."},...]' 的文本。

    Returns:
        id 字符串列表。
    """
    if not subrows_text or subrows_text[0] != "[":
        return []
    objs = split_top_level_objects(subrows_text)
    ids: List[str] = []
    for obj in objs:
        fields = parse_top_level_fields(obj)
        if "id" in fields:
            ids.append(fields["id"])
    return ids
