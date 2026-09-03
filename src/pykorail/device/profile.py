"""기기 프로파일 — "폰 한 대"의 신원과 그것을 User-Agent 로 렌더하는 방법."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DeviceProfileLike(Protocol):
    """:class:`DeviceProfile` 이 아니어도 이 세 필드만 있으면 클라이언트에 주입할 수 있습니다.

    읽기 전용 프로퍼티로 선언해 뒀으므로 ``frozen=True`` 데이터클래스도 그대로
    만족합니다. 이미 자기 앱에서 기기 카탈로그를 굴리고 있다면(예: KTX·SRT 를 같이
    다루느라 Chrome 버전까지 들고 있는 프로파일) 그 객체를 변환 없이 넘기면 됩니다.
    """

    @property
    def model(self) -> str:
        """기기 모델명 (예: ``SM-S928N``)."""
        ...

    @property
    def android(self) -> str:
        """안드로이드 메이저 버전 문자열 (예: ``"14"``)."""
        ...

    @property
    def build_id(self) -> str:
        """``ro.build.id`` 값 (예: ``UP1A.231005.007``)."""
        ...


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """이 패키지가 기본 제공하는 기기 프로파일 구현.

    :mod:`pykorail.device.catalog` 가 정합성 제약(버전 ↔ 빌드ID 프리픽스, 모델 ↔
    유효 버전 범위)을 만족하는 조합만 조립해 둡니다. 직접 만들어 써도 되지만,
    실재하지 않는 조합은 그 자체가 탐지 신호가 될 수 있습니다.
    """

    id: str
    marketing: str
    model: str
    android: str
    build_id: str


def dalvik_user_agent(profile: DeviceProfileLike) -> str:
    """기기 프로파일 → 코레일 API 요청에 쓰는 순수 Dalvik User-Agent.

    주의: 실제 코레일 앱(com.korail.talk v7.0.1)은 OkHttp/Retrofit 를 쓰고 UA 를 지정하지
    않아 ``okhttp/<버전>`` 기본값을 보냅니다 — 이 Dalvik UA 를 보내는 게 아닙니다(2026-08
    디컴파일 확인). 그래도 서버가 이 Dalvik 형태를 받아 주므로(korail2 유래의 유효한 위장값)
    그대로 씁니다. **작동하는 UA 는 근거 없이 바꾸지 마세요.**
    ``Dalvik/2.1.0`` 과 ``Linux; U;`` 는 안드로이드 5.0+ 에서 고정이고, 안드로이드 버전·모델·
    빌드ID 만 프로파일에서 바뀝니다. 이 값은
    :class:`~pykorail.auth.dynapath.DynaPathMasterEngine` 의 서명(``os=``·``dm=``)과
    반드시 같은 기기를 가리켜야 합니다 — 클라이언트가 같은 프로파일로 둘 다 채웁니다.
    """
    return f"Dalvik/2.1.0 (Linux; U; Android {profile.android}; {profile.model} Build/{profile.build_id})"
