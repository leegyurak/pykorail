"""파이썬 최소 버전 강제.

``requires-python`` 은 패키지 매니저를 통해 설치할 때만 걸립니다. 소스를 그대로
복사해 오거나 ``PYTHONPATH`` 로 끌어다 쓰는 경우를 대비해 임포트 시점에도 막습니다.
빈 슬롯 데이터클래스·``X | Y`` 런타임 유니언 등 3.10 문법을 실제로 쓰기 때문에,
낮은 버전에서는 알아보기 힘든 ``SyntaxError`` 대신 명확한 메시지를 냅니다.
"""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 10)

if sys.version_info < MIN_PYTHON:  # pragma: no cover - 낮은 버전에서만 실행
    raise RuntimeError(
        f"pykorail 은 파이썬 {'.'.join(map(str, MIN_PYTHON))} 이상이 필요합니다 "
        f"(현재 {'.'.join(map(str, sys.version_info[:3]))})."
    )
