"""결제 수단.

카드 정보를 낱개 인자로 흩뿌리지 않고 한 값 객체로 묶습니다 — 결제는 인자 순서를
잘못 넣으면 조용히 실패하거나 엉뚱한 승인이 나는 경로라, 이름으로 묶어 두는 편이
안전합니다.
"""

from __future__ import annotations

from dataclasses import dataclass

#: 결제 인증 구분 코드 (``hidAthnDvCd1``).
_INDIVIDUAL = "J"
_CORPORATE = "S"


@dataclass(frozen=True)
class Card:
    """결제에 쓸 신용카드.

    ``expire`` 와 ``verify_number`` 는 앞자리 0 이 의미를 가지므로 **문자열**입니다
    (``"0412"`` 를 정수로 넘기면 ``412`` 가 됩니다).

    ::

        card = Card(number="1234567812345678", password="12", verify_number="900101", expire="2812")
        korail.reservations.pay(reservation, card)
    """

    #: 카드번호 (하이픈 없이).
    number: str
    #: 카드 비밀번호 앞 2자리.
    password: str
    #: 소유자 확인번호. 개인카드면 생년월일 ``YYMMDD``, 법인카드면 사업자등록번호.
    verify_number: str
    #: 유효기간 ``YYMM``.
    expire: str
    #: 할부 개월. 0 이면 일시불.
    installment: int = 0
    #: 법인카드 여부.
    is_corporate: bool = False

    def __post_init__(self) -> None:
        for field, value in (
            ("number", self.number),
            ("password", self.password),
            ("verify_number", self.verify_number),
            ("expire", self.expire),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"Card.{field} 는 비어 있지 않은 문자열이어야 합니다")
        if self.installment < 0:
            raise ValueError("Card.installment 는 0 이상이어야 합니다")

    @property
    def auth_type(self) -> str:
        """서버 인증 구분 코드 (``S``=법인 / ``J``=개인)."""
        return _CORPORATE if self.is_corporate else _INDIVIDUAL

    def __repr__(self) -> str:
        """카드번호는 뒤 4자리만 남깁니다 — 로그·트레이스백에 전체가 찍히면 안 됩니다."""
        masked = f"****{self.number[-4:]}" if len(self.number) >= 4 else "****"
        return f"Card(number={masked!r}, installment={self.installment}, is_corporate={self.is_corporate})"
