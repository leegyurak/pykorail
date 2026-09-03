"""요청을 보내기 전에 클라이언트가 잡아내는 입력 오류."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from pykorail.exceptions.base import PykorailError

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from datetime import datetime

#: 오타 제안에 쓸 유사도 하한. 낮추면 엉뚱한 역을 권하게 됩니다.
_SUGGESTION_CUTOFF = 0.6
_MAX_SUGGESTIONS = 3


class StationNotFoundError(PykorailError):
    """역 마스터에 없는 역 이름입니다.

    조회를 보내 봐야 빈 결과만 돌아오므로, 요청 전에 막고 오타 후보를 함께 알려
    줍니다. 서버 응답이 아니라 클라이언트 검증이라
    :class:`~pykorail.exceptions.base.KorailError` 가 아닌 형제 타입입니다.
    """

    def __init__(self, names: Sequence[str], known: Collection[str] = ()) -> None:
        #: 찾지 못한 역 이름들. 출발·도착이 둘 다 틀렸으면 둘 다 담깁니다.
        self.names = list(names)
        #: 이름별 오타 후보.
        self.suggestions = {
            name: difflib.get_close_matches(name, known, n=_MAX_SUGGESTIONS, cutoff=_SUGGESTION_CUTOFF)
            for name in self.names
        }
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        parts = []
        for name in self.names:
            candidates = self.suggestions.get(name)
            if candidates:
                parts.append(f"{name!r} (혹시 {', '.join(repr(c) for c in candidates)}?)")
            else:
                parts.append(repr(name))
        return f"존재하지 않는 역입니다: {', '.join(parts)}"


class PastDepartureError(PykorailError):
    """이미 지난 시각으로 열차를 조회했습니다.

    서버는 과거 시각에도 그냥 빈 결과를 주기 때문에, "이미 떠난 열차" 와 "그 시간대에
    열차가 없음" 이 구분되지 않습니다. 취소표를 기다리는 루프가 출발 시각을 넘겨도
    조용히 계속 도는 상황을 막으려고 요청 전에 걸러냅니다.
    """

    def __init__(self, requested: datetime, now: datetime) -> None:
        #: 호출자가 요청한 출발 시각 (KST).
        self.requested = requested
        #: 판정 기준이 된 현재 시각 (KST).
        self.now = now
        super().__init__(
            f"이미 지난 시각으로는 조회할 수 없습니다: "
            f"요청 {requested:%Y-%m-%d %H:%M} · 현재 {now:%Y-%m-%d %H:%M} (KST)"
        )
