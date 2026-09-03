"""배포 메타데이터 정합성.

버전의 유일한 출처는 **git 태그**입니다 (hatch-vcs). `git tag v0.2.0` 이 곧 0.2.0
릴리스이고, 소스 어디에도 숫자를 적지 않습니다 — 두 곳에 적으면 반드시 어긋납니다.
여기서는 그 구성이 무너지지 않았는지 지킵니다.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import pykorail

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
PYPROJECT_TEXT = PYPROJECT.read_text(encoding="utf-8")


def _project_field(name: str) -> str:
    """``pyproject.toml`` 의 최상위 문자열 필드를 읽습니다.

    ``tomllib`` 은 3.11+ 라 3.10 에서 못 쓰고, 이 하나 때문에 ``tomli`` 를 의존성에
    넣고 싶지도 않아 정규식으로 읽습니다.
    """
    match = re.search(rf'^{name} = "([^"]+)"', PYPROJECT_TEXT, re.M)
    assert match is not None, f"pyproject.toml 에 {name} 이 없습니다"
    return match.group(1)


class TestVersionSource:
    def test_version_is_dynamic(self) -> None:
        """버전을 pyproject 에 하드코딩하면 태그와 어긋납니다."""
        # when & then
        assert 'dynamic = ["version"]' in PYPROJECT_TEXT

    def test_no_hardcoded_version_field(self) -> None:
        # when
        literal = re.search(r'^version = "', PYPROJECT_TEXT, re.M)

        # then
        assert literal is None

    def test_version_comes_from_vcs(self) -> None:
        # when & then
        assert "[tool.hatch.version]" in PYPROJECT_TEXT
        assert 'source = "vcs"' in PYPROJECT_TEXT

    def test_build_requires_hatch_vcs(self) -> None:
        """빌드 백엔드가 태그를 못 읽으면 버전이 0.0.0 으로 나갑니다."""
        # when & then
        assert "hatch-vcs" in PYPROJECT_TEXT

    def test_fallback_exists_for_gitless_builds(self) -> None:
        """소스 tarball·얕은 체크아웃에서도 빌드가 죽지 않아야 합니다."""
        # when & then
        assert "fallback-version" in PYPROJECT_TEXT

    def test_runtime_version_is_resolvable(self) -> None:
        # when & then
        assert pykorail.__version__

    def test_runtime_version_is_pep440(self) -> None:
        """태그가 없는 개발 트리에서는 dev/local 세그먼트가 붙을 수 있습니다."""
        # when & then
        assert re.fullmatch(
            r"\d+\.\d+(\.\d+)?([abc]\d+|rc\d+)?(\.dev\d+)?(\+[\w.]+)?",
            pykorail.__version__,
        ), pykorail.__version__

    def test_source_has_no_version_literal(self) -> None:
        """`__version__ = "0.1.0"` 같은 하드코딩이 되살아나는 것을 막습니다."""
        # given
        init = (Path(__file__).resolve().parent.parent / "src/pykorail/__init__.py").read_text(encoding="utf-8")

        # when
        literal = re.search(r'^__version__ = "', init, re.M)

        # then
        assert literal is None


class TestMetadata:
    def test_name(self) -> None:
        # when
        name = _project_field("name")

        # then
        assert name == "pykorail"

    def test_requires_python_floor_matches_runtime_guard(self) -> None:
        """``requires-python`` 과 ``_compat.MIN_PYTHON`` 이 같은 하한을 말해야 합니다."""
        # given
        from pykorail._compat import MIN_PYTHON

        # when
        declared = _project_field("requires-python")

        # then
        assert declared == ">=" + ".".join(map(str, MIN_PYTHON))

    def test_ruff_target_matches_minimum(self) -> None:
        # given
        from pykorail._compat import MIN_PYTHON

        # when
        target = _project_field("target-version")

        # then
        assert target == "py{}{}".format(*MIN_PYTHON)

    @pytest.mark.parametrize("minor", [10, 11, 12, 13, 14])
    def test_declares_a_classifier_for_each_supported_minor(self, minor: int) -> None:
        """CI 매트릭스와 classifier 가 어긋나면 사용자가 지원 범위를 오해합니다."""
        # when & then
        assert f'"Programming Language :: Python :: 3.{minor}"' in PYPROJECT_TEXT


class TestCoverageGate:
    def test_threshold_is_ninety(self) -> None:
        """커버리지 게이트가 조용히 낮춰지는 것을 막습니다."""
        # when & then
        assert "--cov-fail-under=90" in PYPROJECT_TEXT


class TestWorkflows:
    WORKFLOWS = Path(__file__).resolve().parent.parent / ".github/workflows"

    @pytest.mark.parametrize("name", ["ci.yml", "release.yml"])
    def test_checkout_fetches_tags(self, name: str) -> None:
        """얕은 체크아웃이면 hatch-vcs 가 태그를 못 봐서 0.0.0 이 배포됩니다."""
        # given
        text = (self.WORKFLOWS / name).read_text(encoding="utf-8")

        # when
        checkouts = text.count("actions/checkout@")

        # then
        assert text.count("fetch-depth: 0") == checkouts

    @pytest.mark.parametrize("name", ["ci.yml", "release.yml"])
    def test_matrix_covers_supported_versions(self, name: str) -> None:
        # given
        text = (self.WORKFLOWS / name).read_text(encoding="utf-8")

        # when & then
        assert '"3.10", "3.11", "3.12", "3.13", "3.14"' in text
