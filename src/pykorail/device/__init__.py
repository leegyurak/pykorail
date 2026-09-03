"""기기 프로파일 — 클라이언트에 주입해 User-Agent 와 DynaPath 서명을 함께 바꿉니다.

::

    from pykorail import Korail
    from pykorail.device import profile_by_id, random_profile

    profile = profile_by_id(saved_id) or random_profile()  # 최초 1회만 뽑고 id 를 저장
    korail = Korail("id", "pw", device_profile=profile)
"""

from __future__ import annotations

from pykorail.device.catalog import (
    BUILD_ID,
    CATALOG_SIZE,
    DEVICE_PROFILES,
    PROFILES_BY_ID,
    profile_by_id,
    random_profile,
)
from pykorail.device.profile import DeviceProfile, DeviceProfileLike, dalvik_user_agent

__all__ = [
    "BUILD_ID",
    "CATALOG_SIZE",
    "DEVICE_PROFILES",
    "PROFILES_BY_ID",
    "DeviceProfile",
    "DeviceProfileLike",
    "dalvik_user_agent",
    "profile_by_id",
    "random_profile",
]
