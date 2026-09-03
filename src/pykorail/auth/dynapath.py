"""DynaPath 요청 서명 (``x-dynapath-m-token``).

코레일 앱이 예매 계열 엔드포인트에 붙이는 무결성 토큰을 재현합니다. 알고리즘은
앱에서 그대로 옮긴 것이라 **바이트 단위로 같아야** 서버가 받아 줍니다 — 변수
이름은 읽기 좋게 바꿨지만 연산 순서·상수는 손대지 마세요.

토큰이 광고하는 기기(``os=``·``dm=``)는 User-Agent 가 광고하는 기기와 반드시
같아야 합니다. :class:`~pykorail.client.Korail` 이 같은 프로파일로 둘 다 채웁니다.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, Final

if TYPE_CHECKING:
    from pykorail.device import DeviceProfileLike

#: 인코딩 알파벳. 순서가 곧 알고리즘의 일부입니다.
_TABLE: Final = "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"

_RADIX: Final = 161  # 청크를 하나의 정수로 접을 때의 진법
_MODULUS: Final = 30  # 출력 자릿수 진법 (= 커스텀 테이블 길이)
_CHUNK: Final = 2  # 한 번에 접는 코드포인트 수


class DynaPathMasterEngine:
    """DynaPath 토큰 생성기.

    인스턴스 하나가 "앱 실행 한 번"에 대응합니다 — 생성 시각을 ``it=`` 필드로
    서명에 담기 때문에, 세션마다 새로 만들지 말고 클라이언트와 수명을 맞추세요.
    """

    APP_ID: ClassVar[str] = "com.korail.talk"
    AS_VALUE: ClassVar[str] = "%5B38ff229cb34c7dda8e28220a2d750cce%5D"
    DEVICE_MODEL: ClassVar[str] = "SM-S928N"
    OS_VERSION: ClassVar[str] = "13"
    OS_TYPE: ClassVar[str] = "Android"
    SDK_VERSION: ClassVar[str] = "v1"

    def __init__(self, device_model: str | None = None, os_version: str | None = None) -> None:
        self.app_start_ts = str(int(time.time() * 1000))
        # 기본값을 클래스 상수와 같게 둬 미주입 시 서명이 바이트 단위로 동일합니다.
        self.device_model = device_model or self.DEVICE_MODEL
        self.os_version = os_version or self.OS_VERSION

    @classmethod
    def from_profile(cls, profile: DeviceProfileLike | None) -> DynaPathMasterEngine:
        """기기 프로파일로 엔진을 만듭니다. ``None`` 이면 클래스 기본값을 씁니다."""
        if profile is None:
            return cls()
        return cls(device_model=profile.model, os_version=profile.android)

    # ------------------------------------------------------------ 인코딩 원시연산
    @staticmethod
    def _to_code_units(data: str) -> list[int]:
        """문자열을 앱 고유의 가변길이 7비트 코드 유닛으로 펼칩니다.

        UTF-8 이 아닙니다 — 연속 바이트가 7비트를 쓰고 선행 바이트의 상위 비트
        패턴도 다릅니다. 서로게이트(0xD800~0xDFFF)는 앱과 마찬가지로 버립니다.
        """
        result: list[int] = []
        for char in data:
            cp = ord(char)
            if cp < 128:
                result.append(cp)
            elif cp < 2048:
                result.append(128 | ((cp >> 7) & 15))
                result.append(cp & 127)
            elif cp >= 262144:
                result.append(160)
                result.append((cp >> 14) & 127)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
            elif (63488 & cp) != 55296:
                result.append(((cp >> 14) & 15) | 144)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
        return result

    @staticmethod
    def _derive_key(key_str: str) -> int:
        """키 문자열을 커스텀 테이블 셔플에 쓸 큰 정수로 접습니다.

        각 문자마다 최상위 세트 비트를 찾아 그 두 배를 진법으로 삼습니다.
        코드포인트가 0 이면 16 회 탐색이 모두 실패해 진법이 0 이 되고 누산값이
        초기화되는데, 앱과 동작을 맞추기 위해 그대로 둡니다.
        """
        accumulator = 0
        for char in key_str:
            cp = ord(char)
            high_bit = 32768
            for _ in range(16):
                if (high_bit & cp) != 0:
                    break
                high_bit >>= 1
            accumulator = (accumulator * (high_bit << 1)) + cp
        return accumulator

    @staticmethod
    def _pick_unused_char(base_table: str, position: int, used: str) -> str:
        """``used`` 에 아직 없는 문자 중 ``position`` 번째를 고릅니다."""
        seen = 0
        for char in base_table:
            if char not in used:
                if seen == position:
                    return char
                seen += 1
        return " "

    @classmethod
    def _build_table(cls, seed: int, size: int, base_table: str) -> str:
        """``seed`` 로 ``base_table`` 에서 길이 ``size`` 의 커스텀 알파벳을 뽑습니다.

        팩토리얼 진법(Lehmer code) 방식이라 같은 seed 는 항상 같은 알파벳을 냅니다.
        """
        picked = ""
        remaining = seed
        for i in range(size):
            divisor = size - i
            picked += cls._pick_unused_char(base_table, remaining % divisor, picked)
            remaining //= divisor
        return picked

    @classmethod
    def _encode(cls, data: str, table: str) -> str:
        """코드 유닛을 ``_CHUNK`` 개씩 묶어 ``_MODULUS`` 진수 자릿수로 펼칩니다."""
        units = cls._to_code_units(data)
        out: list[str] = []
        digits = [0] * (_CHUNK + 1)

        idx = 0
        tail = len(units) % _CHUNK
        body_end = len(units) - tail

        while idx < body_end:
            value = 0
            for _ in range(_CHUNK):
                value = (value * _RADIX) + units[idx]
                idx += 1
            for i in range(_CHUNK + 1):
                digits[i] = value % _MODULUS
                value //= _MODULUS
            for i in range(_CHUNK, -1, -1):
                out.append(table[digits[i]])

        if tail > 0:
            value = 0
            for _ in range(tail):
                value = (value * _RADIX) + units[idx]
                idx += 1
            for i in range(tail + 1):
                digits[i] = value % _MODULUS
                value //= _MODULUS
            for i in range(tail, -1, -1):
                out.append(table[digits[i]])

        return "".join(out)

    # ------------------------------------------------------------------- 공개 API
    def generate_token(self, device_id: str, ts: int, rand: str) -> str:
        """``x-dynapath-m-token`` 헤더 값을 만듭니다.

        Args:
            device_id: 앱이 들고 다니는 기기 식별자.
            ts: 요청 시각 (epoch 밀리초).
            rand: 요청마다 새로 뽑는 4자 영대문자·숫자 논스.
        """
        payload = (
            f"ai={self.APP_ID}&di={device_id}&as={self.AS_VALUE}&"
            f"su=false&dbg=false&emu=false&hk=false&it={self.app_start_ts}&"
            f"ts={ts}&rt=0&os={self.os_version}&dm={self.device_model}&st={self.OS_TYPE}&sv={self.SDK_VERSION}"
        )

        dyn_key = f"{self.SDK_VERSION}+{rand}+{ts}"
        key_part = self._encode(dyn_key, _TABLE)
        custom_table = self._build_table(self._derive_key(dyn_key), _MODULUS, _TABLE)
        body_part = self._encode(payload, custom_table)
        return f"bEeEP{_TABLE[len(key_part)]}{key_part}{body_part}"
