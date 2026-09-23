---
name: tech-blog-healthcheck
description: 어제 오후와 오늘 새벽 회차가 정상이었는지 매일 오전 9시에 한 번 점검한다
---

기술 블로그 자동 작성 루틴이 정상 동작했는지 점검한다. **점검만 하고 고치지 않는다.**

## 점검 대상 — 루틴 4개

| 작업 | 시각 | 편수 |
|---|---|---|
| `tech-blog-daily` | 07:00 · 12:00 · 19:00 · 23:00 | 회차당 3편 |
| `tech-blog-exam` | 02:00 · 15:00 | 회차당 단답형 2편 또는 논술형 1편 |
| `tech-blog-concept` | 04:00 · 17:00 | 회차당 2편 |

**하루 총 22편.** 오전 9시에 확인하는 시점에서는 **어제 12·15·17·19·23시**와
**오늘 2·4·7시** 회차가 모두 끝나 있어야 한다. 여덟 회차다.

저장소: `D:\workspace\claude\tech_blog` (origin: https://github.com/SSongGY/tech-blog)

## 절차

### 1. 실행 이력 확인

`mcp__scheduled-tasks__list_scheduled_tasks`로 네 작업의 `enabled`·`nextRunAt`·`lastRunAt`을 본다.
**돌아온 taskId 목록과 `automation/scheduled-tasks/`의 파일 목록이 같은지도 본다.**
어느 한쪽에만 있으면 보고한다 — 작업을 지웠는데 사본이 남았거나, 사본만 있고
등록이 안 된 것이다. `tasks-diff`는 파일만 비교해서 이 경우를 잡지 못한다.
`mcp__scheduled-tasks__list_task_runs`를 `tech-blog-daily`, `tech-blog-exam`,
`tech-blog-concept` **각각에 대해** 호출한다.

| 상황 | 판단 |
|---|---|
| 최근 회차가 전부 `succeeded` | 정상. 3번으로 결과 확인 |
| `status: running` | 회차가 2시간 넘게 돌고 있으면 **문제.** 멈췄을 수 있다고 보고 |
| `status: failed` | **문제.** error 내용과 함께 보고 |
| `enabled: false` | **문제.** 작업이 꺼져 있다고 보고 |
| `tech-blog-daily` 마지막 실행이 **10시간** 넘게 없음 | **문제.** 회차를 건너뛰었다고 보고 |
| `exam`·`concept` 마지막 실행이 **15시간** 넘게 없음 | **문제.** 하루 2회이므로 한 회차를 빠뜨린 것 |
| `nextRunAt`이 **모레 이후** | 확인 필요. 아래 주의를 먼저 읽는다 |

앱이 꺼져 있어 밀린 정도는 문제로 보지 않되, 위 한계를 넘으면 알린다.

**`nextRunAt` 하나로 판단하지 않는다.** 이 값은 이미 예약에 걸린 이번 차례가 아니라
**그 다음 차례**를 가리킬 때가 있다. 예약 시각 직전에 보면 내일 날짜로 보이므로,
그것만 보고 건너뛰었다고 판단하면 틀린다. **`lastRunAt`을 함께 본다.**
수동 실행도 그날의 예약 실행을 막지 않는다 — 둘 다 돈다.

### 2. 아직 실행 중이면

저장소 파일을 **절대 건드리지 않는다.** 진행 상황만 읽는다.

```bash
python scripts/blog.py recent 6
```

`<- 뼈대만` 표시가 붙은 글은 아직 본문이 없다. 2시간 넘게 그대로면 멈춘 것으로 보고한다.
`find -exec`는 쓰지 않는다 — 임의 명령을 실행하는 구문이라 권한 프롬프트에서 멈춘다.

### 3. 끝났으면 결과 확인

```bash
cd /d/workspace/claude/tech_blog
python scripts/blog.py lint
python scripts/blog.py status
python scripts/blog.py exam-status
python scripts/blog.py tasks-diff
git log --oneline -12
git status --short
git rev-parse HEAD origin/main
```

확인할 것:

- `lint`에 `[NG]`가 있으면 **문제.** 어느 글의 어떤 항목인지 보고
- `tasks-diff`가 `[다름]`·`[없음]`·`[사본없음]`을 내면 **문제.** 스케줄 작업과
  `automation/scheduled-tasks/`의 사본이 어긋난 것이다. 어느 작업인지 보고한다.
  **직접 맞추지 않는다** — 어느 쪽이 맞는지는 사용자가 정한다
- 워킹트리에 커밋 안 된 변경이 남아 있으면 **문제**
- `HEAD`와 `origin/main` 해시가 다르면 **푸시가 안 된 것.** 문제로 보고
- 최근 24시간 글이 **9편보다 적으면** 그 사실과 회차별 편수를 보고
- 트랙별 `todo` 잔량이 `low_watermark`(10) 이하인 트랙이 있으면 알려준다.
  **`basics`를 특히 본다** — 표준 SQL 기본 문법은 실제로 유한해서 가장 먼저 마른다
- `exam-status`에 `skipped`가 늘었으면 어느 문제를 왜 건너뛰었는지 알려준다
- `verification: manual-only` 글이 쌓여 있으면 편수를 알려준다

### 4. 보고

**문제가 없으면 한 줄로 끝낸다.** 예: `정상 — 어제 12·15·17·19·23시와 오늘 2·4·7시 회차 모두 완료, 22편, lint 통과, 푸시됨`

여기에 쓴 글 제목만 덧붙인다. 사용자가 무엇이 쌓였는지 알 수 있게.

문제가 있을 때만 자세히 쓴다.
- 무엇이 잘못됐는지
- 마지막 정상 회차가 언제였는지
- 확인해 볼 지점 (직접 고치지는 않는다)

## 하지 말 것

- **저장소를 고치지 않는다.** 커밋·푸시·파일 수정·`git add` 전부 금지
- 다른 루틴이 `running`이면 저장소 파일을 읽기만 한다
- 스케줄 작업을 끄거나 고치지 않는다
- 글을 대신 써주지 않는다
- 원격 DB에 접속하지 않는다

읽기만 한다. 고치는 판단은 사용자가 한다.

윈도우 콘솔에서 한글이 깨지면 명령 앞에 `PYTHONUTF8=1`을 붙인다.

## 명령 실행 규칙

- **Bash 도구로 실행한다.** PowerShell 도구는 허용 규칙이 없어 전부 물어본다
- **`cd`로 작업 폴더를 옮기지 않는다.** 이미 저장소 루트에서 시작한다
- **명령 앞에 환경변수나 변수 할당을 붙이지 않는다.** 규칙이 맨 앞부분으로 맞춰 본다
- **`python -c`로 즉석 코드를 짜지 않는다.** 필요한 일은 `blog.py`에 명령이 있다.
  PDF 본문은 `python scripts/blog.py pdf-text <경로> --find <검색어>`
- `for`·`while` 루프, `sleep` 대기, `find -exec`, 서브셸, `xargs`,
  명령 치환 `$(...)` 을 쓰지 않는다. 다른 회차를 기다려야 하면
  `mcp__scheduled-tasks__list_task_runs` 를 다시 부른다
