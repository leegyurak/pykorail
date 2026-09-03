"""문서가 코드와 어긋나지 않는지 지킵니다.

`docs/reference.md` 는 API 표면 전체를, `README.md` 는 사용자가 처음 보는 것들을
담당합니다. 문장까지 검사하지는 않고, **이름과 숫자**처럼 틀리면 사용자가 바로
헛짚게 되는 것만 봅니다.
"""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path
from typing import Any

import pytest

import pykorail
from pykorail.client import Korail
from pykorail.device import DEVICE_PROFILES
from pykorail.exceptions import KorailError
from pykorail.exceptions.api import _coded_subclasses
from pykorail.models import Card, Passenger, Reservation, Seat, Station, Ticket, Train
from pykorail.options import ReserveOption, TrainType
from pykorail.resources import ReservationResource, StationResource, TicketResource, TrainResource

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
REFERENCE = (ROOT / "docs/reference.md").read_text(encoding="utf-8")
DOCS = README + REFERENCE

PASSENGER_TYPES = [
    "AdultPassenger",
    "ChildPassenger",
    "ToddlerPassenger",
    "SeniorPassenger",
    "Disability1To3Passenger",
    "Disability4To6Passenger",
]


def public_methods(cls: type) -> list[str]:
    return [n for n, _ in inspect.getmembers(cls, inspect.isfunction) if not n.startswith("_")]


class TestExports:
    @pytest.mark.parametrize("name", sorted(n for n in pykorail.__all__ if not n.startswith("__")))
    def test_every_export_is_documented(self, name: str) -> None:
        """공개 심볼은 문서 어딘가에 나와야 합니다 (던더는 제외)."""
        # when & then
        assert name in DOCS


class TestResourceMethods:
    @pytest.mark.parametrize(
        ("resource", "prefix"),
        [
            (StationResource, "korail.stations"),
            (TrainResource, "korail.trains"),
            (ReservationResource, "korail.reservations"),
            (TicketResource, "korail.tickets"),
        ],
        ids=lambda v: v if isinstance(v, str) else v.__name__,
    )
    def test_resource_section_exists(self, resource: type, prefix: str) -> None:
        # when & then
        assert f"### `{prefix}`" in REFERENCE

    @pytest.mark.parametrize(
        "method",
        sorted(
            set(public_methods(StationResource))
            | set(public_methods(TrainResource))
            | set(public_methods(ReservationResource))
            | set(public_methods(TicketResource))
        ),
    )
    def test_every_resource_method_is_documented(self, method: str) -> None:
        # when & then — 표에서는 `all(...)`, 시그니처 블록에서는 `search(` 로 나옵니다.
        assert f"{method}(" in REFERENCE

    @pytest.mark.parametrize("method", sorted(public_methods(Korail)))
    def test_every_client_method_is_documented(self, method: str) -> None:
        # when & then
        assert f"`{method}(" in REFERENCE


class TestModelFields:
    @pytest.mark.parametrize(
        ("model", "fields"),
        [
            (Card, ["number", "password", "verify_number", "expire", "installment", "is_corporate"]),
            (Station, ["code", "name", "latitude", "longitude", "group", "major"]),
            (Seat, ["car", "seat", "seat_type", "passenger_type", "price", "original_price", "discount"]),
            (Reservation, ["train", "rsv_id", "price", "seat_no_count", "seats", "wct_no"]),
            (Ticket, ["train", "seat_no", "car_no", "price", "pnr_no"]),
            (Train, ["train_no", "train_type", "run_date", "wait_reserve_flag"]),
        ],
        ids=lambda v: v if isinstance(v, str) else getattr(v, "__name__", "fields"),
    )
    def test_documented_fields_exist_on_the_model(self, model: Any, fields: list[str]) -> None:
        """문서가 설명하는 필드가 실제로 있어야 합니다 (반대 방향 드리프트 방지)."""
        # when
        actual = {f.name for f in dataclasses.fields(model)}

        # then
        assert set(fields) <= actual

    @pytest.mark.parametrize("model", [Card, Station, Seat, Reservation, Ticket, Train])
    def test_model_has_a_section(self, model: type) -> None:
        # when & then
        assert f"### `{model.__name__}`" in REFERENCE


