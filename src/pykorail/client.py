"""코레일 스마트 예매 클라이언트.

:class:`Korail` 은 세션 수명(로그인·로그아웃·연결)만 책임지고, 실제 엔드포인트는
:mod:`pykorail.resources` 의 리소스들이 나눠 갖습니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorail.api import ApiClient
from pykorail.auth.signer import RequestSigner
from pykorail.constants import (
    API_ENDPOINTS,
    API_KEY,
    APP_VERSION,
    DEFAULT_HEADERS,
    DEVICE,
    EMAIL_REGEX,
    HYPHENLESS_PHONE_REGEX,
    PHONE_NUMBER_REGEX,
)
from pykorail.crypto import encrypt_password
from pykorail.device import dalvik_user_agent
from pykorail.exceptions import LoginFailedError
from pykorail.resources import ReservationResource, StationResource, TicketResource, TrainResource
from pykorail.transport import create_session

if TYPE_CHECKING:
    from types import TracebackType

    from pykorail.device import DeviceProfileLike


class Korail:
    """코레일 스마트 앱 API 를 감싼 동기 클라이언트.

    생성자는 네트워크를 건드리지 않습니다 — 객체를 만드는 일과 로그인하는 일은
    별개입니다. 한 줄로 끝내고 싶으면 :meth:`logged_in` 을 쓰세요::

        with Korail.logged_in("me@example.com", "password") as korail:
            trains = korail.trains.search("서울", "부산")

    또는 명시적으로::

        korail = Korail()
        korail.login("me@example.com", "password")

    ``device_profile`` 을 주입하면 User-Agent 와 DynaPath 서명이 **같은 기기**를
    가리키도록 함께 바뀝니다. 둘 중 하나만 바꾸면 그 불일치가 곧 탐지 신호입니다::

        from pykorail.device import profile_by_id, random_profile

        profile = profile_by_id(saved_id) or random_profile()
        korail = Korail(device_profile=profile)

    Attributes:
        stations: 역 마스터 조회·검증 (:class:`~pykorail.resources.StationResource`).
        trains: 시간표 조회 (:class:`~pykorail.resources.TrainResource`).
        reservations: 예매·결제·취소 (:class:`~pykorail.resources.ReservationResource`).
        tickets: 승차권 조회·환불 (:class:`~pykorail.resources.TicketResource`).
    """

    def __init__(
        self,
        verbose: bool = False,
        device_profile: DeviceProfileLike | None = None,
        validate_stations: bool = True,
    ) -> None:
        # 공유 dict 를 오염시키지 않도록 복사한 뒤 User-Agent 만 갈아 끼웁니다.
        headers = dict(DEFAULT_HEADERS)
        if device_profile is not None:
            headers["User-Agent"] = dalvik_user_agent(device_profile)

        self._api = ApiClient(create_session(headers), RequestSigner(device_profile), verbose)
        self._idx: str | None = None
        self.device_profile = device_profile

        self.stations = StationResource(self._api)
        self.trains = TrainResource(self._api, self.stations, validate_stations)
        self.reservations = ReservationResource(self._api)
        self.tickets = TicketResource(self._api)

    @classmethod
    def logged_in(
        cls,
        korail_id: str,
        korail_pw: str,
        *,
        verbose: bool = False,
        device_profile: DeviceProfileLike | None = None,
        validate_stations: bool = True,
    ) -> Korail:
        """클라이언트를 만들고 곧바로 로그인합니다.

        Raises:
            LoginFailedError: 자격증명이 없거나 암호화 키 발급이 실패했습니다.
            KorailError: 서버가 로그인을 거부했습니다.
        """
        korail = cls(verbose=verbose, device_profile=device_profile, validate_stations=validate_stations)
        try:
            if not korail.login(korail_id, korail_pw):
                raise LoginFailedError("아이디 또는 비밀번호가 올바르지 않습니다")
        except BaseException:
            korail.close()
            raise
        return korail

    # ------------------------------------------------------------- 세션 상태
    @property
    def verbose(self) -> bool:
        return self._api.verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        self._api.verbose = value

    @property
    def logined(self) -> bool:
        return self._api.account.logined

    @property
    def membership_number(self) -> str | None:
        return self._api.account.membership_number

    @property
    def name(self) -> str | None:
        return self._api.account.name

    @property
    def email(self) -> str | None:
        return self._api.account.email

    @property
    def phone_number(self) -> str | None:
        return self._api.account.phone_number

    # ------------------------------------------------------------- 컨텍스트 관리
    def __enter__(self) -> Korail:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """HTTP 연결을 정리합니다. 로그아웃은 하지 않습니다."""
        self._api.close()

    # --------------------------------------------------------------------- 인증
    def _encrypt_password(self, password: str) -> str:
        """서버에서 1회용 암호화 키를 받아 비밀번호를 암호화합니다.

        함께 내려오는 ``idx`` 는 로그인 폼에 되돌려 줘야 하므로 보관합니다.
        """
        payload = self._api.post(API_ENDPOINTS["code"], data={"code": "app.login.cphd"})
        cipher_info = payload.get("app.login.cphd")
        if payload.get("strResult") != "SUCC" or not cipher_info:
            raise LoginFailedError(code=payload.get("h_msg_cd"))

        self._idx = cipher_info["idx"]
        return encrypt_password(password, cipher_info["key"])

    def login(self, korail_id: str, korail_pw: str) -> bool:
        """로그인합니다. 성공하면 ``True``, 자격증명이 틀리면 ``False``.

        Raises:
            LoginFailedError: 아이디/비밀번호가 비었거나 암호화 키 발급이 실패했습니다.
        """
        if not korail_id or not korail_pw:
            raise LoginFailedError("아이디와 비밀번호가 필요합니다")

        # 하이픈 없는 휴대폰 번호는 회원번호로 잘못 조회돼 "비밀번호가 틀렸다"는
        # 엉뚱한 응답을 받습니다. 서버에 보내기 전에 분명하게 알려 줍니다.
        if HYPHENLESS_PHONE_REGEX.match(korail_id):
            hyphenated = f"{korail_id[:3]}-{korail_id[3:-4]}-{korail_id[-4:]}"
            raise LoginFailedError(
                f"휴대폰 번호로 로그인하려면 하이픈을 넣어야 합니다: {korail_id!r} 대신 {hyphenated!r}"
            )

        # 아이디 형태에 따라 서버가 조회할 컬럼이 달라집니다: 5=이메일, 4=휴대폰, 2=회원번호.
        if EMAIL_REGEX.match(korail_id):
            input_flag = "5"
        elif PHONE_NUMBER_REGEX.match(korail_id):
            input_flag = "4"
        else:
            input_flag = "2"

        encrypted_pw = self._encrypt_password(korail_pw)

        url = API_ENDPOINTS["login"]
        headers, sid = self._api.sign(url)
        data = {
            "Device": DEVICE,
            "Version": APP_VERSION,
            "Key": API_KEY,
            "txtMemberNo": korail_id,
            "txtPwd": encrypted_pw,
            "txtInputFlg": input_flag,
            "idx": self._idx,
        }
        if sid:
            data["Sid"] = sid

        payload = self._api.post(url, data=data, headers=headers)
        account = self._api.account

        if payload.get("strResult") == "SUCC" and payload.get("strMbCrdNo"):
            account.logined = True
            account.membership_number = payload["strMbCrdNo"]
            account.name = payload["strCustNm"]
            account.email = payload["strEmailAdr"]
            account.phone_number = payload["strCpNo"]
            return True

        account.clear()
        return False

    def logout(self) -> None:
        """서버 로그인 세션을 끊습니다.

        HTTP 연결은 그대로 둡니다 — 로그아웃은 프로토콜 상태이고 연결은 자원이라
        수명이 다릅니다. 같은 클라이언트로 다른 계정에 다시 로그인하려면 연결이
        살아 있어야 합니다. 연결까지 정리하려면 :meth:`close` 를 부르거나
        ``with`` 문을 쓰세요.
        """
        self._api.get(API_ENDPOINTS["logout"])
        self._api.account.clear()
