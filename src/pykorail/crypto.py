"""앱이 쓰는 대칭키 원시연산.

전부 앱 동작을 그대로 옮긴 것입니다 — 이중 base64 나 개행 접미사처럼 어색해
보이는 부분도 서버가 그 형태를 기대하므로 손대지 마세요.
"""

from __future__ import annotations

import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def encrypt_sid(device: str, ts: int, key: bytes) -> str:
    """``Sid`` 폼 필드 값을 만듭니다.

    키를 IV 로 재사용하는 AES-CBC 입니다(앱과 동일). 결과 끝의 개행도 앱이 보내는
    그대로이므로 유지합니다.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv=key)
    ciphertext = cipher.encrypt(pad(f"{device}{ts}".encode(), 16))
    return base64.b64encode(ciphertext).decode("utf-8") + "\n"


def encrypt_password(password: str, key: str) -> str:
    """로그인 비밀번호를 서버가 발급한 1회용 키로 암호화합니다.

    키 문자열이 그대로 AES 키이고 그 앞 16바이트가 IV 입니다. base64 를 두 번
    씌우는 것도 앱 동작 그대로입니다.
    """
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, key[:16].encode("utf-8"))
    ciphertext = cipher.encrypt(pad(password.encode("utf-8"), AES.block_size))
    return base64.b64encode(base64.b64encode(ciphertext)).decode("utf-8")