class TestOptionCodes:
    @pytest.mark.parametrize("name", sorted(n for n in vars(TrainType) if not n.startswith("_")))
    def test_train_type_constant_is_documented(self, name: str) -> None:
        # when & then
        assert f"`{name}`" in REFERENCE

    @pytest.mark.parametrize("name", sorted(n for n in vars(TrainType) if not n.startswith("_")))
    def test_train_type_code_is_documented(self, name: str) -> None:
        # when & then
        assert f"| `{getattr(TrainType, name)}` |" in REFERENCE

    @pytest.mark.parametrize("name", sorted(n for n in vars(ReserveOption) if not n.startswith("_")))
    def test_reserve_option_is_documented(self, name: str) -> None:
        # when & then
        assert f"`{name}`" in REFERENCE


class TestPassengerTable:
    @pytest.mark.parametrize("name", PASSENGER_TYPES)
    def test_passenger_class_is_documented(self, name: str) -> None:
        # when & then
        assert f"`{name}`" in REFERENCE

    @pytest.mark.parametrize("name", PASSENGER_TYPES)
    def test_passenger_codes_match_the_table(self, name: str) -> None:
        # given
        cls = getattr(pykorail, name)

        # when
        row = next(line for line in REFERENCE.splitlines() if line.startswith(f"| `{name}` |"))

        # then
        assert f"`{cls.TYPE_CODE}`" in row
        assert f"`{cls.DEFAULT_DISCOUNT}`" in row


class TestErrorCodes:
    @pytest.mark.parametrize(
        "error_type",
        sorted(_coded_subclasses(KorailError), key=lambda e: e.__name__),
        ids=lambda e: e.__name__,
    )
    def test_every_mapped_code_is_documented(self, error_type: type[KorailError]) -> None:
        """예외 트리에 적힌 코드가 실제 매핑과 같아야 합니다."""
        # given
        line = next(ln for ln in REFERENCE.splitlines() if f"{error_type.__name__} " in ln and "──" in ln)

        # when
        missing = [code for code in sorted(error_type.codes) if code not in line]

        # then
        assert missing == []


class TestFacts:
    def test_station_count(self) -> None:
        """281개는 실측값입니다. 바뀌면 문서도 바뀌어야 합니다."""
        # when & then
        assert "281개" in REFERENCE

    def test_device_catalog_size(self) -> None:
        # when & then
        assert f"{len(DEVICE_PROFILES)}개" in REFERENCE

    def test_first_profile_example_is_accurate(self) -> None:
        # given
        first = DEVICE_PROFILES[0]

        # when & then
        assert f"id='{first.id}'" in REFERENCE
        assert f"model='{first.model}'" in REFERENCE
        assert f"build_id='{first.build_id}'" in REFERENCE

    def test_python_floor(self) -> None:
        # given
        from pykorail._compat import MIN_PYTHON

        # when & then
        assert f"파이썬 {'.'.join(map(str, MIN_PYTHON))} 이상" in README

    def test_passenger_signature_defaults_match(self) -> None:
        """문서가 보여주는 기본값이 실제 시그니처와 같아야 합니다."""
        # when
        params = inspect.signature(Passenger.__init__).parameters

        # then
        assert params["count"].default == 1
        assert params["discount_type"].default is None
        assert "count=1" in REFERENCE
        assert "discount_type=None" in REFERENCE


class TestReadmeShape:
    """README 는 "처음 보는 사람" 용입니다 — 길어지면 레퍼런스로 보내세요."""

    def test_links_to_the_reference(self) -> None:
        # when & then
        assert "docs/reference.md" in README

    def test_stays_short(self) -> None:
        """레퍼런스가 다시 README 로 새어 들어오는 것을 막습니다."""
        # when
        length = len(README.splitlines())

        # then
        assert length < 260, "레퍼런스성 내용은 docs/reference.md 로 옮기세요"

    def test_shows_install_and_usage_early(self) -> None:
        """설치와 첫 예제가 첫 화면 안에 있어야 합니다."""
        # when
        head = "\n".join(README.splitlines()[:40])

        # then
        assert "pip install pykorail" in head
        assert "korail.trains.search" in head

    def test_has_no_table_of_contents(self) -> None:
        """목차가 필요할 만큼 길면 이미 너무 깁니다."""
        # when & then
        assert "## 목차" not in README
