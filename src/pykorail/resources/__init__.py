"""리소스 — 엔드포인트를 도메인별로 묶은 API 표면.

:class:`~pykorail.client.Korail` 이 하나씩 들고 있고, 전부 같은
:class:`~pykorail.api.ApiClient` 를 공유해 세션·서명·로그인 상태를 나눠 씁니다::

    korail.stations.list()
    korail.trains.search("서울", "부산")
    korail.reservations.create(train)
    korail.tickets.list()
"""

from __future__ import annotations

from pykorail.resources.base import Resource
from pykorail.resources.reservations import ReservationResource
from pykorail.resources.stations import StationResource
from pykorail.resources.tickets import TicketResource
from pykorail.resources.trains import TrainResource, to_kst

__all__ = [
    "ReservationResource",
    "Resource",
    "StationResource",
    "TicketResource",
    "TrainResource",
    "to_kst",
]
