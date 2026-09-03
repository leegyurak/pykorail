"""테스트 코드 자체의 규약을 강제합니다.

두 가지를 봅니다.

1. **제어 흐름 금지** — 테스트에 분기·반복이 들어가면 "무엇이 검증됐는지"가 실행
   경로에 따라 달라져서, 통과해도 무엇을 통과한 건지 알 수 없게 됩니다. 케이스가
   여러 개면 :func:`pytest.mark.parametrize` 로 펼쳐 실패한 케이스가 이름으로
   드러나게 하세요.

2. **Given–When–Then** — 준비·실행·검증의 경계를 주석으로 명시합니다. 경계가
   보이면 "무엇을 하다가 무엇이 깨졌는지"를 읽는 사람이 바로 압니다.

컴프리헨션은 값을 뽑아내는 **식**이라 허용합니다 (``[s.name for s in stations]``).
금지 대상은 제어 흐름 **문**(``if`` / ``for`` / ``while``)입니다.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
TEST_FILES = sorted(TESTS_DIR.glob("test_*.py"))
BANNED = (ast.If, ast.For, ast.While, ast.AsyncFor)

GIVEN = re.compile(r"^\s*#\s*given\b", re.I)
WHEN = re.compile(r"^\s*#.*\bwhen\b", re.I)
THEN = re.compile(r"^\s*#.*\bthen\b", re.I)


def _parse(path: Path) -> tuple[ast.Module, list[str]]:
    source = path.read_text(encoding="utf-8")
    return ast.parse(source), source.splitlines()


def _test_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]


def control_flow_violations(path: Path) -> list[str]:
    """파일 안의 제어 흐름 문 위치를 모읍니다."""
    tree, _ = _parse(path)
    return [f"{path.name}:{node.lineno} {type(node).__name__}" for node in ast.walk(tree) if isinstance(node, BANNED)]


def gwt_violations(path: Path) -> list[str]:
    """Given–When–Then 주석이 빠진 테스트를 모읍니다.

    ``# when`` 과 ``# then`` 은 모든 테스트에 있어야 합니다. ``# given`` 은 실행
    전에 준비할 코드가 있을 때만 필요합니다 — 준비가 없는데 빈 Given 을 두면
    잡음일 뿐입니다. 예외 검증처럼 실행과 검증이 한 덩어리면 ``# when & then``
    처럼 한 줄로 묶어도 됩니다.
    """
    tree, lines = _parse(path)
    violations: list[str] = []

    def body_lines(fn: ast.FunctionDef) -> list[str]:
        end = fn.end_lineno or fn.lineno
        return lines[fn.lineno - 1 : end]

    def first_marker_line(fn: ast.FunctionDef, pattern: re.Pattern[str]) -> int | None:
        matches = [i for i, line in enumerate(body_lines(fn), fn.lineno) if pattern.match(line)]
        return matches[0] if matches else None

    def first_statement_line(fn: ast.FunctionDef) -> int:
        # 독스트링은 준비 코드가 아닙니다.
        statements = [
            node
            for node in fn.body
            if not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
        ]
        return statements[0].lineno if statements else fn.lineno

    checked = [(fn, first_marker_line(fn, WHEN), first_marker_line(fn, THEN)) for fn in _test_functions(tree)]

    violations.extend(f"{path.name}:{fn.lineno} {fn.name} — '# when' 없음" for fn, when, _ in checked if when is None)
    violations.extend(f"{path.name}:{fn.lineno} {fn.name} — '# then' 없음" for fn, _, then in checked if then is None)
    violations.extend(
        f"{path.name}:{fn.lineno} {fn.name} — '# then' 이 '# when' 보다 앞에 있음"
        for fn, when, then in checked
        if when is not None and then is not None and then < when
    )
    violations.extend(
        f"{path.name}:{fn.lineno} {fn.name} — 준비 코드가 있는데 '# given' 없음"
        for fn, when, _ in checked
        if when is not None and first_statement_line(fn) < when and first_marker_line(fn, GIVEN) is None
    )
    return sorted(violations)


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_no_control_flow_statements(path: Path) -> None:
    """테스트에는 if/for/while 문을 쓰지 않습니다 — parametrize 로 펼치세요."""
    # given: 이 저장소의 테스트 파일 하나
    # when
    violations = control_flow_violations(path)

    # then
    assert violations == []


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_every_test_follows_given_when_then(path: Path) -> None:
    """모든 테스트는 준비·실행·검증 경계를 주석으로 드러냅니다."""
    # when
    violations = gwt_violations(path)

    # then
    assert violations == []


class TestCheckersActuallyWork:
    """검사기가 조용히 무력화되면 위 두 테스트는 항상 통과합니다."""

    def test_control_flow_checker_catches_an_if(self, tmp_path: Path) -> None:
        # given
        sample = tmp_path / "test_sample.py"
        sample.write_text("def test_f(x):\n    if x:\n        return 1\n    return 0\n", encoding="utf-8")

        # when
        found = control_flow_violations(sample)

        # then
        assert found == ["test_sample.py:2 If"]

    def test_gwt_checker_catches_a_missing_marker(self, tmp_path: Path) -> None:
        # given
        sample = tmp_path / "test_sample.py"
        sample.write_text("def test_f():\n    assert True\n", encoding="utf-8")

        # when
        found = gwt_violations(sample)

        # then
        assert found == [
            "test_sample.py:1 test_f — '# then' 없음",
            "test_sample.py:1 test_f — '# when' 없음",
        ]

    def test_gwt_checker_requires_given_when_there_is_setup(self, tmp_path: Path) -> None:
        # given
        sample = tmp_path / "test_sample.py"
        sample.write_text(
            "def test_f():\n    value = 1\n\n    # when\n    result = value + 1\n\n    # then\n    assert result\n",
            encoding="utf-8",
        )

        # when
        found = gwt_violations(sample)

        # then
        assert found == ["test_sample.py:1 test_f — 준비 코드가 있는데 '# given' 없음"]

    def test_gwt_checker_accepts_a_combined_marker(self, tmp_path: Path) -> None:
        # given
        sample = tmp_path / "test_sample.py"
        sample.write_text("def test_f():\n    # when & then\n    assert True\n", encoding="utf-8")

        # when
        found = gwt_violations(sample)

        # then
        assert found == []


def test_every_test_file_is_checked() -> None:
    # when
    count = len(TEST_FILES)

    # then
    assert count >= 10
