# 에이전트 설정 지도

이 저장소는 다섯 개 코딩 에이전트를 지원합니다. **규범은 루트의 `AGENTS.md` 하나**
이고, 각 도구는 자기 진입점에서 거기로 수렴합니다. 규칙을 바꿀 때는 `AGENTS.md` 를
고치세요 — 아래 파일들은 도구별 배선일 뿐입니다.

| 도구 | 읽는 것 | 비고 |
| --- | --- | --- |
| **Codex** | `AGENTS.md` + `.agents/skills/`<sup>※</sup> | 문서상 cwd 에서 저장소 루트까지 거슬러 올라가며 `.agents/skills` 를 스캔합니다 |
| **Claude Code** | `CLAUDE.md` → `@AGENTS.md` + `.claude/skills/` | `.claude/agents/` 서브에이전트. **이 저장소에서 실제로 확인된 유일한 조합입니다.** |
| **Pi** | `AGENTS.md` + `.agents/skills/`<sup>※</sup> | |
| **Cursor** | `.cursor/rules/*.mdc` (+ 스킬<sup>※</sup>) | 글롭 범위별 규칙 4개 (아래 참조) |
| **OpenCode** | `AGENTS.md` + `.opencode/agents/` (+ 스킬<sup>※</sup>) | 서브에이전트는 OpenCode 프론트매터 스키마 |

<sup>※</sup> **미검증.** `SKILL.md` 는 2025-12 에 공개된 열린 표준이고 표준 문서상
Codex · Cursor · OpenCode · Gemini CLI 등이 같은 형식을 읽습니다. 다만 **이
저장소에서 Claude Code 외의 도구로 실제 로드를 확인한 적은 없습니다.** 표준을
믿고 스킬 하나만 두되, 특정 도구에서 반드시 적용돼야 하는 규칙이라면 그 도구의
전용 진입점(예: Cursor 의 `.cursor/rules/`)에도 두세요.

그래서 도구별로 스킬을 복제하지는 않습니다. 복제가 필요한 것은 프론트매터 스키마가
다른 `.opencode/agents/` 의 서브에이전트와, 자체 포맷인 `.cursor/rules/` 뿐입니다.

## 파일 배치

```
AGENTS.md                       ← 규범 (Codex · Pi · OpenCode 가 직접 읽음)
CLAUDE.md                       ← @AGENTS.md 임포트 + Claude 전용 안내

.claude/
├── agents/                     ← Claude Code 서브에이전트
│   ├── architecture-guard.md
│   ├── wire-parity-auditor.md
│   └── test-author.md
└── skills/                     ← 스킬 원본 (다섯 도구 공용, SKILL.md 표준)
    ├── verify/SKILL.md
    ├── add-endpoint/SKILL.md
    ├── add-error-code/SKILL.md
    └── commit/SKILL.md          ← Cursor 용 사본이 .cursor/rules/commit.mdc 에도

.agents/
├── README.md                   ← 이 파일
└── skills → ../.claude/skills  ← 심볼릭 링크 (Codex·Pi 가 .agents/skills 를 읽음)

.opencode/agents/               ← 같은 서브에이전트, OpenCode 스키마
├── architecture-guard.md
├── wire-parity-auditor.md
└── test-author.md

.cursor/rules/
├── architecture.mdc            ← alwaysApply: true
├── commit.mdc                  ← alwaysApply: true
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
- **commit** — 커밋 메시지·PR 제목·브랜치 이름 규약(`ADD:`·`FIX:`·`REF:`·`DEL:`·
  `DOCS:`·`UPT:`), 경계 판단 기준, 릴리스 노트 라벨 대응

## 유지보수

- **규칙을 바꾸려면 `AGENTS.md`.** 다섯 도구가 전부 따라옵니다 (Cursor 는
  `.cursor/rules/` 도 함께 손봐야 합니다 — 자체 포맷이라 임포트가 안 됩니다).
- **서브에이전트를 바꾸면 `.claude/agents/` 와 `.opencode/agents/` 를 함께**
  고치세요. 본문은 같아야 합니다.
- **스킬은 `.claude/skills/` 한 곳만** 고치면 됩니다 — Codex·Pi 는 `.agents/skills`
  심볼릭 링크로 같은 파일을 봅니다. 심볼릭 링크를 지원하지 않는 환경(일부 Windows
  체크아웃)에서는 그쪽 스킬 탐색만 조용히 비고 `AGENTS.md` 는 그대로 동작합니다.
- **`AGENTS.md` 에 절을 추가하면 Cursor 도 보게 할지 판단하세요.** 글롭에 매이는
  규칙은 기존 `.mdc` 에 넣고, 글롭과 무관하고 항상 지켜야 하는 절차(커밋 규약 등)는
  `alwaysApply: true` 인 `.mdc` 를 새로 만듭니다. Cursor 는 `AGENTS.md` 도
  `.claude/skills/` 도 읽지 않으므로, 복제하지 않으면 **Cursor 만 그 규칙을
  모릅니다.**
- **규범을 스킬로 옮길지 판단하는 기준**: 항상 알아야 하는 것(계층 규칙, 외부 API
  불변식)은 `AGENTS.md`, **특정 작업을 할 때만** 필요한 절차(커밋 쓰기, 엔드포인트
  추가)는 스킬입니다. `AGENTS.md` 는 매 세션 컨텍스트에 통째로 올라가지만 스킬은
  필요할 때만 열립니다.
