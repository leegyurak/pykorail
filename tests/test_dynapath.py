"""DynaPath 서명 회귀 테스트.

토큰은 서버가 바이트 단위로 검증하므로, 알고리즘이 조금이라도 달라지면 로그인이
통째로 막힙니다. 고정 입력에 대한 골든 값을 박아 두고 리팩터링 사고를 잡습니다.
"""

from __future__ import annotations

import pytest

from pykorail.auth.dynapath import _TABLE, DynaPathMasterEngine
from pykorail.device import DeviceProfile


@pytest.fixture
def engine() -> DynaPathMasterEngine:
    engine = DynaPathMasterEngine()
    # 생성 시각이 서명에 들어가므로 고정해야 결과가 재현됩니다.
    engine.app_start_ts = "1700000000000"
    return engine


def test_token_is_stable_for_fixed_input(engine: DynaPathMasterEngine) -> None:
    # when
    first = engine.generate_token("558a4f02041657ea", 1700000001234, "AB12")
    second = engine.generate_token("558a4f02041657ea", 1700000001234, "AB12")

    # then
    assert first == second
    # 원본 구현(ktx.py)이 같은 입력에 대해 내놓던 값 그대로입니다.
    assert first == (
        "bEeEPSYj1Dm5CMM4Pv4ff4GR4GR4GR4GDK3FFmJaRyn3PkmGmvPkqJaRPyD3wdPv1f5G4wMCMfmudCEaGPGGPmGldCMG41Gf513"
        "Pff3myw5mug4CRCn9JlJC1vJdD4nnJEv4uYmRfGkgJE9JgqCMKJl44uGCMYf5d3kg4mPPvv4uCJkg4al4mPPvv4uC4133kg4mPP"
        "vv4uC4YYyndJa133Mf5v3lJGllGPfGPfGPfGPfGPfG4j3jymknCjdGPfGPfGPfGlPC1vf5F3lJG4jPkMmknCDk4nCynDvlFa5mC"
        "nfvkj3YKmkMPd33qq4jwf5dY1CYD5"
    )


def test_token_prefix_and_length_marker(engine: DynaPathMasterEngine) -> None:
    """토큰은 ``bEeEP`` + 키 길이를 나타내는 테이블 문자로 시작합니다."""
    # when
    token = engine.generate_token("558a4f02041657ea", 1700000001234, "AB12")

    # then
    assert token.startswith("bEeEP")
    length_marker = token[5]
    assert length_marker in _TABLE
    # 마커가 가리키는 길이만큼이 키 파트, 나머지가 본문 파트입니다.
    assert len(token) > 6 + _TABLE.index(length_marker)


def test_nonce_changes_the_token(engine: DynaPathMasterEngine) -> None:
    # when
    first = engine.generate_token("dev", 1700000001234, "AAAA")
    second = engine.generate_token("dev", 1700000001234, "BBBB")

    # then
    assert first != second


def test_timestamp_changes_the_token(engine: DynaPathMasterEngine) -> None:
    # when
    first = engine.generate_token("dev", 1700000001234, "AAAA")
    second = engine.generate_token("dev", 1700000009999, "AAAA")

    # then
    assert first != second


def test_default_engine_signs_as_the_documented_device() -> None:
    # when
    engine = DynaPathMasterEngine()

    # then
    assert engine.device_model == "SM-S928N"
    assert engine.os_version == "13"


def test_profile_drives_the_signature() -> None:
    # given
    profile = DeviceProfile(
        id="s21-a15",
        marketing="Galaxy S21",
        model="SM-G991N",
        android="15",
        build_id="AP3A.240905.015.A2",
    )

    # when
    engine = DynaPathMasterEngine.from_profile(profile)

    # then
    assert engine.device_model == "SM-G991N"
    assert engine.os_version == "15"


def test_from_profile_without_profile_matches_defaults() -> None:
    """프로파일 미주입 시 서명은 기본 엔진과 동일해야 합니다."""
    # given
    injected = DynaPathMasterEngine.from_profile(None)
    default = DynaPathMasterEngine()
    injected.app_start_ts = default.app_start_ts = "1700000000000"

    # when
    from_injected = injected.generate_token("dev", 1700000001234, "AAAA")
    from_default = default.generate_token("dev", 1700000001234, "AAAA")

    # then
    assert from_injected == from_default


def test_encode_handles_empty_input() -> None:
    # when
    encoded = DynaPathMasterEngine._encode("", _TABLE)

    # then
    assert encoded == ""


def test_encode_handles_multibyte_input() -> None:
    """한글은 3바이트 경로를 타므로 인코딩이 죽지 않는지 확인합니다."""
    # when
    encoded = DynaPathMasterEngine._encode("서울역", _TABLE)

    # then
    assert encoded


def test_build_table_produces_a_permutation() -> None:
    # when
    table = DynaPathMasterEngine._build_table(123456789, 30, _TABLE)

    # then
    assert len(table) == 30
    assert len(set(table)) == 30, "커스텀 테이블에 중복 문자가 있으면 디코딩이 깨집니다"
    assert set(table) <= set(_TABLE)
