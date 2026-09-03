# 에이전트 설정 지도

이 저장소는 다섯 개 코딩 에이전트를 지원합니다. **규범은 루트의 `AGENTS.md` 하나**
이고, 각 도구는 자기 진입점에서 거기로 수렴합니다. 규칙을 바꿀 때는 `AGENTS.md` 를
고치세요 — 아래 파일들은 도구별 배선일 뿐입니다.

| 도구 | 읽는 것 | 비고 |
| --- | --- | --- |
| **Codex** | `AGENTS.md` | 루트 파일을 그대로 읽습니다. 추가 설정 없음. |
| **Claude Code** | `CLAUDE.md` → `@AGENTS.md` | `.claude/agents/` 서브에이전트, `.claude/skills/` 스킬 |
| **Pi** | `AGENTS.md` | `.agents/skills` → `.claude/skills` 심볼릭 링크로 스킬 공유 |
| **Cursor** | `.cursor/rules/*.mdc` | 글롭 범위별 규칙 3개 (아래 참조) |
| **OpenCode** | `AGENTS.md` + `.opencode/agents/` | 서브에이전트는 OpenCode 프론트매터 스키마 |

## 파일 배치

```
AGENTS.md                       ← 규범 (Codex · Pi · OpenCode 가 직접 읽음)
CLAUDE.md                       ← @AGENTS.md 임포트 + Claude 전용 안내

.claude/
├── agents/                     ← Claude Code 서브에이전트
│   ├── architecture-guard.md
│   ├── wire-parity-auditor.md
│   └── test-author.md
└── skills/                     ← 스킬 원본 (Claude Code + Pi 공용)
    ├── verify/SKILL.md
    ├── add-endpoint/SKILL.md
    └── add-error-code/SKILL.md

.agents/
├── README.md                   ← 이 파일
└── skills → ../.claude/skills  ← 심볼릭 링크 (Pi 가 .agents/skills 를 읽음)

.opencode/agents/               ← 같은 서브에이전트, OpenCode 스키마
├── architecture-guard.md
├── wire-parity-auditor.md
└── test-author.md

.cursor/rules/
├── architecture.mdc            ← alwaysApply: true
├── python-style.mdc            ← globs: src/**/*.py
└── testing.mdc                 ← globs: tests/**/*.py
```

## 서브에이전트

세 개 모두 Claude Code(`.claude/agents/`)와 OpenCode(`.opencode/agents/`)에 같은
내용으로 존재합니다. 본문은 동일하고 프론트매터 스키마만 다릅니다.

- **architecture-guard** (읽기 전용) — 계층 위반, 클라이언트에 붙은 엔드포인트,
  가변 모델, 잘못된 상속. `resources/`·`models/`·`client.py`·`api.py` 수정 후.
- **wire-parity-auditor** (읽기 전용) — 요청 페이로드가 그대로인지 증명.
  `constants.py`·`auth/`·`crypto.py`·폼 필드를 건드렸다면 **반드시**.
- **test-author** (쓰기 가능) — 규약에 맞는 pytest 작성. 커버리지가 90% 아래로
  떨어졌을 때.

## 스킬

- **verify** — 전체 게이트 실행 + 실패 진단
- **add-endpoint** — 새 코레일 엔드포인트를 상수→모델→리소스→테스트로 붙이는 절차
- **add-error-code** — 새 응답 코드를 예외 계층에 매핑
- **address-review** — PR 리뷰를 끝까지 처리: CI·리뷰 대기 → 반영 판단 → 답글 →
  resolve (미해결 스레드가 있으면 머지 버튼이 잠깁니다)

## 유지보수

- **규칙을 바꾸려면 `AGENTS.md`.** 다섯 도구가 전부 따라옵니다 (Cursor 는
  `.cursor/rules/` 도 함께 손봐야 합니다 — 자체 포맷이라 임포트가 안 됩니다).
- **서브에이전트를 바꾸면 `.claude/agents/` 와 `.opencode/agents/` 를 함께**
  고치세요. 본문은 같아야 합니다.
- **스킬은 `.claude/skills/` 한 곳만** 고치면 됩니다 — Pi 는 심볼릭 링크로 봅니다.
  심볼릭 링크를 지원하지 않는 환경(일부 Windows 체크아웃)에서는 Pi 의 스킬 탐색만
  조용히 비고, `AGENTS.md` 는 그대로 동작합니다.
