"""코레일 응답 코드(``h_msg_cd``)에 대응하는 구체 예외들.

새 코드를 다룰 때는 :class:`~pykorail.exceptions.base.KorailError` 를 상속하고
``codes``·``default_msg`` 만 채우면 됩니다 — :func:`error_for_code` 가 서브클래스
트리를 훑어 자동으로 찾아가므로 등록 테이블을 따로 손댈 필요가 없습니다.
"""

from __future__ import annotations

from pykorail.exceptions.base import KorailError


class NeedToLoginError(KorailError):
    """세션이 없거나 만료됐습니다. :meth:`~pykorail.client.Korail.login` 을 다시 호출하세요."""

    codes = frozenset({"P058"})
    default_msg = "Need to Login"


class NoResultsError(KorailError):
    """조건에 맞는 열차·예약·승차권이 없습니다."""

    codes = frozenset({"P100", "WRG000000", "WRD000061", "WRT300005"})
    default_msg = "No Results"


class SoldOutError(KorailError):
    """좌석이 매진됐습니다."""

    codes = frozenset({"IRT010110", "ERR211161"})
    default_msg = "Sold out"


class LoginFailedError(KorailError):
    """로그인 준비 단계(비밀번호 암호화 키 발급)가 실패했습니다.

    응답 코드로 승격되는 타입이 아니라 클라이언트가 직접 던집니다.
    """

    default_msg = "Failed to fetch the password encryption key"


def _coded_subclasses(root: type[KorailError]) -> list[type[KorailError]]:
    """``codes`` 가 비어 있지 않은 :class:`KorailError` 하위 타입을 깊이 우선으로 모읍니다."""
    found: list[type[KorailError]] = []
    for subclass in root.__subclasses__():
        if subclass.codes:
            found.append(subclass)
        found.extend(_coded_subclasses(subclass))
    return found


def error_for_code(code: str | None, msg: str | None = None) -> KorailError:
    """응답 코드를 가장 구체적인 예외 인스턴스로 바꿉니다.

    매칭되는 코드가 없으면 서버 메시지를 담은 :class:`KorailError` 를 돌려줍니다.
    반환만 하고 raise 하지 않으므로 호출부에서 ``raise error_for_code(...)`` 하세요.
    """
    if code is not None:
        for error_type in _coded_subclasses(KorailError):
            if code in error_type.codes:
                return error_type(code=code)
    return KorailError(msg, code)
