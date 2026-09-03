#!/usr/bin/env bash
# main 브랜치 보호 규칙(ruleset)을 적용합니다.
#
#   .github/scripts/setup-branch-protection.sh
#
# 저장소 파일만으로는 머지를 막을 수 없습니다 — 브랜치 보호는 GitHub **저장소 설정**
# 이라 API 로 한 번 켜 줘야 합니다. `.github/CODEOWNERS` 는 "누가 승인해야 하는가" 만
# 정하고, "승인 없이는 못 머지" 는 이 스크립트가 만드는 ruleset 이 강제합니다.
#
# 필요한 것: gh CLI 로그인 + 대상 저장소 admin 권한.
# 여러 번 실행해도 안전합니다 (있으면 갱신).

set -euo pipefail

RULESET_FILE="$(dirname "$0")/../rulesets/main-protection.json"
RULESET_NAME="main protection"

command -v gh >/dev/null || {
  echo "gh CLI 가 필요합니다: https://cli.github.com" >&2
  exit 1
}

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
echo "대상 저장소: $REPO"

# 이름이 같은 ruleset 이 이미 있으면 새로 만들지 않고 갱신합니다.
existing_id="$(
  gh api "repos/$REPO/rulesets" --jq \
    ".[] | select(.name == \"$RULESET_NAME\") | .id" 2>/dev/null || true
)"

if [ -n "$existing_id" ]; then
  echo "기존 ruleset($existing_id) 갱신"
  gh api --method PUT "repos/$REPO/rulesets/$existing_id" --input "$RULESET_FILE" >/dev/null
else
  echo "새 ruleset 생성"
  gh api --method POST "repos/$REPO/rulesets" --input "$RULESET_FILE" >/dev/null
fi

echo
echo "적용된 규칙:"
echo "  · main 은 PR 로만 변경 가능 (직접 푸시 금지)"
echo "  · 승인 1개 이상 + CODEOWNERS(@leegyurak) 승인 필수"
echo "  · 새 커밋이 올라오면 기존 승인 무효화"
echo "  · 마지막 푸시한 사람 외의 승인 필요"
echo "  · 리뷰 코멘트 전부 해결해야 머지 가능"
echo "  · 상태 체크 'ci-ok' 통과 필수 (최신 main 기준)"
echo "  · main 삭제·강제푸시 금지"
echo
echo "참고: 저장소 admin 은 PR 규칙을 우회할 수 있게 열어 뒀습니다"
echo "      (bypass_mode: pull_request). 1인 저장소에서 자기 PR 은 스스로 승인할 수"
echo "      없어 아무것도 머지하지 못하게 되기 때문입니다."
echo "      본인 PR 도 예외 없이 막으려면 main-protection.json 의 bypass_actors 를"
echo "      빈 배열로 바꾸고 다시 실행하세요 — 그 뒤로는 다른 리뷰어가 필요합니다."
