"""응답 dict → 파이썬 값으로 옮길 때 쓰는 관용 파서.

코레일 응답은 필드를 통째로 빼먹거나 빈 문자열로 채워 보내는 경우가 있습니다.
모델 생성이 그런 이유로 죽으면 안 되므로, 여기서 전부 흡수합니다.
"""

from __future__ import annotations

from typing import Any


def text(data: dict[str, Any], key: str, default: str = "") -> str:
    """문자열 필드를 읽습니다. 없거나 ``None`` 이면 ``default``."""
    value = data.get(key)
    return default if value is None else str(value)


def integer(data: dict[str, Any], key: str, default: int = 0) -> int:
    """정수 필드를 읽습니다. 없거나 숫자로 못 읽으면 ``default``."""
    value = data.get(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def floating(data: dict[str, Any], key: str, default: float | None = None) -> float | None:
    """실수 필드를 읽습니다. 없거나 숫자로 못 읽으면 ``default``."""
    value = data.get(key)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def hhmm(value: str) -> str:
    """``HHMMSS`` → ``HH:MM``. 형식이 안 맞으면 원본을 그대로 돌려줍니다."""
    if len(value) < 4 or not value[:4].isdigit():
        return value
    return f"{value[:2]}:{value[2:4]}"


def mmdd(value: str, separator: str = "/") -> str:
    """``YYYYMMDD`` → ``MM/DD``. 형식이 안 맞으면 원본을 그대로 돌려줍니다."""
    if len(value) < 8 or not value.isdigit():
        return value
    return f"{int(value[4:6]):02d}{separator}{int(value[6:8]):02d}"
