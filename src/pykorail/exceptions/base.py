"""예외 계층의 뿌리."""

from __future__ import annotations


class PykorailError(Exception):
    """이 패키지가 던지는 모든 예외의 최상위 타입.

    호출자가 ``except PykorailError`` 하나로 라이브러리 유래 실패를 전부 잡을 수
    있도록 존재합니다. 직접 raise 하지 말고 하위 타입을 쓰세요.
    """


class KorailError(PykorailError):
    """코레일 API 가 ``strResult=FAIL`` 로 응답했을 때 던집니다.

    서버가 준 메시지(``h_msg_txt``)와 코드(``h_msg_cd``)를 그대로 실어 나릅니다.
    알려진 코드는 :mod:`pykorail.exceptions.api` 의 구체 타입으로 승격되고,
    나머지는 이 타입 그대로 올라옵니다.

    하위 타입은 ``__init__`` 을 덮어쓰지 말고 ``codes`` 와 ``default_msg`` 클래스
    속성만 채우세요. 생성자 시그니처가 계층 전체에서 같아야
    :func:`~pykorail.exceptions.api.error_for_code` 가 균일하게 조립할 수 있습니다.
    """

    #: 이 예외 타입으로 승격할 코레일 응답 코드(``h_msg_cd``).
    codes: frozenset[str] = frozenset()

    #: ``msg`` 를 생략했을 때 쓸 사람이 읽을 설명.
    default_msg: str | None = None

    def __init__(self, msg: str | None = None, code: str | None = None) -> None:
        self.msg = msg if msg is not None else self.default_msg
        self.code = code
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f"{self.msg} ({self.code})"
