---
name: address-review
description: PR 에 올라온 Claude 코드 리뷰를 끝까지 처리합니다. CI 와 리뷰가 올라올 때까지 기다렸다가, 지적마다 반영하거나 반영하지 않기로 판단하고, 그 결정을 해당 코멘트의 답글로 달고 resolve 합니다. "리뷰 반영해줘"·"리뷰 처리해줘"·"코멘트 정리해줘" 라고 하거나 PR 을 올린 직후에 사용하세요. resolve 는 REST 로 안 되고 GraphQL 이 필요합니다.
---

# 리뷰 받아서 끝내기

PR 을 올린 다음 **리뷰가 올라올 때까지 기다렸다가, 지적을 하나도 남기지 않고**
처리합니다. 규칙은 단순합니다.

> **반영하든 안 하든, 답글을 달고 resolve 합니다.**
> 답글 없는 resolve 는 기록을 지우는 것이고, resolve 없는 답글은 다음 사람에게
> "아직 처리 중" 으로 보입니다.

`main` 보호 규칙에 `required_review_thread_resolution: true` 가 걸려 있어, 미해결
스레드가 하나라도 있으면 머지 버튼이 잠깁니다.

## 0. 사전 확인

```bash
PR=<번호>
REPO=leegyurak/pykorail
```

리뷰 워크플로가 **이 PR 에서 도는지** 먼저 보세요. `.github/workflows/claude-review.yml`
자체를 고치는 PR 이면 Anthropic 쪽 검증에 걸려 **건너뛰어지고, 그때 잡은 초록불로
뜹니다.** 로그에 `Workflow validation failed` 가 있으면 그 경우이고, 리뷰를 기다려도
오지 않습니다.

## 1. 리뷰가 올라올 때까지 기다리기

CI 통과와 리뷰 게시는 별개입니다. **둘 다** 기다리세요. 리뷰는 몇 분 걸립니다
(이 저장소 실측 약 6~7분).

폴링하지 말고 Monitor 로 걸어 두고 다른 일을 하세요.

```bash
# 모든 체크가 끝날 때까지 — 끝나면 한 줄 나오고 종료합니다
prev=""
for i in $(seq 1 40); do
  s=$(gh pr checks "$PR" --repo "$REPO" --json name,bucket 2>/dev/null || echo '[]')
  cur=$(echo "$s" | jq -r '.[] | select(.bucket!="pending") | "\(.name): \(.bucket)"' | sort)
  comm -13 <(echo "$prev") <(echo "$cur")
  prev=$cur
  echo "$s" | jq -e 'length>0 and all(.bucket!="pending")' >/dev/null && { echo "ALL CHECKS DONE"; break; }
  sleep 20
done
```

체크가 끝나도 인라인 코멘트 게시는 몇 초 늦을 수 있습니다. 스레드가 0건이면 한 번
더 확인하세요.

## 2. 스레드 목록 가져오기

**`resolve` 는 REST API 에 없습니다. GraphQL 만 됩니다.** 그리고 답글을 달 때
쓰는 것은 코멘트 ID 가 아니라 **스레드 ID**(`PRRT_…`) 입니다.

```bash
gh api graphql -f query='
query($o:String!,$r:String!,$p:Int!){
  repository(owner:$o,name:$r){ pullRequest(number:$p){
    reviewThreads(first:50){ nodes{
      id isResolved isOutdated path line
      comments(first:1){ nodes{ author{login} body } } } } } }
}' -f o=leegyurak -f r=pykorail -F p="$PR" \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[]
        | select(.isResolved==false)
        | "\(.id)\t\(.path):\(.line)\t\(.comments.nodes[0].body[0:100]|gsub("\n";" "))"'
```

전문을 읽어야 판단할 수 있습니다. 머리표(`[P1 · 확신 높음]`)만 보고 처리하지
마세요 — 본문에 근거와 제안 코드가 들어 있습니다.

## 3. 지적마다 판단하기

### 먼저 검증하세요 — 동의할 때도, 반대할 때도

리뷰는 **틀릴 수 있습니다.** 그리고 리뷰가 "실행하지 못했다" 고 밝힌 지적은 특히
그렇습니다. 반대로 맞을 때도 많습니다. 어느 쪽이든 **재현해 보고 판단하세요.**

```bash
# 예: 오탐 지적이면 실제로 오탐인지 최소 재현으로 확인
uv run python - <<'PY'
...
PY
```

> ⚠️ **검증 스크립트 자체가 틀릴 수 있습니다.** 이 저장소에서 실제로 있었던 일:
> `Path.write_text` 가 `None` 을 반환한다고 착각해 조건이 항상 거짓이 되는 프로브를
> 짰고, "지적이 전부 틀렸다" 는 잘못된 결론을 냈습니다. **기대값과 실제값을 함께
> 출력**하고, 이미 참인 것을 아는 케이스(대조군)를 하나 넣어 프로브가 살아 있는지
> 확인하세요.

