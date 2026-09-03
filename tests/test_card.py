"""결제 수단 값 객체."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from pykorail.models import Card

VALID: dict[str, Any] = {
    "number": "1234567812345678",
    "password": "12",
    "verify_number": "900101",
    "expire": "2812",
}


def card_with(**overrides: Any) -> Card:
    """유효한 카드 위에 필드를 덮어써 만듭니다.

    일부러 잘못된 타입을 넣는 테스트가 있어 ``Any`` 로 받습니다 — 정적 검사가
    런타임 가드 테스트를 막으면 안 됩니다.
    """
    merged: dict[str, Any] = {**VALID, **overrides}
    return Card(**merged)


class TestConstruction:
    def test_builds_from_keywords(self) -> None:
        # when
        card = card_with()

        # then
        assert card.number == "1234567812345678"
        assert card.installment == 0
        assert card.is_corporate is False

    def test_is_frozen(self) -> None:
        # given
        card = card_with()

        # when & then
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(card, "number", "9999")  # noqa: B010 — 정적 검사를 통과시키려는 의도적 우회

    def test_equality_is_by_value(self) -> None:
        # when
        first, second = card_with(), card_with()

        # then
        assert first == second


class TestAuthType:
    def test_individual_by_default(self) -> None:
        # when
        auth_type = card_with().auth_type

        # then
        assert auth_type == "J"

    def test_corporate(self) -> None:
        # given
        card = card_with(is_corporate=True)

        # when
        auth_type = card.auth_type

        # then
        assert auth_type == "S"


class TestValidation:
    @pytest.mark.parametrize("field", ["number", "password", "verify_number", "expire"])
    def test_rejects_empty_fields(self, field: str) -> None:
        # when & then
        with pytest.raises(ValueError, match=field):
            card_with(**{field: ""})

    @pytest.mark.parametrize("field", ["number", "password", "verify_number", "expire"])
    def test_rejects_non_string_fields(self, field: str) -> None:
        """앞자리 0 이 의미를 가지므로 정수를 받으면 안 됩니다."""
        # when & then
        with pytest.raises(ValueError, match=field):
            card_with(**{field: 1234})

    def test_rejects_negative_installment(self) -> None:
        # when & then
        with pytest.raises(ValueError, match="installment"):
            card_with(installment=-1)

    def test_accepts_leading_zero_expire(self) -> None:
        # when
        card = card_with(expire="0412")

        # then
        assert card.expire == "0412"


class TestRepr:
    def test_masks_the_card_number(self) -> None:
        """트레이스백·로그에 카드번호 전체가 찍히면 안 됩니다."""
        # given
        card = card_with()

        # when
        rendered = repr(card)

        # then
        assert "1234567812345678" not in rendered
        assert "****5678" in rendered

    def test_never_shows_the_verify_number(self) -> None:
        # given
        card = card_with()

        # when
        rendered = repr(card)

        # then
        assert "900101" not in rendered

    def test_short_number_is_fully_masked(self) -> None:
        # given
        card = card_with(number="12")

        # when
        rendered = repr(card)

        # then
        assert "****" in rendered
