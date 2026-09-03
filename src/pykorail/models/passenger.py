"""승객 유형과 할인 구분.

승객은 "유형 + 할인 + 등록카드"가 같으면 하나로 합쳐 보냅니다 — 코레일 폼이
승객 블록을 인덱스로 받기 때문에, 같은 조건을 두 블록으로 쪼개 보낼 이유가
없습니다. :meth:`Passenger.reduce` 가 그 합치기를 합니다.
"""

from __future__ import annotations

from functools import reduce as _reduce
from itertools import groupby
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Sequence


class Passenger:
    """승객 묶음 한 종류. 직접 쓰지 말고 하위 타입을 쓰세요.

    하위 타입은 ``TYPE_CODE`` 와 ``DEFAULT_DISCOUNT`` 만 채웁니다 — 생성자
    시그니처가 계층 전체에서 같아야 :meth:`reduce` 가 합칠 때 같은 방식으로
    다시 만들 수 있습니다.
    """

    #: 코레일 승객 유형 코드 (``txtPsgTpCd``). 1=어른, 3=어린이 계열.
    TYPE_CODE: ClassVar[str] = "1"
    #: 유형별 기본 할인 코드 (``txtDiscKndCd``).
    DEFAULT_DISCOUNT: ClassVar[str] = "000"

    def __init__(
        self,
        count: int = 1,
        discount_type: str | None = None,
        card: str = "",
        card_no: str = "",
        card_pw: str = "",
    ) -> None:
        self.count = count
        self.discount_type = self.DEFAULT_DISCOUNT if discount_type is None else discount_type
        self.card = card
        self.card_no = card_no
        self.card_pw = card_pw

    @property
    def typecode(self) -> str:
        return self.TYPE_CODE

    def group_key(self) -> str:
        """합칠 수 있는 승객끼리 같아지는 키."""
        return f"{self.typecode}_{self.discount_type}_{self.card}_{self.card_no}_{self.card_pw}"

    @staticmethod
    def reduce(passengers: Sequence[Passenger]) -> list[Passenger]:
        """같은 조건의 승객을 합치고, 인원이 0 이하인 항목은 버립니다.

        ``itertools.groupby`` 는 **연속된** 같은 키만 묶으므로 먼저 키로 정렬합니다 —
        정렬 없이는 ``[어른, 어린이, 어른]`` 이 어른 블록 두 개로 나가 버립니다.

        ``list`` 가 아니라 ``Sequence`` 를 받는 것은 의도적입니다. ``list`` 는 불변
        (invariant)이라 ``[AdultPassenger(2)]`` 처럼 한 종류만 담은 리스트를 넘기면
        타입 검사에서 걸립니다 — 가장 흔한 호출 형태가 막히면 안 됩니다.
        """
        if not all(isinstance(passenger, Passenger) for passenger in passengers):
            raise TypeError("Passengers must be based on Passenger")

        merged = [
            _reduce(lambda a, b: a + b, group)
            for _, group in groupby(sorted(passengers, key=lambda p: p.group_key()), key=lambda p: p.group_key())
        ]
        return [passenger for passenger in merged if passenger.count > 0]

    def __add__(self, other: Passenger) -> Passenger:
        if not isinstance(other, self.__class__):
            raise TypeError("Cannot add different passenger types")
        if self.group_key() != other.group_key():
            raise TypeError(
                f"Cannot add passengers with different group keys: {self.group_key()} vs {other.group_key()}"
            )
        return self.__class__(
            count=self.count + other.count,
            discount_type=self.discount_type,
            card=self.card,
            card_no=self.card_no,
            card_pw=self.card_pw,
        )

    def get_dict(self, index: int) -> dict[str, Any]:
        """예매 폼에 실을 인덱스별 승객 필드."""
        return {
            f"txtPsgTpCd{index}": self.typecode,
            f"txtDiscKndCd{index}": self.discount_type,
            f"txtCompaCnt{index}": self.count,
            f"txtCardCode_{index}": self.card,
            f"txtCardNo_{index}": self.card_no,
            f"txtCardPw_{index}": self.card_pw,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(count={self.count}, discount_type={self.discount_type!r})"


class AdultPassenger(Passenger):
    """어른."""

    TYPE_CODE = "1"
    DEFAULT_DISCOUNT = "000"


class ChildPassenger(Passenger):
    """어린이."""

    TYPE_CODE = "3"
    DEFAULT_DISCOUNT = "000"


class ToddlerPassenger(Passenger):
    """유아."""

    TYPE_CODE = "3"
    DEFAULT_DISCOUNT = "321"


class SeniorPassenger(Passenger):
    """경로."""

    TYPE_CODE = "1"
    DEFAULT_DISCOUNT = "131"


class Disability1To3Passenger(Passenger):
    """중증 장애인 (1~3급)."""

    TYPE_CODE = "1"
    DEFAULT_DISCOUNT = "111"


class Disability4To6Passenger(Passenger):
    """경증 장애인 (4~6급)."""

    TYPE_CODE = "1"
    DEFAULT_DISCOUNT = "112"