### P1 은 반영이 기본입니다

`P1` 은 "머지되면 깨진다" 는 뜻입니다. 반영하지 않으려면 **깨지지 않는다는 근거**가
있어야 하고, 그 근거를 답글에 적어야 합니다. "나중에 하겠다" 는 P1 에 대한 답이
아닙니다.

`P2`·`P3` 는 반영하지 않아도 됩니다. 다만 **왜** 를 적으세요.

### 반영하지 않는 정당한 이유

- **이 PR 의 범위를 넘습니다.** 별도 PR 로 다루는 게 리뷰를 흐리지 않습니다.
  이때는 후속으로 무엇을 할지 답글에 적으세요.
- **위험을 알고 감수합니다.** 지적이 맞지만 비용 대비 이득이 없다고 판단한 경우.
  **판단 자체를 기록으로 남기는 것**이 이 답글의 요점입니다.
- **지적이 틀렸습니다.** 재현 결과를 답글에 붙이세요.

"사소해서" 는 이유가 아닙니다 — 사소하면 고치는 게 더 쌉니다.

## 4. 반영하기

고치고, **게이트를 통과시키고**, 커밋한 뒤 푸시하세요. 답글에 커밋 해시를 적으려면
커밋이 먼저입니다.

```bash
uv run ruff format && uv run ruff check --fix && uv run ty check && uv run pytest
```

한 지적에 한 커밋일 필요는 없습니다. 관련된 것끼리 묶고 `commit` 스킬의 접두사를
따르세요.

> **고치다가 새 문제를 만들 수 있습니다.** 이 저장소에서 실제로 있었던 일:
> 오탐을 고치려고 위치 제한을 통째로 없앴다가 미탐 회귀를 만들었고, 다음 리뷰가
> 그것을 잡았습니다. **고친 뒤 원래 케이스와 새 케이스를 함께 테스트에 고정**하세요.

## 5. 답글 + resolve

```bash
reply_resolve() {  # $1=스레드ID  $2=본문
  gh api graphql -f query='mutation($t:ID!,$b:String!){
    addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{databaseId}}}' \
    -f t="$1" -f b="$2" --jq '.data.addPullRequestReviewThreadReply.comment.databaseId' >/dev/null
  gh api graphql -f query='mutation($t:ID!){
    resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' \
    -f t="$1" --jq '.data.resolveReviewThread.thread.isResolved'
}

reply_resolve PRRT_xxx '반영했습니다 (`abc1234`). …'
```

답글에 들어가야 하는 것:

| 반영할 때 | 반영 안 할 때 |
| --- | --- |
| 무엇을 어떻게 고쳤는지 | 왜 안 하는지 |
| 커밋 해시 | 감수하는 위험이 무엇인지 |
| 재현·검증 결과 | 후속으로 무엇을 할지 (있다면) |

"수정했습니다" 한 줄만 남기지 마세요. 다음에 이 스레드를 읽는 사람은 diff 를 다시
따라가야 합니다.

**지적이 맞았다면 맞았다고 쓰세요.** 특히 리뷰가 *내가 방금 한 수정*에서 회귀를
잡아냈다면 그렇게 적으세요 — 기록의 값어치는 정확함에서 나옵니다.

## 6. 새 커밋 → 새 리뷰 → 반복

**푸시하면 리뷰가 다시 돕니다.** 새 스레드가 생길 수 있습니다(실제로 생깁니다).
미해결 스레드가 0이 될 때까지 1~5 를 반복하세요.

```bash
gh api graphql -f query='query($o:String!,$r:String!,$p:Int!){
  repository(owner:$o,name:$r){pullRequest(number:$p){
    reviewThreads(first:50){nodes{isResolved}}}}}' \
  -f o=leegyurak -f r=pykorail -F p="$PR" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved==false)]|length'
```

`0` 이 나오면 끝입니다.

## 7. 사용자에게 보고

- 전체 몇 건 중 몇 건을 반영했고 몇 건을 반영하지 않았는지
- **P1 이 남아 있는지** (남아 있으면 머지하면 안 됩니다)
- 반영하지 않은 것들의 이유를 한 줄씩
- 리뷰가 잡아낸 것 중 **실제 버그가 있었다면 그것을 먼저** 말하세요

승인과 머지는 사용자가 합니다. 스레드를 다 정리했다고 머지하지 마세요.

## 하지 말 것

- **답글 없이 resolve.** 기록이 사라집니다.
- **P1 을 근거 없이 미루기.**
- **재현 없이 "지적이 틀렸다" 고 답하기.**
- 리뷰가 지적한 것만 고치고 **같은 종류의 다른 곳을 놔두기** — 한 군데를 지적받았으면
  같은 실수가 다른 데 있는지 보세요.
- 게이트를 안 돌리고 푸시하기.
