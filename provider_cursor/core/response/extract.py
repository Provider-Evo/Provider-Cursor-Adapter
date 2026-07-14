"""Cursor 平台数据提取工具。"""

from __future__ import annotations

from typing import Dict, List, Optional


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
    in_string = False
    escape = False
    quote: Optional[str] = None

    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
                quote = None
        else:
            if ch in ("'", '"'):
                in_string = True
                quote = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return text[start_index:i + 1]
        i += 1

    raise ValueError("数组未闭合")


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
    in_string = False
    escape = False
    quote: Optional[str] = None
    depth_curly = 0
    obj_start: Optional[int] = None

    while i < n - 1:
        ch = array_text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
                quote = None
        else:
            if ch in ("'", '"'):
                in_string = True
                quote = ch
            elif ch == "{":
                if depth_curly == 0:
                    obj_start = i
                depth_curly += 1
            elif ch == "}":
                depth_curly -= 1
                if depth_curly == 0 and obj_start is not None:
                    objs.append(array_text[obj_start:i + 1])
                    obj_start = None
        i += 1

    return objs


def parse_top_level_fields(obj_text: str) -> Dict[str, str]:
    """只解析对象第一层字段，返回字段名到原始字符串值的映射。

    豁免说明：本函数为完整的解析器 dispatch 逻辑，包含多层嵌套的
    状态机（字符串解析、深度追踪、多类型值处理），天然不可拆分。

    Args:
        obj_text: 形如 '{key:"val",...}' 的对象文本。

    Returns:
        字段名到原始字符串值的字典。
    """
    result: Dict[str, str] = {}
    i = 1
    n = len(obj_text)
    in_string = False
    escape = False
    quote: Optional[str] = None
    depth_curly = 0
    depth_square = 0

    while i < n - 1:
        ch = obj_text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
                quote = None
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            quote = ch
            i += 1
            continue

        if ch == "{":
            depth_curly += 1
            i += 1
            continue
        if ch == "}":
            depth_curly -= 1
            i += 1
            continue
        if ch == "[":
            depth_square += 1
            i += 1
            continue
        if ch == "]":
            depth_square -= 1
            i += 1
            continue

        if depth_curly == 0 and depth_square == 0:
            if ch in "\t\r\n,":
                i += 1
                continue

            key: Optional[str] = None
            if ch in ("'", '"'):
                q = ch
                j = i + 1
                esc = False
                buf: List[str] = []
                while j < n:
                    c = obj_text[j]
                    if esc:
                        buf.append(c)
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == q:
                        break
                    else:
                        buf.append(c)
                    j += 1
                if j >= n:
                    break
                key = "".join(buf)
                i = j + 1
            else:
                j = i
                while j < n and (obj_text[j].isalnum() or obj_text[j] in "_$."):
                    j += 1
                if j == i:
                    i += 1
                    continue
                key = obj_text[i:j]
                i = j

            while i < n and obj_text[i] in "\t\r\n":
                i += 1
            if i >= n or obj_text[i] != ":":
                continue
            i += 1
            while i < n and obj_text[i] in "\t\r\n":
                i += 1
            if i >= n:
                break

            if obj_text[i] in ("'", '"'):
                q2 = obj_text[i]
                i += 1
                buf2: List[str] = []
                esc2 = False
                while i < n:
                    c2 = obj_text[i]
                    if esc2:
                        buf2.append(c2)
                        esc2 = False
                    elif c2 == "\\":
                        esc2 = True
                    elif c2 == q2:
                        i += 1
                        break
                    else:
                        buf2.append(c2)
                    i += 1
                result[key] = "".join(buf2)
                continue

            if obj_text[i] == "{":
                start = i
                dep = 1
                i += 1
                iss = False
                esc3 = False
                iq: Optional[str] = None
                while i < n and dep > 0:
                    c3 = obj_text[i]
                    if iss:
                        if esc3:
                            esc3 = False
                        elif c3 == "\\":
                            esc3 = True
                        elif c3 == iq:
                            iss = False
                            iq = None
                    else:
                        if c3 in ("'", '"'):
                            iss = True
                            iq = c3
                        elif c3 == "{":
                            dep += 1
                        elif c3 == "}":
                            dep -= 1
                    i += 1
                result[key] = obj_text[start:i]
                continue

            if obj_text[i] == "[":
                start2 = i
                dep2 = 1
                i += 1
                iss2 = False
                esc4 = False
                iq2: Optional[str] = None
                while i < n and dep2 > 0:
                    c4 = obj_text[i]
                    if iss2:
                        if esc4:
                            esc4 = False
                        elif c4 == "\\":
                            esc4 = True
                        elif c4 == iq2:
                            iss2 = False
                            iq2 = None
                    else:
                        if c4 in ("'", '"'):
                            iss2 = True
                            iq2 = c4
                        elif c4 == "[":
                            dep2 += 1
                        elif c4 == "]":
                            dep2 -= 1
                    i += 1
                result[key] = obj_text[start2:i]
                continue

            start3 = i
            while i < n and obj_text[i] not in ",}":
                i += 1
            result[key] = obj_text[start3:i].strip()
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
